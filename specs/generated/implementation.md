# Thumper Counter - Implementation Documentation
Generated: Wed Nov  5 00:55:21 CST 2025

## Project Structure
```
Project structure:
./scripts/generate.py
./scripts/ingest_images.py
./scripts/populate_locations.py
./scripts/test_detection.py
./src/backend/__init__.py
./src/backend/api/__init__.py
./src/backend/api/images.py
./src/backend/api/locations.py
./src/backend/app/__init__.py
./src/backend/app/main.py
./src/backend/core/__init__.py
./src/backend/core/database.py
./src/backend/models/__init__.py
./src/backend/models/deer.py
./src/backend/models/detection.py
./src/backend/models/image.py
./src/backend/models/location.py
./src/backend/schemas/__init__.py
./src/backend/schemas/image.py
./src/backend/schemas/location.py
./src/backend/services/__init__.py
./src/worker/__init__.py
./src/worker/celery_app.py
./src/worker/ml/__init__.py
./src/worker/tasks/__init__.py
./src/worker/tasks/process_images.py
./test_db.py
```

## Database Models
Location: src/backend/models/
```python
# File: src/backend/models/__init__.py

# File: src/backend/models/deer.py
class DeerSex(enum.Enum):
class Deer(Base):
    def to_dict(self) -> dict:
    def to_dict_with_features(self) -> dict:
    def is_named(self) -> bool:
    def days_since_last_seen(self) -> int:
    def feature_dimension(self) -> int:
    def update_sighting(self, timestamp: datetime, confidence: float) -> None:
    def set_name(self, name: str) -> None:
    def update_sex(self, new_sex: DeerSex) -> None:
    def cosine_similarity(self, other_vector: List[float]) -> float:
    def get_recent_detections(self, limit: int = 10):
    def get_detection_locations(self, db_session) -> List[dict]:

# File: src/backend/models/detection.py
class Detection(Base):
    def to_dict(self) -> dict:
    def to_dict_with_relations(self) -> dict:
    def is_matched(self) -> bool:
    def bbox_coords(self) -> Tuple[int, int, int, int]:
    def bbox_area(self) -> int:
    def bbox_center(self) -> Tuple[float, float]:
    def set_bbox(self, x: int, y: int, width: int, height: int) -> None:
    def set_bbox_from_yolo(self, x_center: float, y_center: float,
    def get_crop_coordinates(self) -> Tuple[int, int, int, int]:
    def match_to_deer(self, deer_id: uuid.UUID) -> None:
    def unmatch(self) -> None:
    def iou(self, other: "Detection") -> float:
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
    def to_yolo_format(self, img_width: int, img_height: int) -> Tuple[float, float, float, float]:

# File: src/backend/models/image.py
class ProcessingStatus(enum.Enum):
class Image(Base):
    def to_dict(self) -> dict:
    def is_processed(self) -> bool:
    def can_reprocess(self) -> bool:
    def mark_queued(self) -> None:
    def mark_processing(self) -> None:
    def mark_completed(self) -> None:
    def mark_failed(self) -> None:

# File: src/backend/models/location.py
class Location(Base):
    def to_dict(self) -> dict:
    def latitude(self) -> Optional[float]:
    def longitude(self) -> Optional[float]:
    def has_coordinates(self) -> bool:
    def set_coordinates(self, latitude: float, longitude: float) -> None:
    def increment_image_count(self) -> None:
    def recalculate_image_count(self, db_session) -> int:
    def activate(self) -> None:
    def deactivate(self) -> None:
    def get_recent_images(self, limit: int = 10):
    def get_processed_image_count(self, db_session) -> int:

```

## API Endpoints
Location: src/backend/api/
```python
# File: src/backend/api/__init__.py

# File: src/backend/api/images.py
def extract_exif_data(file_path: Path) -> dict:
def extract_timestamp_from_exif(exif_data: dict) -> Optional[datetime]:
def extract_timestamp_from_filename(filename: str) -> Optional[datetime]:
def get_location_by_name_or_id(
@router.post(
async def upload_images(
@router.get(
def list_images(
@router.get(
def get_image(

# File: src/backend/api/locations.py
@router.post(
def create_location(
@router.get(
def list_locations(
@router.get(
def get_location(
@router.get(
def get_location_by_name(
@router.patch(
def update_location(

```

## Worker Tasks
Location: src/worker/
```python
# File: src/worker/tasks/__init__.py

# File: src/worker/tasks/process_images.py
class ModelCache:
    def __new__(cls):
    def get_detection_model(self):
    def get_classification_model(self):
    def get_reid_model(self):
def extract_exif_data(image_path: Path) -> Dict:
def check_image_quality(image: np.ndarray) -> Tuple[bool, str]:
def preprocess_image(image_path: Path) -> Tuple[Optional[np.ndarray], Dict]:
def detect_deer(self: Task, image_paths: List[str]) -> Dict:
def classify_deer(self: Task, detection_data: Dict) -> Dict:
def reidentify_deer(self: Task, classification_data: Dict, database_features: Optional[List[Dict]] = None) -> Dict:
def process_pipeline(self: Task, image_paths: List[str], database_features: Optional[List[Dict]] = None) -> Dict:

```

## Configuration Files
```
-rwxrwxrwx 1 fdominguez fdominguez 4567 Nov  5 00:02 docker-compose.yml
```

## Python Dependencies
```
Main requirements:
sqlalchemy>=2.0.0,<3.0.0          # ORM for database models
psycopg2-binary>=2.9.0            # PostgreSQL driver
alembic>=1.12.0                   # Database migrations
fastapi>=0.104.0                  # Modern web framework
uvicorn[standard]>=0.24.0         # ASGI server
python-multipart>=0.0.6           # Form data support
pydantic>=2.0.0                   # Data validation
celery>=5.3.0                     # Distributed task queue
redis>=5.0.0                      # Redis client for Celery broker
flower>=2.0.0                     # Celery monitoring
torch>=2.0.0                      # PyTorch for ML models
torchvision>=0.15.0               # Computer vision models
ultralytics>=8.0.0                # YOLOv8 for detection
pillow>=10.0.0                    # Image processing (needed for EXIF extraction)
opencv-python>=4.8.0              # OpenCV for image processing
numpy>=1.24.0                     # Numerical computing
python-dotenv>=1.0.0              # Environment variable loading
httpx>=0.25.0                     # HTTP client for async requests
pytest>=7.4.0                     # Testing framework
pytest-asyncio>=0.21.0            # Async test support
```
