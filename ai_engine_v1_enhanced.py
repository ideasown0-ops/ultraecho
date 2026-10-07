"""
AI Engine V1.1 Enhanced - كشف الأعضاء + كشف الأمراض + التشخيص
"""

import logging
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathology_engine import PathologyDetectionEngine, OrganAssessment

logger = logging.getLogger("ultrasound")


@dataclass
class AIAnalysisResultEnhanced:
    """نتيجة التحليل المحسنة - تشمل التشخيص"""
    frame_id: str
    organs_detected: dict                  # {organ_name: confidence}
    image_quality: float                   # 0-100
    frame_score: float                     # 0-100
    quality_level: str                     # EXCELLENT, GOOD, FAIR, POOR
    organ_assessments: List[OrganAssessment]  # التقييمات الطبية
    recommendations: List[str]
    timestamp: str


class AIEngineV1Enhanced:
    """محرك AI المحسن - يجمع بين كشف الأعضاء والتشخيص"""
    
    def __init__(self):
        # محركات منفصلة
        self.organ_detector = OrganDetectionEngine()
        self.quality_assessor = ImageQualityAssessment()
        self.frame_selector = FrameSelectionEngine()
        self.pathology_engine = PathologyDetectionEngine()
        
        logger.info("AI Engine V1.1 Enhanced initialized with pathology detection")
    
    def analyze_abdominal_ultrasound_enhanced(self, frame: np.ndarray, 
                                              frame_id: str) -> AIAnalysisResultEnhanced:
        """تحليل كامل - كشف أعضاء + أمراض + تشخيص"""
        
        # 1. كشف الأعضاء
        organs_detected = self.organ_detector.detect_organs(frame)
        
        # 2. تقييم جودة الصورة
        quality_score = self.quality_assessor.assess_image(frame)
        
        # 3. درجة الصورة
        frame_score = self.frame_selector.calculate_frame_score(frame, organs_detected)
        
        # 4. تصنيف الجودة
        quality_level = self._classify_quality(quality_score)
        
        # 5. كشف الأمراض والتشخيص
        organ_assessments = self._assess_organs_for_pathology(organs_detected, frame)
        
        # 6. التوصيات
        recommendations = self._generate_recommendations(
            organs_detected, quality_score, organ_assessments
        )
        
        result = AIAnalysisResultEnhanced(
            frame_id=frame_id,
            organs_detected=organs_detected,
            image_quality=quality_score,
            frame_score=frame_score,
            quality_level=quality_level,
            organ_assessments=organ_assessments,
            recommendations=recommendations,
            timestamp=self._get_timestamp()
        )
        
        logger.info(f"Enhanced analysis completed: {len(organ_assessments)} organs assessed")
        return result
    
    def _assess_organs_for_pathology(self, organs_detected: dict, 
                                     frame: np.ndarray) -> List[OrganAssessment]:
        """تقييم الأعضاء لكشف الأمراض"""
        assessments = []
        
        for organ_name, confidence in organs_detected.items():
            # إنشاء بيانات العضو
            organ_data = self._extract_organ_data(organ_name, frame, confidence)
            
            # استخدام محرك كشف الأمراض
            assessment = self.pathology_engine.assess_organ(organ_name, organ_data)
            assessments.append(assessment)
        
        return assessments
    
    def _extract_organ_data(self, organ_name: str, frame: np.ndarray, 
                           confidence: float) -> dict:
        """استخراج بيانات العضو للتحليل"""
        
        # تحليل بسيط لخصائص الصورة
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # الحجم
        height, width = frame.shape[:2]
        organ_size = self._estimate_organ_size(organ_name, height, width)
        
        # تحليل الصدى (التجانس)
        echotexture = self._analyze_echotexture(gray)
        
        # الخصائص الأخرى
        organ_data = {
            "confidence": confidence,
            "size": organ_size,
            "echotexture": echotexture,
            "size_normal": self._is_size_normal(organ_name, organ_size),
            "echotexture_normal": "متجانس" in echotexture,
            "has_abnormalities": False,  # سيتم تحديثه لاحقاً
            "color_doppler": "لم يتم فحصه"
        }
        
        return organ_data
    
    def _estimate_organ_size(self, organ_name: str, height: int, width: int) -> str:
        """تقدير حجم العضو"""
        # هذا تقدير مبسط
        normal_sizes = {
            "liver": "15 cm",
            "kidney_left": "10-12 cm",
            "kidney_right": "10-12 cm",
            "pancreas": "2-3 cm",
            "spleen": "10-12 cm"
        }
        
        return normal_sizes.get(organ_name.lower(), "غير معروف")
    
    def _is_size_normal(self, organ_name: str, size: str) -> bool:
        """التحقق من أن الحجم طبيعي"""
        # تحقق مبسط - يمكن تحسينه
        return "طبيعي" not in size.lower() or size == "غير معروف"
    
    def _analyze_echotexture(self, gray_image: np.ndarray) -> str:
        """تحليل خصائص الصدى"""
        
        # حساب التباين والانحراف المعياري
        mean = np.mean(gray_image)
        std = np.std(gray_image)
        
        # حساب التجانس
        if std < 30:
            return "متجانس"
        elif std < 60:
            return "متجانس نسبياً مع تغييرات طفيفة"
        else:
            return "غير متجانس"
    
    def _classify_quality(self, quality_score: float) -> str:
        """تصنيف جودة الصورة"""
        if quality_score >= 85:
            return "EXCELLENT"
        elif quality_score >= 70:
            return "GOOD"
        elif quality_score >= 55:
            return "FAIR"
        else:
            return "POOR"
    
    def _generate_recommendations(self, organs_detected: dict, 
                                 quality_score: float,
                                 assessments: List[OrganAssessment]) -> List[str]:
        """توليد التوصيات"""
        recommendations = []
        
        # بناءً على جودة الصورة
        if quality_score < 55:
            recommendations.append("🔴 جودة الصورة منخفضة جداً - أعد التقاط الصورة")
        elif quality_score < 70:
            recommendations.append("⚠️ جودة الصورة دون المثالية - حاول تحسين الفحص")
        else:
            recommendations.append("✅ جودة الصورة جيدة للتحليل")
        
        # بناءً على عدد الأعضاء المكتشفة
        if len(organs_detected) < 3:
            recommendations.append("⚠️ عدد الأعضاء المكتشفة أقل من المتوقع")
        
        # بناءً على التقييمات
        for assessment in assessments:
            if assessment.findings:
                for finding in assessment.findings:
                    if finding.risk_level.value == "عالي":
                        recommendations.append(
                            f"🔴 وجود نتائج عالية الخطورة في {assessment.organ_name}"
                        )
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """الحصول على الوقت الحالي"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# محركات المساعدة (من الإصدار السابق)
# ============================================================================

class OrganDetectionEngine:
    """محرك كشف الأعضاء"""
    
    def detect_organs(self, frame: np.ndarray) -> dict:
        """كشف الأعضاء"""
        # هذا مثال - في التطبيق الحقيقي يستخدم نماذج AI
        organs = {
            "liver": 92.0,
            "kidney_left": 87.0,
            "kidney_right": 85.0,
            "pancreas": 78.0,
            "spleen": 81.0
        }
        return organs


class ImageQualityAssessment:
    """تقييم جودة الصورة"""
    
    def assess_image(self, frame: np.ndarray) -> float:
        """تقييم جودة الصورة"""
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # حساب الحدة
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # حساب التباين
        contrast = gray.std()
        
        # درجة الجودة المركبة
        quality = (sharpness / 1000) + (contrast / 2.56)
        quality = min(100, max(0, quality))
        
        return quality


class FrameSelectionEngine:
    """محرك اختيار أفضل صورة"""
    
    def calculate_frame_score(self, frame: np.ndarray, organs: dict) -> float:
        """حساب درجة الصورة"""
        
        # حساب درجة الأعضاء
        organ_score = sum(organs.values()) / len(organs) if organs else 0
        
        # حساب درجة الحدة
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness_score = min(100, laplacian.var() / 10)
        
        # الدرجة النهائية
        score = (organ_score * 0.6) + (sharpness_score * 0.4)
        
        return score
