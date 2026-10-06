import json
from pathlib import Path
from typing import Any, Optional

class AppConfig:
    """Application configuration manager"""
    
    _instance = None
    DEFAULT_CONFIG = {
        "window": {"width": 1400, "height": 900, "maximized": False},
        "video": {"capture_device_id": -1, "default_resolution": "640x480", "target_fps": 30, "show_fps": True},
        "ai": {"backend": "cpu", "enable_gpu": False},
        "paths": {"captures_dir": "captures", "videos_dir": "videos", "models_dir": "models"},
        "logging": {"level": "INFO"}
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = "settings.json"):
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        self._load()
    
    def _load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.config.update(json.load(f))
            except: pass
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self.save()
    
    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
