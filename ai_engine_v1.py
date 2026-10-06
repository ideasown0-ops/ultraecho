"""
AI Engine V1.0
Organ Detection + Quality Assessment + Frame Selection
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from enum import Enum

logger = logging.getLogger("ultrasound")


class OrganConfidence(Enum):
    """Confidence levels for organ detection"""
    VERY_HIGH = "very_high"  # > 90%
    HIGH = "high"            # 70-90%
    MEDIUM = "medium"        # 50-70%
    LOW = "low"              # 30-50%
    VERY_LOW = "very_low"    # < 30%


class ImageQuality(Enum):
    """Image quality assessment levels"""
    EXCELLENT = "excellent"  # > 85%
    GOOD = "good"            # 70-85%
    FAIR = "fair"            # 55-70%
    POOR = "poor"            # < 55%


@dataclass
class DetectedOrgan:
    """Represents a detected organ"""
    organ_name: str
    confidence: float  # 0-100
    bounding_box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    area_pixels: int
    centroid: Tuple[float, float]
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def confidence_level(self) -> OrganConfidence:
        if self.confidence > 90:
            return OrganConfidence.VERY_HIGH
        elif self.confidence > 70:
            return OrganConfidence.HIGH
        elif self.confidence > 50:
            return OrganConfidence.MEDIUM
        elif self.confidence > 30:
            return OrganConfidence.LOW
        else:
            return OrganConfidence.VERY_LOW


@dataclass
class QualityAssessment:
    """Image quality assessment result"""
    overall_score: float  # 0-100
    sharpness_score: float
    contrast_score: float
    noise_level: float
    artifacts_detected: List[str]
    quality_level: ImageQuality
    recommendations: List[str]
    assessed_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AIAnalysisResult:
    """Complete analysis result for a frame"""
    frame_id: str
    detected_organs: List[DetectedOrgan]
    quality_assessment: QualityAssessment
    is_best_frame: bool
    frame_score: float  # 0-100 (combined quality + organs)
    processing_time_ms: float
    models_used: List[str]
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class OrganDetectionEngine:
    """Detects organs in ultrasound images"""
    
    ORGANS_ABDOMEN = [
        "liver",
        "kidney_left",
        "kidney_right",
        "pancreas",
        "spleen",
        "gallbladder",
        "bile_duct",
        "bladder",
        "aorta",
        "inferior_vena_cava",
        "stomach",
        "small_intestine"
    ]
    
    def __init__(self):
        self.model = None
        self.model_name = "organ_detection_v1"
        self.detection_history = []
    
    def detect_organs(self, frame: np.ndarray) -> List[DetectedOrgan]:
        """
        Detect organs in a frame
        Returns list of detected organs with confidence scores
        """
        detected = []
        
        try:
            # V1.0 Stub Implementation
            # In production: use ONNX model inference
            
            frame_h, frame_w = frame.shape[:2]
            
            # Simulated detections for demo
            # In V1.0+: real YOLOv8 inference
            demo_organs = [
                {
                    "name": "liver",
                    "confidence": 0.92,
                    "box": (100, 150, 500, 550)
                },
                {
                    "name": "kidney_left",
                    "confidence": 0.87,
                    "box": (50, 200, 200, 450)
                },
                {
                    "name": "kidney_right",
                    "confidence": 0.85,
                    "box": (550, 200, 700, 450)
                },
                {
                    "name": "pancreas",
                    "confidence": 0.78,
                    "box": (250, 350, 450, 500)
                },
                {
                    "name": "spleen",
                    "confidence": 0.81,
                    "box": (50, 100, 250, 400)
                }
            ]
            
            for org in demo_organs:
                x1, y1, x2, y2 = org["box"]
                area = (x2 - x1) * (y2 - y1)
                centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                
                detected.append(DetectedOrgan(
                    organ_name=org["name"],
                    confidence=org["confidence"] * 100,
                    bounding_box=(x1, y1, x2, y2),
                    area_pixels=area,
                    centroid=centroid
                ))
            
            self.detection_history.append(detected)
            
            logger.info(f"Detected {len(detected)} organs")
            return detected
            
        except Exception as e:
            logger.error(f"Error in organ detection: {e}")
            return []
    
    def get_organ_confidence(self, organ_name: str, detections: List[DetectedOrgan]) -> Optional[float]:
        """Get confidence for a specific organ"""
        for detection in detections:
            if detection.organ_name == organ_name:
                return detection.confidence
        return None
    
    def get_most_confident_organs(self, detections: List[DetectedOrgan], top_k: int = 5) -> List[DetectedOrgan]:
        """Get top K most confident detections"""
        return sorted(detections, key=lambda x: x.confidence, reverse=True)[:top_k]


class ImageQualityAssessment:
    """Assesses image quality for ultrasound"""
    
    def __init__(self):
        self.model = None
        self.model_name = "quality_assessment_v1"
        self.quality_history = []
    
    def assess_quality(self, frame: np.ndarray) -> QualityAssessment:
        """
        Assess image quality
        Returns quality score 0-100
        """
        try:
            # V1.0 Stub Implementation
            # Real implementation would use deep learning model
            
            # Calculate basic metrics
            if len(frame.shape) == 3:
                gray = np.mean(frame, axis=2)
            else:
                gray = frame
            
            # Sharpness (Laplacian variance)
            laplacian = np.var(np.gradient(gray))
            sharpness_score = min(100, (laplacian / 100) * 100)
            
            # Contrast (standard deviation)
            contrast_score = min(100, (np.std(gray) / 255) * 100)
            
            # Noise estimation
            noise_level = max(0, 100 - (np.mean(frame) / 255 * 100))
            
            # Overall quality
            overall_score = (sharpness_score * 0.4 + contrast_score * 0.4 + (100 - noise_level) * 0.2)
            
            # Determine quality level
            if overall_score > 85:
                quality_level = ImageQuality.EXCELLENT
            elif overall_score > 70:
                quality_level = ImageQuality.GOOD
            elif overall_score > 55:
                quality_level = ImageQuality.FAIR
            else:
                quality_level = ImageQuality.POOR
            
            # Generate recommendations
            recommendations = []
            if sharpness_score < 60:
                recommendations.append("Image is blurry, adjust transducer position")
            if contrast_score < 50:
                recommendations.append("Low contrast, adjust gain settings")
            if noise_level > 40:
                recommendations.append("High noise detected, check probe connection")
            if overall_score < 55:
                recommendations.append("Poor quality overall, recapture image")
            
            assessment = QualityAssessment(
                overall_score=overall_score,
                sharpness_score=sharpness_score,
                contrast_score=contrast_score,
                noise_level=noise_level,
                artifacts_detected=["shadowing"] if noise_level > 50 else [],
                quality_level=quality_level,
                recommendations=recommendations
            )
            
            self.quality_history.append(assessment)
            logger.info(f"Image quality: {quality_level.value} ({overall_score:.1f}%)")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            return QualityAssessment(
                overall_score=0,
                sharpness_score=0,
                contrast_score=0,
                noise_level=100,
                artifacts_detected=["error"],
                quality_level=ImageQuality.POOR,
                recommendations=["Error in assessment"]
            )


class FrameSelectionEngine:
    """Selects best frames from video sequence"""
    
    def __init__(self):
        self.model = None
        self.model_name = "frame_selection_v1"
        self.frame_scores = []
        self.best_frames = []
    
    def score_frame(self, 
                   detections: List[DetectedOrgan],
                   quality: QualityAssessment) -> float:
        """
        Score a frame based on detections and quality
        Returns 0-100 score
        """
        try:
            # Quality contribution (40%)
            quality_score = quality.overall_score * 0.4
            
            # Detection contribution (60%)
            # Based on number and confidence of detections
            num_organs = len(detections)
            avg_confidence = np.mean([d.confidence for d in detections]) if detections else 0
            
            detection_score = (num_organs / len(OrganDetectionEngine.ORGANS_ABDOMEN) * 50 +
                             (avg_confidence / 100) * 10) * 0.6
            
            frame_score = quality_score + detection_score
            
            self.frame_scores.append(frame_score)
            return frame_score
            
        except Exception as e:
            logger.error(f"Error in frame scoring: {e}")
            return 0
    
    def select_best_frames(self, n: int = 5) -> List[Tuple[int, float]]:
        """
        Select best N frames from history
        Returns list of (frame_index, score) tuples
        """
        if not self.frame_scores:
            return []
        
        # Get indices and scores
        scored_frames = [(i, score) for i, score in enumerate(self.frame_scores)]
        
        # Sort by score and return top N
        best = sorted(scored_frames, key=lambda x: x[1], reverse=True)[:n]
        
        self.best_frames = best
        return best


class AIEngineV1:
    """Main AI Engine combining all V1.0 features"""
    
    def __init__(self):
        self.organ_detector = OrganDetectionEngine()
        self.quality_assessor = ImageQualityAssessment()
        self.frame_selector = FrameSelectionEngine()
        self.analysis_history = []
    
    def analyze_abdominal_ultrasound(self, frame: np.ndarray, frame_id: str) -> AIAnalysisResult:
        """
        Perform complete analysis on a frame
        Returns comprehensive analysis result
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Detect organs
            detections = self.organ_detector.detect_organs(frame)
            
            # 2. Assess quality
            quality = self.quality_assessor.assess_quality(frame)
            
            # 3. Score frame
            frame_score = self.frame_selector.score_frame(detections, quality)
            
            # 4. Determine if best frame
            is_best = len(self.frame_selector.best_frames) < 5 or \
                     frame_score > self.frame_selector.best_frames[-1][1]
            
            processing_time = (time.time() - start_time) * 1000
            
            result = AIAnalysisResult(
                frame_id=frame_id,
                detected_organs=detections,
                quality_assessment=quality,
                is_best_frame=is_best,
                frame_score=frame_score,
                processing_time_ms=processing_time,
                models_used=[
                    self.organ_detector.model_name,
                    self.quality_assessor.model_name,
                    self.frame_selector.model_name
                ]
            )
            
            self.analysis_history.append(result)
            logger.info(f"Analysis complete: {len(detections)} organs, quality: {quality.quality_level.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return AIAnalysisResult(
                frame_id=frame_id,
                detected_organs=[],
                quality_assessment=QualityAssessment(
                    overall_score=0,
                    sharpness_score=0,
                    contrast_score=0,
                    noise_level=100,
                    artifacts_detected=["error"],
                    quality_level=ImageQuality.POOR,
                    recommendations=["Error occurred"]
                ),
                is_best_frame=False,
                frame_score=0,
                processing_time_ms=0,
                models_used=[]
            )
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of all analyses"""
        if not self.analysis_history:
            return {}
        
        total_organs = sum(len(r.detected_organs) for r in self.analysis_history)
        avg_quality = np.mean([r.quality_assessment.overall_score for r in self.analysis_history])
        avg_processing_time = np.mean([r.processing_time_ms for r in self.analysis_history])
        
        return {
            "total_frames_analyzed": len(self.analysis_history),
            "total_organs_detected": total_organs,
            "average_quality_score": avg_quality,
            "average_processing_time_ms": avg_processing_time,
            "best_frames_count": len(self.frame_selector.best_frames)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = AIEngineV1()
    
    # Test with dummy frame
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = engine.analyze_abdominal_ultrasound(dummy_frame, "test_frame_001")
    
    print(f"\nAnalysis Summary:")
    print(f"  Detected organs: {len(result.detected_organs)}")
    print(f"  Quality level: {result.quality_assessment.quality_level.value}")
    print(f"  Frame score: {result.frame_score:.1f}")
    print(f"  Processing time: {result.processing_time_ms:.2f}ms")
