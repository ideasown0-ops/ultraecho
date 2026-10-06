"""
Main Window V1.0
Enhanced UI with AI Analysis, Database, and Advanced Features
"""

import logging
import os
from typing import Optional
from datetime import datetime
import uuid

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QProgressBar, QFileDialog,
    QCheckBox, QSlider, QDialog, QFormLayout, QLineEdit,
    QDateTimeEdit, QStatusBar, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal, QDateTime
from PySide6.QtGui import QPixmap, QImage, QIcon, QColor, QFont

import cv2
import numpy as np

from app.config import AppConfig
from app.video.device_manager import DeviceManager, VideoDevice
from app.video.capture_manager import CaptureManager
from app.video.video_player import VideoPlayer
from app.video.frame_processor import FrameProcessor

from ai_models_config import AIModelManager, ModelDownloadManager
from ai_engine_v1 import AIEngineV1, AIAnalysisResult
from database_manager import DatabaseManager, Patient, Examination, AnalysisReport

logger = logging.getLogger("ultrasound")


class FrameDisplayWidget(QWidget):
    """Custom widget for displaying ultrasound frames"""
    
    def __init__(self):
        super().__init__()
        self.image = None
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black;")
    
    def paintEvent(self, event):
        """Paint the frame"""
        from PySide6.QtGui import QPainter
        
        painter = QPainter(self)
        
        if self.image:
            # Draw the pixmap to fill the widget
            painter.drawPixmap(
                self.rect(),  # Target rectangle (full widget)
                self.image,   # Source pixmap
                self.image.rect()  # Source rectangle
            )
        else:
            # Draw black background
            painter.fillRect(self.rect(), self.palette().color(self.backgroundRole()))
        
        painter.end()


class PatientManagementDialog(QDialog):
    """Dialog for patient management"""
    
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
        self.age.setMaximum(120)
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
            'patient_id': self.patient_id.text(),
            'name': self.name.text(),
            'age': self.age.value(),
            'gender': self.gender.currentText(),
            'contact': self.contact.text(),
            'medical_history': self.medical_history.toPlainText()
        }


class AIAnalysisWidget(QWidget):
    """Widget for displaying AI analysis results"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Analysis results display
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Organ", "Confidence", "Quality", "Status"])
        
        layout.addWidget(QLabel("Detected Organs:"))
        layout.addWidget(self.results_table)
        
        # Quality assessment
        quality_group = QHBoxLayout()
        quality_group.addWidget(QLabel("Image Quality:"))
        self.quality_label = QLabel("Good")
        self.quality_label.setStyleSheet("color: green; font-weight: bold;")
        quality_group.addWidget(self.quality_label)
        self.quality_score = QProgressBar()
        self.quality_score.setMaximum(100)
        quality_group.addWidget(self.quality_score)
        
        layout.addLayout(quality_group)
        
        # Frame scoring
        score_group = QHBoxLayout()
        score_group.addWidget(QLabel("Frame Score:"))
        self.frame_score = QProgressBar()
        self.frame_score.setMaximum(100)
        score_group.addWidget(self.frame_score)
        self.is_best_label = QLabel("")
        score_group.addWidget(self.is_best_label)
        
        layout.addLayout(score_group)
        
        # Recommendations
        layout.addWidget(QLabel("Recommendations:"))
        self.recommendations = QTextEdit()
        self.recommendations.setReadOnly(True)
        self.recommendations.setMaximumHeight(100)
        layout.addWidget(self.recommendations)
        
        self.setLayout(layout)
    
    def update_analysis(self, analysis: AIAnalysisResult):
        """Update widget with analysis results"""
        # Clear table
        self.results_table.setRowCount(0)
        
        # Add organs
        for i, organ in enumerate(analysis.detected_organs):
            self.results_table.insertRow(i)
            self.results_table.setItem(i, 0, QTableWidgetItem(organ.organ_name))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{organ.confidence:.1f}%"))
            self.results_table.setItem(i, 2, QTableWidgetItem(analysis.quality_assessment.quality_level.value))
            status = "✓ Best Frame" if analysis.is_best_frame else ""
            self.results_table.setItem(i, 3, QTableWidgetItem(status))
        
        # Update quality
        quality_score = analysis.quality_assessment.overall_score
        self.quality_score.setValue(int(quality_score))
        self.quality_label.setText(f"{analysis.quality_assessment.quality_level.value.upper()}")
        
        # Color code
        if quality_score > 85:
            self.quality_label.setStyleSheet("color: green; font-weight: bold;")
        elif quality_score > 70:
            self.quality_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.quality_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Update frame score
        self.frame_score.setValue(int(analysis.frame_score))
        if analysis.is_best_frame:
            self.is_best_label.setText("⭐ BEST FRAME")
            self.is_best_label.setStyleSheet("color: gold; font-weight: bold;")
        else:
            self.is_best_label.setText("")
        
        # Update recommendations
        recommendations_text = "\n".join(analysis.quality_assessment.recommendations)
        self.recommendations.setText(recommendations_text if recommendations_text else "Image quality is good. No recommendations.")


class MainWindowV1(QMainWindow):
    """Main window for AI Ultrasound Assistant V1.0"""
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.setWindowTitle("AI Ultrasound Assistant - V1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
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
        
        # Setup status bar FIRST (before anything else that might use it)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)
        
        # Create shared UI components BEFORE setup_ui
        self.frame_display = FrameDisplayWidget()
        self.frame_info_label = QLabel("Ready")
        self.fps_label = QLabel("FPS: 0")
        
        # Setup UI
        self.setup_ui()
        self.load_devices()
        
        # Setup timers
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.setInterval(33)  # ~30 FPS
    
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Left panel - Controls
        left_panel = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Live Capture
        self.live_capture_tab = self.create_live_capture_tab()
        self.tabs.addTab(self.live_capture_tab, "Live Capture")
        
        # Tab 2: Recorded Video
        self.recorded_video_tab = self.create_recorded_video_tab()
        self.tabs.addTab(self.recorded_video_tab, "Recorded Video")
        
        # Tab 3: Patient Management
        self.patient_tab = self.create_patient_tab()
        self.tabs.addTab(self.patient_tab, "Patients")
        
        # Tab 4: AI Analysis
        self.analysis_tab = AIAnalysisWidget()
        self.tabs.addTab(self.analysis_tab, "AI Analysis")
        
        # Tab 5: Settings
        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Tab 6: About
        self.about_tab = self.create_about_tab()
        self.tabs.addTab(self.about_tab, "About")
        
        left_panel.addWidget(self.tabs)
        
        # Right panel - Video display
        right_panel = QVBoxLayout()
        
        # Frame display (created in __init__)
        right_panel.addWidget(self.frame_display)
        
        # Frame info (created in __init__)
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.frame_info_label)
        info_layout.addWidget(self.fps_label)
        
        right_panel.addLayout(info_layout)
        
        # Main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        
        central_widget.setLayout(main_layout)
    
    def create_live_capture_tab(self) -> QWidget:
        """Create live capture tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Device selection
        layout.addWidget(QLabel("Select Capture Device:"))
        
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        device_layout.addWidget(self.device_combo)
        
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.load_devices)
        device_layout.addWidget(refresh_btn)
        layout.addLayout(device_layout)
        
        # Resolution selection
        layout.addWidget(QLabel("Resolution:"))
        res_layout = QHBoxLayout()
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "800x600", "1024x768", "1280x720"])
        res_layout.addWidget(self.resolution_combo)
        layout.addLayout(res_layout)
        
        # FPS selection
        layout.addWidget(QLabel("Target FPS:"))
        fps_layout = QHBoxLayout()
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(5, 60)
        self.fps_spin.setValue(30)
        fps_layout.addWidget(self.fps_spin)
        layout.addLayout(fps_layout)
        
        # Controls
        control_layout = QHBoxLayout()
        
        self.start_capture_btn = QPushButton("Start Capture")
        self.start_capture_btn.clicked.connect(self.start_capture)
        control_layout.addWidget(self.start_capture_btn)
        
        self.stop_capture_btn = QPushButton("Stop Capture")
        self.stop_capture_btn.clicked.connect(self.stop_capture)
        self.stop_capture_btn.setEnabled(False)
        control_layout.addWidget(self.stop_capture_btn)
        
        layout.addLayout(control_layout)
        
        # Frame capture
        frame_layout = QHBoxLayout()
        self.capture_frame_btn = QPushButton("Capture Frame")
        self.capture_frame_btn.clicked.connect(self.capture_frame)
        self.capture_frame_btn.setEnabled(False)
        frame_layout.addWidget(self.capture_frame_btn)
        layout.addLayout(frame_layout)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.capture_status = QTextEdit()
        self.capture_status.setReadOnly(True)
        self.capture_status.setMaximumHeight(150)
        layout.addWidget(self.capture_status)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_recorded_video_tab(self) -> QWidget:
        """Create recorded video tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.video_path_label = QLabel("No video selected")
        file_layout.addWidget(self.video_path_label)
        
        browse_btn = QPushButton("Browse Video")
        browse_btn.clicked.connect(self.browse_video)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Video display
        layout.addWidget(QLabel("Video:"))
        layout.addWidget(self.frame_display)
        layout.addWidget(self.frame_info_label)
        
        # Playback controls
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.pause_video)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # Progress slider
        layout.addWidget(QLabel("Progress:"))
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setMinimum(0)
        self.video_slider.setMaximum(100)
        self.video_slider.sliderMoved.connect(self.on_slider_moved)
        self.video_slider.setEnabled(False)
        layout.addWidget(self.video_slider)
        
        # Frame capture
        capture_layout = QHBoxLayout()
        capture_frame_btn = QPushButton("📸 Capture Frame & Analyze")
        capture_frame_btn.clicked.connect(self.capture_from_video)
        capture_layout.addWidget(capture_frame_btn)
        layout.addLayout(capture_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_patient_tab(self) -> QWidget:
        """Create patient management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        new_patient_btn = QPushButton("New Patient")
        new_patient_btn.clicked.connect(self.new_patient)
        btn_layout.addWidget(new_patient_btn)
        
        new_exam_btn = QPushButton("New Examination")
        new_exam_btn.clicked.connect(self.new_examination)
        btn_layout.addWidget(new_exam_btn)
        
        layout.addLayout(btn_layout)
        
        # Patient list
        layout.addWidget(QLabel("Patients:"))
        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(4)
        self.patients_table.setHorizontalHeaderLabels(["ID", "Name", "Age", "Contact"])
        layout.addWidget(self.patients_table)
        
        # Refresh patient list
        self.refresh_patients_list()
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Application Settings"))
        
        # Window size
        layout.addWidget(QLabel("Window Size:"))
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setValue(self.config.get("window.width"))
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        layout.addLayout(size_layout)
        
        # AI Settings
        layout.addWidget(QLabel("AI Settings:"))
        self.gpu_checkbox = QCheckBox("Enable GPU Acceleration")
        self.gpu_checkbox.setChecked(self.config.get("ai.enable_gpu"))
        layout.addWidget(self.gpu_checkbox)
        
        # Model management
        layout.addWidget(QLabel("Model Management:"))
        download_models_btn = QPushButton("Download AI Models")
        download_models_btn.clicked.connect(self.download_models)
        layout.addWidget(download_models_btn)
        
        self.models_status = QLabel("Models status: Not checked")
        layout.addWidget(self.models_status)
        
        # Save settings
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_about_tab(self) -> QWidget:
        """Create about tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setText("""
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
        layout.addWidget(about_text)
        
        widget.setLayout(layout)
        return widget
    
    def load_devices(self):
        """Load available capture devices"""
        self.device_combo.clear()
        try:
            devices = self.device_manager.enumerate_devices()
        except Exception as e:
            logger.warning(f"Error enumerating devices: {e}")
            devices = []
        
        for device in devices:
            self.device_combo.addItem(f"{device.name} ({device.index})", device)
        
        if not devices:
            self.device_combo.addItem("No devices found")
        
        self.update_status(f"Found {len(devices)} capture device(s)")
    
    def start_capture(self):
        """Start live capture"""
        if self.device_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No capture device selected")
            return
        
        try:
            device = self.device_combo.currentData()
            if not isinstance(device, VideoDevice):
                QMessageBox.warning(self, "Error", "No valid device selected")
                return
            
            self.capture_manager = CaptureManager(device.index)
            
            if self.capture_manager.start():
                self.is_capturing = True
                self.start_capture_btn.setEnabled(False)
                self.stop_capture_btn.setEnabled(True)
                self.capture_frame_btn.setEnabled(True)
                self.display_timer.start()
                self.update_status(f"Capturing from {device.name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to start capture")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error starting capture: {str(e)}")
            logger.error(f"Capture error: {e}")
    
    def stop_capture(self):
        """Stop live capture"""
        if self.capture_manager:
            self.capture_manager.stop()
        
        self.is_capturing = False
        self.display_timer.stop()
        self.start_capture_btn.setEnabled(True)
        self.stop_capture_btn.setEnabled(False)
        self.capture_frame_btn.setEnabled(False)
        self.update_status("Capture stopped")
    
    def capture_frame(self):
        """Capture current frame"""
        if not self.capture_manager:
            return
        
        frame = self.capture_manager.get_latest_frame()
        if frame is not None:
            # Create frame ID
            self.current_frame_id += 1
            frame_id = f"F{self.current_frame_id:06d}"
            
            # Save frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frame_path = f"captures/{timestamp}_{frame_id}.jpg"
            os.makedirs("captures", exist_ok=True)
            cv2.imwrite(frame_path, frame)
            
            # Analyze with AI
            analysis = self.ai_engine.analyze_abdominal_ultrasound(frame, frame_id)
            self.analysis_tab.update_analysis(analysis)
            
            # Store in database
            if self.current_exam:
                organs = [o.organ_name for o in analysis.detected_organs]
                self.db_manager.add_captured_frame(
                    frame_id, self.current_exam, frame_path,
                    analysis.quality_assessment.overall_score, organs
                )
                
                # Add AI analysis
                analysis_id = f"A{self.current_frame_id:06d}"
                self.db_manager.add_ai_analysis(
                    analysis_id, frame_id, self.current_exam,
                    [o.organ_name for o in analysis.detected_organs],
                    analysis.quality_assessment.overall_score,
                    analysis.frame_score,
                    analysis.processing_time_ms,
                    analysis.models_used,
                    analysis.is_best_frame
                )
            
            self.update_status(f"Frame captured: {frame_id}")
    
    def browse_video(self):
        """Browse for video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)"
        )
        
        if file_path:
            if self.video_player.open_video(file_path):
                self.video_path_label.setText(os.path.basename(file_path))
                self.play_btn.setEnabled(True)
                self.video_slider.setEnabled(True)
                info = self.video_player.get_info()
                self.frame_info_label.setText(
                    f"Video: {info['total_frames']} frames @ {info['fps']:.1f} FPS | "
                    f"Size: {info['width']}x{info['height']}"
                )
                self.update_status(f"Video loaded: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to open video: {os.path.basename(file_path)}")
                self.update_status("Failed to load video")
    
    def play_video(self):
        """Play video"""
        self.video_player.play()
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.display_timer.start()
        self.update_status("Playing video")
    
    def pause_video(self):
        """Pause video"""
        self.video_player.pause()
        self.display_timer.stop()
        self.update_status("Video paused")
    
    def stop_video(self):
        """Stop video"""
        self.video_player.stop()
        self.display_timer.stop()
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.update_status("Video stopped")
    
    def on_slider_moved(self, value):
        """Handle slider position change"""
        if hasattr(self, 'video_player') and self.video_player.cap:
            frame_num = int((value / 100.0) * self.video_player.total_frames)
            self.video_player.seek(frame_num)
            frame = self.video_player.get_frame_at(frame_num)
            if frame is not None:
                self.display_frame(frame)
    
    def capture_from_video(self):
        """Capture current frame from video and analyze with AI"""
        if not hasattr(self, 'video_player') or self.video_player.current_frame is None:
            QMessageBox.warning(self, "Warning", "Please load and play a video first!")
            return
        
        frame = self.video_player.current_frame
        if frame is None:
            QMessageBox.warning(self, "Warning", "No frame available!")
            return
        
        frame_id = f"V{uuid.uuid4().hex[:8]}"
        
        try:
            # Make sure captures directory exists
            import os
            os.makedirs("captures", exist_ok=True)
            
            # Analyze with AI
            self.update_status(f"Analyzing frame {frame_id}...")
            logger.info(f"Starting AI analysis for frame {frame_id}")
            
            result = self.ai_engine.analyze_abdominal_ultrasound(frame, frame_id)
            
            logger.info(f"AI analysis complete: {len(result.detected_organs)} organs detected")
            logger.info(f"Quality: {result.quality_assessment.overall_score:.1f}, Score: {result.frame_score:.1f}")
            
            # Save frame
            frame_path = f"captures/{frame_id}.jpg"
            cv2.imwrite(frame_path, frame)
            logger.info(f"Frame saved to {frame_path}")
            
            # Display results
            self.display_ai_results(result)
            
            # Save to database
            if hasattr(self, 'current_patient_id') and hasattr(self, 'current_exam_id'):
                self.db_manager.add_captured_frame(
                    frame_id, self.current_exam_id, frame_path, result.quality_assessment.overall_score
                )
                self.db_manager.add_ai_analysis(
                    f"A{uuid.uuid4().hex[:8]}", frame_id, self.current_exam_id,
                    [o.organ_name for o in result.detected_organs],
                    result.quality_assessment.overall_score,
                    result.frame_score,
                    result.processing_time_ms,
                    result.models_used,
                    result.is_best_frame
                )
                logger.info("Results saved to database")
            
            self.update_status(f"Frame {frame_id} captured and analyzed!")
            
        except Exception as e:
            logger.error(f"Error capturing frame: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to capture/analyze frame: {e}")
    
    def new_patient(self):
        """Create new patient"""
        dialog = PatientManagementDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_patient_data()
            patient = Patient(
                patient_id=data['patient_id'],
                name=data['name'],
                age=data['age'],
                gender=data['gender'],
                contact=data['contact'],
                medical_history=data['medical_history']
            )
            
            if self.db_manager.add_patient(patient):
                self.current_patient = patient.patient_id
                self.refresh_patients_list()
                self.update_status(f"Patient {patient.name} added")
            else:
                QMessageBox.warning(self, "Error", "Failed to add patient")
    
    def new_examination(self):
        """Create new examination"""
        if not self.current_patient:
            QMessageBox.warning(self, "Error", "Please select or create a patient first")
            return
        
        exam_id = f"E{uuid.uuid4().hex[:8].upper()}"
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
        
        if self.db_manager.add_examination(exam):
            self.current_exam = exam_id
            self.update_status(f"Examination {exam_id} created")
        else:
            QMessageBox.warning(self, "Error", "Failed to create examination")
    
    def refresh_patients_list(self):
        """Refresh patient list table"""
        patients = self.db_manager.list_patients()
        self.patients_table.setRowCount(0)
        
        for i, patient in enumerate(patients):
            self.patients_table.insertRow(i)
            self.patients_table.setItem(i, 0, QTableWidgetItem(patient.patient_id))
            self.patients_table.setItem(i, 1, QTableWidgetItem(patient.name))
            self.patients_table.setItem(i, 2, QTableWidgetItem(str(patient.age)))
            self.patients_table.setItem(i, 3, QTableWidgetItem(patient.contact))
    
    def download_models(self):
        """Download AI models"""
        QMessageBox.information(self, "Models", "Model download feature coming in V1.1\nUsing local ONNX models for now")
    
    def save_settings(self):
        """Save application settings"""
        self.config.set("window.width", self.width_spin.value())
        self.config.set("ai.enable_gpu", self.gpu_checkbox.isChecked())
        self.config.save()
        self.update_status("Settings saved")
        QMessageBox.information(self, "Settings", "Settings saved successfully")
    
    def update_display(self):
        """Update display with latest frame (from capture or video)"""
        frame = None
        
        # Priority: Video playback over capture
        if hasattr(self, 'video_player') and self.video_player.is_playing:
            frame = self.video_player.get_current_frame()
            if frame is not None:
                try:
                    self.display_frame(frame)
                    # Update slider position
                    if hasattr(self, 'video_slider') and self.video_player.total_frames > 0:
                        self.video_slider.blockSignals(True)
                        slider_value = int((self.video_player.current_frame_num / self.video_player.total_frames) * 100)
                        self.video_slider.setValue(min(100, max(0, slider_value)))
                        self.video_slider.blockSignals(False)
                    # Update frame info
                    info = self.video_player.get_info()
                    self.frame_info_label.setText(
                        f"Frame: {info['current_frame']}/{info['total_frames']} | "
                        f"Size: {info['width']}x{info['height']} | "
                        f"FPS: {info['fps']:.1f}"
                    )
                except Exception as e:
                    logger.error(f"Error updating display: {e}")
        
        # Fallback to live capture
        elif self.is_capturing and self.capture_manager:
            frame = self.capture_manager.get_latest_frame()
            if frame is not None:
                self.display_frame(frame)
                stats = self.capture_manager.get_stats()
                self.fps_label.setText(f"FPS: {stats.current_fps:.1f}")
    
    def display_frame(self, frame):
        """Display frame on widget"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = frame_rgb.shape
        bytes_per_line = 3 * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale to widget
        scaled = pixmap.scaledToWidth(self.frame_display.width(), Qt.SmoothTransformation)
        self.frame_display.image = scaled
        self.frame_display.update()
        
        self.frame_info_label.setText(f"Size: {w}x{h}")
    
    def display_ai_results(self, result):
        """Display AI analysis results using AIAnalysisWidget"""
        try:
            logger.info(f"Displaying AI results...")
            logger.info(f"  Organs detected: {len(result.detected_organs)}")
            logger.info(f"  Quality score: {result.quality_assessment.overall_score:.1f}")
            logger.info(f"  Frame score: {result.frame_score:.1f}")
            
            # Use analysis_tab to display results
            if hasattr(self, 'analysis_tab'):
                self.analysis_tab.update_analysis(result)
                logger.info(f"Analysis widget updated with {len(result.detected_organs)} organs")
            else:
                logger.error("Analysis tab not found!")
                return
            
            # Switch to AI Analysis tab
            if hasattr(self, 'tabs'):
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == "AI Analysis":
                        self.tabs.setCurrentIndex(i)
                        logger.info("Switched to AI Analysis tab")
                        break
            
            logger.info(f"Results displayed successfully!")
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}", exc_info=True)
    
    def update_status(self, message: str):
        """Update status bar"""
        self.status_label.setText(message)
        logger.info(message)
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.capture_manager:
            self.capture_manager.stop()
        self.db_manager.close()
        event.accept()


if __name__ == "__main__":
    from app.config import AppConfig
    logging.basicConfig(level=logging.INFO)
    
    config = AppConfig()
    window = MainWindowV1(config)
    window.show()
