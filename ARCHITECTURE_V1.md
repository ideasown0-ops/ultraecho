# 🏗️ AI Ultrasound Assistant - Architecture Documentation V1.0

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Ultrasound Machine                          │
│                  (Video Output / HDMI)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│            Capture Hardware                                  │
│    (EasyCAP, HDMI Capture, USB Video Capture)               │
└──────────────────────────┬──────────────────────────────────┘
                           │ DirectShow / USB Video
┌──────────────────────────▼──────────────────────────────────┐
│                     Windows PC                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Ultrasound Assistant V1.0                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │         Main Application (PySide6 UI)          │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │         │          │           │         │          │  │
│  │         ▼          ▼           ▼         ▼          │  │
│  │  ┌────────────┐ ┌──────────┐ ┌───────┐ ┌────────┐  │  │
│  │  │   Video    │ │   AI     │ │  DB   │ │ Config │  │  │
│  │  │   Layer    │ │  Engine  │ │Manager│ │Manager │  │  │
│  │  └────────────┘ └──────────┘ └───────┘ └────────┘  │  │
│  │         │          │           │                    │  │
│  │    ┌────▼────┐ ┌───▼────┐ ┌───▼──────┐            │  │
│  │    │Capture  │ │Quality │ │  SQLite  │            │  │
│  │    │Manager  │ │Assessor│ │  DB      │            │  │
│  │    └─────────┘ └────────┘ └──────────┘            │  │
│  │         │          │                               │  │
│  │    ┌────▼────┐ ┌───▼──────┐                       │  │
│  │    │Frame    │ │Organ Det. │                       │  │
│  │    │Processor│ │ Engine    │                       │  │
│  │    └─────────┘ └───────────┘                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                      │                                    │  │
│  ┌──────────────────▼─────────────────────────────────┐  │  │
│  │          Storage Layer                             │  │  │
│  │  ┌─────────────────────────────────────────────┐  │  │  │
│  │  │   captures/     videos/      models/        │  │  │  │
│  │  │   (JPEG frames) (references) (ONNX models)  │  │  │  │
│  │  │                                              │  │  │  │
│  │  │   ultrasound.db (SQLite)                    │  │  │  │
│  │  │   settings.json (Config)                    │  │  │  │
│  │  └─────────────────────────────────────────────┘  │  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Architectural Layers

### 1. **Presentation Layer (UI)**

**File**: `main_window_v1.py`

**Components**:
- Main window with tabbed interface
- Live capture widget
- Video playback widget
- Patient management interface
- AI analysis display
- Settings interface

**Responsibilities**:
- Handle user input
- Display real-time video
- Show analysis results
- Manage patient/exam creation
- Display application status

**Design Pattern**: Model-View-Controller (MVC)
- Model: Database manager, AI engine
- View: PyQt6 widgets
- Controller: Main window event handlers

---

### 2. **Video Capture Layer**

**Files**: 
- `app/video/device_manager.py`
- `app/video/capture_manager.py`
- `app/video/video_player.py`
- `app/video/frame_processor.py`

**Components**:

**DeviceManager**
```python
- enumerate_devices()         # Find available capture devices
- get_device_capabilities()   # Check resolution/FPS support
- validate_device()           # Test device connectivity
```

**CaptureManager**
```
- start()                      # Begin capturing
- stop()                       # Stop capture
- get_latest_frame()           # Current frame from buffer
- get_stats()                  # FPS, resolution, dropped frames
```

**VideoPlayer**
```python
- open_video(path)            # Load video file
- play()                       # Start playback
- pause()                      # Pause playback
- seek(frame_num)             # Jump to frame
- get_current_frame()         # Current playback frame
```

**FrameProcessor**
```python
- resize_frame()              # Maintain aspect ratio
- convert_color_space()       # BGR to RGB conversion
- add_annotations()           # Draw bounding boxes
- save_frame()                # Export to JPEG
```

**Key Design Decisions**:
- ✅ No hardcoded device names (auto-enumeration)
- ✅ Threaded capture (non-blocking UI)
- ✅ Single-frame buffer (always latest)
- ✅ Error resilience (reconnect on disconnect)

---

### 3. **AI/ML Layer**

**Files**:
- `ai_models_config.py`
- `ai_engine_v1.py`

**Architecture**:

#### **Model Manager**
```python
AIModelManager
├── load_model(key)           # Load ONNX model
├── download_model(url)       # Download from remote
├── get_model_info()          # Model metadata
└── get_models_by_task()      # Filter by task

ModelDownloadManager
├── add_to_queue()            # Queue models
├── download_all()            # Batch download
└── progress_callback()       # Monitor progress
```

#### **AI Engine V1.0**
```python
AIEngineV1
├── OrganDetectionEngine
│   ├── detect_organs(frame)      # YOLO inference
│   ├── get_organ_confidence()    # Single organ score
│   └── get_top_organs(k)         # Best K detections
│
├── ImageQualityAssessment
│   ├── assess_quality(frame)     # Quality metrics
│   ├── calculate_sharpness()     # Laplacian variance
│   ├── calculate_contrast()      # Std deviation
│   └── estimate_noise()          # Gaussian model
│
└── FrameSelectionEngine
    ├── score_frame()              # Combined scoring
    ├── select_best_frames(n)      # Top N frames
    └── get_frame_history()        # All frames ranked
```

**Data Structures**:

```python
@dataclass
DetectedOrgan:
    organ_name: str
    confidence: float          # 0-100
    bounding_box: Tuple[4]     # x1, y1, x2, y2
    centroid: Tuple[2]         # Center coordinates
    area_pixels: int

@dataclass
QualityAssessment:
    overall_score: float
    sharpness_score: float
    contrast_score: float
    noise_level: float
    artifacts_detected: List[str]
    quality_level: ImageQuality
    recommendations: List[str]

@dataclass
AIAnalysisResult:
    frame_id: str
    detected_organs: List[DetectedOrgan]
    quality_assessment: QualityAssessment
    is_best_frame: bool
    frame_score: float         # Combined score
    processing_time_ms: float
    models_used: List[str]
```

**Algorithm Details**:

**Organ Detection (YOLO)**
```
Input: 480x640 RGB frame
↓
[CNN Processing - 12.5 MB Model]
↓
Output: Bounding boxes + confidence scores
Organs: Liver, Kidney L/R, Pancreas, Spleen, etc.
Latency: 100-300ms
```

**Quality Assessment (Multi-metric)**
```
Input: Raw ultrasound frame
↓
Metric 1: Sharpness = Laplacian(frame).var()
Metric 2: Contrast = std(frame)
Metric 3: Noise = Gaussian estimation
↓
Quality = (Sharp × 0.4) + (Contrast × 0.4) + ((100-Noise) × 0.2)
↓
Output: 0-100 score + recommendations
```

**Frame Selection (Weighted Scoring)**
```
For each frame:
  Score = (Quality × 0.4) + (DetectionWeight × 0.6)
  
DetectionWeight = (NumOrgans/MaxOrgans × 50) + (AvgConfidence × 10)

Rank all frames by score
Return top 5
```

---

### 4. **Data Layer**

**File**: `database_manager.py`

**Database Schema**:

```sql
-- Patients Table
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    contact TEXT,
    medical_history TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Examinations Table
CREATE TABLE examinations (
    exam_id TEXT PRIMARY KEY,
    patient_id TEXT FOREIGN KEY,
    exam_type TEXT,
    exam_date TIMESTAMP,
    modality TEXT,
    indication TEXT,
    findings TEXT,
    status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Analysis Reports Table
CREATE TABLE analysis_reports (
    report_id TEXT PRIMARY KEY,
    exam_id TEXT FOREIGN KEY,
    ai_findings TEXT,
    detected_organs TEXT (JSON),
    quality_score REAL,
    recommendations TEXT,
    created_at TIMESTAMP
);

-- Captured Frames Table
CREATE TABLE captured_frames (
    frame_id TEXT PRIMARY KEY,
    exam_id TEXT FOREIGN KEY,
    frame_path TEXT,
    quality_score REAL,
    organs_detected TEXT (JSON),
    timestamp TIMESTAMP,
    created_at TIMESTAMP
);

-- AI Analysis History Table
CREATE TABLE ai_analysis_history (
    analysis_id TEXT PRIMARY KEY,
    frame_id TEXT FOREIGN KEY,
    exam_id TEXT FOREIGN KEY,
    detected_organs TEXT (JSON),
    quality_score REAL,
    frame_score REAL,
    processing_time_ms REAL,
    models_used TEXT (JSON),
    is_best_frame INTEGER,
    created_at TIMESTAMP
);
```

**CRUD Operations**:
```python
# Create
add_patient(patient)
add_examination(exam)
add_analysis_report(report)

# Read
get_patient(id)
get_patient_examinations(patient_id)
get_exam_report(exam_id)

# Update
(Implementation in V1.1)

# Delete
(Implementation in V1.1)

# Query
list_patients()
list_examinations()
get_statistics()
```

---

### 5. **Configuration Layer**

**File**: `app/config.py`

**Settings Management**:
```json
{
  "window": {
    "width": 1400,
    "height": 900,
    "maximized": false
  },
  "video": {
    "capture_device_id": -1,
    "default_resolution": "640x480",
    "target_fps": 30,
    "show_fps": true
  },
  "ai": {
    "backend": "cpu",
    "enable_gpu": false
  },
  "paths": {
    "captures_dir": "captures",
    "videos_dir": "videos",
    "models_dir": "models"
  },
  "logging": {
    "level": "INFO"
  }
}
```

**Persistence**:
- Auto-load on startup
- Auto-save on change
- Fallback to defaults if corrupted

---

## Data Flow Diagrams

### Live Capture Flow

```
User selects device
         ↓
DeviceManager.enumerate_devices()
         ↓
CaptureManager.start()
         ↓
    [Capture Loop - Threaded]
    Frame → DirectShow buffer
         ↓
    get_latest_frame() [Non-blocking]
         ↓
    UI Timer [33ms = ~30 FPS]
         ↓
    Display on screen
         ↓
    [User clicks "Capture Frame"]
         ↓
    AIEngineV1.analyze()
         ↓
    DetectedOrgans + Quality
         ↓
    DatabaseManager.add_ai_analysis()
         ↓
    Update UI with results
```

### Video Playback Flow

```
User selects file
         ↓
VideoPlayer.open_video(path)
         ↓
OpenCV VideoCapture(path)
         ↓
User clicks "Play"
         ↓
    [Playback Loop]
    Read frame from file
         ↓
    Update slider position
         ↓
    Display frame
         ↓
    [User clicks "Capture Frame"]
         ↓
    Same analysis as live capture
```

### Analysis Flow

```
Frame input (480×640×3)
         ↓
    ┌────▼─────┐
    │ Parallel │
    └────┬─────┘
    ┌────┴──────────┐
    │               │
    ▼               ▼
[Organ Detection] [Quality Assessment]
    │               │
    ▼               ▼
[Confidence Filter] [Metrics Compute]
    │               │
    ▼               ▼
[Organ List]    [Quality Score]
    │               │
    └───────┬───────┘
            ▼
    [Frame Scoring]
            ▼
    [Best Frame Check]
            ▼
    [AIAnalysisResult]
            ▼
    [Database Storage]
            ▼
    [UI Update]
```

---

## Design Patterns Used

### 1. **Singleton Pattern**
```python
class AppConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. **Factory Pattern**
```python
class AIEngineFactory:
    @staticmethod
    def create(backend="cpu"):
        if backend == "cpu":
            return AIEngineV1()
        elif backend == "gpu":
            return AIEngineGPU()
```

### 3. **Observer Pattern**
```python
# UI listens to capture manager updates
capture_manager.on_frame_captured.connect(
    self.handle_new_frame
)
```

### 4. **Strategy Pattern**
```python
# Different model backends
class ModelBackend:
    def inference(frame): pass

class ONNXBackend(ModelBackend): pass
class TorchBackend(ModelBackend): pass
class TensorRTBackend(ModelBackend): pass
```

---

## Scalability & Extension Points

### Adding New Organ Detection

```python
# In ai_engine_v1.py
class OrganDetectionEngine:
    ORGANS_ABDOMEN = [
        "liver",
        "kidney_left",
        # ... add new organ
        "appendix"  # V1.2
    ]
```

### Adding GPU Support

```python
# In ai_engine_v1.py
if config.get("ai.enable_gpu"):
    device = "cuda"
else:
    device = "cpu"

# Model loaded on correct device
session = rt.InferenceSession(
    model_path,
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
```

### Adding Segmentation (V2.0)

```python
# New class in ai_engine_v1.py
class OrganSegmentation:
    def segment_organ(frame, organ_name):
        # Pixel-level mask
        return segmentation_mask
```

### Adding Measurements (V2.0)

```python
# New class
class MeasurementEngine:
    def measure_distance(point1, point2):
        return distance_mm
    
    def measure_area(contour):
        return area_mm2
```

---

## Error Handling Strategy

### Layer-wise Error Handling

```python
# UI Layer
try:
    device = self.load_device()
except DeviceNotFoundError:
    QMessageBox.warning("Device not found")

# Video Layer
try:
    frame = self.capture_manager.get_frame()
except CaptureError:
    self.capture_manager.reconnect()

# AI Layer
try:
    result = self.ai_engine.analyze(frame)
except InferenceError:
    logger.error("Inference failed")
    return empty_result()

# Database Layer
try:
    self.db.add_record()
except DatabaseError:
    self.db.rollback()
```

---

## Performance Optimization

### Current Optimizations (V1.0)
- ✅ Threaded capture (non-blocking UI)
- ✅ Single-frame buffer (memory efficient)
- ✅ Lazy model loading
- ✅ Batch processing ready

### Future Optimizations (V2.0+)
- ⏳ Frame batching (process multiple frames)
- ⏳ Model quantization (faster inference)
- ⏳ GPU acceleration
- ⏳ Caching (organ detection cache)

---

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Test error conditions

### Integration Tests
- Test component interactions
- Test database transactions
- Test file I/O

### System Tests
- Test end-to-end workflows
- Test with real hardware
- Performance benchmarking

---

## Version Evolution Strategy

```
V1.0: Foundation
  ├─ Live capture
  ├─ Video playback
  ├─ Organ detection
  ├─ Quality assessment
  └─ Basic DB

V1.1: Enhancement
  ├─ Model download manager
  ├─ PDF reports
  ├─ Dark theme
  └─ Performance tuning

V2.0: Segmentation
  ├─ Organ segmentation
  ├─ Measurements
  ├─ Lesion detection
  └─ Advanced UI

V5.0: Pregnancy/Fetal
  ├─ Fetal module
  ├─ Biometry
  └─ Growth tracking
```

**Key Principle**: Each version adds new features without breaking existing functionality.

---

## Deployment Architecture

```
Development:
  ai_ultrasound_v1/
  ├── Source code
  └── Tests

Production:
  AI_Ultrasound_Assistant.exe
  ├── Embedded Python
  ├── All dependencies bundled
  └── Auto-update capability
```

---

This architecture is designed for:
- ✅ Extensibility (add new organs, features)
- ✅ Maintainability (clean separation of concerns)
- ✅ Reliability (error handling, redundancy)
- ✅ Performance (threading, optimization)
- ✅ Scalability (cloud integration ready)

