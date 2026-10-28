// ============================================================================
// LUNGRAY COMPLETE BILINGUAL INTERNATIONALIZATION DICTIONARY (EN / VI)
// Mirrored 1:1 between English and Vietnamese
// ============================================================================

import { Language } from "../types";

export interface I18nContent {
  nav: {
    backToPacs: string;
    instituteName: string;
    reportTitle: string;
    sectionNames: string[];
    switchLanguage: string;
  };
  section0_hero: {
    hudStatus: string;
    hudBadge: string;
    mainTitle: string;
    subtitle: string;
    statAurocTitle: string;
    statAurocSub: string;
    statTbTitle: string;
    statTbSub: string;
    statImagesTitle: string;
    statImagesSub: string;
    statLatencyTitle: string;
    statLatencySub: string;
    ctaExplore: string;
    ctaMethodology: string;
  };
  section1_problem: {
    tag: string;
    title: string;
    description: string;
    painPointLabel: string;
    aiSolutionLabel: string;
    painPoints: {
      title: string;
      desc: string;
      impact: string;
    }[];
    solutions: {
      title: string;
      desc: string;
      benefit: string;
    }[];
    natureQuote: string;
    natureCitation: string;
  };
  section2_datasets: {
    tag: string;
    title: string;
    description: string;
    filterAll: string;
    filterPrimary: string;
    filterGroundTruth: string;
    filterOod: string;
    tableHeaders: {
      dataset: string;
      cohort: string;
      splitProtocol: string;
      clinicalRole: string;
      integrity: string;
    };
    leakageDisciplineTitle: string;
    leakageDisciplineDesc: string;
  };
  section3_balancing: {
    tag: string;
    title: string;
    description: string;
    imbalanceTitle: string;
    imbalanceDesc: string;
    rawRatioLabel: string;
    balancedRatioLabel: string;
    starvationWarning: string;
    pipelineTitle: string;
    pipelineSteps: {
      step: string;
      title: string;
      sub: string;
      desc: string;
    }[];
  };
  section4_architecture: {
    tag: string;
    title: string;
    description: string;
    backboneTitle: string;
    backboneDesc: string;
    normLayerTitle: string;
    normLayerDesc: string;
    headsTitle: string;
    headA: { title: string; subtitle: string; desc: string; loss: string };
    headB: { title: string; subtitle: string; desc: string; loss: string };
    headC: { title: string; subtitle: string; desc: string; loss: string };
    drawerTitle: string;
    closeDrawer: string;
    tensorDimensions: string;
    parameterCount: string;
    activationFunction: string;
    dropoutRate: string;
  };
  section5_training: {
    tag: string;
    title: string;
    description: string;
    scrubberLabel: string;
    scrubberSub: string;
    epochPrefix: string;
    chartTitleLoss: string;
    chartTitleAuc: string;
    trainLossLabel: string;
    valScoreLabel: string;
    lrLabel: string;
    ampTitle: string;
    ampDesc: string;
  };
  section6_evaluation: {
    tag: string;
    title: string;
    description: string;
    tabLeaderboard: string;
    tabConfusion: string;
    tabShortcut: string;
    tabOod: string;
    leaderboardTitle: string;
    tableDisease: string;
    tableAuroc: string;
    tableCi95: string;
    tableThreshold: string;
    tableBenchmark: string;
    confusionTitle: string;
    confusionDesc: string;
    shortcutTitle: string;
    shortcutDesc: string;
    rawCamMetric: string;
    groundedMetric: string;
    auditStatusPass: string;
    oodTitle: string;
    oodDesc: string;
    retentionLabel: string;
  };
  footer: {
    copyright: string;
    confidentiality: string;
    pageIndicator: string;
  };
}

export const I18N_DICTIONARY: Record<Language, I18nContent> = {
  en: {
    nav: {
      backToPacs: "Back to PACS Viewer",
      instituteName: "LungRay Healthcare AI Consortium",
      reportTitle: "Clinical Monograph & System Verification Report",
      sectionNames: [
        "Clinical Context",
        "Problem Statement",
        "Data Infrastructure",
        "Data Balancing",
        "Model Architecture",
        "Training Dynamics",
        "Evaluation & Benchmarks",
      ],
      switchLanguage: "Language",
    },
    section0_hero: {
      hudStatus: "Clinical Acceptance Grade: Production Ready (Gate 6 Approved)",
      hudBadge: "Multi-Task CADx + WSOL Grounding",
      mainTitle: "LungRay Interactive Data & Machine Learning Storytelling Experience",
      subtitle:
        "A unified 3-head deep learning architecture resolving clinical task fragmentation, spurious shortcut learning, and unverified visual heatmaps across 160,000+ multi-center chest radiographs.",
      statAurocTitle: "0.8538",
      statAurocSub: "Composite Macro AUROC (0.4A + 0.3B + 0.3C)",
      statTbTitle: "1.0000",
      statTbSub: "Active TB Screening AUROC",
      statImagesTitle: "160,953",
      statImagesSub: "Multi-Center CXR Images",
      statLatencyTitle: "674 ms",
      statLatencySub: "Local CPU Inference Latency",
      ctaExplore: "Launch Interactive Story &darr;",
      ctaMethodology: "Launch PACS Viewer &rarr;",
    },
    section1_problem: {
      tag: "Clinical Problem Statement",
      title: "Three Existential Crises in Chest Radiography AI",
      description:
        "While computer vision models frequently claim diagnostic parity with radiologists, clinical translation remains halted by three systemic structural failures.",
      painPointLabel: "Conventional Workflow Dilemmas (Pain Points)",
      aiSolutionLabel: "LungRay Engineered Breakthroughs (Clinical Impact)",
      painPoints: [
        {
          title: "1. Task Fragmentation & Memory Overload",
          desc: "Hospitals must run 3 separate neural networks for general thoracic findings, TB triage, and COVID-19 screening. This triples GPU VRAM footprint and inflates inference latency beyond real-time limits.",
          impact: "Requires multiple server GPUs; ignores shared anatomical features across comorbidity cases.",
        },
        {
          title: "2. Spurious Shortcut Learning (Nature MI 2021)",
          desc: "As exposed by DeGrave et al., pandemic COVID-19 models frequently memorized hospital markers, 'PORTABLE' text labels, or scanner borders instead of true pulmonary consolidation.",
          impact: "False sense of clinical accuracy; catastrophic failure when deployed to community clinics.",
        },
        {
          title: "3. Unverified Intuitive Heatmaps",
          desc: "Conventional Grad-CAM outputs are merely subjective colorful overlays without quantitative spatial correlation (IoU) against certified board radiologist bounding boxes.",
          impact: "Physicians cannot verify whether the network localized the pathology or adjacent ribs.",
        },
      ],
      solutions: [
        {
          title: "Shared DenseNet-121 Multi-Task Backbone",
          desc: "A single lightweight 6.97M parameter encoder serves 3 isolated task heads simultaneously with parameter-free LayerNorm feature projection.",
          benefit: "66% VRAM reduction; fast CPU inference in 674ms (<150ms on RTX GPU).",
        },
        {
          title: "Clinical Pulmonary Grounding & Shortcut Audit",
          desc: "Offline morphological lung segmentation constrains model attention strictly within lung parenchyma, backed by automated Wilcoxon audit verification.",
          benefit: "94.92% in-lung energy ratio (100% pass rate >= 80% threshold, p = 1.15 x 10^-26).",
        },
        {
          title: "Quantitative WSOL Dual-Metric Grounding",
          desc: "Continuous activation maps are adaptively binarized and tested against ground-truth expert bounding boxes from Vietnam and international cohorts.",
          benefit: "0.7631 Box-IoU on RSNA Pneumonia and 0.6049 Box-IoU on VinDr-CXR.",
        },
      ],
      natureQuote:
        "AI for radiographic COVID-19 detection frequently relies on superficial shortcuts rather than true pathology, failing to generalize across institutions.",
      natureCitation: "DeGrave et al., Nature Machine Intelligence, 2021",
    },
    section2_datasets: {
      tag: "Data Infrastructure",
      title: "Six Multi-Center Datasets & Zero Patient Leakage Discipline",
      description:
        "LungRay orchestrates 160,953 radiographs across four continents with uncompromising scientific data separation protocols.",
      filterAll: "All Datasets (6)",
      filterPrimary: "Training Cohorts",
      filterGroundTruth: "Expert Box Validation",
      filterOod: "External Generalization",
      tableHeaders: {
        dataset: "Dataset Archive",
        cohort: "Images / Patients",
        splitProtocol: "Partitioning Strategy",
        clinicalRole: "Clinical Role",
        integrity: "Data Integrity Grade",
      },
      leakageDisciplineTitle: "Zero Patient Data Leakage Protocol (NIH ChestX-ray14)",
      leakageDisciplineDesc:
        "In clinical radiography, patients undergo multiple longitudinal examinations over months. Random image-level splitting contaminates the test cohort with the same patient's skeletal idiosyncrasies. LungRay strictly stratifies by Patient_ID with 70% Train / 10% Val / 20% Test (Train ∩ Test = ∅).",
    },
    section3_balancing: {
      tag: "Data Balancing & Pipelines",
      title: "Mitigating Extreme Imbalance & Anatomic Safety",
      description:
        "Multi-task learning on disparate datasets risks severe task starvation and label dominance without engineered sampling.",
      imbalanceTitle: "Anti-Task Starvation Batch Composition",
      imbalanceDesc:
        "NIH ChestX-ray14 (112,120) vastly outweighs COVIDx CXR-4 (~16,400) and TB (7,000). A naive uniform sampler yields a 16 : 2.3 : 1 ratio, starving Heads B and C of gradient updates.",
      rawRatioLabel: "Raw Data Composition (NIH 82.2% | COVIDx 12.0% | TB 5.1%)",
      balancedRatioLabel: "LungRay Weighted Multi-Task Sampler (60% NIH | 25% COVIDx | 15% TB)",
      starvationWarning:
        "Fixed allocation: 10 NIH / 4 COVIDx / 2 TB images per mini-batch of 16 guarantees robust gradient flow across all 3 classification heads.",
      pipelineTitle: "Anatomically Constrained Medical Preprocessing Pipeline",
      pipelineSteps: [
        {
          step: "01",
          title: "DICOM & Grayscale Ingestion",
          sub: "16-bit to 8-bit Safe Remap",
          desc: "Extracts pixel array, normalizes window center/width (WL/WW), and strips identifying PHI metadata.",
        },
        {
          step: "02",
          title: "Resolution Standardization",
          sub: "512 x 512 Spatial Dimension",
          desc: "Preserves subtle nodule and fibrosis textures lost at 224px while enabling 16x16 final feature resolution.",
        },
        {
          step: "03",
          title: "Anatomic Augmentation",
          sub: "Strict Zero-Vertical-Flip",
          desc: "Subtle +-7 deg tilt, CLAHE, and scaling. Vertical flips are strictly forbidden to preserve superior-inferior gravity.",
        },
        {
          step: "04",
          title: "Weighted Batch Sampling",
          sub: "60:25:15 Quota Engine",
          desc: "Yields deterministic multi-task batches with dynamic oversampling for minority disease cohorts.",
        },
        {
          step: "05",
          title: "PyTorch Tensor Ingestion",
          sub: "ImageNet Norm & FP16 AMP",
          desc: "Channel-wise z-score normalization and automatic mixed precision casting for gradient backpropagation.",
        },
      ],
    },
    section4_architecture: {
      tag: "Deep Learning Architecture",
      title: "Shared DenseNet-121 Encoder & Masked Multi-Task Engine",
      description:
        "A decoupled multi-head neural network providing independent taxonomic outputs without inter-head gradient interference.",
      backboneTitle: "Shared Encoder Backbone (DenseNet-121)",
      backboneDesc:
        "Dense connections reuse feature maps across dense blocks 1 through 4, outputting 1024-dimensional feature maps at 16x16 resolution with only 6.97M parameters.",
      normLayerTitle: "Parameter-Free LayerNorm & Dropout",
      normLayerDesc:
        "nn.LayerNorm(1024, elementwise_affine=False) standardizes the feature vector without introducing learnable scale/bias keys, preserving 100% backward compatibility.",
      headsTitle: "Three Independent Clinical Task Heads",
      headA: {
        title: "Head A: Thoracic Pathologies (NIH)",
        subtitle: "14 Multi-label Pathologies",
        desc: "Outputs independent Sigmoids calibrated against Youden's J decision thresholds.",
        loss: "Asymmetric Loss (ASL) + Dynamic Focal Loss",
      },
      headB: {
        title: "Head B: Tuberculosis Screening (TB)",
        subtitle: "Binary Normal vs Active TB",
        desc: "Single-logit Sigmoid classification achieving 1.0000 AUROC separation.",
        loss: "BCEWithLogitsLoss (Positive Weighting)",
      },
      headC: {
        title: "Head C: COVID-19 Triage (COVIDx)",
        subtitle: "COVID-19 vs Normal vs Pneumonia",
        desc: "Evaluated with honest in-lung pulmonary grounding to eliminate peripheral shortcuts.",
        loss: "CrossEntropy / Asymmetric Loss",
      },
      drawerTitle: "Layer Parameter Specification",
      closeDrawer: "Close Drawer",
      tensorDimensions: "Tensor Dimensions",
      parameterCount: "Parameter Count",
      activationFunction: "Activation Function",
      dropoutRate: "Dropout Probability",
    },
    section5_training: {
      tag: "Training Dynamics",
      title: "Epoch-by-Epoch Convergence & Cosine Learning Schedule",
      description:
        "Interactive visualization of 24 training epochs executed on Kaggle Tesla GPU with mixed precision and gradient isolation.",
      scrubberLabel: "Epoch Scrubber (Step 1 to 24)",
      scrubberSub:
        "Drag slider to inspect training state, loss values, and validation AUROCs at any epoch.",
      epochPrefix: "Epoch",
      chartTitleLoss: "Training Loss Convergence (Total & Sub-tasks)",
      chartTitleAuc: "Validation AUROC Performance by Head",
      trainLossLabel: "Total Training Loss",
      valScoreLabel: "Composite Validation Score",
      lrLabel: "Cosine Annealing Learning Rate",
      ampTitle: "PyTorch Mixed Precision (AMP) & Masked Backprop",
      ampDesc:
        "Trained using torch.cuda.amp.autocast() with FP16 gradients. For any batch item belonging to task k, gradients are routed exclusively to Head k and the shared backbone, ensuring zero cross-task gradient leakage.",
    },
    section6_evaluation: {
      tag: "Rigorous Evaluation",
      title: "Clinical Benchmarks, WSOL Grounding & Shortcut Audit",
      description:
        "Transparent empirical validation backed by 1,000-sample Bootstrap 95% Confidence Intervals and radiologist bounding box IoUs.",
      tabLeaderboard: "Head A 14 Pathologies",
      tabConfusion: "Head C Confusion Matrix",
      tabShortcut: "Shortcut Learning Audit",
      tabOod: "CheXpert OOD Generalization",
      leaderboardTitle: "Macro AUROC: 0.8271 [0.8110 – 0.8432] across 14 Thoracic Diseases",
      tableDisease: "Pathology",
      tableAuroc: "LungRay AUROC",
      tableCi95: "95% Bootstrap CI",
      tableThreshold: "Optimal Threshold (τ)",
      tableBenchmark: "Stanford CheXNet Reference",
      confusionTitle: "COVIDx CXR-4 Multi-Class Confusion Matrix",
      confusionDesc:
        "Honest classification after eliminating scanner border shortcuts (Normalized per-class accuracy).",
      shortcutTitle: "Clinical Pulmonary Grounding Audit (N = 150)",
      shortcutDesc:
        "Measuring the percentage of Grad-CAM activation energy residing strictly within anatomical lung fields.",
      rawCamMetric: "Baseline Raw Grad-CAM: 38.49% ± 10.45% (0/150 pass >=80%)",
      groundedMetric: "LungRay Clinical Grounded: 94.92% ± 1.60% (150/150 pass >=80%)",
      auditStatusPass: "Statistical Significance: Wilcoxon W = 11325.0, p = 1.15 x 10^-26",
      oodTitle: "Stanford CheXpert External Generalization (22,433 Images)",
      oodDesc: "Zero-shot testing on an independent hospital without parameter updates.",
      retentionLabel:
        "Average Generalization Retention Rate: 94.75% (ΔAUC = +0.0447 ≤ 0.080 safety ceiling)",
    },
    footer: {
      copyright: "© 2026 LungRay Healthcare AI Research Consortium. All rights reserved.",
      confidentiality:
        "Pre-Clinical Validation & System Acceptance Monograph • Prepared for Defense Committee",
      pageIndicator: "Interactive Section",
    },
  },
  vi: {
    nav: {
      backToPacs: "Về Hệ Thống Đọc Phim PACS",
      instituteName: "Viện Nghiên Cứu Trí Tuệ Nhân Tạo Y Tế LungRay",
      reportTitle: "Báo Cáo Chuyên Khảo Lâm Sàng & Nghiệm Thu Hệ Thống",
      sectionNames: [
        "Bối Cảnh Lâm Sàng",
        "Bối Cảnh Vấn Đề",
        "Hạ Tầng Dữ Liệu",
        "Cân Bằng Dữ Liệu",
        "Kiến Trúc Mô Hình",
        "Quá Trình Huấn Luyện",
        "Đánh Giá & Kiểm Toán",
      ],
      switchLanguage: "Ngôn ngữ",
    },
    section0_hero: {
      hudStatus: "Trạng Thái Nghiệm Thu: Sẵn Sàng Vận Hành (Gate 6 Phê Duyệt)",
      hudBadge: "Đa Nhiệm CADx + Định Vị WSOL",
      mainTitle: "Trải Nghiệm Trực Quan Hóa Dữ Liệu & Học Máy Tương Tác LungRay",
      subtitle:
        "Kiến trúc học sâu 3 đầu hợp nhất giải quyết triệt để sự phân mảnh tác vụ, hiện tượng khai thác đặc trưng giả mạo và bản đồ nhiệt thiếu kiểm chứng trên hơn 160.000 phim X-quang đa trung tâm.",
      statAurocTitle: "0.8538",
      statAurocSub: "Điểm AUROC Đa Nhiệm Hợp Nhất (0.4A + 0.3B + 0.3C)",
      statTbTitle: "1.0000",
      statTbSub: "AUROC Sàng Lọc Lao (TB)",
      statImagesTitle: "160.953",
      statImagesSub: "Ảnh X-Quang Đa Trung Tâm",
      statLatencyTitle: "674 ms",
      statLatencySub: "Độ Trễ Suy Luận Trên CPU",
      ctaExplore: "Khám Phá Dữ Liệu Tương Tác &darr;",
      ctaMethodology: "Mở Trạm Đọc Phim PACS &rarr;",
    },
    section1_problem: {
      tag: "Bối Cảnh Vấn Đề Lâm Sàng",
      title: "Ba Cuộc Khủng Hoảng Nền Tảng Trong Ứng Dụng AI X-Quang Ngực",
      description:
        "Mặc dù các mô hình thị giác máy tính liên tục công bố điểm số ngang ngửa chuyên gia, việc đưa vào ứng dụng thực tế bị đình trệ bởi các rào cản kiến trúc cố hữu.",
      painPointLabel: "Thực Trạng Rào Cản (Điểm Đau Lâm Sàng)",
      aiSolutionLabel: "Giải Pháp Đột Phá LungRay (Tác Động)",
      painPoints: [
        {
          title: "1. Phân Mảnh Tác Vụ & Cạn Kiệt Bộ Nhớ VRAM",
          desc: "Bệnh viện phải chạy 3 mạng nơ-ron rời rạc cho 14 bệnh tổng quát, Lao phổi và COVID-19, gây quá tải gấp 3 lần bộ nhớ GPU và kéo dài độ trễ suy luận.",
          impact: "Đòi hỏi nhiều GPU máy chủ đắt tiền; bỏ lỡ mối tương quan giải phẫu giữa các ca đồng nhiễm.",
        },
        {
          title: "2. Khai Thác Đặc Trưng Giả Mạo (Shortcut Learning)",
          desc: "Theo Nature MI (2021), mô hình COVID-19 thường đạt điểm cao nhờ ghi nhớ chữ 'PORTABLE', nhãn R/L hoặc vết cắt viền máy chụp thay vì tổn thương phổi thực tế.",
          impact: "Tạo cảm giác chính xác giả tạo; thất bại thảm hại khi triển khai sang bệnh viện tuyến cơ sở.",
        },
        {
          title: "3. Bản Đồ Nhiệt Cảm Tính Thiếu Kiểm Chứng",
          desc: "Grad-CAM truyền thống chỉ dừng lại ở các mảng màu minh họa đẹp mắt mà hoàn toàn không có chỉ số tương quan không gian (IoU) đối chiếu với nhãn khoanh vùng của bác sĩ.",
          impact: "Bác sĩ X-quang không thể xác minh AI bắt trúng mô bệnh hay chỉ đang kích hoạt vào xương sườn.",
        },
      ],
      solutions: [
        {
          title: "Kiến Trúc Đa Nhiệm Shared DenseNet-121",
          desc: "Một bộ mã hóa duy nhất 6.97 triệu tham số phục vụ đồng thời 3 nhánh nhiệm vụ độc lập, kết hợp tầng chiếu LayerNorm parameter-free.",
          benefit: "Giảm 66% bộ nhớ VRAM; suy luận CPU mượt mà trong 674ms (<150ms trên GPU RTX).",
        },
        {
          title: "Định Vị Phế Trường Lâm Sàng & Kiểm Toán Khách Quan",
          desc: "Thuật toán phân đoạn hình thái học ngoại tuyến ép buộc sự chú ý của mạng nằm trọn vẹn trong nhu mô phổi, có kiểm định thống kê Wilcoxon xác thực.",
          benefit: "Đạt 94.92% năng lượng trong phổi (100% ca đạt chuẩn >= 80%, p = 1.15 x 10^-26).",
        },
        {
          title: "Định Lượng WSOL Đối Chiếu Bác Sĩ Độc Lập",
          desc: "Bản đồ kích hoạt liên tục được nhị phân hóa thích nghi và kiểm thử trực tiếp so với Bounding Box chuyên gia từ Việt Nam và quốc tế.",
          benefit: "Đạt Box-IoU 0.7631 trên RSNA Pneumonia và 0.6049 trên VinDr-CXR.",
        },
      ],
      natureQuote:
        "AI phát hiện COVID-19 trên X-quang thường dựa vào các đường tắt hời hợt thay vì bệnh lý thực thụ, thất bại khi khái quát hóa giữa các cơ sở y tế.",
      natureCitation: "DeGrave và cộng sự, Nature Machine Intelligence, 2021",
    },
    section2_datasets: {
      tag: "Hạ Tầng Dữ Liệu",
      title: "Sáu Bộ Dữ Liệu Đa Trung Tâm & Kỷ Luật Không Rò Rỉ Bệnh Nhân",
      description:
        "LungRay quy tụ 160.953 phim chụp lồng ngực từ 4 châu lục với giao thức phân tách dữ liệu khoa học nghiêm ngặt bậc nhất.",
      filterAll: "Tất Cả Bộ Dữ Liệu (6)",
      filterPrimary: "Tập Huấn Luyện Chính",
      filterGroundTruth: "Tập Kiểm Thử Bounding Box",
      filterOod: "Đánh Giá Ngoại Suy (OOD)",
      tableHeaders: {
        dataset: "Tập Dữ Liệu",
        cohort: "Số Lượng Ảnh / Bệnh Nhân",
        splitProtocol: "Quy Chuẩn Phân Chia",
        clinicalRole: "Vai Trò Lâm Sàng",
        integrity: "Mức Liêm Chính Dữ Liệu",
      },
      leakageDisciplineTitle: "Kỷ Luật Zero Patient Data Leakage (NIH ChestX-ray14)",
      leakageDisciplineDesc:
        "Trong lâm sàng, một bệnh nhân chụp nhiều phim qua các đợt khám. Chia ngẫu nhiên theo ảnh sẽ làm lộ khung xương của cùng một người ở cả tập huấn luyện và kiểm thử. LungRay phân chia nghiêm ngặt 100% theo Patient_ID với tỷ lệ 70% Train / 10% Val / 20% Test (Train ∩ Test = ∅).",
    },
    section3_balancing: {
      tag: "Cân Bằng Dữ Liệu & Quy Trình",
      title: "Xử Lý Mất Cân Bằng Cực Hạn & An Toàn Giải Phẫu",
      description:
        "Huấn luyện đa nhiệm từ các nguồn dữ liệu chênh lệch lớn đòi hỏi kỹ thuật lấy mẫu chuyên sâu để ngăn ngừa đói tác vụ.",
      imbalanceTitle: "Cơ Chế Lấy Mẫu Chống Đói Tác Vụ (Anti-Task Starvation)",
      imbalanceDesc:
        "NIH ChestX-ray14 (112.120 ảnh) lớn áp đảo so với COVIDx CXR-4 (~16.400) và TB (7.000). Bộ lấy mẫu ngẫu nhiên sẽ tạo tỷ lệ 16 : 2.3 : 1, làm triệt tiêu gradient của Head B và Head C.",
      rawRatioLabel: "Tỷ Lệ Thô Tự Nhiên (NIH 82.2% | COVIDx 12.0% | TB 5.1%)",
      balancedRatioLabel: "Bộ Lấy Mẫu Đa Nhiệm Cân Bằng (60% NIH | 25% COVIDx | 15% TB)",
      starvationWarning:
        "Cố định hạn ngạch: 10 ảnh NIH / 4 ảnh COVIDx / 2 ảnh TB trong mỗi mini-batch 16 giúp duy trì dòng chảy gradient đồng đều cho cả 3 đầu phân loại.",
      pipelineTitle: "Quy Trình Tiền Xử Lý Ảnh Y Tế Ràng Buộc Giải Phẫu",
      pipelineSteps: [
        {
          step: "01",
          title: "Tiếp Nhận DICOM & Ảnh Xám",
          sub: "Chuyển Đổi An Toàn 16-bit sang 8-bit",
          desc: "Đọc ma trận điểm ảnh, chuẩn hóa cửa sổ sáng tối (WL/WW), và loại bỏ sạch thông tin định danh cá nhân PHI.",
        },
        {
          step: "02",
          title: "Quy Chuẩn Độ Phân Giải",
          sub: "Kích Thước Cố Định 512 x 512",
          desc: "Bảo tồn nốt mờ nhỏ và dải xơ hóa vốn bị xóa nhòa ở độ phân giải 224px, cho feature map 16x16 sắc nét.",
        },
        {
          step: "03",
          title: "Tăng Cường An Toàn",
          sub: "Tuyệt Đối Cấm Lật Dọc (No Vertical Flip)",
          desc: "Xoay nhẹ +-7 độ, cân bằng tương phản CLAHE. Cấm lật dọc nhằm bảo tồn cấu trúc đỉnh phổi - vòm hoành.",
        },
        {
          step: "04",
          title: "Lấy Mẫu Đa Nhiệm Cân Bằng",
          sub: "Hạn Ngạch 60:25:15",
          desc: "Tạo mini-batch theo tỷ lệ vàng với cơ chế lấy mẫu lặp (oversampling) ngẫu nhiên cho tập bệnh lý nhỏ.",
        },
        {
          step: "05",
          title: "Đóng Gói Tensor PyTorch",
          sub: "Chuẩn Hóa ImageNet & FP16 AMP",
          desc: "Chuẩn hóa z-score theo kênh và chuyển đổi định dạng nửa chính xác (AMP) phục vụ lan truyền ngược.",
        },
      ],
    },
    section4_architecture: {
      tag: "Kiến Trúc Học Sâu",
      title: "Shared DenseNet-121 Encoder & Động Cơ Cách Ly Gradient",
      description:
        "Mô hình đa nhiệm tách rời cung cấp chẩn đoán độc lập trên 3 không gian nhãn mà không gây xung đột gradient.",
      backboneTitle: "Bộ Mã Hóa Dùng Chung (DenseNet-121 Backbone)",
      backboneDesc:
        "Các kết nối dày đặc tái sử dụng đặc trưng qua các khối dense block 1 đến 4, xuất ra feature map 1024 chiều ở độ phân giải 16x16 chỉ với 6.97M tham số.",
      normLayerTitle: "Tầng Chuẩn Hóa LayerNorm Không Tham Số",
      normLayerDesc:
        "nn.LayerNorm(1024, elementwise_affine=False) chuẩn hóa vector đặc trưng mà không sinh thêm trọng số scale/bias, bảo tồn 100% tính tương thích checkpoint.",
      headsTitle: "Ba Nhánh Phân Loại Lâm Sàng Độc Lập",
      headA: {
        title: "Head A: 14 Bệnh Lồng Ngực (NIH)",
        subtitle: "Đa Nhãn Phức Hợp",
        desc: "Xuất xác suất qua hàm Sigmoid độc lập, hiệu chuẩn theo ngưỡng Youden's J.",
        loss: "Asymmetric Loss (ASL) + Dynamic Focal Loss",
      },
      headB: {
        title: "Head B: Sàng Lọc Lao Phổi (TB)",
        subtitle: "Nhị Phân Bình Thường vs Lao",
        desc: "Phân loại nhị phân 1 logit đạt độ phân biệt tuyệt đối 1.0000 AUROC.",
        loss: "BCEWithLogitsLoss (Cân bằng trọng số dương)",
      },
      headC: {
        title: "Head C: Phân Luồng COVID-19 (COVIDx)",
        subtitle: "COVID-19 vs Bình Thường vs Viêm Phổi",
        desc: "Được kiểm toán trung thực với giải thuật định vị phế trường để loại bỏ shortcut viền ảnh.",
        loss: "CrossEntropy / Asymmetric Loss",
      },
      drawerTitle: "Thông Số Kỹ Thuật Chi Tiết Từng Tầng",
      closeDrawer: "Đóng Bảng Chi Tiết",
      tensorDimensions: "Kích Thước Tensor",
      parameterCount: "Số Lượng Tham Số",
      activationFunction: "Hàm Kích Hoạt",
      dropoutRate: "Tỷ Lệ Dropout",
    },
    section5_training: {
      tag: "Động Lực Học Huấn Luyện",
      title: "Hội Tụ Qua 24 Epoch & Lịch Trình Tốc Độ Học Cosine",
      description:
        "Trực quan hóa tương tác 24 chu kỳ huấn luyện thực nghiệm trên GPU Kaggle Tesla với bộ nhớ bán chính xác và cách ly gradient.",
      scrubberLabel: "Thanh Trượt Chu Kỳ Huấn Luyện (Epoch 1 đến 24)",
      scrubberSub:
        "Kéo thanh trượt để quan sát trạng thái mất mát, độ chính xác và điểm AUROC tại từng thời điểm.",
      epochPrefix: "Chu Kỳ",
      chartTitleLoss: "Độ Hội Tụ Hàm Mất Mát (Tổng Thể & Từng Nhánh)",
      chartTitleAuc: "Hiệu Năng AUROC Tập Kiểm Định Theo Từng Head",
      trainLossLabel: "Mất Mát Huấn Luyện Tổng Thể",
      valScoreLabel: "Điểm Kiểm Định Hợp Nhất",
      lrLabel: "Tốc Độ Học Cosine Annealing",
      ampTitle: "Bộ Nhớ Bán Chính Xác PyTorch AMP & Cách Ly Gradient",
      ampDesc:
        "Huấn luyện bằng torch.cuda.amp.autocast() với gradient FP16. Mẫu thuộc bài toán k chỉ cập nhật trọng số cho Head k và phần Encoder dùng chung, bảo đảm zero gradient leakage giữa các bài toán.",
    },
    section6_evaluation: {
      tag: "Đánh Giá Thực Nghiệm Nghiêm Ngặt",
      title: "Chuẩn Lâm Sàng, Định Vị WSOL & Kiểm Toán Đặc Trưng Giả Mạo",
      description:
        "Đánh giá thực nghiệm minh bạch với Khoảng tin cậy 95% Bootstrap từ 1.000 lần tái lấy mẫu và Box-IoU đối chiếu bác sĩ.",
      tabLeaderboard: "14 Bệnh Head A",
      tabConfusion: "Ma Trận Nhầm Lẫn Head C",
      tabShortcut: "Kiểm Toán Shortcut Learning",
      tabOod: "Khái Quát Hóa CheXpert OOD",
      leaderboardTitle: "Macro AUROC: 0.8271 [0.8110 – 0.8432] trên 14 Bệnh Lý Lồng Ngực",
      tableDisease: "Bệnh Lý",
      tableAuroc: "LungRay AUROC",
      tableCi95: "Khoảng Tin Cậy 95% CI",
      tableThreshold: "Ngưỡng Tối Ưu (τ)",
      tableBenchmark: "Chuẩn Stanford CheXNet",
      confusionTitle: "Ma Trận Nhầm Lẫn Đa Lớp COVIDx CXR-4",
      confusionDesc:
        "Đánh giá trung thực sau khi loại bỏ hoàn toàn shortcut viền ảnh (Tỷ lệ chuẩn hóa theo lớp).",
      shortcutTitle: "Kiểm Toán Năng Lượng Trong Phổi (N = 150)",
      shortcutDesc:
        "Đo lường tỷ lệ phần trăm năng lượng kích hoạt Grad-CAM nằm trọn vẹn trong phế trường phổi.",
      rawCamMetric: "Mô hình Gốc Chưa Xử Lý: 38.49% ± 10.45% (0/150 ca đạt >=80%)",
      groundedMetric: "Định Vị Phế Trường LungRay: 94.92% ± 1.60% (150/150 ca đạt >=80%)",
      auditStatusPass: "Mức Ý Nghĩa Thống Kê: Wilcoxon W = 11325.0, p = 1.15 x 10^-26",
      oodTitle: "Thử Thách Xuyên Bệnh Viện Stanford CheXpert (22.433 Ảnh)",
      oodDesc: "Thử nghiệm ngoại suy không qua tinh chỉnh trọng số trên cơ sở y tế độc lập.",
      retentionLabel:
        "Tỷ Lệ Duy Trì Năng Lực Trung Bình: 94.75% (ΔAUC = +0.0447 ≤ ngưỡng an toàn 0.080)",
    },
    footer: {
      copyright:
        "Bản quyền nghiên cứu © 2026 Viện Nghiên Cứu Trí Tuệ Nhân Tạo Y Tế LungRay. Đã đăng ký bản quyền.",
      confidentiality:
        "Chuyên Khảo Thẩm Định Tiền Lâm Sàng & Nghiệm Thu Hệ Thống • Tài Liệu Phục Vụ Hội Đồng Bảo Vệ",
      pageIndicator: "Chương Tương Tác",
    },
  },
};

export function getDictionary(lang: Language): I18nContent {
  return I18N_DICTIONARY[lang] || I18N_DICTIONARY.en;
}
