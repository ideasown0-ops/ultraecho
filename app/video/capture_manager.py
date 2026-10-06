import cv2
import threading
import numpy as np
from dataclasses import dataclass

@dataclass
class CaptureStats:
    current_fps: float
    resolution: tuple
    frame_count: int
    dropped_frames: int

class CaptureManager:
    def __init__(self, device_index: int):
        self.device_index = device_index
        self.cap = None
        self.running = False
        self.latest_frame = None
        self.thread = None
        self.frame_count = 0
        self.fps = 0
    
    def start(self) -> bool:
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            return False
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True
    
    def _capture_loop(self):
        import time
        prev_time = time.time()
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.latest_frame = frame
                self.frame_count += 1
                curr_time = time.time()
                if curr_time - prev_time > 0.1:
                    self.fps = 1 / (curr_time - prev_time)
                    prev_time = curr_time
    
    def get_latest_frame(self):
        return self.latest_frame
    
    def get_stats(self) -> CaptureStats:
        h, w = (0, 0) if self.latest_frame is None else (self.latest_frame.shape[0], self.latest_frame.shape[1])
        return CaptureStats(self.fps, (w, h), self.frame_count, 0)
    
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
