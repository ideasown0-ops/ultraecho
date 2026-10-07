"""
Pathology Detection Engine V1.0
كشف الأمراض والآفات الموجودة في الأعضاء
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

logger = logging.getLogger("ultrasound")


class OrganStatus(Enum):
    """حالة العضو"""
    NORMAL = "سليم"
    ABNORMAL = "غير سليم"
    SUSPICIOUS = "مريب"
    PATHOLOGICAL = "مرضي"


class RiskLevel(Enum):
    """مستوى الخطورة"""
    LOW = "منخفض"
    MEDIUM = "متوسط"
    HIGH = "عالي"
    CRITICAL = "حرج"


@dataclass
class PathologicalFinding:
    """نتيجة طبية شعاعية"""
    finding_name: str              # اسم الآفة (e.g., "تضخم كبدي")
    description: str               # وصف التفصيلي
    location: str                  # الموقع (e.g., "الفص الأيمن")
    size_mm: Optional[float]       # الحجم بـ mm
    characteristics: List[str]     # الخصائص
    risk_level: RiskLevel          # مستوى الخطورة
    confidence: float              # ثقة الكشف (0-100)


@dataclass
class DiagnosticPossibility:
    """احتمالية تشخيصية"""
    diagnosis_name: str            # اسم التشخيص
    probability: float             # احتمالية (0-100)
    description: str               # وصف
    risk_level: RiskLevel          # مستوى الخطورة
    recommended_action: str        # الإجراء الموصى به
    related_findings: List[str]    # الآفات المرتبطة


@dataclass
class OrganAssessment:
    """تقييم شامل للعضو"""
    organ_name: str
    status: OrganStatus
    size: str                      # طبيعي / مضخم / مصغر
    echotexture: str               # الصدى: طبيعي / متجانس / غير متجانس
    color_doppler: str             # الدوبلر: طبيعي / متزايد / متناقص
    findings: List[PathologicalFinding]
    differential_diagnosis: List[DiagnosticPossibility]
    recommendations: List[str]


class PathologyDetectionEngine:
    """محرك كشف الأمراض"""
    
    def __init__(self):
        self.medical_knowledge = self._load_medical_knowledge()
        logger.info("Pathology Detection Engine initialized")
    
    def _load_medical_knowledge(self) -> dict:
        """تحميل قاعدة المعرفة الطبية"""
        return {
            "liver": {
                "normal_size": "15 cm",
                "normal_echotexture": "متجانس",
                "pathologies": self._get_liver_pathologies(),
                "findings": self._get_liver_findings()
            },
            "kidney_left": {
                "normal_size": "10-12 cm",
                "normal_echotexture": "متجانس",
                "pathologies": self._get_kidney_pathologies(),
                "findings": self._get_kidney_findings()
            },
            "kidney_right": {
                "normal_size": "10-12 cm",
                "normal_echotexture": "متجانس",
                "pathologies": self._get_kidney_pathologies(),
                "findings": self._get_kidney_findings()
            },
            "pancreas": {
                "normal_size": "2-3 cm",
                "normal_echotexture": "متجانس",
                "pathologies": self._get_pancreas_pathologies(),
                "findings": self._get_pancreas_findings()
            },
            "spleen": {
                "normal_size": "10-12 cm",
                "normal_echotexture": "متجانس",
                "pathologies": self._get_spleen_pathologies(),
                "findings": self._get_spleen_findings()
            }
        }
    
    def assess_organ(self, organ_name: str, organ_data: dict) -> OrganAssessment:
        """تقييم شامل للعضو"""
        organ_name_lower = organ_name.lower().replace("_", " ")
        
        # الحصول على البيانات المخزنة
        knowledge = self.medical_knowledge.get(organ_name.lower(), {})
        
        # تحديد الحالة
        status = self._determine_status(organ_data)
        
        # كشف الآفات
        findings = self._detect_findings(organ_name.lower(), organ_data)
        
        # التشخيص التفاضلي
        differential = self._generate_differential_diagnosis(organ_name.lower(), findings)
        
        # التوصيات
        recommendations = self._generate_recommendations(organ_name, status, findings)
        
        return OrganAssessment(
            organ_name=organ_name_lower,
            status=status,
            size=organ_data.get("size", "غير معروف"),
            echotexture=organ_data.get("echotexture", "غير معروف"),
            color_doppler=organ_data.get("color_doppler", "لم يتم فحصه"),
            findings=findings,
            differential_diagnosis=differential,
            recommendations=recommendations
        )
    
    def _determine_status(self, organ_data: dict) -> OrganStatus:
        """تحديد حالة العضو"""
        # هذا تحليل بسيط - يمكن تحسينه
        has_abnormalities = organ_data.get("has_abnormalities", False)
        size_normal = organ_data.get("size_normal", True)
        echotexture_normal = organ_data.get("echotexture_normal", True)
        
        if has_abnormalities:
            return OrganStatus.ABNORMAL
        elif not size_normal or not echotexture_normal:
            return OrganStatus.SUSPICIOUS
        else:
            return OrganStatus.NORMAL
    
    def _detect_findings(self, organ_name: str, organ_data: dict) -> List[PathologicalFinding]:
        """كشف الآفات الموجودة"""
        findings = []
        
        # تحليل البيانات وإضافة الآفات المكتشفة
        if organ_data.get("has_lesion"):
            findings.append(PathologicalFinding(
                finding_name="آفة",
                description=organ_data.get("lesion_description", "آفة موجودة"),
                location=organ_data.get("lesion_location", "موقع غير محدد"),
                size_mm=organ_data.get("lesion_size"),
                characteristics=organ_data.get("lesion_characteristics", []),
                risk_level=RiskLevel.MEDIUM,
                confidence=organ_data.get("lesion_confidence", 50)
            ))
        
        if organ_data.get("is_enlarged"):
            findings.append(PathologicalFinding(
                finding_name="تضخم",
                description="العضو أكبر من الحجم الطبيعي",
                location=organ_name,
                size_mm=organ_data.get("size_mm"),
                characteristics=["حجم مزاد", "محيط مزاد"],
                risk_level=RiskLevel.MEDIUM,
                confidence=80
            ))
        
        if organ_data.get("has_calcification"):
            findings.append(PathologicalFinding(
                finding_name="تكلس",
                description="وجود مناطق تكلسية",
                location=organ_data.get("calcification_location", organ_name),
                size_mm=organ_data.get("calcification_size"),
                characteristics=["إعاقة صدى", "ظل خلفي"],
                risk_level=RiskLevel.HIGH,
                confidence=90
            ))
        
        return findings
    
    def _generate_differential_diagnosis(self, organ_name: str, 
                                        findings: List[PathologicalFinding]) -> List[DiagnosticPossibility]:
        """توليد قائمة التشخيصات المحتملة"""
        diagnoses = []
        
        if not findings:
            return diagnoses
        
        # قاعدة معرفية مبسطة للتشخيصات
        diagnosis_map = {
            "liver": self._get_liver_diagnoses(findings),
            "kidney_left": self._get_kidney_diagnoses(findings),
            "kidney_right": self._get_kidney_diagnoses(findings),
            "pancreas": self._get_pancreas_diagnoses(findings),
            "spleen": self._get_spleen_diagnoses(findings)
        }
        
        return diagnosis_map.get(organ_name, [])
    
    def _generate_recommendations(self, organ_name: str, 
                                 status: OrganStatus, 
                                 findings: List[PathologicalFinding]) -> List[str]:
        """توليد التوصيات الطبية"""
        recommendations = []
        
        if status == OrganStatus.NORMAL:
            recommendations.append("✅ العضو سليم - لا توجد آفات واضحة")
            recommendations.append("✅ المتابعة الدورية العادية كافية")
        
        elif status == OrganStatus.SUSPICIOUS:
            recommendations.append("⚠️ وجود نتائج مريبة - بحاجة لمتابعة دقيقة")
            recommendations.append("⚠️ قد تحتاج لفحوصات إضافية (MRI, CT)")
            recommendations.append("⚠️ مراجعة طبيب متخصص موصى بها")
        
        elif status == OrganStatus.ABNORMAL:
            recommendations.append("🔴 وجود نتائج غير طبيعية واضحة")
            recommendations.append("🔴 فحوصات متقدمة مطلوبة بشكل عاجل")
            recommendations.append("🔴 استشارة متخصص إشعاعي ضرورية")
        
        # توصيات محددة بناءً على الآفات
        for finding in findings:
            if finding.risk_level == RiskLevel.CRITICAL:
                recommendations.append(f"🚨 الآفة '{finding.finding_name}' تتطلب متابعة عاجلة")
            elif finding.risk_level == RiskLevel.HIGH:
                recommendations.append(f"⚠️ الآفة '{finding.finding_name}' تتطلب متابعة دقيقة")
        
        return recommendations
    
    # Liver pathologies
    def _get_liver_pathologies(self) -> dict:
        return {
            "cirrhosis": "تليف الكبد",
            "hepatitis": "التهاب الكبد",
            "fatty_liver": "الكبد الدهني",
            "hemangioma": "ورم وعائي",
            "hepatic_cyst": "كيسة كبدية"
        }
    
    def _get_liver_findings(self) -> dict:
        return {
            "nodular_surface": "سطح عقدي",
            "heterogeneous_echotexture": "صدى غير متجانس",
            "ascites": "استسقاء",
            "splenomegaly": "تضخم الطحال"
        }
    
    def _get_liver_diagnoses(self, findings: List[PathologicalFinding]) -> List[DiagnosticPossibility]:
        diagnoses = []
        
        for finding in findings:
            if "تضخم" in finding.finding_name:
                diagnoses.append(DiagnosticPossibility(
                    diagnosis_name="تضخم الكبد (Hepatomegaly)",
                    probability=70,
                    description="تضخم كبدي بسيط أو متوسط",
                    risk_level=RiskLevel.MEDIUM,
                    recommended_action="فحوصات دم شاملة + متابعة دورية",
                    related_findings=["تضخم"]
                ))
            
            if "آفة" in finding.finding_name:
                diagnoses.append(DiagnosticPossibility(
                    diagnosis_name="ورم كبدي محتمل",
                    probability=50,
                    description="وجود آفة تحتاج لتقييم إضافي",
                    risk_level=RiskLevel.HIGH,
                    recommended_action="MRI أو CT للتأكد من طبيعة الآفة",
                    related_findings=["آفة"]
                ))
        
        return diagnoses
    
    # Kidney pathologies
    def _get_kidney_pathologies(self) -> dict:
        return {
            "hydronephrosis": "توسع حوضي",
            "pyelonephritis": "التهاب الحويضة",
            "renal_stone": "حصوة كلوية",
            "cyst": "كيسة كلوية",
            "atrophy": "ضمور"
        }
    
    def _get_kidney_findings(self) -> dict:
        return {
            "dilated_calyx": "حويصلات موسعة",
            "echogenic_focus": "بؤرة صدى",
            "shadowing": "ظل خلفي",
            "cortical_thinning": "ترقق قشري"
        }
    
    def _get_kidney_diagnoses(self, findings: List[PathologicalFinding]) -> List[DiagnosticPossibility]:
        diagnoses = []
        
        for finding in findings:
            if "تكلس" in finding.finding_name or "ظل" in finding.characteristics:
                diagnoses.append(DiagnosticPossibility(
                    diagnosis_name="حصوة كلوية (Nephrolithiasis)",
                    probability=80,
                    description="احتمال وجود حصوة كلوية",
                    risk_level=RiskLevel.HIGH,
                    recommended_action="CT بدون تباين (gold standard) للتأكد",
                    related_findings=["ظل خلفي", "إعاقة صدى"]
                ))
        
        return diagnoses
    
    # Pancreas pathologies
    def _get_pancreas_pathologies(self) -> dict:
        return {
            "pancreatitis": "التهاب البنكرياس",
            "pseudocyst": "كيسة كاذبة",
            "pancreatic_cancer": "سرطان البنكرياس",
            "fatty_infiltration": "تسلل دهني"
        }
    
    def _get_pancreas_findings(self) -> dict:
        return {
            "edema": "وذمة",
            "heterogeneous": "صدى غير متجانس",
            "cyst": "كيسة"
        }
    
    def _get_pancreas_diagnoses(self, findings: List[PathologicalFinding]) -> List[DiagnosticPossibility]:
        diagnoses = []
        
        if findings:
            diagnoses.append(DiagnosticPossibility(
                diagnosis_name="آفة بنكرياسية",
                probability=60,
                description="وجود نتائج غير طبيعية في البنكرياس",
                risk_level=RiskLevel.HIGH,
                recommended_action="CT أو MRI للتقييم الإضافي",
                related_findings=[f.finding_name for f in findings]
            ))
        
        return diagnoses
    
    # Spleen pathologies
    def _get_spleen_pathologies(self) -> dict:
        return {
            "splenomegaly": "تضخم الطحال",
            "splenic_infarction": "احتشاء طحالي",
            "splenic_rupture": "تمزق طحالي"
        }
    
    def _get_spleen_findings(self) -> dict:
        return {
            "enlarged": "مضخم",
            "heterogeneous": "غير متجانس"
        }
    
    def _get_spleen_diagnoses(self, findings: List[PathologicalFinding]) -> List[DiagnosticPossibility]:
        diagnoses = []
        
        for finding in findings:
            if "تضخم" in finding.finding_name:
                diagnoses.append(DiagnosticPossibility(
                    diagnosis_name="تضخم الطحال (Splenomegaly)",
                    probability=75,
                    description="تضخم طحالي قد يكون بسبب عدة أمراض",
                    risk_level=RiskLevel.MEDIUM,
                    recommended_action="فحوصات دم شاملة + تقييم إكلينيكي",
                    related_findings=["تضخم"]
                ))
        
        return diagnoses
