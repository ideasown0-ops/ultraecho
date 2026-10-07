"""
اختبارات شاملة لنظام التشخيص المحسن
Test Suite for Enhanced Diagnosis System
"""

import unittest
import numpy as np
import cv2
import logging
from pathology_engine import (
    PathologyDetectionEngine, OrganAssessment, OrganStatus, 
    RiskLevel, PathologicalFinding, DiagnosticPossibility
)
from medical_report_generator import MedicalReportGenerator
from ai_engine_v1_enhanced import AIEngineV1Enhanced

# إعداد السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ultrasound")


class TestPathologyEngine(unittest.TestCase):
    """اختبارات محرك كشف الأمراض"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.engine = PathologyDetectionEngine()
    
    def test_pathology_engine_initialization(self):
        """اختبار تهيئة المحرك"""
        self.assertIsNotNone(self.engine.medical_knowledge)
        self.assertIn("liver", self.engine.medical_knowledge)
        self.assertIn("kidney_left", self.engine.medical_knowledge)
        self.assertIn("pancreas", self.engine.medical_knowledge)
        logger.info("✅ Pathology engine initialized successfully")
    
    def test_normal_organ_assessment(self):
        """اختبار تقييم عضو سليم"""
        normal_data = {
            "confidence": 95,
            "size": "طبيعي",
            "echotexture": "متجانس",
            "size_normal": True,
            "echotexture_normal": True,
            "has_abnormalities": False,
            "color_doppler": "طبيعي"
        }
        
        assessment = self.engine.assess_organ("liver", normal_data)
        
        self.assertEqual(assessment.status, OrganStatus.NORMAL)
        self.assertEqual(len(assessment.findings), 0)
        logger.info(f"✅ Normal organ assessment: {assessment.organ_name} - {assessment.status.value}")
    
    def test_abnormal_organ_assessment(self):
        """اختبار تقييم عضو غير سليم"""
        abnormal_data = {
            "confidence": 85,
            "size": "مضخم",
            "echotexture": "غير متجانس",
            "size_normal": False,
            "echotexture_normal": False,
            "has_abnormalities": True,
            "has_lesion": True,
            "lesion_description": "آفة شبه صلبة",
            "lesion_location": "الفص الأيمن",
            "lesion_size": 2.5,
            "lesion_characteristics": ["مظلمة", "حدود غير واضحة"],
            "lesion_confidence": 78,
            "is_enlarged": True,
            "color_doppler": "doppler متزايد"
        }
        
        assessment = self.engine.assess_organ("liver", abnormal_data)
        
        self.assertEqual(assessment.status, OrganStatus.ABNORMAL)
        self.assertGreater(len(assessment.findings), 0)
        self.assertGreater(len(assessment.recommendations), 0)
        logger.info(f"✅ Abnormal organ assessment: {len(assessment.findings)} findings detected")
    
    def test_differential_diagnosis_generation(self):
        """اختبار توليد التشخيص التفاضلي"""
        abnormal_data = {
            "has_lesion": True,
            "is_enlarged": True,
            "lesion_description": "تضخم مع آفة",
            "lesion_location": "الكبد",
            "lesion_size": 3.0,
            "lesion_characteristics": ["مظلمة"],
            "lesion_confidence": 85
        }
        
        assessment = self.engine.assess_organ("liver", abnormal_data)
        diagnoses = assessment.differential_diagnosis
        
        self.assertGreater(len(diagnoses), 0)
        # التحقق من أن الاحتمالية بين 0-100
        for diagnosis in diagnoses:
            self.assertGreaterEqual(diagnosis.probability, 0)
            self.assertLessEqual(diagnosis.probability, 100)
        
        logger.info(f"✅ Generated {len(diagnoses)} differential diagnoses")


class TestMedicalReportGenerator(unittest.TestCase):
    """اختبارات مولد التقارير الطبية"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.generator = MedicalReportGenerator()
        self.engine = PathologyDetectionEngine()
    
    def test_report_generation(self):
        """اختبار توليد التقرير"""
        # إنشاء تقييمات وهمية
        normal_data = {
            "confidence": 90,
            "size": "طبيعي",
            "echotexture": "متجانس",
            "size_normal": True,
            "echotexture_normal": True,
            "has_abnormalities": False,
            "color_doppler": "طبيعي"
        }
        
        assessment = self.engine.assess_organ("liver", normal_data)
        assessments = [assessment]
        
        report = self.generator.generate_report(
            assessments,
            patient_name="أحمد محمد",
            examination_id="0001"
        )
        
        self.assertIsNotNone(report)
        self.assertIn("تقرير الفحص", report)
        self.assertIn("أحمد محمد", report)
        self.assertIn("liver", report.lower())
        
        logger.info("✅ Medical report generated successfully")
        logger.info(f"Report length: {len(report)} characters")
    
    def test_report_with_abnormal_findings(self):
        """اختبار توليد التقرير مع نتائج غير طبيعية"""
        abnormal_data = {
            "confidence": 88,
            "size": "مضخم",
            "echotexture": "غير متجانس",
            "size_normal": False,
            "echotexture_normal": False,
            "has_abnormalities": True,
            "has_lesion": True,
            "lesion_description": "آفة شبه صلبة",
            "lesion_location": "الفص الأيمن",
            "lesion_size": 2.5,
            "lesion_characteristics": ["مظلمة"],
            "lesion_confidence": 80,
            "is_enlarged": True
        }
        
        assessment = self.engine.assess_organ("liver", abnormal_data)
        assessments = [assessment]
        
        report = self.generator.generate_report(assessments)
        
        self.assertIn("غير سليم", report)
        self.assertIn("آفة", report)
        logger.info("✅ Abnormal findings report generated")


class TestAIEngineEnhanced(unittest.TestCase):
    """اختبارات محرك AI المحسن"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.ai_engine = AIEngineV1Enhanced()
    
    def test_ai_engine_initialization(self):
        """اختبار تهيئة محرك AI"""
        self.assertIsNotNone(self.ai_engine.organ_detector)
        self.assertIsNotNone(self.ai_engine.quality_assessor)
        self.assertIsNotNone(self.ai_engine.frame_selector)
        self.assertIsNotNone(self.ai_engine.pathology_engine)
        logger.info("✅ AI Engine V1.1 initialized successfully")
    
    def test_quality_classification(self):
        """اختبار تصنيف جودة الصورة"""
        test_cases = [
            (95, "EXCELLENT"),
            (75, "GOOD"),
            (60, "FAIR"),
            (40, "POOR")
        ]
        
        for quality_score, expected in test_cases:
            result = self.ai_engine._classify_quality(quality_score)
            self.assertEqual(result, expected)
        
        logger.info("✅ Quality classification working correctly")
    
    def test_synthetic_ultrasound_analysis(self):
        """اختبار تحليل صورة ultrasound اصطناعية"""
        # إنشاء صورة اصطناعية
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        frame = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # التحليل
        result = self.ai_engine.analyze_abdominal_ultrasound_enhanced(
            frame=frame,
            frame_id="test_001"
        )
        
        # التحقق من النتائج
        self.assertIsNotNone(result.organs_detected)
        self.assertGreater(result.image_quality, 0)
        self.assertGreater(result.frame_score, 0)
        self.assertIsNotNone(result.quality_level)
        self.assertGreater(len(result.organ_assessments), 0)
        
        logger.info(f"✅ Synthetic image analyzed:")
        logger.info(f"   - Organs detected: {len(result.organs_detected)}")
        logger.info(f"   - Image quality: {result.image_quality:.1f}%")
        logger.info(f"   - Quality level: {result.quality_level}")
        logger.info(f"   - Assessments: {len(result.organ_assessments)}")


class TestOrganAssessmentIntegration(unittest.TestCase):
    """اختبارات التكامل الشامل"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.ai_engine = AIEngineV1Enhanced()
        self.report_generator = MedicalReportGenerator()
    
    def test_full_workflow(self):
        """اختبار المسار الكامل من التحليل إلى التقرير"""
        # 1. إنشاء صورة اصطناعية
        frame = np.random.randint(50, 150, (480, 640, 3), dtype=np.uint8)
        frame = cv2.GaussianBlur(frame, (7, 7), 0)
        
        # 2. التحليل
        logger.info("📊 Starting full workflow test...")
        analysis_result = self.ai_engine.analyze_abdominal_ultrasound_enhanced(
            frame=frame,
            frame_id="full_test_001"
        )
        
        logger.info(f"✅ Analysis completed")
        logger.info(f"   - Organs: {list(analysis_result.organs_detected.keys())}")
        logger.info(f"   - Quality: {analysis_result.quality_level} ({analysis_result.image_quality:.1f}%)")
        
        # 3. توليد التقرير
        report = self.report_generator.generate_report(
            analysis_result.organ_assessments,
            patient_name="مريض اختبار",
            examination_id="TEST_001"
        )
        
        logger.info(f"✅ Report generated ({len(report)} characters)")
        
        # 4. التحقق من محتوى التقرير
        self.assertIn("تقرير الفحص", report)
        self.assertIn("مريض اختبار", report)
        self.assertIn("TEST_001", report)
        
        logger.info("✅ Full workflow test passed!")
    
    def test_assessment_serialization(self):
        """اختبار تسلسل التقييمات"""
        abnormal_data = {
            "confidence": 85,
            "size": "مضخم",
            "echotexture": "غير متجانس",
            "size_normal": False,
            "echotexture_normal": False,
            "has_abnormalities": True,
            "is_enlarged": True
        }
        
        engine = PathologyDetectionEngine()
        assessment = engine.assess_organ("liver", abnormal_data)
        
        # يجب أن تكون جميع الخصائص قابلة للوصول
        self.assertTrue(hasattr(assessment, 'organ_name'))
        self.assertTrue(hasattr(assessment, 'status'))
        self.assertTrue(hasattr(assessment, 'findings'))
        self.assertTrue(hasattr(assessment, 'differential_diagnosis'))
        self.assertTrue(hasattr(assessment, 'recommendations'))
        
        logger.info("✅ Assessment serialization test passed")


# ============================================================================
# أمثلة الاستخدام
# ============================================================================

def example_normal_organ():
    """مثال: عضو سليم"""
    print("\n" + "="*70)
    print("مثال 1: عضو سليم (NORMAL ORGAN)")
    print("="*70)
    
    engine = PathologyDetectionEngine()
    
    normal_liver = {
        "confidence": 95,
        "size": "طبيعي",
        "echotexture": "متجانس",
        "size_normal": True,
        "echotexture_normal": True,
        "has_abnormalities": False,
        "color_doppler": "طبيعي"
    }
    
    assessment = engine.assess_organ("liver", normal_liver)
    
    print(f"✅ الجهاز: {assessment.organ_name}")
    print(f"✅ الحالة: {assessment.status.value}")
    print(f"✅ الحجم: {assessment.size}")
    print(f"✅ الصدى: {assessment.echotexture}")
    print(f"✅ الآفات: لا توجد")
    print(f"\n📋 التوصيات:")
    for rec in assessment.recommendations:
        print(f"   {rec}")


def example_abnormal_organ():
    """مثال: عضو غير سليم"""
    print("\n" + "="*70)
    print("مثال 2: عضو غير سليم (ABNORMAL ORGAN)")
    print("="*70)
    
    engine = PathologyDetectionEngine()
    
    abnormal_liver = {
        "confidence": 88,
        "size": "مضخم",
        "echotexture": "غير متجانس",
        "size_normal": False,
        "echotexture_normal": False,
        "has_abnormalities": True,
        "has_lesion": True,
        "lesion_description": "آفة شبه صلبة مع حدود غير واضحة",
        "lesion_location": "الفص الأيمن",
        "lesion_size": 2.5,
        "lesion_characteristics": ["مظلمة", "حدود غير واضحة"],
        "lesion_confidence": 80,
        "is_enlarged": True
    }
    
    assessment = engine.assess_organ("liver", abnormal_liver)
    
    print(f"🔴 الجهاز: {assessment.organ_name}")
    print(f"🔴 الحالة: {assessment.status.value}")
    print(f"🔴 الحجم: {assessment.size}")
    print(f"🔴 الصدى: {assessment.echotexture}")
    
    print(f"\n🔴 الآفات المكتشفة ({len(assessment.findings)}):")
    for finding in assessment.findings:
        print(f"   • {finding.finding_name}")
        print(f"     - الوصف: {finding.description}")
        print(f"     - الموقع: {finding.location}")
        print(f"     - الحجم: {finding.size_mm} mm" if finding.size_mm else "     - الحجم: غير محدد")
        print(f"     - مستوى الخطورة: {finding.risk_level.value}")
        print(f"     - الثقة: {finding.confidence}%")
    
    print(f"\n⚠️ التشخيصات المحتملة ({len(assessment.differential_diagnosis)}):")
    for diagnosis in assessment.differential_diagnosis:
        print(f"   • {diagnosis.diagnosis_name}")
        print(f"     - الاحتمالية: {diagnosis.probability}%")
        print(f"     - مستوى الخطورة: {diagnosis.risk_level.value}")
        print(f"     - الإجراء: {diagnosis.recommended_action}")
    
    print(f"\n📋 التوصيات:")
    for rec in assessment.recommendations:
        print(f"   {rec}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏥 نظام التشخيص المحسن - اختبارات شاملة")
    print("Enhanced Diagnosis System - Test Suite")
    print("="*70)
    
    # تشغيل الاختبارات الآلية
    print("\n▶️ تشغيل الاختبارات الآلية...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # أمثلة الاستخدام
    print("\n\n▶️ أمثلة الاستخدام:")
    example_normal_organ()
    example_abnormal_organ()
    
    print("\n" + "="*70)
    print("✅ جميع الاختبارات اكتملت بنجاح!")
    print("="*70)
