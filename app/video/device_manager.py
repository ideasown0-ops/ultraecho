import cv2
from dataclasses import dataclass
from typing import List

@dataclass
class VideoDevice:
    index: int
    name: str
    driver: str = "DirectShow"

class DeviceManager:
    def enumerate_devices(self) -> List[VideoDevice]:
        devices = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append(VideoDevice(index=i, name=f"Video Capture Device {i}"))
                cap.release()
        return devices
