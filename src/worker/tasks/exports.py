"""
Export worker tasks for PDF reports and ZIP archives.
Feature: 008-rut-season-analysis
Feature: 010-infrastructure-fixes (Redis status tracking)

Celery tasks for generating downloadable exports with Redis status updates.
"""

import os
import io
import json
import csv
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import redis

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from PIL import Image

from worker.celery_app import celery_app
from backend.models.detection import Detection
from backend.models.image import Image as ImageModel
from backend.core.database import engine
from sqlalchemy.orm import sessionmaker


# Export file storage
EXPORT_DIR = Path("/mnt/exports")
EXPORT_DIR.mkdir(exist_ok=True)

# Redis client for status tracking (Feature 010)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


@celery_app.task(name="worker.tasks.exports.generate_pdf_report_task", bind=True)
def generate_pdf_report_task(self, job_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate PDF report from request configuration.

    Feature 010: Updates job status in Redis with 1-hour TTL.

    Args:
        job_id: Unique job identifier
        request_data: PDFReportRequest data

    Returns:
        dict: Result with file_path, file_size, status
    """
    print(f"[INFO] Starting PDF report generation: job_id={job_id}")

    # Feature 010: Set initial "processing" status in Redis
    key = f"export_job:{job_id}"
    initial_status = {
        "status": "processing",
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat()
    }
    redis_client.setex(key, 3600, json.dumps(initial_status))
    print(f"[INFO] Set initial status in Redis: {key}")

    try:
        # Create PDF file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{job_id}_{timestamp}.pdf"
        file_path = EXPORT_DIR / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Title
        title = request_data.get("title") or f"Seasonal Activity Report"
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C5530'),  # Dark green
            spaceAfter=30,
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))

        # Date range
        start_date = request_data.get("start_date", "N/A")
        end_date = request_data.get("end_date", "N/A")
        date_text = f"<b>Period:</b> {start_date} to {end_date}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 20))

        # Report type and configuration
        report_type = request_data.get("report_type", "seasonal_activity")
        config_text = f"<b>Report Type:</b> {report_type.replace('_', ' ').title()}"
        story.append(Paragraph(config_text, styles['Normal']))
        story.append(Spacer(1, 30))

        # Summary section
        summary_heading = Paragraph("<b>Summary</b>", styles['Heading2'])
        story.append(summary_heading)
        story.append(Spacer(1, 12))

        summary_text = f"""
        This report provides analysis of wildlife activity patterns during the specified period.
        Data includes detection counts, classification breakdowns, and activity trends.
        Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))

        # Placeholder table (in full implementation, populate with real data)
        if request_data.get("include_tables", True):
            table_data = [
                ['Metric', 'Value'],
                ['Report Type', report_type],
                ['Start Date', start_date],
                ['End Date', end_date],
                ['Group By', request_data.get('group_by', 'month')],
            ]

            table = Table(table_data, colWidths=[3 * inch, 3 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
            story.append(Spacer(1, 30))

        # Generated by footer
        footer_text = f"""
        <para align=center>
        Generated with Thumper Counter<br/>
        Deer Tracking System - Rut Season Analysis
        </para>
        """
        story.append(Spacer(1, 40))
        story.append(Paragraph(footer_text, styles['Normal']))

        # Build PDF
        doc.build(story)

        # Get file size
        file_size = file_path.stat().st_size

        print(f"[OK] PDF report generated: {file_path} ({file_size} bytes)")

        # Feature 010: Update status to "completed" in Redis
        completed_status = {
            "status": "completed",
            "job_id": job_id,
            "filename": filename,
            "download_url": f"/api/static/exports/{filename}",
            "file_size_bytes": file_size,
            "created_at": initial_status["created_at"],
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(completed_status))
        print(f"[OK] Updated Redis status to completed: {key}")

        return completed_status

    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        import traceback
        traceback.print_exc()

        # Feature 010: Update status to "failed" in Redis
        failed_status = {
            "status": "failed",
            "job_id": job_id,
            "error": str(e),
            "created_at": initial_status.get("created_at", datetime.utcnow().isoformat()),
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(failed_status))
        print(f"[WARN] Updated Redis status to failed: {key}")

        return failed_status


@celery_app.task(name="worker.tasks.exports.create_zip_archive_task", bind=True)
def create_zip_archive_task(self, job_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create ZIP archive with detection crops and metadata.

    Feature 010: Updates job status in Redis with 1-hour TTL.

    Args:
        job_id: Unique job identifier
        request_data: ZIPExportRequest data

    Returns:
        dict: Result with file_path, file_size, status
    """
    print(f"[INFO] Starting ZIP archive creation: job_id={job_id}")

    # Feature 010: Set initial "processing" status in Redis
    key = f"export_job:{job_id}"
    initial_status = {
        "status": "processing",
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat()
    }
    redis_client.setex(key, 3600, json.dumps(initial_status))
    print(f"[INFO] Set initial status in Redis: {key}")

    try:
        # Create ZIP file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"detections_{job_id}_{timestamp}.zip"
        file_path = EXPORT_DIR / filename

        # Get detection IDs
        detection_ids = request_data.get("detection_ids", [])
        include_crops = request_data.get("include_crops", True)
        include_metadata = request_data.get("include_metadata_csv", True)
        crop_size = request_data.get("crop_size", 300)

        # Create database session
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            # Query detections
            detections = db.query(Detection).filter(
                Detection.id.in_(detection_ids)
            ).all()

            print(f"[INFO] Found {len(detections)} detections to export")

            # Create ZIP archive
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:

                # Add metadata CSV if requested
                if include_metadata:
                    csv_buffer = io.StringIO()
                    csv_writer = csv.writer(csv_buffer)

                    # CSV headers
                    csv_writer.writerow([
                        'detection_id',
                        'image_id',
                        'classification',
                        'confidence',
                        'bbox_x',
                        'bbox_y',
                        'bbox_width',
                        'bbox_height',
                        'deer_id',
                        'created_at'
                    ])

                    # CSV rows
                    for det in detections:
                        bbox = det.bbox or {}
                        final_classification = det.corrected_classification if det.corrected_classification else det.classification

                        csv_writer.writerow([
                            str(det.id),
                            str(det.image_id),
                            final_classification,
                            det.confidence,
                            bbox.get('x', 0),
                            bbox.get('y', 0),
                            bbox.get('width', 0),
                            bbox.get('height', 0),
                            str(det.deer_id) if det.deer_id else '',
                            det.created_at.isoformat() if det.created_at else ''
                        ])

                    # Add CSV to ZIP
                    zipf.writestr('metadata.csv', csv_buffer.getvalue())
                    print(f"[OK] Added metadata.csv with {len(detections)} rows")

                # Add cropped images if requested
                if include_crops:
                    crops_added = 0
                    for i, det in enumerate(detections):
                        # Get image
                        image = db.query(ImageModel).filter(ImageModel.id == det.image_id).first()
                        if not image or not image.path:
                            print(f"[WARN] Image not found for detection {det.id}")
                            continue

                        # Check if image file exists
                        if not os.path.exists(image.path):
                            print(f"[WARN] Image file not found: {image.path}")
                            continue

                        try:
                            # Open image and crop
                            with Image.open(image.path) as img:
                                bbox = det.bbox or {}
                                x = bbox.get('x', 0)
                                y = bbox.get('y', 0)
                                w = bbox.get('width', 0)
                                h = bbox.get('height', 0)

                                # Crop detection
                                crop = img.crop((x, y, x + w, y + h))

                                # Resize if needed
                                if crop_size:
                                    crop.thumbnail((crop_size, crop_size), Image.Resampling.LANCZOS)

                                # Save to buffer
                                img_buffer = io.BytesIO()
                                crop.save(img_buffer, format='JPEG', quality=90)

                                # Add to ZIP
                                crop_filename = f"crops/detection_{det.id}.jpg"
                                zipf.writestr(crop_filename, img_buffer.getvalue())
                                crops_added += 1

                        except Exception as e:
                            print(f"[ERROR] Failed to crop detection {det.id}: {e}")
                            continue

                        # Progress update (every 100 detections)
                        if (i + 1) % 100 == 0:
                            print(f"[INFO] Processed {i + 1}/{len(detections)} detections")

                    print(f"[OK] Added {crops_added} detection crops to ZIP")

        finally:
            db.close()

        # Get file size
        file_size = file_path.stat().st_size

        print(f"[OK] ZIP archive created: {file_path} ({file_size} bytes)")

        # Feature 010: Update status to "completed" in Redis
        completed_status = {
            "status": "completed",
            "job_id": job_id,
            "filename": filename,
            "download_url": f"/api/static/exports/{filename}",
            "file_size_bytes": file_size,
            "created_at": initial_status["created_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "processed_count": len(detections)
        }
        redis_client.setex(key, 3600, json.dumps(completed_status))
        print(f"[OK] Updated Redis status to completed: {key}")

        return completed_status

    except Exception as e:
        print(f"[ERROR] ZIP archive creation failed: {e}")
        import traceback
        traceback.print_exc()

        # Feature 010: Update status to "failed" in Redis
        failed_status = {
            "status": "failed",
            "job_id": job_id,
            "error": str(e),
            "created_at": initial_status.get("created_at", datetime.utcnow().isoformat()),
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(failed_status))
        print(f"[WARN] Updated Redis status to failed: {key}")

        return failed_status
