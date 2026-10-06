# 📚 API Reference - AI Ultrasound Assistant V1.0

## Table of Contents
1. [AI Engine API](#ai-engine-api)
2. [Database API](#database-api)
3. [Video Capture API](#video-capture-api)
4. [Configuration API](#configuration-api)
5. [Model Manager API](#model-manager-api)

---

## AI Engine API

### `AIEngineV1`

Main AI analysis engine for ultrasound images.

```python
from ai_engine_v1 import AIEngineV1
import numpy as np

# Initialize
engine = AIEngineV1()

# Analyze frame
frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
result = engine.analyze_abdominal_ultrasound(frame, frame_id="frame_001")
```

#### **Methods**

##### `analyze_abdominal_ultrasound(frame, frame_id) → AIAnalysisResult`

Performs complete AI analysis on ultrasound frame.

**Parameters:**
- `frame` (np.ndarray): Input image (H×W×3 BGR)
- `frame_id` (str): Unique frame identifier

**Returns:**
```python
AIAnalysisResult(
    frame_id: str,
    detected_organs: List[DetectedOrgan],
    quality_assessment: QualityAssessment,
    is_best_frame: bool,
    frame_score: float,
    processing_time_ms: float,
    models_used: List[str]
)
```

**Example:**
```python
result = engine.analyze_abdominal_ultrasound(frame, "F001")

# Access results
for organ in result.detected_organs:
    print(f"{organ.organ_name}: {organ.confidence:.1f}%")

print(f"Quality: {result.quality_assessment.quality_level.value}")
print(f"Processing time: {result.processing_time_ms:.2f}ms")
```

---

##### `get_analysis_summary() → Dict`

Get summary of all analyses performed.

**Returns:**
```python
{
    "total_frames_analyzed": int,
    "total_organs_detected": int,
    "average_quality_score": float,
    "average_processing_time_ms": float,
    "best_frames_count": int
}
```

**Example:**
```python
summary = engine.get_analysis_summary()
print(f"Analyzed {summary['total_frames_analyzed']} frames")
print(f"Average quality: {summary['average_quality_score']:.1f}%")
```

---

### `OrganDetectionEngine`

Detects organs in ultrasound images.

```python
from ai_engine_v1 import OrganDetectionEngine

detector = OrganDetectionEngine()
detections = detector.detect_organs(frame)
```

#### **Methods**

##### `detect_organs(frame) → List[DetectedOrgan]`

Detects organs in frame.

**Parameters:**
- `frame` (np.ndarray): Input image

**Returns:**
List of `DetectedOrgan` objects

**Properties:**
```python
class DetectedOrgan:
    organ_name: str                # "liver", "kidney_left", etc.
    confidence: float              # 0-100
    bounding_box: Tuple[4]         # (x1, y1, x2, y2)
    area_pixels: int               # Bounding box area
    centroid: Tuple[2]             # (x_center, y_center)
    confidence_level: OrganConfidence  # VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW
    detected_at: str               # ISO timestamp
```

**Example:**
```python
detections = detector.detect_organs(frame)
for organ in detections:
    print(f"{organ.organ_name}")
    print(f"  Confidence: {organ.confidence:.1f}%")
    print(f"  Level: {organ.confidence_level.value}")
    print(f"  Box: {organ.bounding_box}")
```

---

##### `get_organ_confidence(organ_name, detections) → Optional[float]`

Get confidence score for specific organ.

**Parameters:**
- `organ_name` (str): Name of organ to find
- `detections` (List[DetectedOrgan]): List from detect_organs()

**Returns:**
Confidence score (0-100) or None if not found

**Example:**
```python
confidence = detector.get_organ_confidence("liver", detections)
if confidence and confidence > 85:
    print("High confidence liver detection!")
```

---

##### `get_most_confident_organs(detections, top_k=5) → List[DetectedOrgan]`

Get top K most confident detections.

**Parameters:**
- `detections` (List[DetectedOrgan]): List from detect_organs()
- `top_k` (int): Number of top results to return

**Returns:**
Sorted list of top K detections

**Example:**
```python
top_organs = detector.get_most_confident_organs(detections, top_k=3)
for i, organ in enumerate(top_organs):
    print(f"{i+1}. {organ.organ_name} ({organ.confidence:.1f}%)")
```

---

### `ImageQualityAssessment`

Evaluates ultrasound image quality.

```python
from ai_engine_v1 import ImageQualityAssessment

assessor = ImageQualityAssessment()
quality = assessor.assess_quality(frame)
```

#### **Methods**

##### `assess_quality(frame) → QualityAssessment`

Assesses image quality.

**Parameters:**
- `frame` (np.ndarray): Input image

**Returns:**
```python
QualityAssessment(
    overall_score: float,           # 0-100
    sharpness_score: float,
    contrast_score: float,
    noise_level: float,             # 0-100
    artifacts_detected: List[str],
    quality_level: ImageQuality,    # EXCELLENT, GOOD, FAIR, POOR
    recommendations: List[str]
)
```

**Example:**
```python
quality = assessor.assess_quality(frame)

print(f"Overall: {quality.overall_score:.1f}%")
print(f"Quality: {quality.quality_level.value}")

if quality.recommendations:
    print("Recommendations:")
    for rec in quality.recommendations:
        print(f"  - {rec}")
```

---

### `FrameSelectionEngine`

Selects best frames from sequence.

```python
from ai_engine_v1 import FrameSelectionEngine

selector = FrameSelectionEngine()
score = selector.score_frame(detections, quality)
```

#### **Methods**

##### `score_frame(detections, quality) → float`

Calculate combined score for frame.

**Parameters:**
- `detections` (List[DetectedOrgan]): From organ detection
- `quality` (QualityAssessment): From quality assessment

**Returns:**
Frame score (0-100)

**Example:**
```python
frame_score = selector.score_frame(detections, quality)
print(f"Frame score: {frame_score:.1f}/100")
```

---

##### `select_best_frames(n=5) → List[Tuple[int, float]]`

Select best N frames from history.

**Parameters:**
- `n` (int): Number of frames to select

**Returns:**
List of (frame_index, score) tuples

**Example:**
```python
best_frames = selector.select_best_frames(n=5)
for idx, score in best_frames:
    print(f"Frame {idx}: {score:.1f}")
```

---

## Database API

### `DatabaseManager`

Manages SQLite database for patients and examinations.

```python
from database_manager import DatabaseManager

db = DatabaseManager(db_path="ultrasound.db")
```

#### **Patient Management**

##### `add_patient(patient) → bool`

Add new patient to database.

**Parameters:**
- `patient` (Patient): Patient object

**Example:**
```python
from database_manager import Patient

patient = Patient(
    patient_id="P001",
    name="Ahmed Ali",
    age=45,
    gender="M",
    contact="1234567890",
    medical_history="Hypertension"
)

if db.add_patient(patient):
    print("Patient added successfully")
```

---

##### `get_patient(patient_id) → Optional[Patient]`

Retrieve patient by ID.

**Parameters:**
- `patient_id` (str): Patient ID

**Returns:**
Patient object or None if not found

**Example:**
```python
patient = db.get_patient("P001")
if patient:
    print(f"{patient.name}, age {patient.age}")
```

---

##### `list_patients() → List[Patient]`

Get all patients.

**Returns:**
List of all Patient objects

**Example:**
```python
patients = db.list_patients()
for patient in patients:
    print(f"{patient.patient_id}: {patient.name}")
```

---

#### **Examination Management**

##### `add_examination(exam) → bool`

Add new examination.

**Parameters:**
- `exam` (Examination): Examination object

**Example:**
```python
from database_manager import Examination
from datetime import datetime

exam = Examination(
    exam_id="E001",
    patient_id="P001",
    exam_type="abdominal",
    exam_date=datetime.now().isoformat(),
    modality="ultrasound",
    indication="Abdominal pain",
    findings="",
    status="in_progress"
)

db.add_examination(exam)
```

---

##### `get_patient_examinations(patient_id) → List[Examination]`

Get all exams for patient.

**Parameters:**
- `patient_id` (str): Patient ID

**Returns:**
List of Examination objects

**Example:**
```python
exams = db.get_patient_examinations("P001")
for exam in exams:
    print(f"{exam.exam_id}: {exam.exam_date}")
```

---

#### **Analysis Reports**

##### `add_analysis_report(report) → bool`

Store AI analysis report.

**Parameters:**
- `report` (AnalysisReport): Report object

**Example:**
```python
from database_manager import AnalysisReport

report = AnalysisReport(
    report_id="R001",
    exam_id="E001",
    ai_findings="Normal liver, no lesions",
    detected_organs=["liver", "kidney_left", "kidney_right"],
    quality_score=87.5,
    recommendations="Good quality for diagnosis"
)

db.add_analysis_report(report)
```

---

##### `get_exam_report(exam_id) → Optional[AnalysisReport]`

Get analysis report for exam.

**Parameters:**
- `exam_id` (str): Examination ID

**Returns:**
AnalysisReport object or None

**Example:**
```python
report = db.get_exam_report("E001")
if report:
    print(f"Quality: {report.quality_score}")
    print(f"Organs: {report.detected_organs}")
```

---

#### **Database Statistics**

##### `get_statistics() → Dict`

Get database statistics.

**Returns:**
```python
{
    "total_patients": int,
    "total_examinations": int,
    "total_frames": int,
    "average_quality_score": float
}
```

**Example:**
```python
stats = db.get_statistics()
print(f"Total patients: {stats['total_patients']}")
print(f"Avg quality: {stats['average_quality_score']:.1f}%")
```

---

### `close()`

Close database connection.

**Example:**
```python
db.close()
```

---

## Video Capture API

### `DeviceManager`

Enumerate and manage capture devices.

```python
from app.video.device_manager import DeviceManager

manager = DeviceManager()
devices = manager.enumerate_devices()
```

#### **Methods**

##### `enumerate_devices() → List[VideoDevice]`

List all available capture devices.

**Returns:**
```python
List[VideoDevice(
    index: int,
    name: str,
    driver: str
)]
```

**Example:**
```python
devices = manager.enumerate_devices()
for device in devices:
    print(f"{device.index}: {device.name}")
```

---

### `CaptureManager`

Handle live video capture from device.

```python
from app.video.capture_manager import CaptureManager

capture = CaptureManager(device_index=0)
capture.start()
frame = capture.get_latest_frame()
capture.stop()
```

#### **Methods**

##### `start() → bool`

Start capturing from device.

**Returns:**
True if started successfully

##### `stop()`

Stop capturing.

##### `get_latest_frame() → Optional[np.ndarray]`

Get current frame from buffer.

**Returns:**
Frame as numpy array or None if no frame available

##### `get_stats() → CaptureStats`

Get capture statistics.

---

### `VideoPlayer`

Play recorded video files.

```python
from app.video.video_player import VideoPlayer

player = VideoPlayer()
player.open_video("video.mp4")
player.play()
frame = player.get_current_frame()
```

#### **Methods**

##### `open_video(path) → bool`

Load video file.

##### `play()`

Start playback.

##### `pause()`

Pause playback.

##### `stop()`

Stop and reset.

##### `seek(frame_num)`

Jump to frame number.

##### `get_current_frame() → Optional[np.ndarray]`

Get current frame.

---

## Configuration API

### `AppConfig`

Application configuration management.

```python
from app.config import AppConfig

config = AppConfig()
```

#### **Methods**

##### `get(key: str, default=None)`

Get configuration value.

**Parameters:**
- `key` (str): Config key (e.g., "video.resolution")
- `default`: Value if key not found

**Returns:**
Configuration value

**Example:**
```python
resolution = config.get("video.default_resolution")
fps = config.get("video.target_fps", 30)
```

---

##### `set(key: str, value)`

Set configuration value.

**Parameters:**
- `key` (str): Config key
- `value`: Value to set

**Example:**
```python
config.set("video.target_fps", 30)
config.set("ai.enable_gpu", True)
```

---

##### `save()`

Save configuration to file.

**Example:**
```python
config.save()
```

---

## Model Manager API

### `AIModelManager`

Manage ONNX AI models.

```python
from ai_models_config import AIModelManager

manager = AIModelManager(models_dir="models")
```

#### **Methods**

##### `get_available_models() → List[str]`

List all available models.

##### `get_model_info(model_key: str) → Dict`

Get model information.

**Returns:**
```python
{
    "name": str,
    "task": str,
    "organs": List[str],
    "size_mb": float,
    "version": str,
    "downloaded": bool
}
```

---

##### `get_models_by_task(task: str) → List[str]`

Get models for specific task.

**Parameters:**
- `task` (str): Task name ("organ_detection", "quality_assessment", etc.)

---

##### `get_models_for_organ(organ: str) → List[str]`

Get models that detect specific organ.

**Parameters:**
- `organ` (str): Organ name

---

##### `download_model(model_key: str, progress_callback=None) → bool`

Download model from remote.

---

## Error Handling

### Exception Types

```python
# Capture errors
CaptureError
DeviceNotFoundError
CaptureTimeoutError

# AI errors
InferenceError
ModelLoadError
InvalidFrameError

# Database errors
DatabaseError
PatientNotFoundError
ExaminationNotFoundError

# Video errors
VideoLoadError
CodecNotSupportedError
```

### Example Error Handling

```python
try:
    result = engine.analyze_abdominal_ultrasound(frame, frame_id)
except InferenceError as e:
    logger.error(f"Analysis failed: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

---

## Performance Tips

1. **Batch Processing**
   ```python
   frames = [frame1, frame2, frame3]
   results = [engine.analyze_abdominal_ultrasound(f, f"F{i}") 
              for i, f in enumerate(frames)]
   ```

2. **GPU Acceleration**
   ```python
   config.set("ai.enable_gpu", True)
   config.set("ai.backend", "tensorrt")
   ```

3. **Memory Management**
   ```python
   # Don't keep all frames in memory
   frame = capture.get_latest_frame()
   process(frame)
   del frame  # Free memory
   ```

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete example using all V1.0 APIs"""

from ai_engine_v1 import AIEngineV1
from database_manager import DatabaseManager, Patient, Examination
from app.config import AppConfig
from app.video.capture_manager import CaptureManager
from datetime import datetime
import uuid

# Initialize
config = AppConfig()
db = DatabaseManager()
ai_engine = AIEngineV1()
capture = CaptureManager(0)

# Create patient
patient = Patient(
    patient_id=f"P{uuid.uuid4().hex[:8]}",
    name="John Doe",
    age=50,
    gender="M",
    contact="555-1234",
    medical_history="None"
)
db.add_patient(patient)

# Create examination
exam = Examination(
    exam_id=f"E{uuid.uuid4().hex[:8]}",
    patient_id=patient.patient_id,
    exam_type="abdominal",
    exam_date=datetime.now().isoformat(),
    modality="ultrasound",
    indication="Routine checkup",
    findings="",
    status="in_progress"
)
db.add_examination(exam)

# Capture and analyze
capture.start()
for i in range(10):
    frame = capture.get_latest_frame()
    if frame is not None:
        # Analyze
        result = ai_engine.analyze_abdominal_ultrasound(frame, f"F{i:06d}")
        
        # Store results
        db.add_ai_analysis(
            f"A{i:06d}",
            f"F{i:06d}",
            exam.exam_id,
            [o.organ_name for o in result.detected_organs],
            result.quality_assessment.overall_score,
            result.frame_score,
            result.processing_time_ms,
            result.models_used,
            result.is_best_frame
        )
        
        print(f"Frame {i}: {result.quality_assessment.quality_level.value}")

capture.stop()
db.close()
```

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Status**: Complete ✅

