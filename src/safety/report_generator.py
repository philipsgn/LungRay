"""
LungRay Grounded Clinical Report Generator (RAG-lite Engine)
============================================================
Produces deterministic, evidence-grounded preliminary structured radiology reports.
Combines:
1. Active disease predictions from Head A, B, and C.
2. Anatomical localization extracted directly from Grad-CAM heatmap peak & spatial extent.
3. Standard ICD-10 medical lexicon and clinical reporting templates.
4. Clinician-grade narrative synthesis with highlighted <u>...</u> keywords.
5. Strict Fail-Safe Lockout: Refuses report generation if the scan is REJECTED by SafetyPolicy.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.safety.reject_policy import SafetyDecision


# ICD-10 Mapping for LungRay 14 NIH pathologies + TB + COVID-19
ICD10_MAP: Dict[str, str] = {
    "Atelectasis": "J98.11 (Xẹp phổi)",
    "Cardiomegaly": "I51.7 (Bóng tim to)",
    "Effusion": "J90 (Tràn dịch màng phổi)",
    "Infiltration": "J18.9 (Thâm nhiễm nhu mô phổi)",
    "Mass": "R91.8 (Khối mờ nhu mô phổi)",
    "Nodule": "R91.1 (Nốt mờ đơn độc phổi)",
    "Pneumonia": "J18.9 (Viêm phổi thùy/kẽ)",
    "Pneumothorax": "J93.9 (Tràn khí màng phổi)",
    "Consolidation": "J18.9 (Đông đặc nhu mô phổi)",
    "Edema": "J81.0 (Phù phổi cấp/mô kẽ)",
    "Emphysema": "J43.9 (Khí phế thũng)",
    "Fibrosis": "J84.10 (Xơ hóa phổi)",
    "Pleural_Thickening": "J94.9 (Dày dính màng phổi)",
    "Hernia": "K44.9 (Thoát vị hoành)",
    "Tuberculosis": "A15.0 (Lao phổi tiến triển)",
    "COVID-19": "U07.1 (Nhiễm virus SARS-CoV-2 thể hô hấp)",
}

DISEASE_NAME_VN: Dict[str, str] = {
    "Atelectasis": "Xẹp phổi",
    "Cardiomegaly": "Bóng tim to",
    "Effusion": "Tràn dịch màng phổi",
    "Infiltration": "Thâm nhiễm nhu mô",
    "Mass": "Khối u lồng ngực",
    "Nodule": "Nốt mờ phổi",
    "Pneumonia": "Viêm phổi",
    "Pneumothorax": "Tràn khí màng phổi",
    "Consolidation": "Đông đặc phế nang",
    "Edema": "Phù phổi cấp",
    "Emphysema": "Khí phế thũng",
    "Fibrosis": "Xơ hóa phổi",
    "Pleural_Thickening": "Dày dính màng phổi",
    "Hernia": "Thoát vị hoành",
    "Tuberculosis": "Lao phổi tiến triển",
    "COVID-19": "Viêm phổi do COVID-19",
}


@dataclass
class ClinicalReport:
    """Dataclass holding structured report fields."""
    status: str  # "GENERATED" or "BLOCKED"
    is_blocked: bool
    findings: List[str] = field(default_factory=list)
    anatomical_locations: List[str] = field(default_factory=list)
    icd10_codes: List[str] = field(default_factory=list)
    impression: str = ""
    recommendations: List[str] = field(default_factory=list)
    disclaimer: str = (
        "Báo cáo này được tổng hợp tự động từ kết quả phân tích giải phẫu và xác suất AI; "
        "chỉ mang tính tham khảo sơ bộ cho bác sĩ chẩn đoán hình ảnh, không thay thế kết luận y khoa chính thức."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_blocked": self.is_blocked,
            "findings": self.findings,
            "anatomical_locations": self.anatomical_locations,
            "icd10_codes": self.icd10_codes,
            "impression": self.impression,
            "recommendations": self.recommendations,
            "disclaimer": self.disclaimer,
        }


def extract_anatomical_zone_from_heatmap(
    heatmap: Optional[np.ndarray],
) -> Tuple[str, str]:
    """
    Extracts lateral and vertical anatomical zones from Grad-CAM activation peak.
    """
    if heatmap is None or not isinstance(heatmap, np.ndarray) or heatmap.size == 0:
        return "Nhu mô phổi hai bên", "Vùng phế trường rải rác"

    # Find peak activation coordinates
    if heatmap.ndim == 3:
        heatmap_2d = np.mean(heatmap, axis=-1)
    else:
        heatmap_2d = heatmap

    h, w = heatmap_2d.shape[:2]
    if h == 0 or w == 0:
        return "Nhu mô phổi hai bên", "Vùng phế trường rải rác"

    y_idx, x_idx = np.unravel_index(np.argmax(heatmap_2d), heatmap_2d.shape)
    norm_x = x_idx / float(w)
    norm_y = y_idx / float(h)

    # Lateral classification
    if norm_x < 0.45:
        lateral = "Phế trường phổi phải (Right hemithorax)"
    elif norm_x > 0.55:
        lateral = "Phế trường phổi trái (Left hemithorax)"
    else:
        lateral = "Vùng bóng tim và rốn phổi hai bên (Mediastinal/Hilar region)"

    # Vertical classification
    if norm_y < 0.35:
        vertical = "Vùng đỉnh phổi (Upper zone)"
    elif norm_y > 0.65:
        vertical = "Vùng đáy phổi / góc sườn hoành (Lower zone / Costophrenic angle)"
    else:
        vertical = "Vùng giữa phế trường (Mid zone)"

    return lateral, vertical


class ClinicalReportGenerator:
    """
    Generates deterministic grounded reports based on predictions and heatmap.
    Synthesizes clinician-grade narrative impressions with highlighted keywords.
    """

    def generate(
        self,
        predictions_a: Dict[str, float],
        thresholds_a: Dict[str, float],
        head_b_result: Optional[Dict[str, Any]] = None,
        head_c_result: Optional[Dict[str, Any]] = None,
        heatmap: Optional[np.ndarray] = None,
        safety_decision: Optional[SafetyDecision] = None,
        in_lung_ratio: Optional[float] = None,
    ) -> ClinicalReport:
        """
        Generates structured clinical report. Refuses if scan is REJECTED.
        """
        # Strict Fail-Safe Lockout
        if safety_decision is not None and not safety_decision.is_safe:
            return ClinicalReport(
                status="BLOCKED",
                is_blocked=True,
                findings=["Ảnh chụp bị hệ thống từ chối do rơi vào vùng phân phối bất thường (OOD) hoặc bất định."],
                anatomical_locations=[],
                icd10_codes=[],
                impression=(
                    "BÁO CÁO TỰ ĐỘNG BỊ KHÓA AN TOÀN: Hình ảnh không đáp ứng tiêu chuẩn "
                    "kiểm định chất lượng giải phẫu của phế trường ngực thẳng người lớn. "
                    "Hệ thống từ chối đưa ra kết luận chẩn đoán tự động nhằm bảo đảm an toàn bệnh nhân."
                ),
                recommendations=[
                    "Kiểm tra lại tư thế chụp của bệnh nhân (yêu cầu phim ngực thẳng PA/AP người lớn).",
                    "Loại bỏ các dị vật cản quang ngoài lồng ngực hoặc chụp lại phim đạt chuẩn chất lượng DICOM.",
                    "Hội chẩn trực tiếp với bác sĩ chuyên khoa chẩn đoán hình ảnh.",
                ],
            )

        active_items: List[Dict[str, Any]] = []

        # 1. Analyze Head A (NIH 14)
        for disease, prob in predictions_a.items():
            thresh = thresholds_a.get(disease, 0.5)
            if prob >= thresh:
                active_items.append({
                    "disease": disease,
                    "name_vn": DISEASE_NAME_VN.get(disease, disease),
                    "prob": prob,
                    "thresh": thresh,
                    "delta": prob - thresh,
                    "head": "head_a",
                    "icd": ICD10_MAP.get(disease, disease),
                })

        # 2. Analyze Head B (TB)
        if head_b_result and head_b_result.get("is_positive", False):
            tb_prob = head_b_result.get("tb_probability", 0.0)
            active_items.append({
                "disease": "Tuberculosis",
                "name_vn": DISEASE_NAME_VN.get("Tuberculosis", "Lao phổi"),
                "prob": tb_prob,
                "thresh": 0.5,
                "delta": tb_prob - 0.5 + 0.1,  # Priority bump
                "head": "head_b",
                "icd": ICD10_MAP["Tuberculosis"],
            })

        # 3. Analyze Head C (COVID-19)
        if head_c_result and head_c_result.get("is_positive", False):
            cov_prob = head_c_result.get("covid_probability", 0.0)
            active_items.append({
                "disease": "COVID-19",
                "name_vn": DISEASE_NAME_VN.get("COVID-19", "COVID-19"),
                "prob": cov_prob,
                "thresh": 0.5,
                "delta": cov_prob - 0.5 + 0.05,
                "head": "head_c",
                "icd": ICD10_MAP["COVID-19"],
            })

        # Extract Anatomy from Heatmap
        lateral, vertical = extract_anatomical_zone_from_heatmap(heatmap)
        locations = [f"{lateral} - {vertical}"]

        # 4. Formulate Narrative Impression & Concise Findings
        if not active_items:
            findings = [
                "Phế trường hai bên <u>trong sáng</u>, không ghi nhận tổn thương dạng đông đặc, thâm nhiễm hay nốt mờ bất thường.",
                "Chỉ số tim - lồng ngực và các góc sườn hoành hai bên <u>trong giới hạn bình thường</u>.",
            ]
            icd_codes = []
            impression = (
                "Chưa phát hiện tổn thương thâm nhiễm, đông đặc hay nốt mờ bất thường rõ rệt "
                "trên phế trường hai phổi trong phạm vi 14 bệnh lý khảo sát. "
                "Bóng tim và trung thất trong giới hạn sinh lý bình thường. Các góc sườn hoành hai bên nhọn."
            )
            recommendations = [
                "Theo dõi lâm sàng định kỳ theo phác đồ sức khỏe tổng quát.",
                "Đối chiếu thêm với các triệu chứng hô hấp thực tế nếu bệnh nhân có biểu hiện ho hoặc sốt kéo dài.",
            ]
        else:
            # Sort by delta descending (highest clinical significance first)
            active_items.sort(key=lambda x: x["delta"], reverse=True)
            top_items = active_items[:3]  # Focus on Top 2-3 key findings

            icd_codes = [item["icd"] for item in active_items]
            active_names = [item["disease"] for item in active_items]

            # Concise Clinician Findings (Top 2-3 priority bullets)
            findings = []
            for idx, it in enumerate(top_items):
                label_prefix = "Tổn thương trọng điểm" if idx == 0 else "Dấu hiệu phối hợp"
                findings.append(
                    f"<u>{label_prefix}</u>: Ghi nhận <u>{it['name_vn']} ({it['disease']})</u> với độ tin cậy vượt ngưỡng "
                    f"({it['prob'] * 100:.1f}%), định vị giải phẫu tại <u>{locations[0]}</u>."
                )

            # Check for XAI audit status
            if in_lung_ratio is not None and in_lung_ratio < 0.80:
                findings.append(
                    f"⚠️ <u>Cảnh báo Kiểm toán XAI</u>: Tỷ lệ năng lượng tập trung trong phế trường chỉ đạt "
                    f"<u>{in_lung_ratio * 100:.1f}%</u> (&lt; 80%). Nghi ngờ vùng kích hoạt chịu ảnh hưởng bởi nhiễu ảnh ngoài lồng ngực."
                )

            # Syndromic Clinical Narrative Synthesis
            has_effusion = any(x["disease"] == "Effusion" for x in active_items)
            has_cardio = any(x["disease"] == "Cardiomegaly" for x in active_items)
            has_tb = any(x["disease"] == "Tuberculosis" for x in active_items)
            has_covid = any(x["disease"] == "COVID-19" for x in active_items)
            has_pneumonia = any(x["disease"] in ["Pneumonia", "Consolidation", "Infiltration"] for x in active_items)
            has_pneu_thorax = any(x["disease"] == "Pneumothorax" for x in active_items)

            # Smart Clinical Report Guardrail:
            # Rule: Acute infectious pulmonary diseases (TB or COVID-19) strictly require
            # parenchymal airspace infiltration / consolidation / pneumonia. If parenchymal
            # lung fields are completely clear, or if shortcut audit fails (< 80%),
            # suppress false positive diagnosis and alert the clinician.
            has_parenchymal_infiltrate = any(
                predictions_a.get(p, 0.0) >= thresholds_a.get(p, 0.45)
                for p in ["Infiltration", "Consolidation", "Pneumonia"]
            )
            is_shortcut_alarm = (in_lung_ratio is not None and in_lung_ratio < 0.80)
            only_infection_positive = (has_tb or has_covid) and not has_parenchymal_infiltrate

            if is_shortcut_alarm or only_infection_positive:
                findings = [
                    "Phế trường hai bên <u>không ghi nhận tổn thương thực thể</u> dạng đông đặc hay thâm nhiễm nhu mô phế nang đối ứng.",
                    f"⚠️ <u>CẢNH BÁO AN TOÀN AI (NGHI NGỜ DƯƠNG TÍNH GIẢ / SHORTCUT HOẶC TỔN THƯƠNG KÍNH MỜ GGO)</u>: "
                    f"Hệ thống ghi nhận kích hoạt cao ở nhánh nhiễm trùng ({'COVID-19 ' if has_covid else ''}{'Lao phổi' if has_tb else ''}) "
                    f"nhưng <u>nhu mô phổi chưa có đông đặc phế nang tương ứng</u>"
                    f"{f' (năng lượng trong phổi chỉ đạt {in_lung_ratio * 100:.1f}%, dưới chuẩn 80%)' if in_lung_ratio is not None else ' (không có thâm nhiễm nhu mô đối ứng)'}. "
                    f"Nghi ngờ kết quả chịu ảnh hưởng bởi ký tự đánh dấu thành ngực (chữ R/L), viền máy chụp ngoại lai, hoặc tổn thương kính mờ (GGO) ngoại vi giai đoạn sớm."
                ]
                narrative_lead = (
                    "PHIM X-QUANG CHƯA GHI NHẬN TỔN THƯƠNG THỰC THỂ NỘI NHU MÔ PHỔI (NGHI NGỜ DƯƠNG TÍNH GIẢ DO NHIỄU MÁY CHỤP / SHORTCUT). "
                    "Khuyến nghị bác sĩ lâm sàng loại trừ chẩn đoán nhiễm trùng cấp tính dựa trên hình ảnh này nếu có dấu hiệu nhiễu ký tự; "
                    "trường hợp bệnh nhân có triệu chứng hô hấp nghi ngờ COVID-19 thể kính mờ (GGO) hoặc Lao tiềm ẩn, cần chỉ định chụp CT lồng ngực và xét nghiệm vi sinh (RT-PCR / GeneXpert) để xác chẩn."
                )
                recommendations = [
                    "<u>Khuyến nghị an toàn</u>: Đề nghị bác sĩ kiểm tra phim gốc nhằm loại trừ dương tính giả do ký tự ngoài thành ngực hoặc viền máy chụp.",
                    "<u>Tầm soát lâm sàng</u>: Trường hợp nghi ngờ thể kính mờ (GGO) sớm do COVID-19, thực hiện xét nghiệm RT-PCR hoặc chụp CT độ phân giải cao (HRCT).",
                ]
            elif has_effusion and has_cardio:
                narrative_lead = (
                    f"Hình ảnh X-quang ghi nhận dấu hiệu gợi ý <u>Tràn dịch màng phổi (Effusion)</u> kết hợp "
                    f"<u>Bóng tim to (Cardiomegaly)</u>, phù hợp với hội chứng <u>suy tim sung huyết</u> hoặc ứ trệ tuần hoàn phổi tiến triển. "
                    f"Trọng tâm kích hoạt giải phẫu định vị tại <u>{locations[0]}</u>."
                )
            elif has_tb:
                narrative_lead = (
                    f"Phát hiện vùng tổn thương thâm nhiễm nhu mô phế trường với độ đặc hiệu cao, gợi ý "
                    f"<u>Lao phổi tiến triển (Tuberculosis)</u>. Vùng giải phẫu trọng điểm định vị tại <u>{locations[0]}</u>. "
                    f"Cần khẩn trương đối chiếu xét nghiệm vi sinh (AFB đờm, PCR) để tầm soát lây nhiễm."
                )
            elif has_covid:
                narrative_lead = (
                    f"Ghi nhận tổn thương thâm nhiễm nhu mô phổi phân bố ngoại vi, gợi ý <u>Viêm phổi do COVID-19</u>. "
                    f"Vùng tập trung kích hoạt giải phẫu chính định vị tại <u>{locations[0]}</u>."
                )
            elif has_pneu_thorax:
                narrative_lead = (
                    f"CẢNH BÁO CẤP CỨU: Phát hiện đường viền màng phổi tạng co rút kèm vùng tăng sáng vô mạch, gợi ý "
                    f"<u>Tràn khí màng phổi (Pneumothorax)</u> tại <u>{locations[0]}</u>. Đề nghị bác sĩ lâm sàng thăm khám khẩn cấp."
                )
            elif has_pneumonia:
                primary_pneu = next(x for x in active_items if x["disease"] in ["Pneumonia", "Consolidation", "Infiltration"])
                narrative_lead = (
                    f"Hình ảnh X-quang nổi bật với hội chứng tổn thương phế nang dạng <u>{primary_pneu['name_vn']} ({primary_pneu['disease']})</u> "
                    f"tại <u>{locations[0]}</u>, phản ánh tình trạng <u>viêm nhiễm nhu mô phổi tiến triển</u>."
                )
            else:
                top_str = ", ".join([f"<u>{it['name_vn']} ({it['disease']})</u>" for it in top_items])
                narrative_lead = (
                    f"Hình ảnh X-quang ghi nhận dấu hiệu gợi ý: {top_str}. "
                    f"Vùng tập trung kích hoạt giải phẫu chính định vị tại <u>{locations[0]}</u>."
                )

            # Clean clinician impression
            impression = narrative_lead

            if not (is_shortcut_alarm or only_infection_positive):
                recommendations = [
                    f"<u>Đối chiếu hình ảnh</u>: Đề nghị bác sĩ lâm sàng đối chiếu tổn thương {top_items[0]['name_vn']} với phim cắt lớp vi tính (CT Thorax) nếu cần xác định rõ ranh giới giải phẫu.",
                    "<u>Hướng xử trí tiếp theo</u>: Hội chẩn chuyên khoa Hô hấp / Tim mạch và theo dõi đáp ứng điều trị lâm sàng.",
                ]

        return ClinicalReport(
            status="GENERATED",
            is_blocked=False,
            findings=findings,
            anatomical_locations=locations,
            icd10_codes=icd_codes,
            impression=impression,
            recommendations=recommendations,
        )
