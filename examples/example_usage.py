"""Example usage of AI Ultrasound Assistant V1.0"""

from ai_engine_v1 import AIEngineV1
from database_manager import DatabaseManager, Patient, Examination
import numpy as np
import uuid
from datetime import datetime

# Initialize
engine = AIEngineV1()
db = DatabaseManager()

# Create test patient
patient = Patient(
    patient_id=f"P{uuid.uuid4().hex[:8]}",
    name="Test Patient",
    age=45,
    gender="M",
    contact="555-1234",
    medical_history="Test"
)
db.add_patient(patient)

# Create exam
exam = Examination(
    exam_id=f"E{uuid.uuid4().hex[:8]}",
    patient_id=patient.patient_id,
    exam_type="abdominal",
    exam_date=datetime.now().isoformat(),
    modality="ultrasound",
    indication="Test exam",
    findings="",
    status="completed"
)
db.add_examination(exam)

# Analyze test frames
for i in range(5):
    # Create dummy ultrasound frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Analyze
    result = engine.analyze_abdominal_ultrasound(frame, f"F{i:03d}")
    
    print(f"\nFrame {i}:")
    print(f"  Organs: {len(result.detected_organs)}")
    print(f"  Quality: {result.quality_assessment.quality_level.value}")
    print(f"  Score: {result.frame_score:.1f}")
    print(f"  Best: {'Yes ⭐' if result.is_best_frame else 'No'}")

# Get summary
print("\n" + "="*50)
print("Summary:")
stats = db.get_statistics()
for key, value in stats.items():
    print(f"  {key}: {value}")

db.close()
