"""Offline, deterministic retrieval of curated educational chest-imaging cards.

ICD-10 references are candidate categories, never an automated coded diagnosis.
Follow-up text is editorial clinical context; Fleischner defines terminology,
not a treatment protocol. No language model or runtime network is used.
"""
from __future__ import annotations

import copy
import re
import unicodedata
from typing import Any

ICD = "WHO ICD-10 classification (reference categories): https://icd.who.int/browse10/2019/en"
FLEISCHNER = "Fleischner Society Glossary of Terms for Thoracic Imaging (2024), terminology: https://doi.org/10.1148/radiol.232558"
TB_WHO = "WHO consolidated guidelines on tuberculosis, Module 3: diagnosis (2025): https://tbksp.who.int/sites/default/files/2025-08/9789240110991-eng.pdf"
COVID_WHO = "WHO guidelines on the use of chest imaging in COVID-19 (2022): https://www.who.int/publications/i/item/9789240055704"

# name, Vietnamese alias, reference category, hallmark, differential, follow-up
_ROWS = [
    ("Atelectasis", "Xẹp phổi", "J98.1", "Đám mờ kèm giảm thể tích; có thể kéo lệch rãnh liên thùy.", "Đông đặc, dịch màng phổi.", "Đối chiếu phim cũ; cân nhắc CT nếu xẹp kéo dài hoặc nghi tắc nghẽn."),
    ("Cardiomegaly", "Bóng tim to", "I51.7", "Bóng tim rộng; tư thế AP và hít vào kém có thể làm tăng giả kích thước.", "Phóng đại do tư thế, dịch màng tim.", "Kiểm tra tư thế chụp; bác sĩ cân nhắc siêu âm tim theo triệu chứng."),
    ("Effusion", "Tràn dịch màng phổi", "J90", "Mờ góc sườn hoành hoặc đường cong dịch.", "Dày màng phổi, xẹp phổi.", "Cân nhắc siêu âm màng phổi để xác định dịch; khảo sát nguyên nhân theo lâm sàng."),
    ("Infiltration", "Thâm nhiễm", "R91", "Nhãn mờ phổi không đặc hiệu; cần mô tả hình thái cụ thể.", "Nhiễm trùng, phù phổi, xẹp phổi.", "Đối chiếu triệu chứng, phim cũ; cân nhắc CT khi bất thường chưa rõ."),
    ("Mass", "Khối phổi", "R91", "Bóng mờ khu trú dạng khối; X-quang không xác định bản chất.", "U, tổn thương viêm, chồng hình.", "Bác sĩ cân nhắc CT ngực để đặc trưng tổn thương trước quyết định tiếp theo."),
    ("Nodule", "Nốt phổi", "R91", "Bóng mờ khu trú dạng nốt; cần phân biệt chồng hình.", "U hạt, u, bóng núm vú.", "Đối chiếu phim cũ; cân nhắc CT, sau đó phân tầng nguy cơ nếu xác nhận nốt."),
    ("Pneumonia", "Viêm phổi", "J18.9", "Mờ nhu mô hoặc đông đặc có thể phù hợp với nhiễm trùng.", "Phù phổi, xuất huyết phế nang, xẹp phổi.", "Đối chiếu triệu chứng và xét nghiệm; bác sĩ quyết định xét nghiệm vi sinh theo mức độ bệnh."),
    ("Pneumothorax", "Tràn khí màng phổi", "J93.9", "Đường màng phổi tạng với mất vân phổi phía ngoài.", "Nếp da, bóng khí lớn.", "Nếu khó thở hoặc huyết động bất ổn: đánh giá cấp cứu ngay; bác sĩ quyết định xử trí."),
    ("Consolidation", "Đông đặc", "R91", "Tăng đậm độ nhu mô có thể thấy phế quản hơi.", "Viêm phổi, phù phổi, xuất huyết.", "Đối chiếu lâm sàng và phim cũ; đây là dấu hiệu hình ảnh, chưa xác định nguyên nhân."),
    ("Edema", "Phù phổi", "J81", "Mờ mô kẽ hoặc phế nang; có thể kèm dịch màng phổi.", "Nhiễm trùng, xuất huyết phế nang.", "Đánh giá hô hấp và tim mạch theo lâm sàng; khó thở cấp cần khám cấp cứu."),
    ("Emphysema", "Khí phế thũng", "J43.9", "Phổi tăng sáng và giảm vân mạch; cơ hoành có thể dẹt.", "Tăng khí phổi, kỹ thuật chụp quá xuyên.", "Cân nhắc đo chức năng hô hấp; CT nếu cần đánh giá cấu trúc theo chỉ định."),
    ("Fibrosis", "Xơ phổi", "J84.1", "Mờ dạng lưới và biến dạng cấu trúc có thể gợi ý xơ.", "Phù mô kẽ, di chứng nhiễm trùng.", "Khám chuyên khoa; cân nhắc HRCT và chức năng hô hấp để đặc trưng bệnh mô kẽ."),
    ("Pleural_Thickening", "Dày màng phổi", "J94.1", "Dày dọc bờ màng phổi; đôi khi kèm vôi hóa.", "Dịch khu trú, mảng màng phổi, mỡ ngoài màng phổi.", "Đối chiếu tiền sử và phim cũ; cân nhắc CT khi không rõ hoặc tiến triển."),
    ("Hernia", "Thoát vị hoành", "K44.9", "Bóng hơi hoặc mức khí dịch sau tim có thể gợi ý thoát vị khe hoành.", "Tổn thương trung thất, chồng hình.", "Cần xác nhận loại thoát vị; cân nhắc CT hoặc khảo sát tiêu hóa theo triệu chứng."),
    ("Tuberculosis", "Lao phổi", "A16.2", "Mờ, hang hoặc tổn thương xơ có thể gợi ý lao nhưng không đặc hiệu.", "Nhiễm trùng khác, u, di chứng lao cũ.", "Sàng lọc dương tính cần đánh giá lâm sàng và xét nghiệm đờm bằng xét nghiệm phân tử nhanh WHO khuyến nghị như Xpert; AFB/cấy theo chỉ định."),
    ("COVID-19", "Covid", "U07.1", "Mờ hai phổi có thể gặp; hình ảnh không đặc hiệu và không xác nhận SARS-CoV-2.", "Viêm phổi virus khác, phù phổi, viêm phổi tổ chức hóa.", "Xét nghiệm virus như RT-PCR hoặc kháng nguyên theo hướng dẫn địa phương; đánh giá triệu chứng và oxy hóa máu."),
]

CLINICAL_KNOWLEDGE_BASE = {
    name: dict(disease=name, icd10=code, hallmarks=hallmark, differential=diff,
               followup=followup, aliases=[name.replace("_", " "), alias],
               coding_note="Mã tham chiếu cần bác sĩ xác nhận. A16.2 chỉ dùng khi lao phổi chưa xác nhận vi khuẩn; U07.1 cần xác nhận virus. Nhãn Hernia cần xác nhận loại thoát vị.",
               citations=[ICD, FLEISCHNER] + ([TB_WHO] if name == "Tuberculosis" else [COVID_WHO] if name == "COVID-19" else []))
    for name, alias, code, hallmark, diff, followup in _ROWS
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().replace("đ", "d"))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in text if not unicodedata.combining(c))).split())


def query_clinical_rag(question: str, active_findings: list[str],
                       anatomical_locations: list[str], is_safe: bool = True,
                       in_lung_ratio: float | None = None) -> dict[str, Any]:
    """Retrieve known cards; context is caller supplied, never independently verified."""
    if not is_safe:
        return dict(status="BLOCKED_OOD", answer="Ca chụp bị OOD Fail-Safe từ chối. Không suy diễn bệnh lý. Kiểm tra đúng ảnh X-quang ngực, chất lượng và dữ liệu đầu vào rồi phân tích lại.", citations=[], retrieved_cards=[])
    normalized = _normalize(question)
    mentioned = [name for name, card in CLINICAL_KNOWLEDGE_BASE.items()
                 if any(re.search(r"\b" + re.escape(_normalize(alias)) + r"\b", normalized)
                        for alias in card["aliases"])]
    # A named question selects its topic; generic quick prompts use active findings.
    selected = mentioned or [name for name in CLINICAL_KNOWLEDGE_BASE
                            if any(_normalize(item) in {_normalize(a) for a in CLINICAL_KNOWLEDGE_BASE[name]["aliases"]}
                                   for item in active_findings)]
    cards = [copy.deepcopy(CLINICAL_KNOWLEDGE_BASE[name]) for name in selected]
    context = "Thông tin tham khảo có cấu trúc; các nhãn mô hình không xác nhận chẩn đoán."
    if in_lung_ratio is None:
        context += " Chưa có audit năng lượng trong phổi."
    elif not 0 <= in_lung_ratio <= 1:
        return dict(status="INVALID_CONTEXT", answer="Tỷ lệ năng lượng phải nằm trong [0, 1].", citations=[], retrieved_cards=[])
    else:
        context += f" Năng lượng trong phổi: {in_lung_ratio:.1%}."
        if in_lung_ratio < 0.8:
            context += " Dưới 80%: cần kiểm tra nhiễu chữ/viền; hạ cờ nghi ngờ lâm sàng."
    context += " Grad-CAM và tỷ lệ năng lượng không phải xác suất đúng hay độ tin cậy đã hiệu chuẩn."
    context += " Vùng do người gọi cung cấp: " + (", ".join(anatomical_locations) if anatomical_locations else "chưa có định vị xác thực") + "."
    if not cards:
        return dict(status="NO_MATCH", answer=context + " Không có mục tri thức phù hợp; không suy diễn ca bệnh bình thường.", citations=[], retrieved_cards=[])
    confidence = any(word in normalized for word in ("tin cay", "giai phau", "confidence"))
    followup = any(word in normalized for word in ("xu tri", "can lam sang", "follow", "treatment"))
    snippets = []
    if not confidence:
        for card in cards:
            content = card["followup"] if followup else card["hallmarks"] + " Phân biệt: " + card["differential"]
            snippets.append(card["disease"] + ": " + content)
    citations = list(dict.fromkeys(source for card in cards for source in card["citations"]))
    return dict(status="GROUNDED_REFERENCE", answer=context + " " + " ".join(snippets), citations=citations, retrieved_cards=cards)
