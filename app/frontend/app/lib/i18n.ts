"use client";

import { useEffect, useState, useCallback } from "react";

export type Language = "vi" | "en";

export const translations = {
  vi: {
    // Header
    headerTitle: "LungRay",
    workstationId: "",
    subTitle: "Phân Tích X-Quang Ngực Đa Nhiệm",
    reportLink: "Báo Cáo Nghiên Cứu",
    apiStatus: "API:",
    apiOnline: "TRỰC TUYẾN",
    apiOffline: "MẤT KẾT NỐI",
    apiProbing: "Đang kiểm tra...",

    // Navigation & Sections
    section1Tab: "1. Trạm Đọc Phim & Scan",
    section2Tab: "2. Kết Quả & Báo Cáo",
    resultsReadyBadge: "Có Kết Quả",
    toggleDropzoneBtn: "Vùng Kéo Thả",
    presetsMenuBtn: "Ca Mẫu Lâm Sàng (4 Ca)",
    presetsMenuTitle: "Chọn Ca Bệnh Lâm Sàng Mẫu:",
    presetsMenuClose: "Đóng",
    viewReportBtn: "Xem Báo Cáo Lâm Sàng Chi Tiết →",
    backToScanBtn: "← Quay Lại Trạm Đọc Phim",
    inspectOnXrayNote: "Bấm vào bất kỳ bệnh lý nào để chuyển về Trạm Đọc Phim xem bản đồ nhiệt Grad-CAM định vị tổn thương.",
    accordion1Title: "Báo Cáo Lâm Sàng & An Toàn OOD",
    accordion2Title: "Sàng Lọc Lao Phổi & COVID-19 (Head B & C)",
    accordion3Title: "14 Bệnh Lý Lồng Ngực (Head A)",
    searchPathologyPlaceholder: "Tìm tên bệnh lý...",
    noPathologyMatch: "Không tìm thấy bệnh lý phù hợp với từ khóa.",
    collapse: "Thu gọn",
    expand: "Mở rộng",
    quickSummaryTitle: "TỔNG HỢP NHANH CHẨN ĐOÁN",
    findingsCount: "tổn thương dương tính",
    noFindingsDetected: "Không có tổn thương dương tính vượt ngưỡng",

    // Dropzone & Presets
    dragPrompt: "Kéo thả phim X-quang ngực (CXR) vào đây hoặc chọn tệp",
    formatsText: "Định dạng: DICOM (.dcm), 16-bit Grayscale, PNG, JPEG (Chuẩn hóa 512x512)",
    browseBtn: "Chọn Tệp Phim X-quang",
    guidelinesTitle: "Quy Chuẩn Kỹ Thuật Phim CXR Tải Lên (Tránh OOD Lockout)",
    guideDimensions: "Kích thước: Khuyến nghị ≥ 512×512 px (Chuẩn DICOM 1024×1024 đến 2500×2048)",
    guideRatio: "Tỷ lệ khung hình: Gần vuông (1:1 hoặc 4:5 đến 5:4) chuẩn ngực thẳng PA/AP",
    guideProjection: "Tư thế chụp: Phim ngực thẳng (PA hoặc AP). Tránh ảnh nghiêng, ảnh CT hoặc chụp màn hình",
    guideOodTip: "Nếu ảnh thực địa bị khóa an toàn, hãy chuyển công tắc [Fail-Safe: BYPASS] trên Header để phân tích ngay",
    dimWarningTitle: "Cảnh Báo Kích Thước Ảnh Thực Tế:",
    dimWarningSmall: "Kích thước nhỏ ({width}×{height} px < 256 px) có thể làm giảm độ nét chi tiết phế nang.",
    dimWarningRatio: "Tỷ lệ khung hình ({ratio}:1) bị lệch so với chuẩn phim ngực thẳng.",
    dimWarningAdvice: "Nếu hệ thống kích hoạt Khóa An Toàn OOD, hãy bật [Fail-Safe: BYPASS] trên thanh Header hoặc bấm nút [Bỏ qua khóa an toàn] để quét tiếp.",
    presetHeading: "Ca Bệnh Kiểm Thử Mẫu (1-Click Presets):",
    presets: {
      normal: { name: "Ca Bình Thường", desc: "Phế trường sáng, không tổn thương" },
      effusion: { name: "Tràn Dịch & Tim To", desc: "Tràn dịch màng phổi & Tim to" },
      tb: { name: "Lao Phổi Tiến Triển", desc: "Tổn thương thâm nhiễm nghi lao" },
      ood: { name: "Nhiễu Ngoại Lai OOD", desc: "Thử nghiệm khóa an toàn Fail-Safe" },
    },
    loadingSample: "Đang nạp dữ liệu ca bệnh mẫu...",

    // Viewport HUD
    noImageTitle: "CHƯA NẠP PHIM X-QUANG",
    noImageSubtitle: "Sẵn sàng tiếp nhận phim chuẩn DICOM / PNG / JPEG",
    patientAnon: "BỆNH NHÂN: VÔ DANH HÓA (ĐÃ KHỬ ĐỊNH DANH PHI)",
    seriesPA: "CHIẾU CHỤP: NGỰC THẲNG SAU - TRƯỚC (PA)",
    matrix512: "MA TRẬN: 512 x 512",
    windowLung: "CỬA SỔ: NHU MÔ PHỔI (WL: -600, WW: 1500)",
    gsdfCalibrated: "HIỂN THỊ: CHUẨN ĐỘ GSDF DICOM",
    scale5cm: "5 cm",
    targetPrefix: "TỔN THƯƠNG:",
    groundedBadge: "PHẾ TRƯỜNG PHỔI",
    unmaskedBadge: "TOÀN BỘ KHUNG HÌNH",
    inLungEnergy: "năng lượng trong phổi",
    auditPassBadge: "ĐẠT CHUẨN ĐỊNH VỊ",
    auditFailBadge: "CẢNH BÁO: NGOÀI PHẾ TRƯỜNG (SHORTCUT)",
    negativeTargetNotice: "Tổn thương này âm tính trên phim. Bản đồ nhiệt chỉ mang tính chất đối chứng, không biểu thị bệnh lý giải phẫu.",
    dualViewBoth: "Hiển Thị Kép",
    dualViewHeatmap: "Bản Đồ Nhiệt",
    dualViewContour: "Viền Tổn Thương",
    dualViewRaw: "Phim Gốc",
    lesionFoci: "ổ tổn thương",
    oodLockoutTitle: "BẤT THƯỜNG NGOẠI LAI (OOD LOCKOUT)",
    oodLockoutDesc: "Ảnh có dấu hiệu nhiễu cực đoan, đảo ngược âm bản hoặc không thuộc lồng ngực. Hệ thống khóa chẩn đoán để ngăn chặn ngộ nhận lâm sàng.",
    extractingCam: "Đang trích xuất bản đồ kích hoạt...",
    analyzingCxr: "Đang phân tích phim X-quang bằng đường ống CADx đa nhiệm...",

    // Fail-Safe Banner
    failSafeVerifiedTitle: "KIỂM ĐỊNH NGOẠI LAI: HỢP LỆ (IN-DISTRIBUTION)",
    failSafeVerifiedDesc: "Đặc trưng giải phẫu đạt chuẩn phân phối CXR ngực thẳng người lớn.",
    failSafeVerifiedBadge: "CHẤP NHẬN",
    failSafeRejectedTitle: "TỪ CHỐI SUY LUẬN: NGOẠI LAI (FAIL-SAFE REJECTED)",
    failSafeRejectedDesc: "Phim chụp rơi vào miền phân phối bất thường hoặc độ bất định vượt ngưỡng an toàn.",
    failSafeRejectedBadge: "ĐÃ KHÓA",
    helmholtzEnergyLabel: "Năng lượng Helmholtz (S_E):",
    shannonEntropyLabel: "Entropy Shannon (H):",
    clinicalRecLabel: "Khuyến cáo lâm sàng:",
    clinicalRecRejectText: "Bác sĩ KHÔNG sử dụng kết quả bên dưới cho quyết định điều trị. Cần chỉ định chụp lại phim chuẩn ngực thẳng PA.",

    // Grounding Filter
    groundingTitle: "BỘ LỌC GIẢI PHẪU XAI",
    groundedBtn: "Bảo Vệ Phế Trường",
    rawBtn: "Bản Đồ Gốc",
    groundedHelp: "Phân vùng giải phẫu phổi kích hoạt. Triệt tiêu nhiễu ký tự chữ R/L, xương đòn và viền ảnh.",
    rawHelp: "Bản đồ Grad-CAM thô chưa lọc giải phẫu, hiển thị toàn bộ năng lượng mô hình học được.",

    // Dashboard Heads
    headATitle: "Head A — 14 Bệnh Lý Lồng Ngực",
    headBTitle: "Head B — Sàng Lọc Lao Phổi (TB Triage)",
    headCTitle: "Head C — Sàng Lọc Cấp Cứu COVID-19",
    clickToExplain: "Bấm để xem định vị",
    targetIndicator: "[Đang Xem]",
    positiveBadge: "DƯƠNG TÍNH",
    negativeBadge: "ÂM TÍNH",
    tbPositive: "Nghi Ngờ Lao Phổi",
    tbNegative: "Âm Tính Lao Phổi",
    covidPositive: "Nghi Ngờ COVID-19",
    covidNegative: "Âm Tính COVID-19",
    inLungRatioLabel: "Năng Lượng Phế Trường:",
    auditPass: "Đạt Chuẩn (≥80%)",
    auditFail: "Không Đạt (<80%)",
    noPredictionsYet: "Tải phim lên để bắt đầu phân tích đa nhiệm.",
    noTbYet: "Chưa có kết quả sàng lọc lao.",
    noCovidYet: "Chưa có kết quả sàng lọc COVID-19.",

    // Alpha Slider
    alphaLabel: "ĐỘ MỜ HEATMAP GRAD-CAM (ALPHA BLEND)",
    alphaUnit: "%",

    // Clinical Report
    reportTitle: "Báo Cáo Chẩn Đoán Sơ Bộ (Grounded Clinical Report)",
    reportBlockedTitle: "BÁO CÁO BỊ KHÓA AN TOÀN",
    reportBlockedText: "Không sinh báo cáo văn bản do ảnh bị từ chối bởi cơ chế Fail-Safe OOD.",
    findingsHeading: "Dấu Hiệu Giải Phẫu (Findings):",
    impressionHeading: "Kết Luận Sơ Bộ (Impression):",
    recommendationsHeading: "Đề Xuất Lâm Sàng (Recommendations):",
    noFindings: "Không phát hiện hình ảnh bất thường rõ rệt trên nhu mô phổi hai bên.",
    normalImpression: "Hình ảnh X-quang ngực thẳng trong giới hạn bình thường.",
    reportDisclaimer: "Báo cáo này được tổng hợp tự động từ kết quả giải phẫu AI; chỉ mang tính tham khảo sơ bộ cho bác sĩ chẩn đoán hình ảnh, không thay thế kết luận y khoa chính thức.",
  },

  en: {
    // Header
    headerTitle: "LungRay",
    workstationId: "",
    subTitle: "Multi-Task Chest X-ray CADx",
    reportLink: "Research Report",
    apiStatus: "API:",
    apiOnline: "ONLINE",
    apiOffline: "OFFLINE",
    apiProbing: "Probing...",

    // Navigation & Sections
    section1Tab: "1. Scan & Viewport Workstation",
    section2Tab: "2. Diagnostic Findings & Report",
    resultsReadyBadge: "Results Ready",
    toggleDropzoneBtn: "Dropzone Drawer",
    presetsMenuBtn: "Clinical Presets (4 Cases)",
    presetsMenuTitle: "Select Standard Clinical Preset:",
    presetsMenuClose: "Close",
    viewReportBtn: "View Detailed Findings & Report →",
    backToScanBtn: "← Return to Workstation",
    inspectOnXrayNote: "Click any pathology to return to Workstation and view localized Grad-CAM heatmap.",
    accordion1Title: "Clinical Diagnostic Report & OOD Safety",
    accordion2Title: "Tuberculosis & COVID-19 Triage (Head B & C)",
    accordion3Title: "14 Thoracic Pathologies (Head A)",
    searchPathologyPlaceholder: "Filter pathology name...",
    noPathologyMatch: "No matching pathology found.",
    collapse: "Collapse",
    expand: "Expand",
    quickSummaryTitle: "DIAGNOSTIC SUMMARY OVERVIEW",
    findingsCount: "positive findings",
    noFindingsDetected: "No positive findings exceeding clinical threshold",

    // Dropzone & Presets
    dragPrompt: "Drag & drop chest radiograph (CXR) here, or browse file",
    formatsText: "Accepted: DICOM (.dcm), 16-bit Grayscale, PNG, JPEG (Automated Rescale to 512x512)",
    browseBtn: "Browse Radiograph File",
    guidelinesTitle: "CXR Upload Technical Standards & Guidelines (Avoid OOD Lockout)",
    guideDimensions: "Resolution: Recommended ≥ 512×512 px (Optimal DICOM 1024×1024 to 2500×2048)",
    guideRatio: "Aspect Ratio: Near-square (1:1 or 4:5 to 5:4) standard frontal PA/AP projection",
    guideProjection: "Projection: Frontal chest (PA or AP). Avoid lateral views, CT slices, or phone camera captures",
    guideOodTip: "If field images trigger safety lockout, toggle [Fail-Safe: BYPASS] on Header to analyze immediately",
    dimWarningTitle: "Image Dimension Pre-Check Notice:",
    dimWarningSmall: "Small resolution ({width}×{height} px < 256 px) may obscure fine parenchymal details.",
    dimWarningRatio: "Aspect ratio ({ratio}:1) deviates from standard frontal CXR projection.",
    dimWarningAdvice: "If the system triggers Fail-Safe OOD Lockout, toggle [Fail-Safe: BYPASS] on Header or click [Bypass Safety & Proceed].",
    presetHeading: "Clinical Test Presets (1-Click):",
    presets: {
      normal: { name: "Normal CXR", desc: "Clear parenchyma, no focal opacity" },
      effusion: { name: "Effusion & Cardio", desc: "Pleural Effusion & Cardiomegaly" },
      tb: { name: "Active Tuberculosis", desc: "Active pulmonary infiltration" },
      ood: { name: "OOD Anomaly", desc: "Fail-Safe Safety Lockout Test" },
    },
    loadingSample: "Loading sample clinical case...",

    // Viewport HUD
    noImageTitle: "NO RADIOGRAPH LOADED",
    noImageSubtitle: "Awaiting DICOM / PNG / JPEG Ingestion",
    patientAnon: "PATIENT: ANONYMIZED (PHI DE-IDENTIFIED)",
    seriesPA: "SERIES: CXR POSTEROANTERIOR (PA)",
    matrix512: "MATRIX: 512 x 512",
    windowLung: "WINDOW: LUNG (WL: -600, WW: 1500)",
    gsdfCalibrated: "RENDER: GSDF CALIBRATED",
    scale5cm: "5 cm",
    targetPrefix: "TARGET:",
    groundedBadge: "PULMONARY GROUNDED",
    unmaskedBadge: "UNMASKED RAW ATTENTION",
    inLungEnergy: "in-lung energy",
    auditPassBadge: "PULMONARY GROUNDED",
    auditFailBadge: "UNGROUNDED (SHORTCUT SUSPECTED)",
    negativeTargetNotice: "Target pathology is negative on this scan. Heatmap displayed for model gradient audit, not anatomical lesion.",
    dualViewBoth: "Dual View",
    dualViewHeatmap: "Heatmap",
    dualViewContour: "Iso-Contour",
    dualViewRaw: "Raw Film",
    lesionFoci: "lesion foci",
    oodLockoutTitle: "OUT-OF-DISTRIBUTION ANOMALY DETECTED",
    oodLockoutDesc: "Film exhibits extreme sensor noise, contrast inversion, or non-thoracic artifacts. Diagnostic interpretation prohibited.",
    extractingCam: "Extracting activation map...",
    analyzingCxr: "Analyzing CXR with multi-task CADx pipeline...",

    // Fail-Safe Banner
    failSafeVerifiedTitle: "FAIL-SAFE VERIFIED (IN-DISTRIBUTION)",
    failSafeVerifiedDesc: "Anatomical features conform to adult posteroanterior CXR distribution.",
    failSafeVerifiedBadge: "ACCEPT",
    failSafeRejectedTitle: "FAIL-SAFE REJECTED (OUT-OF-DISTRIBUTION)",
    failSafeRejectedDesc: "Image falls into anomalous distribution or uncertainty exceeds clinical tolerance.",
    failSafeRejectedBadge: "LOCKED",
    helmholtzEnergyLabel: "Helmholtz Energy (S_E):",
    shannonEntropyLabel: "Shannon Entropy (H):",
    clinicalRecLabel: "Clinical Warning:",
    clinicalRecRejectText: "Clinicians MUST NOT use results below for therapeutic decisions. Repeat PA chest radiography required.",

    // Grounding Filter
    groundingTitle: "XAI ANATOMICAL FILTER",
    groundedBtn: "Pulmonary Grounded",
    rawBtn: "Raw Attention",
    groundedHelp: "Anatomical lung segmentation active. Suppresses non-anatomical noise (letter R/L, clavicles, borders).",
    rawHelp: "Raw Grad-CAM activation showing model shortcuts and boundary energy distribution.",

    // Dashboard Heads
    headATitle: "Head A — 14 Thoracic Pathologies",
    headBTitle: "Head B — Tuberculosis Triage",
    headCTitle: "Head C — COVID-19 Screening",
    clickToExplain: "Click to explain",
    targetIndicator: "[Target]",
    positiveBadge: "POSITIVE",
    negativeBadge: "NEGATIVE",
    tbPositive: "TB Positive",
    tbNegative: "TB Negative",
    covidPositive: "COVID-19 Positive",
    covidNegative: "COVID-19 Negative",
    inLungRatioLabel: "Pulmonary In-Lung Energy:",
    auditPass: "Pass (≥80%)",
    auditFail: "Audit Fail (<80%)",
    noPredictionsYet: "Upload an image to start multi-task analysis.",
    noTbYet: "No tuberculosis screening result yet.",
    noCovidYet: "No COVID-19 screening result yet.",

    // Alpha Slider
    alphaLabel: "GRAD-CAM OVERLAY OPACITY (ALPHA BLEND)",
    alphaUnit: "%",

    // Clinical Report
    reportTitle: "Grounded Clinical Diagnostic Report",
    reportBlockedTitle: "REPORT SAFELY BLOCKED",
    reportBlockedText: "Automated text report inhibited due to Fail-Safe OOD rejection.",
    findingsHeading: "Findings:",
    impressionHeading: "Impression:",
    recommendationsHeading: "Recommendations:",
    noFindings: "No focal consolidation, pneumothorax, or acute pleural effusion identified.",
    normalImpression: "Chest radiograph demonstrates no acute cardiopulmonary abnormality.",
    reportDisclaimer: "This report is synthesized from AI localization and probabilities; intended solely as preliminary reference for radiologists, not replacing formal medical sign-off.",
  },
};

const STORAGE_KEY = "lungray_locale";
const SYNC_EVENT = "lungray_language_change";

export function useLungRayLanguage(): [Language, (newLang: Language) => void] {
  const [lang, setLang] = useState<Language>("vi");

  useEffect(() => {
    // Read from localStorage on mount
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Language | null;
      if (stored === "vi" || stored === "en") {
        setLang(stored);
      }
    } catch {
      // ignore SSR or storage exceptions
    }

    const handleSync = (e: Event) => {
      const customEvent = e as CustomEvent<Language>;
      if (customEvent.detail === "vi" || customEvent.detail === "en") {
        setLang(customEvent.detail);
      }
    };

    window.addEventListener(SYNC_EVENT, handleSync);
    return () => window.removeEventListener(SYNC_EVENT, handleSync);
  }, []);

  const changeLanguage = useCallback((newLang: Language) => {
    setLang(newLang);
    try {
      localStorage.setItem(STORAGE_KEY, newLang);
      window.dispatchEvent(
        new CustomEvent<Language>(SYNC_EVENT, { detail: newLang })
      );
    } catch {
      // ignore
    }
  }, []);

  return [lang, changeLanguage];
}
