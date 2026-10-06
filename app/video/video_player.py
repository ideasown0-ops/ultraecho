import cv2
import logging

logger = logging.getLogger("ultrasound")

class VideoPlayer:
    """Video playback engine with full control"""
    
    def __init__(self):
        self.cap = None
        self.is_playing = False
        self.current_frame = None
        self.current_frame_num = 0
        self.total_frames = 0
        self.fps = 30
        self.width = 0
        self.height = 0
        self.file_path = None
    
    def open_video(self, path: str) -> bool:
        """Open video file"""
        try:
            self.cap = cv2.VideoCapture(path)
            if not self.cap.isOpened():
                logger.error(f"Failed to open video: {path}")
                return False
            
            # Get video properties
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.file_path = path
            self.current_frame_num = 0
            
            # Safety check
            if self.fps <= 0:
                self.fps = 30
            if self.total_frames <= 0:
                self.total_frames = 1000
            
            logger.info(f"Video opened: {self.total_frames} frames @ {self.fps} FPS ({self.width}x{self.height})")
            return True
        except Exception as e:
            logger.error(f"Error opening video: {e}")
            return False
    
    def play(self):
        """Start playback"""
        if self.cap and self.cap.isOpened():
            self.is_playing = True
            logger.info("Video playback started")
        else:
            logger.warning("No video loaded")
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
        logger.info("Video paused")
    
    def stop(self):
        """Stop and reset"""
        self.is_playing = False
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_num = 0
        logger.info("Video stopped")
    
    def seek(self, frame_num: int):
        """Jump to frame number"""
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            self.current_frame_num = frame_num
    
    def get_current_frame(self):
        """Get current frame"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        if self.is_playing:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.current_frame_num = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                return frame
            else:
                # Video ended
                self.is_playing = False
                self.stop()
                return None
        
        return self.current_frame
    
    def get_frame_at(self, frame_num: int):
        """Get specific frame without changing playback"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.cap.read()
        
        if ret:
            self.current_frame = frame
            self.current_frame_num = frame_num
            return frame
        else:
            # Restore position
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
            return None
    
    def close(self):
        """Close video file"""
        if self.cap:
            self.cap.release()
            self.cap = None
            self.is_playing = False
    
    def get_info(self) -> dict:
        """Get video information"""
        return {
            "file": self.file_path,
            "total_frames": self.total_frames,
            "current_frame": self.current_frame_num,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "is_playing": self.is_playing,
            "duration_sec": self.total_frames / self.fps if self.fps > 0 else 0
        }
