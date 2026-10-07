import sys
import os
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.utils.logger import logger

def main():
    logger.info("Initializing AI Ultrasound Assistant V0.1...")
    os.makedirs("captures", exist_ok=True)
    os.makedirs("videos", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
