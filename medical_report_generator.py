"""
Medical Report Generator V1.0
توليد التقارير الطبية الشعاعية الاحترافية
"""

import logging
from datetime import datetime
from pathology_engine import OrganAssessment, PathologicalFinding, DiagnosticPossibility, OrganStatus, RiskLevel

logger = logging.getLogger("ultrasound")


class MedicalReportGenerator:
    """توليد التقارير الطبية"""
    
    def __init__(self):
        self.report_template = self._load_template()
    
    def _load_template(self) -> str:
        return """
╔════════════════════════════════════════════════════════════════════╗
║         تقرير الفحص الموجات فوق الصوتية للبطن                    ║
║              ABDOMINAL ULTRASOUND REPORT                           ║
╚════════════════════════════════════════════════════════════════════╝

التاريخ: {date}
المريض: {patient_name}
رقم الفحص: {examination_id}

════════════════════════════════════════════════════════════════════
🔍 نتائج الفحص - FINDINGS
════════════════════════════════════════════════════════════════════

{findings_section}

════════════════════════════════════════════════════════════════════
⚕️ الانطباع - IMPRESSION
════════════════════════════════════════════════════════════════════

{impression_section}

════════════════════════════════════════════════════════════════════
📋 التشخيص المحتمل - DIFFERENTIAL DIAGNOSIS
════════════════════════════════════════════════════════════════════

{diagnosis_section}

════════════════════════════════════════════════════════════════════
💊 التوصيات - RECOMMENDATIONS
════════════════════════════════════════════════════════════════════

{recommendations_section}

════════════════════════════════════════════════════════════════════
التوقيع: ___________________    التاريخ: {date}
        الطبيب الفاحص
════════════════════════════════════════════════════════════════════
"""
    
    def generate_report(self, assessments: list, 
                       patient_name: str = "غير محدد",
                       examination_id: str = "0000") -> str:
        """توليد التقرير الطبي الكامل"""
        
        findings_section = self._generate_findings_section(assessments)
        impression_section = self._generate_impression_section(assessments)
        diagnosis_section = self._generate_diagnosis_section(assessments)
        recommendations_section = self._generate_recommendations_section(assessments)
        
        report = self.report_template.format(
            date=datetime.now().strftime("%d/%m/%Y %H:%M"),
            patient_name=patient_name,
            examination_id=examination_id,
            findings_section=findings_section,
            impression_section=impression_section,
            diagnosis_section=diagnosis_section,
            recommendations_section=recommendations_section
        )
        
        logger.info(f"Medical report generated for patient {patient_name}")
        return report
    
    def _generate_findings_section(self, assessments: list) -> str:
        """توليد قسم النتائج"""
        section = ""
        
        for assessment in assessments:
            # رأس العضو
            status_symbol = self._get_status_symbol(assessment.status)
            status_text = self._get_status_text(assessment.status)
            
            section += f"\n{'='*60}\n"
            section += f"{status_symbol} {assessment.organ_name.upper()}\n"
            section += f"{'='*60}\n\n"
            
            # معلومات أساسية
            section += f"الحالة العامة: {status_text}\n"
            section += f"الحجم: {assessment.size}\n"
            section += f"الصدى: {assessment.echotexture}\n"
            section += f"الدوبلر اللوني: {assessment.color_doppler}\n\n"
            
            # الآفات المكتشفة
            if assessment.findings:
                section += "الآفات المكتشفة:\n"
                section += "-" * 60 + "\n"
                for i, finding in enumerate(assessment.findings, 1):
                    section += self._format_finding(i, finding)
            else:
                section += "✅ لا توجد آفات واضحة\n\n"
        
        return section
    
    def _format_finding(self, index: int, finding: PathologicalFinding) -> str:
        """تنسيق الآفة الواحدة"""
        risk_icon = self._get_risk_icon(finding.risk_level)
        
        text = f"\n{index}. {risk_icon} {finding.finding_name}\n"
        text += f"   الوصف: {finding.description}\n"
        text += f"   الموقع: {finding.location}\n"
        
        if finding.size_mm:
            text += f"   الحجم: {finding.size_mm} mm\n"
        
        if finding.characteristics:
            text += f"   الخصائص: {', '.join(finding.characteristics)}\n"
        
        text += f"   مستوى الخطورة: {finding.risk_level.value}\n"
        text += f"   ثقة الكشف: {finding.confidence}%\n"
        
        return text
    
    def _generate_impression_section(self, assessments: list) -> str:
        """توليد قسم الانطباع"""
        section = ""
        
        # إحصائيات عامة
        normal_organs = sum(1 for a in assessments if a.status == OrganStatus.NORMAL)
        abnormal_organs = sum(1 for a in assessments if a.status == OrganStatus.ABNORMAL)
        suspicious_organs = sum(1 for a in assessments if a.status == OrganStatus.SUSPICIOUS)
        total_findings = sum(len(a.findings) for a in assessments)
        
        section += f"\nتم فحص {len(assessments)} أعضاء:\n"
        section += f"  ✅ أعضاء سليمة: {normal_organs}\n"
        section += f"  ⚠️  أعضاء مريبة: {suspicious_organs}\n"
        section += f"  🔴 أعضاء غير سليمة: {abnormal_organs}\n"
        section += f"  📊 إجمالي الآفات: {total_findings}\n\n"
        
        # الانطباع العام
        if abnormal_organs > 0:
            section += "🔴 الانطباع العام:\n"
            section += "وجود نتائج غير طبيعية تتطلب متابعة دقيقة وفحوصات إضافية.\n\n"
        elif suspicious_organs > 0:
            section += "⚠️ الانطباع العام:\n"
            section += "وجود نتائج مريبة قد تحتاج لتقييم إضافي.\n\n"
        else:
            section += "✅ الانطباع العام:\n"
            section += "نتائج سليمة - لا توجد آفات واضحة في الأعضاء المفحوصة.\n\n"
        
        return section
    
    def _generate_diagnosis_section(self, assessments: list) -> str:
        """توليد قسم التشخيص المحتمل"""
        section = ""
        
        all_diagnoses = []
        for assessment in assessments:
            all_diagnoses.extend(assessment.differential_diagnosis)
        
        if not all_diagnoses:
            section += "لا توجد تشخيصات محتملة محددة.\n"
            return section
        
        # ترتيب التشخيصات حسب الاحتمالية
        all_diagnoses.sort(key=lambda x: x.probability, reverse=True)
        
        for i, diagnosis in enumerate(all_diagnoses[:5], 1):  # أفضل 5 تشخيصات
            risk_icon = self._get_risk_icon_for_diagnosis(diagnosis.risk_level)
            
            section += f"\n{i}. {risk_icon} {diagnosis.diagnosis_name}\n"
            section += f"   احتمالية: {diagnosis.probability}%\n"
            section += f"   الوصف: {diagnosis.description}\n"
            section += f"   مستوى الخطورة: {diagnosis.risk_level.value}\n"
            section += f"   الإجراء الموصى به: {diagnosis.recommended_action}\n"
        
        return section
    
    def _generate_recommendations_section(self, assessments: list) -> str:
        """توليد قسم التوصيات"""
        section = ""
        
        # جمع جميع التوصيات
        all_recommendations = set()
        for assessment in assessments:
            all_recommendations.update(assessment.recommendations)
        
        # تنسيق التوصيات
        for i, rec in enumerate(sorted(all_recommendations), 1):
            section += f"\n{i}. {rec}"
        
        section += "\n\n📌 ملاحظات هامة:\n"
        section += "• هذا التقرير مساعد تشخيصي ولا يحل محل التقييم الإكلينيكي\n"
        section += "• يجب تأكيد النتائج من قبل طبيب متخصص في الأشعة\n"
        section += "• الفحوصات الإضافية قد تكون مطلوبة للتشخيص الدقيق\n"
        
        return section
    
    def _get_status_symbol(self, status: OrganStatus) -> str:
        """الرمز المناسب لحالة العضو"""
        symbols = {
            OrganStatus.NORMAL: "✅",
            OrganStatus.ABNORMAL: "🔴",
            OrganStatus.SUSPICIOUS: "⚠️",
            OrganStatus.PATHOLOGICAL: "🚨"
        }
        return symbols.get(status, "❓")
    
    def _get_status_text(self, status: OrganStatus) -> str:
        """نص حالة العضو"""
        texts = {
            OrganStatus.NORMAL: "سليم",
            OrganStatus.ABNORMAL: "غير سليم",
            OrganStatus.SUSPICIOUS: "مريب",
            OrganStatus.PATHOLOGICAL: "مرضي"
        }
        return texts.get(status, "غير معروف")
    
    def _get_risk_icon(self, risk_level: RiskLevel) -> str:
        """الرمز المناسب لمستوى الخطورة"""
        icons = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }
        return icons.get(risk_level, "❓")
    
    def _get_risk_icon_for_diagnosis(self, risk_level: RiskLevel) -> str:
        """رمز الخطورة للتشخيصات"""
        icons = {
            RiskLevel.LOW: "✓",
            RiskLevel.MEDIUM: "⚠",
            RiskLevel.HIGH: "‼",
            RiskLevel.CRITICAL: "🚨"
        }
        return icons.get(risk_level, "?")
    
    def save_report_to_file(self, report: str, filename: str = None) -> str:
        """حفظ التقرير في ملف"""
        if filename is None:
            filename = f"ultrasound_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = f"reports/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return None
