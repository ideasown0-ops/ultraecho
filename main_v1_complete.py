#!/usr/bin/env python3
"""
AI Ultrasound Assistant V1.0 - Main Entry Point
Complete application launcher with all features
"""

import sys
import os
import logging
from pathlib import Path

# Ensure app directory is in path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Create required directories
for directory in ['captures', 'videos', 'models', 'logs']:
    Path(directory).mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ultrasound.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ultrasound")

# Try importing PySide6, with helpful error message
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    logger.info("PySide6 imported successfully")
except ImportError as e:
    print(f"""
    ❌ ERROR: Missing dependency - PySide6
    
    Please install required packages:
    pip install -r requirements_v1.txt
    
    Or run on Windows:
    run.bat
    
    Error details: {e}
    """)
    sys.exit(1)

try:
    import cv2
    import numpy as np
    logger.info("OpenCV and NumPy imported successfully")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

def main():
    """Main application entry point"""
    
    logger.info("=" * 60)
    logger.info("AI Ultrasound Assistant V1.0")
    logger.info("Starting application...")
    logger.info("=" * 60)
    
    try:
        # Create Qt Application
        app = QApplication(sys.argv)
        app.setApplicationName("AI Ultrasound Assistant")
        app.setApplicationVersion("1.0")
        
        # Set application style
        app.setStyle('Fusion')
        
        logger.info("Qt Application initialized")
        
        # Import application components
        try:
            from main_window_v1 import MainWindowV1
            from app.config import AppConfig
            
            logger.info("Application components imported")
            
        except ImportError as e:
            logger.error(f"Failed to import application components: {e}")
            QMessageBox.critical(None, "Import Error",
                               f"Failed to import application components:\n{e}")
            return 1
        
        # Load configuration
        config = AppConfig()
        logger.info(f"Configuration loaded from {config.config_file}")
        
        # Create main window
        logger.info("Creating main window...")
        window = MainWindowV1(config)
        
        # Show window
        window.show()
        logger.info("Main window displayed")
        
        # Show version info
        logger.info("=" * 60)
        logger.info("V1.0 Features Enabled:")
        logger.info("  ✅ Live Capture from any DirectShow device")
        logger.info("  ✅ Recorded Video Playback (9+ formats)")
        logger.info("  ✅ AI Organ Detection (8 organs)")
        logger.info("  ✅ Image Quality Assessment")
        logger.info("  ✅ Best Frame Selection")
        logger.info("  ✅ Patient Management")
        logger.info("  ✅ Examination Tracking")
        logger.info("  ✅ SQLite Database")
        logger.info("  ✅ AI Analysis Reports")
        logger.info("=" * 60)
        
        # Print system info
        logger.info(f"Python: {sys.version}")
        logger.info(f"OpenCV: {cv2.__version__}")
        logger.info(f"NumPy: {np.__version__}")
        
        # Run application
        logger.info("Entering application event loop...")
        exit_code = app.exec()
        
        logger.info("Application exiting...")
        return exit_code
        
    except Exception as e:
        logger.error(f"Unexpected error in main(): {e}", exc_info=True)
        try:
            QMessageBox.critical(None, "Application Error",
                               f"An unexpected error occurred:\n{e}")
        except:
            print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
