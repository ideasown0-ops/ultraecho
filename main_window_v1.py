"""
Main Window V1.0 - نسخة مصححة بالكامل
- إصلاح عرض الفيديو (paintEvent كان خاطئاً)
- شريط الحالة يُنشأ أولاً
- update_display يدعم الفيديو المسجل والبث المباشر
- زر تحليل متقدم في تبويب البث المباشر وتبويب الفيديو
"""

import logging
import os
import sys
import uuid
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QComboBox,
    QSpinBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QProgressBar, QFileDialog,
    QCheckBox, QSlider, QDialog, QFormLayout, QLineEdit,
    QStatusBar, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter

import cv2
import numpy as np

from app.config import AppConfig
from app.video.device_manager import DeviceManager, VideoDevice
from app.video.capture_manager import CaptureManager
from app.video.video_player import VideoPlayer

from ai_models_config import AIModelManager
from ai_engine_v1 import AIEngineV1, AIAnalysisResult
from ai_engine_v1_enhanced import AIEngineV1Enhanced
from diagnosis_widget import DiagnosisWidget
from database_manager import DatabaseManager, Patient, Examination

logger = logging.getLogger("ultrasound")


class FrameDisplayWidget(QWidget):
    """ويدجت عرض الفيديو - يرسم الصورة مع الحفاظ على النسبة"""

    def __init__(self):
        super().__init__()
        self.image = None  # QPixmap
        self.setMinimumSize(640, 480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAutoFillBackground(False)

    def set_pixmap(self, pixmap: QPixmap):
        self.image = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)

        if self.image is not None and not self.image.isNull():
            scaled = self.image.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

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

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Organ", "Confidence", "Quality", "Status"])
        layout.addWidget(QLabel("Detected Organs:"))
        layout.addWidget(self.results_table)

        quality_group = QHBoxLayout()
        quality_group.addWidget(QLabel("Image Quality:"))
        self.quality_label = QLabel("Good")
        self.quality_label.setStyleSheet("color: green; font-weight: bold;")
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
        self.results_table.setRowCount(0)

        for i, organ in enumerate(analysis.detected_organs):
            self.results_table.insertRow(i)
            self.results_table.setItem(i, 0, QTableWidgetItem(organ.organ_name))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{organ.confidence:.1f}%"))
            self.results_table.setItem(i, 2, QTableWidgetItem(analysis.quality_assessment.quality_level.value))
            status = "✓ Best Frame" if analysis.is_best_frame else ""
            self.results_table.setItem(i, 3, QTableWidgetItem(status))

        quality_score = analysis.quality_assessment.overall_score
        self.quality_score.setValue(int(quality_score))
        self.quality_label.setText(f"{analysis.quality_assessment.quality_level.value.upper()}")

        if quality_score > 85:
            self.quality_label.setStyleSheet("color: green; font-weight: bold;")
        elif quality_score > 70:
            self.quality_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.quality_label.setStyleSheet("color: red; font-weight: bold;")

        self.frame_score.setValue(int(analysis.frame_score))
        if analysis.is_best_frame:
            self.is_best_label.setText("⭐ BEST FRAME")
            self.is_best_label.setStyleSheet("color: gold; font-weight: bold;")
        else:
            self.is_best_label.setText("")

        text = "\n".join(analysis.quality_assessment.recommendations)
        self.recommendations.setText(text if text else "Image quality is good. No recommendations.")


class MainWindowV1(QMainWindow):
    """Main window for AI Ultrasound Assistant V1.0"""

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.setWindowTitle("AI Ultrasound Assistant - V1.0")
        self.setGeometry(100, 100, 1400, 900)

        # 1) شريط الحالة أولاً (قبل أي شيء يستدعي update_status)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)

        # 2) المكونات
        self.device_manager = DeviceManager()
        self.capture_manager = None
        self.video_player = VideoPlayer()
        self.ai_engine = AIEngineV1()
        self.ai_engine_enhanced = AIEngineV1Enhanced()
        self.db_manager = DatabaseManager()
        self.model_manager = AIModelManager()

        # 3) الحالة
        self.current_patient = None
        self.current_exam = None
        self.current_frame_id = 0
        self.is_capturing = False
        self.last_frame = None  # آخر صورة معروضة (للتحليل)

        # 4) عناصر العرض المشتركة
        self.frame_display = FrameDisplayWidget()
        self.frame_info_label = QLabel("Ready")
        self.fps_label = QLabel("FPS: 0")

        # 5) المؤقت (قبل setup_ui)
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.setInterval(33)

        # 6) الواجهة
        self.setup_ui()
        self.load_devices()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.tabs = QTabWidget()

        self.live_capture_tab = self.create_live_capture_tab()
        self.tabs.addTab(self.live_capture_tab, "Live Capture")

        self.recorded_video_tab = self.create_recorded_video_tab()
        self.tabs.addTab(self.recorded_video_tab, "Recorded Video")

        self.patient_tab = self.create_patient_tab()
        self.tabs.addTab(self.patient_tab, "Patients")

        self.analysis_tab = AIAnalysisWidget()
        self.tabs.addTab(self.analysis_tab, "AI Analysis")

        self.diagnosis_widget = DiagnosisWidget()
        self.tabs.addTab(self.diagnosis_widget, "Advanced Diagnosis")

        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")

        self.about_tab = self.create_about_tab()
        self.tabs.addTab(self.about_tab, "About")

        left_panel.addWidget(self.tabs)

        # اللوحة اليمنى: مكان الفيديو (يُضاف مرة واحدة فقط)
        right_panel = QVBoxLayout()
        right_panel.addWidget(self.frame_display, 1)

        info_layout = QHBoxLayout()
        info_layout.addWidget(self.frame_info_label)
        info_layout.addWidget(self.fps_label)
        right_panel.addLayout(info_layout)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        central_widget.setLayout(main_layout)

    def create_live_capture_tab(self) -> QWidget:
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
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "800x600", "1024x768", "1280x720"])
        layout.addWidget(self.resolution_combo)

        layout.addWidget(QLabel("Target FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(5, 60)
        self.fps_spin.setValue(30)
        layout.addWidget(self.fps_spin)

        control_layout = QHBoxLayout()
        self.start_capture_btn = QPushButton("Start Capture")
        self.start_capture_btn.clicked.connect(self.start_capture)
        control_layout.addWidget(self.start_capture_btn)

        self.stop_capture_btn = QPushButton("Stop Capture")
        self.stop_capture_btn.clicked.connect(self.stop_capture)
        self.stop_capture_btn.setEnabled(False)
        control_layout.addWidget(self.stop_capture_btn)
        layout.addLayout(control_layout)

        self.capture_frame_btn = QPushButton("Capture Frame")
        self.capture_frame_btn.clicked.connect(self.capture_frame)
        self.capture_frame_btn.setEnabled(False)
        layout.addWidget(self.capture_frame_btn)

        # زر التحليل المتقدم للبث المباشر
        self.live_enhanced_btn = QPushButton("🏥 Advanced Analysis (Live)")
        self.live_enhanced_btn.clicked.connect(self.capture_and_analyze_enhanced)
        self.live_enhanced_btn.setEnabled(False)
        layout.addWidget(self.live_enhanced_btn)

        layout.addWidget(QLabel("Status:"))
        self.capture_status = QTextEdit()
        self.capture_status.setReadOnly(True)
        self.capture_status.setMaximumHeight(150)
        layout.addWidget(self.capture_status)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_recorded_video_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.video_path_label = QLabel("No video selected")
        file_layout.addWidget(self.video_path_label)
        browse_btn = QPushButton("Browse Video")
        browse_btn.clicked.connect(self.browse_video)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        control_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_video)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)

        layout.addWidget(QLabel("Progress:"))
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setMinimum(0)
        self.video_slider.setMaximum(100)
        self.video_slider.setEnabled(False)
        self.video_slider.sliderMoved.connect(self.on_slider_moved)
        layout.addWidget(self.video_slider)

        self.video_info = QLabel("No video loaded")
        layout.addWidget(self.video_info)

        analyze_btn = QPushButton("📸 Capture Frame && Analyze")
        analyze_btn.clicked.connect(self.capture_from_video)
        layout.addWidget(analyze_btn)

        enhanced_btn = QPushButton("🏥 Advanced Analysis")
        enhanced_btn.clicked.connect(self.capture_and_analyze_enhanced)
        layout.addWidget(enhanced_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_patient_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        new_patient_btn = QPushButton("New Patient")
        new_patient_btn.clicked.connect(self.new_patient)
        btn_layout.addWidget(new_patient_btn)

        new_exam_btn = QPushButton("New Examination")
        new_exam_btn.clicked.connect(self.new_examination)
        btn_layout.addWidget(new_exam_btn)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Patients:"))
        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(4)
        self.patients_table.setHorizontalHeaderLabels(["ID", "Name", "Age", "Contact"])
        layout.addWidget(self.patients_table)

        self.refresh_patients_list()

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Application Settings"))

        layout.addWidget(QLabel("Window Size:"))
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setMaximum(10000)
        self.width_spin.setValue(self.config.get("window.width") or 1400)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        layout.addLayout(size_layout)

        layout.addWidget(QLabel("AI Settings:"))
        self.gpu_checkbox = QCheckBox("Enable GPU Acceleration")
        self.gpu_checkbox.setChecked(bool(self.config.get("ai.enable_gpu")))
        layout.addWidget(self.gpu_checkbox)

        layout.addWidget(QLabel("Model Management:"))
        download_models_btn = QPushButton("Download AI Models")
        download_models_btn.clicked.connect(self.download_models)
        layout.addWidget(download_models_btn)

        self.models_status = QLabel("Models status: Not checked")
        layout.addWidget(self.models_status)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_about_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h2>AI Ultrasound Assistant</h2>
        <p><b>Version:</b> 1.1</p>
        <h3>Features:</h3>
        <ul>
        <li>Live ultrasound capture (DirectShow)</li>
        <li>Recorded video files (MP4, AVI, MKV...)</li>
        <li>AI organ detection and image quality assessment</li>
        <li>Advanced diagnosis with pathology detection</li>
        <li>Patient management and SQLite database</li>
        </ul>
        """)
        layout.addWidget(about_text)
        widget.setLayout(layout)
        return widget

    # ------------------------------------------------------------- Devices
    def load_devices(self):
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

    # ---------------------------------------------------------- Live capture
    def start_capture(self):
        if self.device_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No capture device selected")
            return

        try:
            device = self.device_combo.currentData()
            if not isinstance(device, VideoDevice):
                QMessageBox.warning(self, "Error", "No valid device selected")
                return

            # إيقاف أي فيديو مسجل يعمل
            if self.video_player.is_playing:
                self.stop_video()

            self.capture_manager = CaptureManager(device.index)

            if self.capture_manager.start():
                self.is_capturing = True
                self.start_capture_btn.setEnabled(False)
                self.stop_capture_btn.setEnabled(True)
                self.capture_frame_btn.setEnabled(True)
                self.live_enhanced_btn.setEnabled(True)
                self.display_timer.setInterval(33)
                self.display_timer.start()
                self.update_status(f"Capturing from {device.name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to start capture")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error starting capture: {str(e)}")
            logger.error(f"Capture error: {e}", exc_info=True)

    def stop_capture(self):
        if self.capture_manager:
            self.capture_manager.stop()

        self.is_capturing = False
        self.display_timer.stop()
        self.start_capture_btn.setEnabled(True)
        self.stop_capture_btn.setEnabled(False)
        self.capture_frame_btn.setEnabled(False)
        self.live_enhanced_btn.setEnabled(False)
        self.update_status("Capture stopped")

    def capture_frame(self):
        """التقاط صورة من البث المباشر + تحليل عادي"""
        frame = self.get_analysis_frame()
        if frame is None:
            QMessageBox.warning(self, "Warning", "No frame available")
            return

        self.current_frame_id += 1
        frame_id = f"F{self.current_frame_id:06d}"
        self.analyze_and_save(frame, frame_id)

    # ---------------------------------------------------------- Video file
    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)"
        )
        if not file_path:
            return

        # إيقاف البث المباشر إن كان يعمل
        if self.is_capturing:
            self.stop_capture()

        ok = self.video_player.open_video(file_path)
        if ok is False:
            QMessageBox.critical(self, "Error", f"Failed to open video: {os.path.basename(file_path)}")
            self.update_status("Failed to load video")
            return

        self.video_path_label.setText(os.path.basename(file_path))
        self.play_btn.setEnabled(True)
        self.video_slider.setEnabled(True)

        try:
            info = self.video_player.get_info()
            self.video_info.setText(
                f"{info['total_frames']} frames @ {info['fps']:.1f} FPS | "
                f"{info['width']}x{info['height']}"
            )
        except Exception:
            self.video_info.setText("Video loaded")

        # عرض أول إطار فوراً
        self.show_first_frame()
        self.update_status(f"Video loaded: {os.path.basename(file_path)}")

    def show_first_frame(self):
        try:
            cap = getattr(self.video_player, "cap", None)
            if cap is not None:
                pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.display_frame(frame)
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        except Exception as e:
            logger.warning(f"Could not show first frame: {e}")

    def play_video(self):
        self.video_player.play()
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

        interval = 33
        try:
            fps = float(self.video_player.get_info().get('fps', 30))
            if fps > 0:
                interval = max(10, int(1000 / fps))
        except Exception:
            pass
        self.display_timer.setInterval(interval)
        self.display_timer.start()
        self.update_status("Playing video")

    def pause_video(self):
        self.video_player.pause()
        self.display_timer.stop()
        self.update_status("Video paused")

    def stop_video(self):
        self.video_player.stop()
        self.display_timer.stop()
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.update_status("Video stopped")

    def on_slider_moved(self, value):
        try:
            total = self.video_player.total_frames
            if total <= 0:
                return
            frame_num = int((value / 100.0) * total)
            self.video_player.seek(frame_num)
            frame = self.video_player.get_frame_at(frame_num)
            if frame is not None:
                self.display_frame(frame)
        except Exception as e:
            logger.warning(f"Seek error: {e}")

    def capture_from_video(self):
        """تحليل عادي للصورة الحالية (فيديو أو بث)"""
        frame = self.get_analysis_frame()
        if frame is None:
            QMessageBox.warning(self, "Warning", "Please load and play a video first!")
            return

        frame_id = f"V{uuid.uuid4().hex[:8]}"
        self.analyze_and_save(frame, frame_id)

    # ---------------------------------------------------------- Analysis
    def get_analysis_frame(self):
        """آخر صورة معروضة على الشاشة (تعمل للفيديو والبث)"""
        if self.last_frame is not None:
            return self.last_frame.copy()
        return None

    def analyze_and_save(self, frame, frame_id):
        try:
            os.makedirs("captures", exist_ok=True)
            frame_path = f"captures/{frame_id}.jpg"
            cv2.imwrite(frame_path, frame)

            self.update_status(f"Analyzing frame {frame_id}...")
            result = self.ai_engine.analyze_abdominal_ultrasound(frame, frame_id)

            self.display_ai_results(result)

            if self.current_exam:
                try:
                    organs = [o.organ_name for o in result.detected_organs]
                    self.db_manager.add_captured_frame(
                        frame_id, self.current_exam, frame_path,
                        result.quality_assessment.overall_score, organs
                    )
                    self.db_manager.add_ai_analysis(
                        f"A{uuid.uuid4().hex[:8]}", frame_id, self.current_exam,
                        organs,
                        result.quality_assessment.overall_score,
                        result.frame_score,
                        result.processing_time_ms,
                        result.models_used,
                        result.is_best_frame
                    )
                except Exception as e:
                    logger.warning(f"Database save failed: {e}")

            self.update_status(f"Frame {frame_id} analyzed")
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to analyze frame: {e}")

    def capture_and_analyze_enhanced(self):
        """التحليل المتقدم (الفيديو المسجل + البث المباشر)"""
        frame = self.get_analysis_frame()
        if frame is None:
            QMessageBox.warning(self, "Warning", "No frame available. Play the video or start capture first.")
            return

        try:
            self.update_status("Running advanced analysis...")
            result = self.ai_engine_enhanced.analyze_abdominal_ultrasound_enhanced(
                frame=frame,
                frame_id=f"capture_{int(datetime.now().timestamp())}"
            )

            self.diagnosis_widget.display_assessments(result.organ_assessments)
            self.tabs.setCurrentWidget(self.diagnosis_widget)

            self.update_status(f"Advanced analysis done: {len(result.organ_assessments)} organs assessed")
            self.capture_status.append(
                f"[{datetime.now().strftime('%H:%M:%S')}] Advanced analysis: "
                f"{len(result.organ_assessments)} organs, quality {result.quality_level}"
            )
        except Exception as e:
            logger.error(f"Enhanced analysis error: {e}", exc_info=True)
            self.update_status(f"Analysis error: {e}")
            QMessageBox.critical(self, "Error", f"Advanced analysis failed: {e}")

    def display_ai_results(self, result):
        try:
            self.analysis_tab.update_analysis(result)
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "AI Analysis":
                    self.tabs.setCurrentIndex(i)
                    break
        except Exception as e:
            logger.error(f"Error displaying results: {e}", exc_info=True)

    # ----------------------------------------------------------- Patients
    def new_patient(self):
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
        patients = self.db_manager.list_patients()
        self.patients_table.setRowCount(0)

        for i, patient in enumerate(patients):
            self.patients_table.insertRow(i)
            self.patients_table.setItem(i, 0, QTableWidgetItem(patient.patient_id))
            self.patients_table.setItem(i, 1, QTableWidgetItem(patient.name))
            self.patients_table.setItem(i, 2, QTableWidgetItem(str(patient.age)))
            self.patients_table.setItem(i, 3, QTableWidgetItem(patient.contact))

    # ----------------------------------------------------------- Settings
    def download_models(self):
        QMessageBox.information(self, "Models", "Model download feature coming in V1.1\nUsing local ONNX models for now")

    def save_settings(self):
        self.config.set("window.width", self.width_spin.value())
        self.config.set("ai.enable_gpu", self.gpu_checkbox.isChecked())
        self.config.save()
        self.update_status("Settings saved")
        QMessageBox.information(self, "Settings", "Settings saved successfully")

    # ------------------------------------------------------------ Display
    def update_display(self):
        """يُستدعى من المؤقت: يعرض إطار الفيديو المسجل أو البث المباشر"""
        try:
            # الأولوية للفيديو المسجل
            if self.video_player.is_playing:
                frame = self.video_player.get_current_frame()
                if frame is not None:
                    self.display_frame(frame)

                    total = self.video_player.total_frames
                    if total > 0:
                        pos = int((self.video_player.current_frame_num / total) * 100)
                        self.video_slider.blockSignals(True)
                        self.video_slider.setValue(min(100, max(0, pos)))
                        self.video_slider.blockSignals(False)

                    try:
                        info = self.video_player.get_info()
                        self.frame_info_label.setText(
                            f"Frame: {info['current_frame']}/{info['total_frames']} | "
                            f"Size: {info['width']}x{info['height']}"
                        )
                        self.fps_label.setText(f"FPS: {info['fps']:.1f}")
                    except Exception:
                        pass
                return

            # البث المباشر
            if self.is_capturing and self.capture_manager:
                frame = self.capture_manager.get_latest_frame()
                if frame is not None:
                    self.display_frame(frame)
                    stats = self.capture_manager.get_stats()
                    self.fps_label.setText(f"FPS: {stats.current_fps:.1f}")
                return

            # لا شيء يعمل: أوقف المؤقت
            self.display_timer.stop()

        except Exception as e:
            logger.error(f"Display update error: {e}", exc_info=True)

    def display_frame(self, frame):
        """عرض إطار على ويدجت الفيديو"""
        if frame is None:
            return
        try:
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            self.last_frame = frame  # للتحليل لاحقاً

            h, w = frame.shape[:2]
            rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
            self.frame_display.set_pixmap(QPixmap.fromImage(qimg))
        except Exception as e:
            logger.error(f"Frame display error: {e}", exc_info=True)

    def update_status(self, message: str):
        self.status_label.setText(message)
        logger.info(message)

    def closeEvent(self, event):
        self.display_timer.stop()
        if self.capture_manager:
            self.capture_manager.stop()
        try:
            self.video_player.stop()
        except Exception:
            pass
        self.db_manager.close()
        event.accept()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    config = AppConfig()
    window = MainWindowV1(config)
    window.show()
    sys.exit(app.exec())