"""
Diagnosis Display Widget V1.0
واجهة عرض التشخيصات والتقارير الطبية
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QTextEdit, QScrollArea,
    QGroupBox, QProgressBar, QComboBox
)
from PySide6.QtGui import QColor, QFont, QIcon, QTextCursor
from PySide6.QtCore import Qt, Signal
from pathology_engine import OrganAssessment, RiskLevel, OrganStatus
from medical_report_generator import MedicalReportGenerator

logger = logging.getLogger("ultrasound")


class DiagnosisStatusCard(QGroupBox):
    """بطاقة عرض حالة العضو"""
    
    def __init__(self, assessment: OrganAssessment, parent=None):
        super().__init__(parent)
        self.assessment = assessment
        self.init_ui()
    
    def init_ui(self):
        """إنشاء الواجهة"""
        layout = QVBoxLayout()
        
        # الرأس - اسم العضو و الحالة
        header_layout = QHBoxLayout()
        
        status_icon = self._get_status_icon()
        status_label = QLabel(status_icon)
        status_label.setStyleSheet("font-size: 24px; margin-right: 10px;")
        
        organ_label = QLabel(self.assessment.organ_name.upper())
        organ_font = QFont()
        organ_font.setPointSize(12)
        organ_font.setBold(True)
        organ_label.setFont(organ_font)
        
        status_text = QLabel(f"الحالة: {self.assessment.status.value}")
        status_text.setStyleSheet(self._get_status_color())
        
        header_layout.addWidget(status_label)
        header_layout.addWidget(organ_label)
        header_layout.addStretch()
        header_layout.addWidget(status_text)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # معلومات العضو
        info_layout = QHBoxLayout()
        
        # الحجم
        size_widget = QGroupBox("الحجم")
        size_layout = QVBoxLayout()
        size_label = QLabel(self.assessment.size)
        size_layout.addWidget(size_label)
        size_widget.setLayout(size_layout)
        info_layout.addWidget(size_widget)
        
        # الصدى
        echo_widget = QGroupBox("الصدى")
        echo_layout = QVBoxLayout()
        echo_label = QLabel(self.assessment.echotexture)
        echo_layout.addWidget(echo_label)
        echo_widget.setLayout(echo_layout)
        info_layout.addWidget(echo_widget)
        
        # الدوبلر
        doppler_widget = QGroupBox("الدوبلر اللوني")
        doppler_layout = QVBoxLayout()
        doppler_label = QLabel(self.assessment.color_doppler)
        doppler_layout.addWidget(doppler_label)
        doppler_widget.setLayout(doppler_layout)
        info_layout.addWidget(doppler_widget)
        
        layout.addLayout(info_layout)
        layout.addSpacing(10)
        
        # الآفات المكتشفة
        if self.assessment.findings:
            findings_widget = QGroupBox("الآفات المكتشفة")
            findings_layout = QVBoxLayout()
            
            for finding in self.assessment.findings:
                finding_text = self._format_finding(finding)
                finding_label = QLabel(finding_text)
                finding_label.setStyleSheet(self._get_finding_style(finding.risk_level))
                finding_label.setWordWrap(True)
                findings_layout.addWidget(finding_label)
            
            findings_widget.setLayout(findings_layout)
            layout.addWidget(findings_widget)
            layout.addSpacing(10)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
    
    def _get_status_icon(self) -> str:
        """الرمز المناسب لحالة العضو"""
        icons = {
            OrganStatus.NORMAL: "✅",
            OrganStatus.ABNORMAL: "🔴",
            OrganStatus.SUSPICIOUS: "⚠️",
            OrganStatus.PATHOLOGICAL: "🚨"
        }
        return icons.get(self.assessment.status, "❓")
    
    def _get_status_color(self) -> str:
        """لون الحالة"""
        if self.assessment.status == OrganStatus.NORMAL:
            return "color: green; font-weight: bold;"
        elif self.assessment.status == OrganStatus.SUSPICIOUS:
            return "color: orange; font-weight: bold;"
        elif self.assessment.status == OrganStatus.ABNORMAL:
            return "color: red; font-weight: bold;"
        else:
            return "color: darkred; font-weight: bold;"
    
    def _format_finding(self, finding) -> str:
        """تنسيق عرض الآفة"""
        text = f"{finding.finding_name}\n"
        text += f"  • الوصف: {finding.description}\n"
        text += f"  • الموقع: {finding.location}\n"
        if finding.size_mm:
            text += f"  • الحجم: {finding.size_mm} mm\n"
        text += f"  • الثقة: {finding.confidence}%"
        return text
    
    def _get_finding_style(self, risk_level: RiskLevel) -> str:
        """ستايل الآفة حسب مستوى الخطورة"""
        if risk_level == RiskLevel.LOW:
            return "color: green; background-color: #e8f5e9; padding: 5px; border-radius: 3px;"
        elif risk_level == RiskLevel.MEDIUM:
            return "color: orange; background-color: #fff3e0; padding: 5px; border-radius: 3px;"
        elif risk_level == RiskLevel.HIGH:
            return "color: red; background-color: #ffebee; padding: 5px; border-radius: 3px;"
        else:
            return "color: darkred; background-color: #b71c1c; color: white; padding: 5px; border-radius: 3px;"


class DiagnosisWidget(QWidget):
    """واجهة العرض الرئيسية للتشخيصات"""
    
    # الإشارات
    report_generated = Signal(str)  # التقرير المولد
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_generator = MedicalReportGenerator()
        self.current_assessments = []
        self.init_ui()
    
    def init_ui(self):
        """إنشاء الواجهة"""
        layout = QVBoxLayout()
        
        # شريط الأدوات
        toolbar_layout = QHBoxLayout()
        
        self.export_button = QPushButton("📄 تصدير التقرير")
        self.export_button.clicked.connect(self.export_report)
        
        self.print_button = QPushButton("🖨️ طباعة")
        self.print_button.clicked.connect(self.print_report)
        
        self.copy_button = QPushButton("📋 نسخ")
        self.copy_button.clicked.connect(self.copy_report)
        
        toolbar_layout.addWidget(self.export_button)
        toolbar_layout.addWidget(self.print_button)
        toolbar_layout.addWidget(self.copy_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # التبويبات
        self.tabs = QTabWidget()
        
        # تبويب التشخيصات
        self.diagnosis_tab = QWidget()
        self.diagnosis_layout = QVBoxLayout()
        self.diagnosis_scroll = QScrollArea()
        self.diagnosis_scroll.setWidgetResizable(True)
        self.diagnosis_scroll_content = QWidget()
        self.diagnosis_scroll_layout = QVBoxLayout()
        self.diagnosis_scroll_content.setLayout(self.diagnosis_scroll_layout)
        self.diagnosis_scroll.setWidget(self.diagnosis_scroll_content)
        self.diagnosis_layout.addWidget(self.diagnosis_scroll)
        self.diagnosis_tab.setLayout(self.diagnosis_layout)
        self.tabs.addTab(self.diagnosis_tab, "📋 التشخيصات")
        
        # تبويب التقرير الطبي
        self.report_tab = QWidget()
        self.report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier New", 10))
        self.report_layout.addWidget(self.report_text)
        self.report_tab.setLayout(self.report_layout)
        self.tabs.addTab(self.report_tab, "📄 التقرير الطبي")
        
        # تبويب التوصيات
        self.recommendations_tab = QWidget()
        self.recommendations_layout = QVBoxLayout()
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_layout.addWidget(self.recommendations_text)
        self.recommendations_tab.setLayout(self.recommendations_layout)
        self.tabs.addTab(self.recommendations_tab, "💊 التوصيات")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def display_assessments(self, assessments: list):
        """عرض التقييمات الطبية"""
        self.current_assessments = assessments
        
        # مسح التخطيط السابق
        while self.diagnosis_scroll_layout.count():
            self.diagnosis_scroll_layout.takeAt(0).widget().deleteLater()
        
        # إضافة بطاقات التشخيص
        for assessment in assessments:
            card = DiagnosisStatusCard(assessment)
            self.diagnosis_scroll_layout.addWidget(card)
        
        self.diagnosis_scroll_layout.addStretch()
        
        # توليد التقرير
        self.generate_report()
        
        # توليد التوصيات
        self.display_recommendations()
        
        logger.info(f"Displayed {len(assessments)} organ assessments")
    
    def generate_report(self):
        """توليد التقرير الطبي"""
        if not self.current_assessments:
            return
        
        report = self.report_generator.generate_report(
            self.current_assessments,
            patient_name="مريض اختبار",
            examination_id="0001"
        )
        
        self.report_text.setText(report)
        self.report_generated.emit(report)
        logger.info("Medical report generated")
    
    def display_recommendations(self):
        """عرض التوصيات الطبية"""
        if not self.current_assessments:
            return
        
        recommendations_text = "📋 التوصيات الطبية\n"
        recommendations_text += "=" * 60 + "\n\n"
        
        all_recommendations = set()
        for assessment in self.current_assessments:
            all_recommendations.update(assessment.recommendations)
        
        if not all_recommendations:
            recommendations_text += "لا توجد توصيات محددة.\n"
        else:
            for i, rec in enumerate(sorted(all_recommendations), 1):
                recommendations_text += f"{i}. {rec}\n\n"
        
        # إضافة ملاحظات مهمة
        recommendations_text += "\n" + "=" * 60 + "\n"
        recommendations_text += "📌 ملاحظات مهمة:\n\n"
        recommendations_text += "• هذا التقرير مساعد تشخيصي ولا يحل محل التقييم الإكلينيكي\n"
        recommendations_text += "• يجب تأكيد النتائج من قبل طبيب متخصص في الأشعة\n"
        recommendations_text += "• الفحوصات الإضافية قد تكون مطلوبة للتشخيص الدقيق\n"
        recommendations_text += "• استشر طبيبك قبل اتخاذ أي إجراء طبي\n"
        
        self.recommendations_text.setText(recommendations_text)
    
    def export_report(self):
        """تصدير التقرير"""
        if not self.current_assessments:
            return
        
        filepath = self.report_generator.save_report_to_file(
            self.report_text.toPlainText()
        )
        
        if filepath:
            logger.info(f"Report exported to {filepath}")
            # يمكن إضافة رسالة تأكيد للمستخدم
    
    def print_report(self):
        """طباعة التقرير"""
        # سيتم تنفيذه لاحقاً
        logger.info("Print report feature (to be implemented)")
    
    def copy_report(self):
        """نسخ التقرير"""
        self.report_text.selectAll()
        self.report_text.copy()
        logger.info("Report copied to clipboard")
