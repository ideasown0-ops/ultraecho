"""
Unit Tests for AI Ultrasound Assistant V1.0
Tests for AI Engine, Database, and Models
"""

import unittest
import logging
import tempfile
import os
from pathlib import Path
import numpy as np
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ultrasound")


class TestAIEngine(unittest.TestCase):
    """Tests for AI Engine V1.0"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test fixtures"""
        from ai_engine_v1 import AIEngineV1
        cls.engine = AIEngineV1()
        cls.test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def test_organ_detection(self):
        """Test organ detection"""
        detections = self.engine.organ_detector.detect_organs(self.test_frame)
        self.assertIsInstance(detections, list)
        self.assertGreater(len(detections), 0)
        
        for detection in detections:
            self.assertGreater(detection.confidence, 0)
            self.assertLess(detection.confidence, 100)
            self.assertIsNotNone(detection.organ_name)
    
    def test_quality_assessment(self):
        """Test image quality assessment"""
        quality = self.engine.quality_assessor.assess_quality(self.test_frame)
        self.assertIsNotNone(quality)
        self.assertGreaterEqual(quality.overall_score, 0)
        self.assertLessEqual(quality.overall_score, 100)
        self.assertIsNotNone(quality.quality_level)
    
    def test_frame_scoring(self):
        """Test frame scoring"""
        detections = self.engine.organ_detector.detect_organs(self.test_frame)
        quality = self.engine.quality_assessor.assess_quality(self.test_frame)
        score = self.engine.frame_selector.score_frame(detections, quality)
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_complete_analysis(self):
        """Test complete analysis pipeline"""
        frame_id = f"test_{uuid.uuid4().hex[:8]}"
        result = self.engine.analyze_abdominal_ultrasound(self.test_frame, frame_id)
        
        self.assertEqual(result.frame_id, frame_id)
        self.assertIsNotNone(result.detected_organs)
        self.assertIsNotNone(result.quality_assessment)
        self.assertGreater(result.processing_time_ms, 0)
    
    def test_analysis_summary(self):
        """Test analysis summary generation"""
        for i in range(5):
            self.engine.analyze_abdominal_ultrasound(self.test_frame, f"test_{i}")
        
        summary = self.engine.get_analysis_summary()
        self.assertEqual(summary['total_frames_analyzed'], 5)
        self.assertGreater(summary['average_quality_score'], 0)


class TestDatabase(unittest.TestCase):
    """Tests for Database Manager"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test database"""
        from database_manager import DatabaseManager, Patient
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.db_path = cls.temp_db.name
        cls.temp_db.close()
        
        cls.db = DatabaseManager(cls.db_path)
        cls.test_patient = Patient(
            patient_id=f"P{uuid.uuid4().hex[:8]}",
            name="Test Patient",
            age=45,
            gender="M",
            contact="1234567890",
            medical_history="Test history"
        )
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup test database"""
        cls.db.close()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
    
    def test_add_patient(self):
        """Test adding a patient"""
        result = self.db.add_patient(self.test_patient)
        self.assertTrue(result)
    
    def test_get_patient(self):
        """Test retrieving a patient"""
        self.db.add_patient(self.test_patient)
        retrieved = self.db.get_patient(self.test_patient.patient_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, self.test_patient.name)
        self.assertEqual(retrieved.age, self.test_patient.age)
    
    def test_list_patients(self):
        """Test listing patients"""
        patients = self.db.list_patients()
        self.assertIsInstance(patients, list)
        self.assertGreater(len(patients), 0)
    
    def test_add_examination(self):
        """Test adding an examination"""
        from database_manager import Examination
        from datetime import datetime
        
        exam = Examination(
            exam_id=f"E{uuid.uuid4().hex[:8]}",
            patient_id=self.test_patient.patient_id,
            exam_type="abdominal",
            exam_date=datetime.now().isoformat(),
            modality="ultrasound",
            indication="Test exam",
            findings="",
            status="completed"
        )
        
        result = self.db.add_examination(exam)
        self.assertTrue(result)
    
    def test_get_statistics(self):
        """Test getting database statistics"""
        stats = self.db.get_statistics()
        
        self.assertIn('total_patients', stats)
        self.assertIn('total_examinations', stats)
        self.assertIn('total_frames', stats)
        self.assertGreaterEqual(stats['total_patients'], 1)


class TestModelManager(unittest.TestCase):
    """Tests for AI Model Manager"""
    
    @classmethod
    def setUpClass(cls):
        """Setup model manager"""
        from ai_models_config import AIModelManager
        cls.temp_dir = tempfile.mkdtemp()
        cls.model_manager = AIModelManager(cls.temp_dir)
    
    def test_get_available_models(self):
        """Test getting available models"""
        models = self.model_manager.get_available_models()
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
    
    def test_get_model_info(self):
        """Test getting model information"""
        models = self.model_manager.get_available_models()
        if models:
            info = self.model_manager.get_model_info(models[0])
            self.assertIsNotNone(info)
            self.assertIn('name', info)
            self.assertIn('task', info)
            self.assertIn('size_mb', info)
    
    def test_get_models_by_task(self):
        """Test getting models by task"""
        models = self.model_manager.get_models_by_task('organ_detection')
        self.assertIsInstance(models, list)
    
    def test_get_models_for_organ(self):
        """Test getting models for specific organ"""
        models = self.model_manager.get_models_for_organ('liver')
        self.assertIsInstance(models, list)


class TestOrganConfidence(unittest.TestCase):
    """Tests for organ confidence levels"""
    
    def test_confidence_levels(self):
        """Test confidence level classification"""
        from ai_engine_v1 import DetectedOrgan, OrganConfidence
        
        # Very high confidence
        organ_vh = DetectedOrgan(
            organ_name="liver",
            confidence=95.0,
            bounding_box=(0, 0, 100, 100),
            area_pixels=10000,
            centroid=(50, 50)
        )
        self.assertEqual(organ_vh.confidence_level, OrganConfidence.VERY_HIGH)
        
        # High confidence
        organ_h = DetectedOrgan(
            organ_name="kidney",
            confidence=80.0,
            bounding_box=(0, 0, 100, 100),
            area_pixels=10000,
            centroid=(50, 50)
        )
        self.assertEqual(organ_h.confidence_level, OrganConfidence.HIGH)
        
        # Medium confidence
        organ_m = DetectedOrgan(
            organ_name="pancreas",
            confidence=60.0,
            bounding_box=(0, 0, 100, 100),
            area_pixels=10000,
            centroid=(50, 50)
        )
        self.assertEqual(organ_m.confidence_level, OrganConfidence.MEDIUM)


class TestImageQuality(unittest.TestCase):
    """Tests for image quality assessment"""
    
    def test_quality_levels(self):
        """Test quality level classification"""
        from ai_engine_v1 import ImageQuality
        
        # Create test assessment
        from ai_engine_v1 import ImageQuality
        
        # Excellent quality
        self.assertEqual(ImageQuality.EXCELLENT.value, "excellent")
        
        # Good quality
        self.assertEqual(ImageQuality.GOOD.value, "good")
        
        # Fair quality
        self.assertEqual(ImageQuality.FAIR.value, "fair")
        
        # Poor quality
        self.assertEqual(ImageQuality.POOR.value, "poor")


class TestFrameSelection(unittest.TestCase):
    """Tests for frame selection engine"""
    
    @classmethod
    def setUpClass(cls):
        """Setup frame selector"""
        from ai_engine_v1 import FrameSelectionEngine
        cls.selector = FrameSelectionEngine()
    
    def test_select_best_frames(self):
        """Test selecting best frames"""
        from ai_engine_v1 import DetectedOrgan, ImageQuality, QualityAssessment
        
        # Create test detections and quality
        detections = [
            DetectedOrgan("liver", 95.0, (0, 0, 100, 100), 10000, (50, 50)),
            DetectedOrgan("kidney", 87.0, (100, 0, 200, 100), 10000, (150, 50))
        ]
        
        quality = QualityAssessment(
            overall_score=85.0,
            sharpness_score=90.0,
            contrast_score=80.0,
            noise_level=10.0,
            artifacts_detected=[],
            quality_level=ImageQuality.EXCELLENT,
            recommendations=[]
        )
        
        # Score frame
        score = self.selector.score_frame(detections, quality)
        self.assertGreater(score, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_pipeline(self):
        """Test complete pipeline: capture -> analyze -> store"""
        from ai_engine_v1 import AIEngineV1
        from database_manager import DatabaseManager, Patient, Examination
        from datetime import datetime
        import tempfile
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_db.name
        temp_db.close()
        
        try:
            db = DatabaseManager(db_path)
            engine = AIEngineV1()
            
            # Create test data
            patient = Patient(
                patient_id=f"P{uuid.uuid4().hex[:8]}",
                name="Integration Test Patient",
                age=50,
                gender="F",
                contact="9876543210",
                medical_history="Integration test"
            )
            
            db.add_patient(patient)
            
            exam = Examination(
                exam_id=f"E{uuid.uuid4().hex[:8]}",
                patient_id=patient.patient_id,
                exam_type="abdominal",
                exam_date=datetime.now().isoformat(),
                modality="ultrasound",
                indication="Integration test",
                findings="",
                status="in_progress"
            )
            
            db.add_examination(exam)
            
            # Analyze frames
            test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            result = engine.analyze_abdominal_ultrasound(test_frame, "integration_test")
            
            # Store analysis
            organs = [o.organ_name for o in result.detected_organs]
            analysis_id = f"A{uuid.uuid4().hex[:8]}"
            
            success = db.add_ai_analysis(
                analysis_id, "test_frame", exam.exam_id,
                organs,
                result.quality_assessment.overall_score,
                result.frame_score,
                result.processing_time_ms,
                result.models_used,
                result.is_best_frame
            )
            
            self.assertTrue(success)
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
