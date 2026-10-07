"""
Main Window V1.0
Enhanced UI with AI Analysis, Database, and Advanced Features
"""

import logging
import os
from datetime import datetime
import uuid

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QComboBox,
    QSpinBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QProgressBar, QFileDialog,
    QCheckBox, QSlider, QDialog, QFormLayout, QLineEdit,
    QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter

import cv2

from app.config import AppConfig
from app.video.device_manager import DeviceManager, VideoDevice
from app.video.capture_manager import CaptureManager
from app.video.video_player import VideoPlayer

from ai_models_config import AIModelManager
from ai_engine_v1 import AIEngineV1, AIAnalysisResult
from database_manager import DatabaseManager, Patient, Examination

logger = logging.getLogger("ultrasound")


class FrameDisplayWidget(QWidget):
    """Custom widget for displaying ultrasound frames."""

    def __init__(self):
        super().__init__()
        self.image = None
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black;")

    def paintEvent(self, event):
        """Paint the current frame correctly using QPainter."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)

        if self.image is not None and not self.image.isNull():
            # Keep the complete image visible and centered.
            scaled = self.image.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2

            painter.drawPixmap(x, y, scaled)


class PatientManagementDialog(QDialog):
    """Dialog for patient management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patient Management")
        self.setGeometry(100, 100, 600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.patient_id = QLineEdit()
        self.patient_id.setText(f"P{uuid.uuid4().hex[:8].upper()}")

        self.name = QLineEdit()

        self.age = QSpinBox()
        self.age.setRange(0, 120)

        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])

        self.contact = QLineEdit()
        self.medical_history = QTextEdit()

        layout.addRow("Patient ID:", self.patient_id)
        layout.addRow("Name:", self.name)
        layout.addRow("Age:", self.age)
        layout.addRow("Gender:", self.gender)
        layout.addRow("Contact:", self.contact)
        layout.addRow("Medical History:", self.medical_history)

        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save Patient")
        save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

        self.setLayout(layout)

    def get_patient_data(self):
        return {
            "patient_id": self.patient_id.text(),
            "name": self.name.text(),
            "age": self.age.value(),
            "gender": self.gender.currentText(),
            "contact": self.contact.text(),
            "medical_history": self.medical_history.toPlainText(),
        }


class AIAnalysisWidget(QWidget):
    """Widget for displaying AI analysis results."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(
            ["Organ", "Confidence", "Quality", "Status"]
        )

        layout.addWidget(QLabel("Detected Organs:"))
        layout.addWidget(self.results_table)

        quality_group = QHBoxLayout()

        quality_group.addWidget(QLabel("Image Quality:"))

        self.quality_label = QLabel("Good")
        self.quality_label.setStyleSheet(
            "color: green; font-weight: bold;"
        )
        quality_group.addWidget(self.quality_label)

        self.quality_score = QProgressBar()
        self.quality_score.setMaximum(100)
        quality_group.addWidget(self.quality_score)

        layout.addLayout(quality_group)

        score_group = QHBoxLayout()

        score_group.addWidget(QLabel("Frame Score:"))

        self.frame_score = QProgressBar()
        self.frame_score.setMaximum(100)
        score_group.addWidget(self.frame_score)

        self.is_best_label = QLabel("")
        score_group.addWidget(self.is_best_label)

        layout.addLayout(score_group)

        layout.addWidget(QLabel("Recommendations:"))

        self.recommendations = QTextEdit()
        self.recommendations.setReadOnly(True)
        self.recommendations.setMaximumHeight(100)

        layout.addWidget(self.recommendations)

        self.setLayout(layout)

    def update_analysis(self, analysis: AIAnalysisResult):
        """Update widget with analysis results."""

        self.results_table.setRowCount(0)

        for i, organ in enumerate(analysis.detected_organs):
            self.results_table.insertRow(i)

            self.results_table.setItem(
                i, 0,
                QTableWidgetItem(organ.organ_name)
            )

            self.results_table.setItem(
                i, 1,
                QTableWidgetItem(f"{organ.confidence:.1f}%")
            )

            self.results_table.setItem(
                i, 2,
                QTableWidgetItem(
                    analysis.quality_assessment.quality_level.value
                )
            )

            status = "✓ Best Frame" if analysis.is_best_frame else ""

            self.results_table.setItem(
                i, 3,
                QTableWidgetItem(status)
            )

        quality_score = analysis.quality_assessment.overall_score

        self.quality_score.setValue(int(quality_score))

        self.quality_label.setText(
            analysis.quality_assessment.quality_level.value.upper()
        )

        if quality_score > 85:
            self.quality_label.setStyleSheet(
                "color: green; font-weight: bold;"
            )
        elif quality_score > 70:
            self.quality_label.setStyleSheet(
                "color: orange; font-weight: bold;"
            )
        else:
            self.quality_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

        self.frame_score.setValue(int(analysis.frame_score))

        if analysis.is_best_frame:
            self.is_best_label.setText("★ BEST FRAME")
            self.is_best_label.setStyleSheet(
                "color: gold; font-weight: bold;"
            )
        else:
            self.is_best_label.setText("")

        recommendations_text = "\n".join(
            analysis.quality_assessment.recommendations
        )

        self.recommendations.setText(
            recommendations_text
            if recommendations_text
            else "Image quality is good. No recommendations."
        )


class MainWindowV1(QMainWindow):
    """Main window for AI Ultrasound Assistant V1.0."""

    def __init__(self, config: AppConfig):
        super().__init__()

        self.config = config

        self.setWindowTitle("AI Ultrasound Assistant - V1.0")
        self.setGeometry(100, 100, 1400, 900)

        # Components
        self.device_manager = DeviceManager()
        self.capture_manager = None
        self.video_player = VideoPlayer()
        self.ai_engine = AIEngineV1()
        self.db_manager = DatabaseManager()
        self.model_manager = AIModelManager()

        # Current state
        self.current_patient = None
        self.current_exam = None
        self.current_frame_id = 0
        self.is_capturing = False

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)

        # Display timer
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.setInterval(33)

        # Setup UI
        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        """Setup the main UI."""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()

        left_panel = QVBoxLayout()

        self.tabs = QTabWidget()

        self.live_capture_tab = self.create_live_capture_tab()
        self.tabs.addTab(
            self.live_capture_tab,
            "Live Capture"
        )

        self.recorded_video_tab = self.create_recorded_video_tab()
        self.tabs.addTab(
            self.recorded_video_tab,
            "Recorded Video"
        )

        self.patient_tab = self.create_patient_tab()
        self.tabs.addTab(
            self.patient_tab,
            "Patients"
        )

        self.analysis_tab = AIAnalysisWidget()
        self.tabs.addTab(
            self.analysis_tab,
            "AI Analysis"
        )

        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(
            self.settings_tab,
            "Settings"
        )

        self.about_tab = self.create_about_tab()
        self.tabs.addTab(
            self.about_tab,
            "About"
        )

        left_panel.addWidget(self.tabs)

        right_panel = QVBoxLayout()

        self.frame_display = FrameDisplayWidget()
        right_panel.addWidget(self.frame_display)

        info_layout = QHBoxLayout()

        self.frame_info_label = QLabel("Ready")
        info_layout.addWidget(self.frame_info_label)

        self.fps_label = QLabel("FPS: 0")
        info_layout.addWidget(self.fps_label)

        right_panel.addLayout(info_layout)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        central_widget.setLayout(main_layout)

    def create_live_capture_tab(self) -> QWidget:
        """Create live capture tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Capture Device:"))

        device_layout = QHBoxLayout()

        self.device_combo = QComboBox()
        device_layout.addWidget(self.device_combo)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.load_devices)
        device_layout.addWidget(refresh_btn)

        layout.addLayout(device_layout)

        layout.addWidget(QLabel("Resolution:"))

        res_layout = QHBoxLayout()

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "640x480",
            "800x600",
            "1024x768",
            "1280x720"
        ])

        res_layout.addWidget(self.resolution_combo)
        layout.addLayout(res_layout)

        layout.addWidget(QLabel("Target FPS:"))

        fps_layout = QHBoxLayout()

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(5, 60)
        self.fps_spin.setValue(30)

        fps_layout.addWidget(self.fps_spin)
        layout.addLayout(fps_layout)

        control_layout = QHBoxLayout()

        self.start_capture_btn = QPushButton("Start Capture")
        self.start_capture_btn.clicked.connect(
            self.start_capture
        )

        control_layout.addWidget(
            self.start_capture_btn
        )

        self.stop_capture_btn = QPushButton("Stop Capture")
        self.stop_capture_btn.clicked.connect(
            self.stop_capture
        )
        self.stop_capture_btn.setEnabled(False)

        control_layout.addWidget(
            self.stop_capture_btn
        )

        layout.addLayout(control_layout)

        frame_layout = QHBoxLayout()

        self.capture_frame_btn = QPushButton("Capture Frame")
        self.capture_frame_btn.clicked.connect(
            self.capture_frame
        )
        self.capture_frame_btn.setEnabled(False)

        frame_layout.addWidget(
            self.capture_frame_btn
        )

        layout.addLayout(frame_layout)

        layout.addWidget(QLabel("Status:"))

        self.capture_status = QTextEdit()
        self.capture_status.setReadOnly(True)
        self.capture_status.setMaximumHeight(150)

        layout.addWidget(self.capture_status)

        layout.addStretch()

        widget.setLayout(layout)

        return widget

    def create_recorded_video_tab(self) -> QWidget:
        """Create recorded video tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        file_layout = QHBoxLayout()

        self.video_path_label = QLabel("No video selected")
        self.video_path_label.setWordWrap(True)

        file_layout.addWidget(
            self.video_path_label
        )

        browse_btn = QPushButton("Browse Video")
        browse_btn.clicked.connect(
            self.browse_video
        )

        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        control_layout = QHBoxLayout()

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(
            self.play_video
        )
        self.play_btn.setEnabled(False)

        control_layout.addWidget(
            self.play_btn
        )

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(
            self.pause_video
        )
        self.pause_btn.setEnabled(False)

        control_layout.addWidget(
            self.pause_btn
        )

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(
            self.stop_video
        )
        self.stop_btn.setEnabled(False)

        control_layout.addWidget(
            self.stop_btn
        )

        layout.addLayout(control_layout)

        layout.addWidget(QLabel("Progress:"))

        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.valueChanged.connect(self.seek_video)
        self.video_slider.setRange(0, 0)
        self.video_slider.setEnabled(False)
        self.video_slider.sliderMoved.connect(
            self.seek_video
        )

        layout.addWidget(self.video_slider)

        self.video_info = QLabel("No video loaded")
        self.video_info.setWordWrap(True)

        layout.addWidget(
            self.video_info
        )

        layout.addStretch()

        widget.setLayout(layout)

        return widget

    def create_patient_tab(self) -> QWidget:
        """Create patient management tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()

        new_patient_btn = QPushButton("New Patient")
        new_patient_btn.clicked.connect(
            self.new_patient
        )

        btn_layout.addWidget(
            new_patient_btn
        )

        new_exam_btn = QPushButton("New Examination")
        new_exam_btn.clicked.connect(
            self.new_examination
        )

        btn_layout.addWidget(
            new_exam_btn
        )

        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Patients:"))

        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(4)

        self.patients_table.setHorizontalHeaderLabels([
            "ID",
            "Name",
            "Age",
            "Contact"
        ])

        layout.addWidget(
            self.patients_table
        )

        self.refresh_patients_list()

        layout.addStretch()

        widget.setLayout(layout)

        return widget

    def create_settings_tab(self) -> QWidget:
        """Create settings tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Application Settings")
        )

        layout.addWidget(
            QLabel("Window Size:")
        )

        size_layout = QHBoxLayout()

        self.width_spin = QSpinBox()

        try:
            width_value = self.config.get("window.width")
        except Exception:
            width_value = 1400

        if not width_value:
            width_value = 1400

        self.width_spin.setRange(800, 3000)
        self.width_spin.setValue(int(width_value))

        size_layout.addWidget(
            QLabel("Width:")
        )
        size_layout.addWidget(
            self.width_spin
        )

        layout.addLayout(
            size_layout
        )

        layout.addWidget(
            QLabel("AI Settings:")
        )

        self.gpu_checkbox = QCheckBox(
            "Enable GPU Acceleration"
        )

        try:
            gpu_enabled = self.config.get(
                "ai.enable_gpu"
            )
        except Exception:
            gpu_enabled = False

        self.gpu_checkbox.setChecked(
            bool(gpu_enabled)
        )

        layout.addWidget(
            self.gpu_checkbox
        )

        layout.addWidget(
            QLabel("Model Management:")
        )

        download_models_btn = QPushButton(
            "Download AI Models"
        )
        download_models_btn.clicked.connect(
            self.download_models
        )

        layout.addWidget(
            download_models_btn
        )

        self.models_status = QLabel(
            "Models status: Not checked"
        )

        layout.addWidget(
            self.models_status
        )

        save_btn = QPushButton(
            "Save Settings"
        )
        save_btn.clicked.connect(
            self.save_settings
        )

        layout.addWidget(
            save_btn
        )

        layout.addStretch()

        widget.setLayout(layout)

        return widget

    def create_about_tab(self) -> QWidget:
        """Create about tab."""

        widget = QWidget()
        layout = QVBoxLayout()

        about_text = QTextEdit()
        about_text.setReadOnly(True)

        about_text.setHtml("""
        <h2>AI Ultrasound Assistant</h2>
        <p><b>Version:</b> 1.0</p>

        <h3>Features:</h3>
        <ul>
        <li>Live ultrasound capture from DirectShow devices</li>
        <li>Support for recorded video files (MP4, AVI, MKV, etc.)</li>
        <li>AI-powered organ detection</li>
        <li>Image quality assessment</li>
        <li>Best frame selection</li>
        <li>Patient management and examination tracking</li>
        <li>SQLite database for data persistence</li>
        </ul>

        <h3>Supported Organs (Abdominal):</h3>
        <ul>
        <li>Liver</li>
        <li>Kidneys (left and right)</li>
        <li>Pancreas</li>
        <li>Spleen</li>
        <li>Gallbladder</li>
        <li>Bile ducts</li>
        <li>Bladder</li>
        <li>Abdominal aorta</li>
        </ul>

        <h3>System Requirements:</h3>
        <ul>
        <li>Windows 10 or 11</li>
        <li>Python 3.12+</li>
        <li>4GB RAM (8GB recommended)</li>
        <li>USB capture device or DirectShow-compatible hardware</li>
        </ul>
        """)

        layout.addWidget(
            about_text
        )

        widget.setLayout(layout)

        return widget

    def load_devices(self):
        """Load available capture devices."""

        self.device_combo.clear()

        devices = self.device_manager.enumerate_devices()

        for device in devices:
            self.device_combo.addItem(
                f"{device.name} ({device.index})",
                device
            )

        if not devices:
            self.device_combo.addItem(
                "No devices found",
                None
            )

        self.update_status(
            f"Found {len(devices)} capture device(s)"
        )

    def start_capture(self):
        """Start live capture."""

        if self.device_combo.count() == 0:
            QMessageBox.warning(
                self,
                "Error",
                "No capture device selected"
            )
            return

        try:
            device = self.device_combo.currentData()

            if not isinstance(device, VideoDevice):
                QMessageBox.warning(
                    self,
                    "Error",
                    "No valid device selected"
                )
                return

            self.capture_manager = CaptureManager(
                device.index
            )

            if self.capture_manager.start():
                self.is_capturing = True

                self.start_capture_btn.setEnabled(False)
                self.stop_capture_btn.setEnabled(True)
                self.capture_frame_btn.setEnabled(True)

                self.display_timer.start()

                self.update_status(
                    f"Capturing from {device.name}"
                )

            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to start capture"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error starting capture: {str(e)}"
            )
            logger.exception(
                "Capture error"
            )

    def stop_capture(self):
        """Stop live capture."""

        if self.capture_manager:
            self.capture_manager.stop()

        self.is_capturing = False

        # Only stop timer if recorded video is not playing.
        if not self.video_player.is_playing:
            self.display_timer.stop()

        self.start_capture_btn.setEnabled(True)
        self.stop_capture_btn.setEnabled(False)
        self.capture_frame_btn.setEnabled(False)

        self.update_status(
            "Capture stopped"
        )

    def capture_frame(self):
        """Capture current live frame."""

        if not self.capture_manager:
            return

        frame = self.capture_manager.get_latest_frame()

        if frame is None:
            return

        self.current_frame_id += 1

        frame_id = f"F{self.current_frame_id:06d}"

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        frame_path = (
            f"captures/{timestamp}_{frame_id}.jpg"
        )

        os.makedirs(
            "captures",
            exist_ok=True
        )

        cv2.imwrite(
            frame_path,
            frame
        )

        analysis = (
            self.ai_engine.analyze_abdominal_ultrasound(
                frame,
                frame_id
            )
        )

        self.analysis_tab.update_analysis(
            analysis
        )

        if self.current_exam:
            organs = [
                o.organ_name
                for o in analysis.detected_organs
            ]

            self.db_manager.add_captured_frame(
                frame_id,
                self.current_exam,
                frame_path,
                analysis.quality_assessment.overall_score,
                organs
            )

            analysis_id = (
                f"A{self.current_frame_id:06d}"
            )

            self.db_manager.add_ai_analysis(
                analysis_id,
                frame_id,
                self.current_exam,
                organs,
                analysis.quality_assessment.overall_score,
                analysis.frame_score,
                analysis.processing_time_ms,
                analysis.models_used,
                analysis.is_best_frame
            )

        self.update_status(
            f"Frame captured: {frame_id}"
        )

    def browse_video(self):
        """Browse for and load a recorded ultrasound video."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.m4v);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Stop any currently running playback.
            self.display_timer.stop()

            if self.video_player:
                self.video_player.pause()

            # Open the selected file.
            opened = self.video_player.open_video(file_path)

            if not opened:
                QMessageBox.critical(
                    self,
                    "Video Error",
                    f"Failed to open video:\n{file_path}"
                )
                self.update_status("Failed to open video")
                return

            info = self.video_player.get_info()

            # Update UI.
            self.video_path_label.setText(os.path.basename(file_path))
            self.video_path_label.setToolTip(file_path)

            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

            total_frames = max(1, int(info["total_frames"]))
            self.video_slider.blockSignals(True)
            self.video_slider.setMinimum(0)
            self.video_slider.setMaximum(total_frames - 1)
            self.video_slider.setValue(0)
            self.video_slider.blockSignals(False)

            self.video_info.setText(
                f"Frame: 0/{info['total_frames']} | "
                f"{info['width']}x{info['height']} | "
                f"{info['fps']:.2f} FPS | "
                f"Duration: {info['duration_sec']:.1f}s"
            )

            # Show the first frame immediately.
            first_frame = self.video_player.get_frame_at(0)

            if first_frame is not None:
                self.display_frame(first_frame)
                self.frame_info_label.setText(
                    f"Recorded video: {info['width']}x{info['height']}"
                )
            else:
                logger.warning("Video opened but first frame could not be read")

            # Use the video's actual FPS.
            fps = float(info.get("fps", 30.0) or 30.0)
            if fps <= 0:
                fps = 30.0

            interval = max(1, int(round(1000.0 / fps)))
            self.display_timer.setInterval(interval)

            self.update_status(
                f"Video loaded: {os.path.basename(file_path)} "
                f"({info['total_frames']} frames, {fps:.2f} FPS)"
            )

        except Exception as e:
            logger.exception("Error loading recorded video")
            QMessageBox.critical(
                self,
                "Video Error",
                f"Error loading video:\n{e}"
            )
            self.update_status("Video loading failed")

    def play_video(self):
        """Start recorded video playback."""
        try:
            if not self.video_player or not self.video_player.cap:
                QMessageBox.warning(
                    self,
                    "No Video",
                    "Please select a video first."
                )
                return

            info = self.video_player.get_info()

            fps = float(info.get("fps", 30.0) or 30.0)
            if fps <= 0:
                fps = 30.0

            self.display_timer.setInterval(
                max(1, int(round(1000.0 / fps)))
            )

            self.video_player.play()

            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

            self.display_timer.start()

            self.update_status("Playing recorded video")

        except Exception as e:
            logger.exception("Error starting video playback")
            QMessageBox.critical(
                self,
                "Playback Error",
                f"Error starting playback:\n{e}"
            )

    def pause_video(self):
        """Pause recorded video playback."""
        try:
            if self.video_player:
                self.video_player.pause()

            self.display_timer.stop()

            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            self.update_status("Video paused")

        except Exception as e:
            logger.exception("Error pausing video")

    def stop_video(self):
        """Stop recorded video and return to first frame."""
        try:
            self.display_timer.stop()

            if self.video_player:
                self.video_player.stop()

                frame = self.video_player.get_frame_at(0)

                if frame is not None:
                    self.display_frame(frame)

                info = self.video_player.get_info()

                self.video_slider.blockSignals(True)
                self.video_slider.setValue(0)
                self.video_slider.blockSignals(False)

                self.video_info.setText(
                    f"Frame: 0/{info['total_frames']} | "
                    f"{info['width']}x{info['height']} | "
                    f"{info['fps']:.2f} FPS | "
                    f"Duration: {info['duration_sec']:.1f}s"
                )

            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

            self.update_status("Video stopped")

        except Exception as e:
            logger.exception("Error stopping video")

    def seek_video(self, frame_num: int):
        """Seek recorded video to a specific frame."""

        if not self.video_player.cap:
            return

        was_playing = self.video_player.is_playing

        self.video_player.seek(
            int(frame_num)
        )

        frame = self.video_player.get_frame_at(
            int(frame_num)
        )

        if frame is not None:
            self.display_frame(frame)

        self.update_video_ui()

        # Restore playback state.
        if was_playing:
            self.video_player.play()

    def update_video_ui(self):
        """Update recorded-video controls and information."""

        info = self.video_player.get_info()

        if info["total_frames"] > 0:
            self.video_slider.blockSignals(True)

            self.video_slider.setValue(
                max(
                    0,
                    min(
                        info["current_frame"],
                        info["total_frames"] - 1
                    )
                )
            )

            self.video_slider.blockSignals(False)

        self.video_info.setText(
            self.format_video_info(info)
        )

        if info["fps"] > 0:
            self.fps_label.setText(
                f"FPS: {info['fps']:.1f}"
            )

    @staticmethod
    def format_video_info(info: dict) -> str:
        """Format video metadata for the UI."""

        fps = info.get("fps", 0)
        current = info.get("current_frame", 0)
        total = info.get("total_frames", 0)
        width = info.get("width", 0)
        height = info.get("height", 0)
        duration = info.get("duration_sec", 0)

        current_seconds = (
            current / fps
            if fps > 0
            else 0
        )

        def fmt_time(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        return (
            f"Frame: {current + 1}/{total} | "
            f"Resolution: {width}x{height} | "
            f"FPS: {fps:.1f} | "
            f"Time: {fmt_time(current_seconds)} / "
            f"{fmt_time(duration)}"
        )

    def new_patient(self):
        """Create new patient."""

        dialog = PatientManagementDialog(
            self
        )

        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_patient_data()

            patient = Patient(
                patient_id=data["patient_id"],
                name=data["name"],
                age=data["age"],
                gender=data["gender"],
                contact=data["contact"],
                medical_history=data["medical_history"]
            )

            if self.db_manager.add_patient(
                patient
            ):
                self.current_patient = (
                    patient.patient_id
                )

                self.refresh_patients_list()

                self.update_status(
                    f"Patient {patient.name} added"
                )

            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to add patient"
                )

    def new_examination(self):
        """Create new examination."""

        if not self.current_patient:
            QMessageBox.warning(
                self,
                "Error",
                "Please select or create a patient first"
            )
            return

        exam_id = (
            f"E{uuid.uuid4().hex[:8].upper()}"
        )

        exam = Examination(
            exam_id=exam_id,
            patient_id=self.current_patient,
            exam_type="abdominal",
            exam_date=datetime.now().isoformat(),
            modality="ultrasound",
            indication="General ultrasound examination",
            findings="",
            status="in_progress"
        )

        if self.db_manager.add_examination(
            exam
        ):
            self.current_exam = exam_id

            self.update_status(
                f"Examination {exam_id} created"
            )

        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to create examination"
            )

    def refresh_patients_list(self):
        """Refresh patient list table."""

        patients = self.db_manager.list_patients()

        self.patients_table.setRowCount(0)

        for i, patient in enumerate(patients):
            self.patients_table.insertRow(i)

            self.patients_table.setItem(
                i,
                0,
                QTableWidgetItem(
                    patient.patient_id
                )
            )

            self.patients_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    patient.name
                )
            )

            self.patients_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    str(patient.age)
                )
            )

            self.patients_table.setItem(
                i,
                3,
                QTableWidgetItem(
                    patient.contact
                )
            )

    def download_models(self):
        """Download AI models."""

        QMessageBox.information(
            self,
            "Models",
            (
                "Model download feature coming in V1.1\n"
                "Using local ONNX models for now"
            )
        )

    def save_settings(self):
        """Save application settings."""

        self.config.set(
            "window.width",
            self.width_spin.value()
        )

        self.config.set(
            "ai.enable_gpu",
            self.gpu_checkbox.isChecked()
        )

        self.config.save()

        self.update_status(
            "Settings saved"
        )

        QMessageBox.information(
            self,
            "Settings",
            "Settings saved successfully"
        )

    def update_display(self):
        """
        Update the main video area.

        Source priority:
        1. Recorded video when it is playing.
        2. Live capture when active.
        """

        try:
            # ------------------------------------------------
            # Recorded video
            # ------------------------------------------------
            if self.video_player and self.video_player.is_playing:
                frame = self.video_player.get_current_frame()

                if frame is not None:
                    self.display_frame(frame)

                    info = self.video_player.get_info()

                    current_frame = int(info.get("current_frame", 0))
                    total_frames = int(info.get("total_frames", 0))

                    if total_frames > 0:
                        self.video_slider.blockSignals(True)
                        self.video_slider.setMinimum(0)
                        self.video_slider.setMaximum(
                            max(0, total_frames - 1)
                        )
                        self.video_slider.setValue(
                            min(current_frame, total_frames - 1)
                        )
                        self.video_slider.blockSignals(False)

                    self.video_info.setText(
                        f"Frame: {current_frame + 1}/{total_frames} | "
                        f"{info['width']}x{info['height']} | "
                        f"{info['fps']:.2f} FPS | "
                        f"Duration: {info['duration_sec']:.1f}s"
                    )

                    self.fps_label.setText(
                        f"FPS: {info['fps']:.1f}"
                    )

                else:
                    # End of recorded video.
                    self.display_timer.stop()

                    self.play_btn.setEnabled(True)
                    self.pause_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)

                    self.update_status("Video playback finished")

                return

            # ------------------------------------------------
            # Live capture
            # ------------------------------------------------
            if self.is_capturing and self.capture_manager:
                frame = self.capture_manager.get_latest_frame()

                if frame is not None:
                    self.display_frame(frame)

                    stats = self.capture_manager.get_stats()

                    self.fps_label.setText(
                        f"FPS: {stats.current_fps:.1f}"
                    )

        except Exception as e:
            logger.exception("Error updating video display")

    def display_frame(self, frame):
        """Display an OpenCV BGR frame in FrameDisplayWidget."""
        try:
            if frame is None:
                return

            if not isinstance(frame, np.ndarray):
                logger.warning("display_frame received non-NumPy frame")
                return

            if frame.size == 0:
                logger.warning("display_frame received empty frame")
                return

            # OpenCV uses BGR; Qt expects RGB.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            height, width, channels = frame_rgb.shape

            # Keep the underlying RGB memory alive through QImage.copy().
            bytes_per_line = channels * width

            qimage = QImage(
                frame_rgb.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888
            ).copy()

            pixmap = QPixmap.fromImage(qimage)

            # FrameDisplayWidget is a custom QWidget.
            # It draws self.image inside paintEvent().
            self.frame_display.image = pixmap
            self.frame_display.update()

            # Update basic frame information.
            if hasattr(self, "frame_info_label"):
                self.frame_info_label.setText(
                    f"Frame: {width}x{height}"
                )

        except Exception as e:
            logger.exception(f"Error displaying video frame: {e}")
    def update_status(self, message: str):
        """Update status bar."""

        self.status_label.setText(
            message
        )

        logger.info(message)

    def closeEvent(self, event):
        """Handle window close."""
        try:
            self.display_timer.stop()

            if self.capture_manager:
                self.capture_manager.stop()

            if self.video_player:
                self.video_player.close()

            self.db_manager.close()

        except Exception as e:
            logger.exception(
                f"Error during application shutdown: {e}"
            )

        event.accept()





