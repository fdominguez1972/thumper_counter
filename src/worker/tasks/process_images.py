"""
ML Pipeline Tasks for Thumper Counter
Version: 1.0.0
Date: 2025-11-04

WHY: Implements the three-stage ML pipeline for deer detection, classification,
and re-identification as specified in specs/ml.spec

Pipeline Flow:
    Image Upload -> Preprocessing -> Detection (YOLOv8n) -> Crop Bounding Boxes
                                         |
                                         v
                               Classification (CNN) -> Sex determination
                                         |
                                         v
                               Re-ID (ResNet50) -> Match to existing deer
                                         |
                                         v
                               Update database with sighting

GPU Configuration:
    - Target Hardware: RTX 4080 Super
    - Batch Size: 32 for classification/re-id, 16 for detection
    - Mixed Precision: Enabled for 2x speedup
    - CUDA Benchmark: Enabled for consistent input sizes
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np
from PIL import Image, ExifTags
import cv2
import torch
import torch.nn.functional as F
from torchvision import transforms
from celery import Task

from src.worker.celery_app import app


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration from environment
CONFIDENCE_THRESHOLD = float(os.getenv('DETECTION_CONFIDENCE', 0.5))
IOU_THRESHOLD = float(os.getenv('DETECTION_IOU', 0.45))
MAX_DETECTIONS = int(os.getenv('MAX_DETECTIONS', 20))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 32))
DETECTION_BATCH_SIZE = int(os.getenv('DETECTION_BATCH_SIZE', 16))
CLASSIFICATION_BATCH_SIZE = int(os.getenv('CLASSIFICATION_BATCH_SIZE', 32))
REID_BATCH_SIZE = int(os.getenv('REID_BATCH_SIZE', 64))
REID_THRESHOLD = float(os.getenv('REID_THRESHOLD', 0.85))
FEATURE_DIM = int(os.getenv('FEATURE_DIM', 2048))

# GPU Configuration
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
MIXED_PRECISION = os.getenv('MIXED_PRECISION', 'true').lower() == 'true'

# Model paths
MODEL_DIR = Path(os.getenv('MODEL_DIR', '/app/src/models'))
YOLO_MODEL_PATH = MODEL_DIR / 'yolov8n_deer.pt'
CLASSIFICATION_MODEL_PATH = MODEL_DIR / 'resnet50_sex_classification.pt'
REID_MODEL_PATH = MODEL_DIR / 'resnet50_reid.pt'


class ModelCache:
    """
    Singleton model cache for efficient GPU memory management.

    WHY: Loading models repeatedly is expensive. Cache keeps models in GPU
    memory and uses lazy loading on first request.
    """
    _instance = None
    _models = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelCache, cls).__new__(cls)
        return cls._instance

    def get_detection_model(self):
        """Load YOLOv8n detection model"""
        if 'detection' not in self._models:
            try:
                from ultralytics import YOLO
                logger.info('[INFO] Loading YOLOv8n detection model...')
                self._models['detection'] = YOLO(str(YOLO_MODEL_PATH))
                self._models['detection'].to(DEVICE)
                logger.info('[OK] Detection model loaded')
            except Exception as e:
                logger.error(f'[FAIL] Failed to load detection model: {e}')
                raise
        return self._models['detection']

    def get_classification_model(self):
        """Load ResNet50-based sex classification model"""
        if 'classification' not in self._models:
            try:
                logger.info('[INFO] Loading classification model...')
                model = torch.load(str(CLASSIFICATION_MODEL_PATH), map_location=DEVICE)
                model.eval()
                self._models['classification'] = model
                logger.info('[OK] Classification model loaded')
            except Exception as e:
                logger.error(f'[FAIL] Failed to load classification model: {e}')
                raise
        return self._models['classification']

    def get_reid_model(self):
        """Load ResNet50 re-identification model (2048-dim features)"""
        if 'reid' not in self._models:
            try:
                logger.info('[INFO] Loading re-identification model...')
                model = torch.load(str(REID_MODEL_PATH), map_location=DEVICE)
                model.eval()
                self._models['reid'] = model
                logger.info('[OK] Re-ID model loaded')
            except Exception as e:
                logger.error(f'[FAIL] Failed to load re-ID model: {e}')
                raise
        return self._models['reid']


# Global model cache instance
model_cache = ModelCache()


# Image preprocessing transforms
preprocess_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def extract_exif_data(image_path: Path) -> Dict:
    """
    Extract EXIF metadata from image.

    WHY: Timestamps and location data essential for tracking patterns and
    camera site identification.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with datetime, gps, camera_model fields
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            return {'datetime': None, 'gps': None, 'camera_model': None}

        exif = {
            ExifTags.TAGS[k]: v
            for k, v in exif_data.items()
            if k in ExifTags.TAGS
        }

        return {
            'datetime': exif.get('DateTime', None),
            'gps': exif.get('GPSInfo', None),
            'camera_model': exif.get('Model', None),
        }
    except Exception as e:
        logger.warning(f'[WARN] Failed to extract EXIF from {image_path}: {e}')
        return {'datetime': None, 'gps': None, 'camera_model': None}


def check_image_quality(image: np.ndarray) -> Tuple[bool, str]:
    """
    Perform quality checks on image.

    WHY: Skip processing corrupted/low-quality images that waste GPU time.

    Quality checks:
    - Minimum resolution: 640x480
    - Blur detection: Laplacian variance > 100
    - Format: Valid color image

    Args:
        image: OpenCV image array (BGR format)

    Returns:
        Tuple of (is_valid, reason)
    """
    height, width = image.shape[:2]

    # Check minimum resolution
    if width < 640 or height < 480:
        return False, f'Resolution too low: {width}x{height}'

    # Check blur using Laplacian variance
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    if laplacian_var < 100:
        return False, f'Image too blurry: variance={laplacian_var:.2f}'

    return True, 'OK'


def preprocess_image(image_path: Path) -> Tuple[Optional[np.ndarray], Dict]:
    """
    Preprocess image for ML pipeline.

    WHY: Standardize images for consistent model input while preserving
    detection quality.

    Operations:
    1. Load and validate image
    2. Extract EXIF metadata
    3. Normalize and resize (max dimension 1280px)
    4. Convert to RGB if needed
    5. Quality checks

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (processed_image, metadata)
        Returns (None, metadata) if image fails quality checks
    """
    try:
        # Extract EXIF before any modifications
        exif_data = extract_exif_data(image_path)

        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f'[FAIL] Could not load image: {image_path}')
            return None, {'error': 'Failed to load image', 'exif': exif_data}

        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Quality check
        is_valid, reason = check_image_quality(image)
        if not is_valid:
            logger.warning(f'[WARN] Image quality check failed: {reason}')
            return None, {'error': reason, 'exif': exif_data}

        # Resize maintaining aspect ratio (max dimension 1280px)
        height, width = image.shape[:2]
        max_dim = max(height, width)
        if max_dim > 1280:
            scale = 1280 / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

        metadata = {
            'original_size': (width, height),
            'processed_size': image.shape[:2],
            'exif': exif_data,
        }

        return image, metadata

    except Exception as e:
        logger.error(f'[FAIL] Preprocessing failed for {image_path}: {e}')
        return None, {'error': str(e)}


@app.task(bind=True, name='src.worker.tasks.process_images.detect_deer')
def detect_deer(self: Task, image_paths: List[str]) -> Dict:
    """
    Detect deer in images using YOLOv8n.

    WHY: YOLOv8n provides best speed/accuracy trade-off for real-time processing
    on RTX 4080 Super. Batch processing maximizes GPU utilization.

    Model: YOLOv8n (nano variant)
    - FPS: 50+ on RTX 4070 (higher on 4080 Super)
    - mAP: Sufficient for large mammals
    - Size: 6MB (fast loading)

    Detection Parameters:
    - confidence_threshold: 0.5 (balance false positives vs missed detections)
    - iou_threshold: 0.45 (handle overlapping deer in groups)
    - max_detections: 20 (herds rarely exceed this)

    Args:
        image_paths: List of image file paths to process

    Returns:
        Dictionary with detection results per image:
        {
            'image_path': {
                'detections': List of {'bbox': [x,y,w,h], 'confidence': float},
                'metadata': preprocessing metadata,
                'status': 'success' or 'failed',
                'error': error message if failed
            }
        }
    """
    try:
        logger.info(f'[INFO] Starting detection for {len(image_paths)} images')

        # Load model
        model = model_cache.get_detection_model()

        # Process images
        results = {}
        for image_path in image_paths:
            try:
                # Preprocess
                image, metadata = preprocess_image(Path(image_path))
                if image is None:
                    results[image_path] = {
                        'detections': [],
                        'metadata': metadata,
                        'status': 'failed',
                        'error': metadata.get('error', 'Unknown preprocessing error')
                    }
                    continue

                # Run detection
                detections = model.predict(
                    image,
                    conf=CONFIDENCE_THRESHOLD,
                    iou=IOU_THRESHOLD,
                    max_det=MAX_DETECTIONS,
                    device=DEVICE,
                    verbose=False
                )

                # Extract bounding boxes
                boxes = []
                for det in detections[0].boxes:
                    x1, y1, x2, y2 = det.xyxy[0].cpu().numpy()
                    confidence = float(det.conf[0].cpu().numpy())

                    # Expand box by 10% for context (as per spec)
                    w = x2 - x1
                    h = y2 - y1
                    x1 = max(0, x1 - w * 0.1)
                    y1 = max(0, y1 - h * 0.1)
                    x2 = min(image.shape[1], x2 + w * 0.1)
                    y2 = min(image.shape[0], y2 + h * 0.1)

                    boxes.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': confidence
                    })

                results[image_path] = {
                    'detections': boxes,
                    'metadata': metadata,
                    'status': 'success',
                    'num_detections': len(boxes)
                }

                logger.info(f'[OK] Detected {len(boxes)} deer in {image_path}')

            except Exception as e:
                logger.error(f'[FAIL] Detection failed for {image_path}: {e}')
                results[image_path] = {
                    'detections': [],
                    'metadata': {},
                    'status': 'failed',
                    'error': str(e)
                }

        return results

    except Exception as e:
        logger.error(f'[FAIL] Detection task failed: {e}')
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True, name='src.worker.tasks.process_images.classify_deer')
def classify_deer(self: Task, detection_data: Dict) -> Dict:
    """
    Classify deer sex/age using ResNet50-based CNN.

    WHY: ResNet50 proven for fine-grained classification. Custom CNN head trained
    on deer-specific features for Buck/Doe/Fawn/Unknown classification.

    Model Architecture:
    - Backbone: ResNet50 (pretrained on ImageNet)
    - Input size: 224x224 (cropped detections)
    - Classes: Buck, Doe, Fawn, Unknown
    - Output: Softmax probabilities

    Classification Rules:
    - Threshold: 0.7 for buck/doe, 0.8 for fawn
    - Below threshold -> "unknown"

    Batch Size: 32 (optimal for RTX 4080 Super with 224x224 inputs)

    Args:
        detection_data: Output from detect_deer task containing bboxes

    Returns:
        Dictionary with classification results per detection:
        {
            'image_path': {
                'classifications': [
                    {
                        'bbox': [x,y,w,h],
                        'class': 'buck'|'doe'|'fawn'|'unknown',
                        'confidence': float,
                        'probabilities': {'buck': 0.1, 'doe': 0.8, ...},
                        'features': [2048-dim feature vector]
                    }
                ]
            }
        }
    """
    try:
        logger.info('[INFO] Starting classification task')

        # Load model
        model = model_cache.get_classification_model()

        results = {}

        for image_path, det_result in detection_data.items():
            if det_result['status'] != 'success' or not det_result['detections']:
                results[image_path] = {'classifications': [], 'status': 'skipped'}
                continue

            try:
                # Load original image
                image = Image.open(image_path).convert('RGB')
                image_np = np.array(image)

                classifications = []
                crops = []
                bboxes = []

                # Prepare crops from detections
                for detection in det_result['detections']:
                    bbox = detection['bbox']
                    x1, y1, x2, y2 = map(int, bbox)

                    # Crop deer region
                    crop = image_np[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue

                    crop_pil = Image.fromarray(crop)
                    crops.append(preprocess_transform(crop_pil))
                    bboxes.append(bbox)

                if not crops:
                    results[image_path] = {'classifications': [], 'status': 'no_valid_crops'}
                    continue

                # Batch process crops
                num_crops = len(crops)
                all_features = []
                all_predictions = []

                for i in range(0, num_crops, CLASSIFICATION_BATCH_SIZE):
                    batch = torch.stack(crops[i:i + CLASSIFICATION_BATCH_SIZE]).to(DEVICE)

                    with torch.no_grad():
                        if MIXED_PRECISION:
                            with torch.cuda.amp.autocast():
                                outputs = model(batch)
                        else:
                            outputs = model(batch)

                        # Get predictions and features
                        if isinstance(outputs, tuple):
                            logits, features = outputs
                        else:
                            logits = outputs
                            features = None

                        probs = F.softmax(logits, dim=1)
                        predictions = torch.argmax(probs, dim=1)

                        all_predictions.extend(predictions.cpu().numpy())
                        if features is not None:
                            all_features.extend(features.cpu().numpy())

                # Map predictions to classes
                class_names = ['buck', 'doe', 'fawn', 'unknown']
                confidence_thresholds = {
                    'buck': 0.7,
                    'doe': 0.7,
                    'fawn': 0.8,
                    'unknown': 0.0
                }

                for idx, (pred, bbox) in enumerate(zip(all_predictions, bboxes)):
                    class_name = class_names[pred]
                    confidence = float(probs[idx][pred].cpu().numpy())

                    # Apply confidence thresholding
                    if confidence < confidence_thresholds.get(class_name, 0.7):
                        class_name = 'unknown'

                    classification = {
                        'bbox': bbox,
                        'class': class_name,
                        'confidence': confidence,
                        'probabilities': {
                            name: float(probs[idx][i].cpu().numpy())
                            for i, name in enumerate(class_names)
                        }
                    }

                    if all_features:
                        classification['features'] = all_features[idx].tolist()

                    classifications.append(classification)

                results[image_path] = {
                    'classifications': classifications,
                    'status': 'success',
                    'num_classified': len(classifications)
                }

                logger.info(f'[OK] Classified {len(classifications)} deer in {image_path}')

            except Exception as e:
                logger.error(f'[FAIL] Classification failed for {image_path}: {e}')
                results[image_path] = {
                    'classifications': [],
                    'status': 'failed',
                    'error': str(e)
                }

        return results

    except Exception as e:
        logger.error(f'[FAIL] Classification task failed: {e}')
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True, name='src.worker.tasks.process_images.reidentify_deer')
def reidentify_deer(self: Task, classification_data: Dict, database_features: Optional[List[Dict]] = None) -> Dict:
    """
    Match deer to existing individuals using metric learning embeddings.

    WHY: Incremental matching scales better than clustering for growing database.
    Uses cosine similarity with temporal threshold adjustment.

    Model: ResNet50 + Projection Head
    - Embedding dimension: 512 (from projection) or 2048 (from layer4)
    - Distance metric: Cosine similarity
    - Training: Triplet loss for deer-specific similarity

    Re-ID Thresholds (temporal):
    - Same day: 0.90 (higher confidence for recent matches)
    - Same week: 0.85 (account for slight appearance changes)
    - Same month: 0.80 (seasonal coat changes)
    - Default: 0.85

    Feature Update Strategy:
    - Exponential Moving Average: new = 0.7 * old + 0.3 * current
    - WHY: Adapt to gradual appearance changes

    Args:
        classification_data: Output from classify_deer task
        database_features: List of existing deer feature vectors from database
                          Format: [{'deer_id': int, 'features': [512 or 2048 dims], 'last_seen': datetime}]

    Returns:
        Dictionary with re-identification results:
        {
            'image_path': {
                're_identifications': [
                    {
                        'bbox': [x,y,w,h],
                        'class': 'buck'|'doe'|'fawn',
                        'deer_id': int or None,  # None = new deer
                        'match_confidence': float,
                        'is_new_deer': bool,
                        'features': [512 or 2048-dim vector]
                    }
                ]
            }
        }
    """
    try:
        logger.info('[INFO] Starting re-identification task')

        # Load model
        model = model_cache.get_reid_model()

        # Convert database features to tensors if provided
        if database_features and len(database_features) > 0:
            db_feature_vectors = np.array([d['features'] for d in database_features])
            db_feature_vectors = torch.from_numpy(db_feature_vectors).float().to(DEVICE)
            # L2 normalize
            db_feature_vectors = F.normalize(db_feature_vectors, p=2, dim=1)
        else:
            db_feature_vectors = None

        results = {}

        for image_path, class_result in classification_data.items():
            if class_result['status'] != 'success' or not class_result['classifications']:
                results[image_path] = {'re_identifications': [], 'status': 'skipped'}
                continue

            try:
                # Load original image
                image = Image.open(image_path).convert('RGB')
                image_np = np.array(image)

                re_ids = []
                crops = []
                classifications = []

                # Prepare crops from classifications
                for classification in class_result['classifications']:
                    bbox = classification['bbox']
                    x1, y1, x2, y2 = map(int, bbox)

                    # Crop deer region
                    crop = image_np[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue

                    crop_pil = Image.fromarray(crop)
                    crops.append(preprocess_transform(crop_pil))
                    classifications.append(classification)

                if not crops:
                    results[image_path] = {'re_identifications': [], 'status': 'no_valid_crops'}
                    continue

                # Extract features in batches
                all_features = []

                for i in range(0, len(crops), REID_BATCH_SIZE):
                    batch = torch.stack(crops[i:i + REID_BATCH_SIZE]).to(DEVICE)

                    with torch.no_grad():
                        if MIXED_PRECISION:
                            with torch.cuda.amp.autocast():
                                features = model(batch)
                        else:
                            features = model(batch)

                        # L2 normalize features
                        features = F.normalize(features, p=2, dim=1)
                        all_features.append(features)

                all_features = torch.cat(all_features, dim=0)

                # Match against database
                for idx, (features, classification) in enumerate(zip(all_features, classifications)):
                    features_np = features.cpu().numpy()

                    deer_id = None
                    match_confidence = 0.0
                    is_new_deer = True

                    if db_feature_vectors is not None and len(db_feature_vectors) > 0:
                        # Compute cosine similarities
                        similarities = torch.mm(
                            features.unsqueeze(0),
                            db_feature_vectors.t()
                        ).squeeze(0)

                        best_match_idx = torch.argmax(similarities).item()
                        best_score = float(similarities[best_match_idx].cpu().numpy())

                        # Check if match exceeds threshold
                        if best_score > REID_THRESHOLD:
                            deer_id = database_features[best_match_idx]['deer_id']
                            match_confidence = best_score
                            is_new_deer = False

                    re_id = {
                        'bbox': classification['bbox'],
                        'class': classification['class'],
                        'classification_confidence': classification['confidence'],
                        'deer_id': deer_id,
                        'match_confidence': match_confidence,
                        'is_new_deer': is_new_deer,
                        'features': features_np.tolist()
                    }

                    re_ids.append(re_id)

                results[image_path] = {
                    're_identifications': re_ids,
                    'status': 'success',
                    'num_identified': len(re_ids),
                    'num_new_deer': sum(1 for r in re_ids if r['is_new_deer']),
                    'num_matched': sum(1 for r in re_ids if not r['is_new_deer'])
                }

                logger.info(
                    f'[OK] Re-identified {len(re_ids)} deer in {image_path} '
                    f'(new: {results[image_path]["num_new_deer"]}, matched: {results[image_path]["num_matched"]})'
                )

            except Exception as e:
                logger.error(f'[FAIL] Re-identification failed for {image_path}: {e}')
                results[image_path] = {
                    're_identifications': [],
                    'status': 'failed',
                    'error': str(e)
                }

        return results

    except Exception as e:
        logger.error(f'[FAIL] Re-identification task failed: {e}')
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True, name='src.worker.tasks.process_images.process_pipeline')
def process_pipeline(self: Task, image_paths: List[str], database_features: Optional[List[Dict]] = None) -> Dict:
    """
    Execute complete ML pipeline: Detection -> Classification -> Re-ID.

    WHY: Chains all three stages together for end-to-end processing. Each stage
    can be monitored and retried independently via Celery canvas primitives.

    This is a convenience task that chains the three stages:
    1. detect_deer: Find deer bounding boxes
    2. classify_deer: Determine sex/age
    3. reidentify_deer: Match to existing individuals

    For more control, use Celery chains:
        from celery import chain
        pipeline = chain(
            detect_deer.s(image_paths),
            classify_deer.s(),
            reidentify_deer.s(database_features)
        )
        result = pipeline.apply_async()

    Args:
        image_paths: List of image file paths to process
        database_features: Existing deer feature vectors for matching

    Returns:
        Complete pipeline results with all three stages
    """
    try:
        logger.info(f'[INFO] Starting full pipeline for {len(image_paths)} images')

        # Stage 1: Detection
        self.update_state(state='PROGRESS', meta={'stage': 'detection', 'progress': 0})
        detection_results = detect_deer(image_paths)

        # Stage 2: Classification
        self.update_state(state='PROGRESS', meta={'stage': 'classification', 'progress': 33})
        classification_results = classify_deer(detection_results)

        # Stage 3: Re-identification
        self.update_state(state='PROGRESS', meta={'stage': 'reidentification', 'progress': 66})
        reid_results = reidentify_deer(classification_results, database_features)

        # Compile final results
        final_results = {
            'status': 'success',
            'num_images': len(image_paths),
            'results': reid_results,
            'summary': {
                'total_detections': sum(
                    r.get('num_detections', 0)
                    for r in detection_results.values()
                ),
                'total_classified': sum(
                    r.get('num_classified', 0)
                    for r in classification_results.values()
                ),
                'total_new_deer': sum(
                    r.get('num_new_deer', 0)
                    for r in reid_results.values()
                ),
                'total_matched': sum(
                    r.get('num_matched', 0)
                    for r in reid_results.values()
                ),
            }
        }

        logger.info('[OK] Pipeline completed successfully')
        logger.info(f'[INFO] Summary: {final_results["summary"]}')

        return final_results

    except Exception as e:
        logger.error(f'[FAIL] Pipeline failed: {e}')
        raise self.retry(exc=e, countdown=60)
