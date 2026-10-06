import cv2
import numpy as np

class FrameProcessor:
    @staticmethod
    def resize_frame(frame: np.ndarray, width: int = 640) -> np.ndarray:
        h, w = frame.shape[:2]
        aspect = w / h
        new_h = int(width / aspect)
        return cv2.resize(frame, (width, new_h))
    
    @staticmethod
    def convert_to_rgb(frame: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def save_frame(frame: np.ndarray, path: str):
        cv2.imwrite(path, frame)
    
    @staticmethod
    def add_fps_text(frame: np.ndarray, fps: float) -> np.ndarray:
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return frame
