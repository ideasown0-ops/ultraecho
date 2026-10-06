"""
AI Models Configuration and Management
Handles ONNX model downloading, caching, and inference
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import urllib.request
import urllib.error

import numpy as np

logger = logging.getLogger("ultrasound")


@dataclass
class ModelConfig:
    """Configuration for a single AI model"""
    name: str
    model_id: str
    url: str
    local_path: str
    size_mb: float
    hash: str
    task: str  # "organ_detection", "quality_assessment", "frame_selection"
    organs: List[str]
    version: str
    enabled: bool = True


class AIModelManager:
    """Manages downloading, caching, and using ONNX models"""
    
    # Model Registry
    MODELS = {
        "organ_detection_v1": ModelConfig(
            name="Organ Detection Model",
            model_id="yolov8n-abdomen-organs",
            url="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx",
            local_path="models/organ_detection.onnx",
            size_mb=12.5,
            hash="abcd1234",
            task="organ_detection",
            organs=["liver", "kidney", "pancreas", "spleen", "gallbladder", "bladder", "aorta", "bile_duct"],
            version="1.0"
        ),
        "quality_assessment_v1": ModelConfig(
            name="Image Quality Assessment",
            model_id="resnet50-ultrasound-quality",
            url="https://github.com/torchvision/models/releases/download/v0.1.0/resnet50.onnx",
            local_path="models/image_quality.onnx",
            size_mb=98.0,
            hash="efgh5678",
            task="quality_assessment",
            organs=[],
            version="1.0"
        ),
        "frame_selection_v1": ModelConfig(
            name="Best Frame Selection",
            model_id="frame-selector-abdomen",
            url="https://raw.githubusercontent.com/pytorch/vision/master/torchvision/models/detection/backbone_utils.py",
            local_path="models/frame_selection.onnx",
            size_mb=45.0,
            hash="ijkl9012",
            task="frame_selection",
            organs=[],
            version="1.0"
        ),
        "segmentation_v1": ModelConfig(
            name="Organ Segmentation",
            model_id="unet-abdomen-segmentation",
            url="https://github.com/milesial/Pytorch-UNet/releases/download/v3.0/checkpoint.pth",
            local_path="models/segmentation.onnx",
            size_mb=78.0,
            hash="mnop3456",
            task="segmentation",
            organs=["liver", "kidney", "pancreas", "spleen"],
            version="1.0"
        )
    }
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.models_dir / "models_config.json"
        self.loaded_models = {}
        self._load_config()
    
    def _load_config(self):
        """Load model configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def _save_config(self):
        """Save model configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def download_model(self, model_key: str, progress_callback=None) -> bool:
        """Download a model from remote URL"""
        if model_key not in self.MODELS:
            logger.error(f"Unknown model: {model_key}")
            return False
        
        model_config = self.MODELS[model_key]
        local_path = self.models_dir / model_config.local_path
        
        # Check if already exists
        if local_path.exists():
            logger.info(f"Model {model_key} already downloaded")
            return True
        
        logger.info(f"Downloading {model_config.name}...")
        
        try:
            def download_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(downloaded * 100 / total_size, 100)
                    if progress_callback:
                        progress_callback(percent, downloaded, total_size)
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(
                model_config.url,
                str(local_path),
                reporthook=download_progress
            )
            
            self.config[model_key] = {
                "downloaded": True,
                "path": str(local_path),
                "size_mb": model_config.size_mb,
                "timestamp": str(Path(local_path).stat().st_mtime)
            }
            self._save_config()
            
            logger.info(f"Downloaded {model_key} successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {model_key}: {e}")
            return False
    
    def load_model(self, model_key: str):
        """Load ONNX model for inference"""
        try:
            # For V1.0, we use stubs
            # In production, use: import onnxruntime as rt
            # session = rt.InferenceSession(model_path)
            
            if model_key not in self.MODELS:
                logger.error(f"Unknown model: {model_key}")
                return None
            
            model_config = self.MODELS[model_key]
            
            # Stub: return model config
            self.loaded_models[model_key] = {
                "config": model_config,
                "status": "ready",
                "inference_count": 0
            }
            
            logger.info(f"Loaded model: {model_key}")
            return self.loaded_models[model_key]
            
        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.MODELS.keys())
    
    def get_model_info(self, model_key: str) -> Optional[Dict]:
        """Get information about a specific model"""
        if model_key in self.MODELS:
            model = self.MODELS[model_key]
            return {
                "name": model.name,
                "task": model.task,
                "organs": model.organs,
                "size_mb": model.size_mb,
                "version": model.version,
                "downloaded": (self.models_dir / model.local_path).exists()
            }
        return None
    
    def get_models_by_task(self, task: str) -> List[str]:
        """Get models for a specific task"""
        return [k for k, v in self.MODELS.items() if v.task == task]
    
    def get_models_for_organ(self, organ: str) -> List[str]:
        """Get models that can detect a specific organ"""
        return [k for k, v in self.MODELS.items() if organ in v.organs]


class ModelDownloadManager:
    """Handles batch model downloading with progress tracking"""
    
    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
        self.download_queue = []
        self.total_size_mb = 0
        self.downloaded_size_mb = 0
    
    def add_to_queue(self, model_keys: List[str]):
        """Add models to download queue"""
        for key in model_keys:
            if key in self.model_manager.MODELS:
                model = self.model_manager.MODELS[key]
                self.download_queue.append(key)
                self.total_size_mb += model.size_mb
    
    def download_all(self, progress_callback=None) -> bool:
        """Download all models in queue"""
        for i, model_key in enumerate(self.download_queue):
            logger.info(f"Downloading {i+1}/{len(self.download_queue)}: {model_key}")
            
            def model_progress(percent, downloaded, total):
                overall_percent = (self.downloaded_size_mb + downloaded/1024/1024) / self.total_size_mb * 100
                if progress_callback:
                    progress_callback(overall_percent, model_key, percent)
            
            if not self.model_manager.download_model(model_key, model_progress):
                logger.error(f"Failed to download {model_key}")
                return False
            
            model = self.model_manager.MODELS[model_key]
            self.downloaded_size_mb += model.size_mb
        
        return True


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    manager = AIModelManager()
    
    print("Available models:")
    for model_key in manager.get_available_models():
        info = manager.get_model_info(model_key)
        print(f"  - {info['name']} ({model_key})")
    
    print("\nOdels for organ detection:")
    for key in manager.get_models_by_task("organ_detection"):
        print(f"  - {key}")
    
    print("\nModels for liver detection:")
    for key in manager.get_models_for_organ("liver"):
        print(f"  - {key}")
