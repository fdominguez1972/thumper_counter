#!/usr/bin/env python3
"""
Test new buck/doe model on sample images to validate classifications.
"""
import sys
sys.path.insert(0, '/app')

from pathlib import Path
from ultralytics import YOLO
import cv2

# Model paths
NEW_MODEL = "/app/src/models/yolov8n_deer.pt"

# Class mapping for new model
CLASS_NAMES = {
    0: "cattle",
    1: "pig",
    2: "raccoon",
    3: "doe",
    4: "unknown",
    5: "buck"
}

def test_model(image_path: str):
    """Test new model on a single image."""
    print(f"\n[INFO] Testing model on: {image_path}")

    # Load model
    model = YOLO(NEW_MODEL)
    print(f"[OK] Model loaded: {NEW_MODEL}")

    # Run inference
    results = model(image_path, conf=0.25, verbose=False)

    # Display results
    for result in results:
        boxes = result.boxes
        if len(boxes) == 0:
            print("[INFO] No detections found")
            continue

        print(f"[INFO] Found {len(boxes)} detection(s):")
        for i, box in enumerate(boxes):
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = CLASS_NAMES.get(class_id, f"unknown_{class_id}")

            print(f"  Detection {i+1}: {class_name} (class_id={class_id}, conf={confidence:.3f})")

def main():
    """Test on random sample images from database."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import os

    # Connect to database using environment variables
    pg_user = os.getenv('POSTGRES_USER', 'deertrack')
    pg_pass = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
    pg_host = os.getenv('POSTGRES_HOST', 'db')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_db = os.getenv('POSTGRES_DB', 'deer_tracking')

    db_url = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
    print(f"[INFO] Connecting to database at {pg_host}:{pg_port}/{pg_db}")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get 5 random completed images with deer detections
    query = text("""
        SELECT i.path
        FROM images i
        JOIN detections d ON d.image_id = i.id
        WHERE i.processing_status = 'completed'
          AND d.classification IN ('doe', 'unknown', 'mature', 'mid', 'young', 'fawn')
        ORDER BY RANDOM()
        LIMIT 5
    """)

    results = session.execute(query)
    image_paths = [row[0] for row in results]

    if not image_paths:
        print("[WARN] No images found in database")
        return

    print(f"[INFO] Testing new model on {len(image_paths)} sample images")
    print(f"[INFO] Model: {NEW_MODEL}")
    print(f"[INFO] Expected classes: buck (5), doe (3), unknown (4), cattle (0), pig (1), raccoon (2)")

    for path in image_paths:
        test_model(path)

    print("\n[OK] Model testing complete")

if __name__ == "__main__":
    main()
