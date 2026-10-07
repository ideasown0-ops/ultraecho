"""
Medical Indicators Extraction Module
Extracts radiological indicators from ultrasound images for diagnostic analysis.
"""

import numpy as np
from typing import Dict, List, Tuple
import cv2


class MedicalIndicatorsExtractor:
    """Extracts quantifiable medical indicators from ultrasound images."""

    def __init__(self):
        """Initialize the indicators extractor."""
        self.indicators = {}

    def extract_all_indicators(self, image: np.ndarray, organ_mask: np.ndarray) -> Dict:
        """
        Extract all medical indicators from organ region.
        
        Args:
            image: Ultrasound image (grayscale or BGR)
            organ_mask: Binary mask of organ region
            
        Returns:
            Dictionary containing all extracted indicators
        """
        if image is None or organ_mask is None:
            return {}

        # Ensure grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        organ_region = gray[organ_mask > 0]
        
        if len(organ_region) == 0:
            return {}

        indicators = {
            'size': self.extract_size(organ_mask),
            'uniformity': self.extract_uniformity(organ_region),
            'boundary_sharpness': self.extract_boundary_sharpness(gray, organ_mask),
            'mean_density': self.extract_mean_density(organ_region),
            'spots_count': self.extract_spots(organ_region),
            'edge_smoothness': self.extract_edge_smoothness(gray, organ_mask),
            'vessel_presence': self.extract_vessel_presence(gray, organ_mask),
            'texture_homogeneity': self.extract_texture_homogeneity(organ_region),
            'fluid_content': self.extract_fluid_content(organ_region),
            'calcification_likelihood': self.extract_calcification(organ_region),
        }
        
        return indicators

    def extract_size(self, organ_mask: np.ndarray) -> Dict:
        """Calculate organ size metrics."""
        area = np.sum(organ_mask > 0)
        if area == 0:
            return {'area_pixels': 0, 'status': 'small'}
        
        contours, _ = cv2.findContours(organ_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(cnt)
            return {
                'area_pixels': area,
                'width': w,
                'height': h,
                'status': 'normal' if 1000 < area < 50000 else ('enlarged' if area >= 50000 else 'small')
            }
        return {'area_pixels': area, 'status': 'unknown'}

    def extract_uniformity(self, organ_region: np.ndarray) -> Dict:
        """Measure homogeneity/uniformity of organ."""
        if len(organ_region) == 0:
            return {'std_dev': 0, 'uniformity_score': 0, 'status': 'unknown'}
        
        std_dev = np.std(organ_region)
        mean_val = np.mean(organ_region)
        
        # Coefficient of variation
        cv = (std_dev / mean_val * 100) if mean_val > 0 else 0
        
        # Uniformity score (0-100, higher = more uniform)
        uniformity_score = max(0, 100 - cv)
        
        status = 'uniform' if uniformity_score > 70 else ('heterogeneous' if uniformity_score < 40 else 'moderately_uniform')
        
        return {
            'std_dev': float(std_dev),
            'uniformity_score': float(uniformity_score),
            'status': status
        }

    def extract_boundary_sharpness(self, image: np.ndarray, organ_mask: np.ndarray) -> Dict:
        """Measure boundary/edge sharpness of organ."""
        # Apply Laplacian for edge detection
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        boundary_region = laplacian[organ_mask > 0]
        
        if len(boundary_region) == 0:
            return {'sharpness_score': 0, 'status': 'unknown'}
        
        sharpness_score = float(np.mean(np.abs(boundary_region)))
        status = 'sharp' if sharpness_score > 100 else ('blurred' if sharpness_score < 30 else 'moderate')
        
        return {
            'sharpness_score': sharpness_score,
            'status': status
        }

    def extract_mean_density(self, organ_region: np.ndarray) -> Dict:
        """Extract density (brightness) metrics."""
        if len(organ_region) == 0:
            return {'mean_density': 0, 'density_status': 'unknown'}
        
        mean_density = float(np.mean(organ_region))
        max_density = float(np.max(organ_region))
        min_density = float(np.min(organ_region))
        
        # Categorize density
        if mean_density < 85:
            density_status = 'hypoechoic'  # Dark
        elif mean_density > 170:
            density_status = 'hyperechoic'  # Bright
        else:
            density_status = 'isoechoic'  # Normal
        
        return {
            'mean_density': mean_density,
            'max_density': max_density,
            'min_density': min_density,
            'density_status': density_status
        }

    def extract_spots(self, organ_region: np.ndarray) -> Dict:
        """Detect spots, nodules, or calcifications."""
        if len(organ_region) == 0:
            return {'spots_count': 0, 'spots_status': 'no_spots'}
        
        # High-intensity spots (potential calcifications or bright spots)
        high_intensity_spots = np.sum(organ_region > 200)
        
        # Low-intensity spots (potential cysts or dark spots)
        low_intensity_spots = np.sum(organ_region < 50)
        
        total_spots = high_intensity_spots + low_intensity_spots
        
        spots_status = 'many_spots' if total_spots > 100 else ('few_spots' if total_spots > 10 else 'no_spots')
        
        return {
            'high_intensity_spots': int(high_intensity_spots),
            'low_intensity_spots': int(low_intensity_spots),
            'spots_count': int(total_spots),
            'spots_status': spots_status
        }

    def extract_edge_smoothness(self, image: np.ndarray, organ_mask: np.ndarray) -> Dict:
        """Measure smoothness of organ boundaries."""
        contours, _ = cv2.findContours(organ_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'smoothness_score': 0, 'edge_status': 'unknown'}
        
        cnt = max(contours, key=cv2.contourArea)
        
        # Perimeter and area for circularity
        perimeter = cv2.arcLength(cnt, True)
        area = cv2.contourArea(cnt)
        
        # Circularity measure (4π * area / perimeter²)
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter ** 2)
        else:
            circularity = 0
        
        smoothness_score = float(circularity * 100)
        edge_status = 'smooth' if circularity > 0.7 else ('irregular' if circularity < 0.5 else 'moderate')
        
        return {
            'smoothness_score': smoothness_score,
            'circularity': float(circularity),
            'edge_status': edge_status
        }

    def extract_vessel_presence(self, image: np.ndarray, organ_mask: np.ndarray) -> Dict:
        """Detect blood vessel presence and flow."""
        # Apply Sobel for vessel-like structures
        sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        vessel_region = magnitude[organ_mask > 0]
        
        if len(vessel_region) == 0:
            return {'vessel_presence': 0, 'vessel_status': 'unknown'}
        
        vessel_presence = float(np.mean(vessel_region))
        vessel_status = 'rich' if vessel_presence > 50 else ('poor' if vessel_presence < 20 else 'moderate')
        
        return {
            'vessel_presence': vessel_presence,
            'vessel_status': vessel_status
        }

    def extract_texture_homogeneity(self, organ_region: np.ndarray) -> Dict:
        """Measure texture homogeneity using entropy and variance."""
        if len(organ_region) == 0:
            return {'texture_homogeneity': 0, 'texture_status': 'unknown'}
        
        # Histogram-based entropy
        hist, _ = np.histogram(organ_region, bins=256, range=(0, 256))
        hist = hist / len(organ_region)
        entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))
        
        # Normalize entropy (max = 8 for 256 bins)
        normalized_entropy = entropy / 8 * 100
        
        # Homogeneity score (inverse of entropy)
        homogeneity_score = 100 - normalized_entropy
        
        texture_status = 'homogeneous' if homogeneity_score > 70 else ('heterogeneous' if homogeneity_score < 40 else 'moderate')
        
        return {
            'texture_homogeneity': float(homogeneity_score),
            'entropy': float(entropy),
            'texture_status': texture_status
        }

    def extract_fluid_content(self, organ_region: np.ndarray) -> Dict:
        """Detect fluid content (cysts, ascites, etc.)."""
        if len(organ_region) == 0:
            return {'fluid_likelihood': 0, 'fluid_status': 'no_fluid'}
        
        # Low-intensity regions indicate fluid
        fluid_pixels = np.sum(organ_region < 100)
        fluid_percentage = (fluid_pixels / len(organ_region)) * 100
        
        fluid_status = 'high_fluid' if fluid_percentage > 30 else ('some_fluid' if fluid_percentage > 10 else 'no_fluid')
        
        return {
            'fluid_percentage': float(fluid_percentage),
            'fluid_likelihood': float(fluid_percentage),
            'fluid_status': fluid_status
        }

    def extract_calcification(self, organ_region: np.ndarray) -> Dict:
        """Detect calcification likelihood (bright, high-density areas)."""
        if len(organ_region) == 0:
            return {'calcification_likelihood': 0, 'calcification_status': 'no_calcification'}
        
        # High-intensity regions indicate calcification
        calcified_pixels = np.sum(organ_region > 200)
        calcification_percentage = (calcified_pixels / len(organ_region)) * 100
        
        calcification_status = 'high_calc' if calcification_percentage > 20 else ('moderate_calc' if calcification_percentage > 5 else 'no_calcification')
        
        return {
            'calcification_percentage': float(calcification_percentage),
            'calcification_likelihood': float(calcification_percentage),
            'calcification_status': calcification_status
        }
