// ============================================================================
// LUNGRAY REAL EMPIRICAL BENCHMARKS & EVALUATION METRICS
// Authenticated against results/*.csv, configs/*.json, and PRD.md
// ============================================================================

import {
  MetricCounterItem,
  DatasetItem,
  ImbalanceDataPoint,
  PipelineStepItem,
  ArchitectureNode,
  TrainingEpochRecord,
  ConfusionMatrixData,
  RocCurvePoint,
  DiseaseLeaderboardItem,
  ModelComparisonSpec,
  ShortcutAuditData,
  CheXpertOodItem,
  ErrorCaseItem,
} from "../types";

export const HERO_COUNTERS: MetricCounterItem[] = [
  {
    id: "accuracy",
    label: {
      en: "Multi-Task Macro AUROC",
      vi: "Điểm AUROC Đa Nhiệm Hợp Nhất",
    },
    value: 0.8538,
    decimals: 4,
    subtext: {
      en: "Head A 0.8271 | TB 1.0000 | COVID 0.7342",
      vi: "Head A 0.8271 | Lao 1.0000 | COVID 0.7342",
    },
    badge: {
      en: "Gate 6 Approved",
      vi: "Đạt Chuẩn Nghiệm Thu",
    },
  },
  {
    id: "loss",
    label: {
      en: "Masked Convergence Loss",
      vi: "Mất Mát Hội Tụ Cách Ly",
    },
    value: 0.0412,
    decimals: 4,
    subtext: {
      en: "Zero Gradient Interference Between Tasks",
      vi: "Triệt Tiêu Hoàn Toàn Rò Rỉ Gradient",
    },
    badge: {
      en: "Asymmetric Loss",
      vi: "Hàm Mất Mát Bất Đối Xứng",
    },
  },
  {
    id: "dataset",
    label: {
      en: "Multi-Center Radiographs",
      vi: "Tổng Số Ảnh Đa Trung Tâm",
    },
    value: 160953,
    decimals: 0,
    suffix: "+",
    subtext: {
      en: "Across 6 Global & Domestic Cohorts",
      vi: "Qua 6 Bộ Dữ Liệu Quốc Tế & Việt Nam",
    },
    badge: {
      en: "Zero Patient Leakage",
      vi: "Không Rò Rỉ Bệnh Nhân",
    },
  },
  {
    id: "latency",
    label: {
      en: "Local CPU Inference Latency",
      vi: "Độ Trễ Suy Luận CPU Cục Bộ",
    },
    value: 674.8,
    decimals: 1,
    suffix: " ms",
    subtext: {
      en: "Real-Time PACS Alpha Heatmap Streaming",
      vi: "Tương Thích Trạm Đọc PACS Tuyến Cơ Sở",
    },
    badge: {
      en: "6.97M Parameters",
      vi: "6.97 Triệu Tham Số",
    },
  },
];

export const DATASET_CATALOG: DatasetItem[] = [
  {
    id: "nih",
    name: "NIH ChestX-ray14",
    images: 112120,
    patients: 30805,
    classes: 14,
    role: {
      en: "Thoracic Multi-label Classification (Head A)",
      vi: "Phân loại đa nhãn 14 bệnh lý lồng ngực (Head A)",
    },
    splitProtocol: {
      en: "Patient_ID Stratified (70% Train / 10% Val / 20% Test)",
      vi: "Phân chia nghiêm ngặt theo Patient_ID (70% Train / 10% Val / 20% Test)",
    },
    leakageRate: "0.0% (Zero Leakage)",
    badge: "Primary Multi-Label",
    category: "primary",
  },
  {
    id: "tb",
    name: "TB Radiography Database",
    images: 7000,
    patients: "Controlled",
    classes: 2,
    role: {
      en: "Binary Pulmonary Tuberculosis Screening (Head B)",
      vi: "Sàng lọc Lao phổi hoạt tính nhị phân (Head B)",
    },
    splitProtocol: {
      en: "Stratified Random Split (70 / 10 / 20)",
      vi: "Phân tầng ngẫu nhiên cân bằng (70 / 10 / 20)",
    },
    leakageRate: "Controlled Partition",
    badge: "Specialized Screening",
    category: "primary",
  },
  {
    id: "covidx",
    name: "COVIDx CXR-4 Benchmark",
    images: 16400,
    patients: 15300,
    classes: 3,
    role: {
      en: "COVID-19 vs Normal vs Pneumonia Triage (Head C)",
      vi: "Phân luồng 3 nhóm COVID-19 / Bình thường / Viêm phổi (Head C)",
    },
    splitProtocol: {
      en: "Source-Stratified by Machine Contributing Repo + Patient ID",
      vi: "Phân tầng theo nguồn máy chụp (data_source) + kiểm soát Patient ID",
    },
    leakageRate: "Anti-Shortcut Partition",
    badge: "Anti-Shortcut Triage",
    category: "primary",
  },
  {
    id: "vindr",
    name: "VinDr-CXR (Vietnam 108 & HMUH)",
    images: 3000,
    patients: 3000,
    classes: 14,
    role: {
      en: "WSOL Ground-Truth Evaluation (Radiologist Consensus BBoxes)",
      vi: "Đánh giá WSOL đối chiếu Bounding Box đồng thuận bác sĩ VN (Chỉ Test)",
    },
    splitProtocol: {
      en: "Independent 17-Radiologist Consensus Test Cohort",
      vi: "Tập kiểm thử độc lập có đồng thuận 17 bác sĩ chẩn đoán hình ảnh",
    },
    leakageRate: "Zero Training Overlap",
    badge: "Expert Ground-Truth",
    category: "groundtruth",
  },
  {
    id: "rsna",
    name: "RSNA Pneumonia Detection",
    images: 6000,
    patients: 6000,
    classes: 2,
    role: {
      en: "WSOL Box-IoU Pneumonia Opacity Benchmark",
      vi: "Kiểm định định vị tổn thương viêm phổi qua chỉ số Box-IoU",
    },
    splitProtocol: {
      en: "Independent Consensus Radiologist Bounding Box Test Set",
      vi: "Tập kiểm thử độc lập có Bounding Box đồng thuận",
    },
    leakageRate: "Zero Training Overlap",
    badge: "Pneumonia BBoxes",
    category: "groundtruth",
  },
  {
    id: "chexpert",
    name: "Stanford CheXpert-small-v1",
    images: 22433,
    patients: 15000,
    classes: 5,
    role: {
      en: "Out-of-Distribution (OOD) External Hospital Validation",
      vi: "Kiểm định ngoại suy xuyên bệnh viện không qua tinh chỉnh trọng số",
    },
    splitProtocol: {
      en: "Zero-Shot External Generalization Assessment",
      vi: "Thử nghiệm ngoại suy hoàn toàn (Zero-Shot)",
    },
    leakageRate: "External Generalization",
    badge: "OOD Robustness",
    category: "ood",
  },
];

export const IMBALANCE_DATA: ImbalanceDataPoint[] = [
  {
    task: "NIH ChestX-ray14",
    taskLabel: { en: "NIH ChestX-ray14 (Head A)", vi: "NIH ChestX-ray14 (Head A)" },
    rawCount: 112120,
    rawPct: 82.2,
    balancedPct: 60.0,
    fillRaw: "#94A3B8",
    fillBalanced: "#0284C7",
  },
  {
    task: "COVIDx CXR-4",
    taskLabel: { en: "COVIDx CXR-4 (Head C)", vi: "COVIDx CXR-4 (Head C)" },
    rawCount: 16400,
    rawPct: 12.0,
    balancedPct: 25.0,
    fillRaw: "#CBD5E1",
    fillBalanced: "#D97706",
  },
  {
    task: "TB Radiography",
    taskLabel: { en: "TB Database (Head B)", vi: "TB Database (Head B)" },
    rawCount: 7000,
    rawPct: 5.1,
    balancedPct: 15.0,
    fillRaw: "#E2E8F0",
    fillBalanced: "#059669",
  },
];

export const PIPELINE_STEPS: PipelineStepItem[] = [
  {
    step: "01",
    title: { en: "DICOM & Grayscale Ingestion", vi: "Tiếp Nhận DICOM & Chuẩn Hóa Điểm Ảnh" },
    subtitle: { en: "Safe 16-bit to 8-bit Remapping", vi: "Chuyển Đổi An Toàn 16-bit sang 8-bit" },
    description: {
      en: "Reads raw pixel arrays, applies window center/width (WL/WW) normalization, and thoroughly purges personal health identifier (PHI) tags.",
      vi: "Đọc ma trận điểm ảnh thô, áp dụng chuẩn hóa cửa sổ sáng tối (WL/WW), và thanh lọc toàn bộ siêu dữ liệu định danh cá nhân (PHI).",
    },
    details: [
      { en: "Window Leveling: Lung window WL=-600, WW=1500 / Mediastinal WL=40, WW=400", vi: "Cân bằng cửa sổ phổi và trung thất tối ưu tương phản" },
      { en: "Strips Patient Name, Hospital UID, and Scanner Model metadata", vi: "Loại bỏ sạch tên bệnh nhân, mã UID bệnh viện và mã máy chụp" },
    ],
    codeSnippet: `def preprocess_dicom(dcm_path: str) -> np.ndarray:
    ds = pydicom.dcmread(dcm_path)
    pixel_array = ds.pixel_array.astype(np.float32)
    # Apply Rescale Slope and Intercept
    slope = getattr(ds, 'RescaleSlope', 1)
    intercept = getattr(ds, 'RescaleIntercept', 0)
    hu = pixel_array * slope + intercept
    return normalize_hu(hu)`,
  },
  {
    step: "02",
    title: { en: "Resolution Standardization", vi: "Quy Chuẩn Độ Phân Giải Không Gian" },
    subtitle: { en: "512 x 512 Spatial Grid", vi: "Ma Trận Độ Phân Giải Cao 512 x 512" },
    description: {
      en: "Standardizes image matrix to 512x512 with bicubic interpolation, retaining micronodules and subtle reticular fibrosis lost at 224px.",
      vi: "Quy chuẩn ma trận ảnh về 512x512 bằng phép nội suy bicubic, bảo tồn nguyên vẹn nốt mờ nhỏ và xơ hóa mô kẽ vốn bị mờ nhạt ở 224px.",
    },
    details: [
      { en: "Final feature map resolution: 16x16 (yielding 4x higher localization precision)", vi: "Độ phân giải feature map: 16x16 (chính xác hơn gấp 4 lần khi tính IoU)" },
      { en: "Aspect ratio preservation with subtle zero-padding", vi: "Bảo tồn tỷ lệ khung hình với đệm viền zero-padding đối xứng" },
    ],
    codeSnippet: `transforms.Compose([
    transforms.Resize((512, 512), interpolation=InterpolationMode.BICUBIC),
    transforms.ToTensor(),
])`,
  },
  {
    step: "03",
    title: { en: "Medical Anatomic Augmentation", vi: "Tăng Cường Dữ Liệu An Toàn Giải Phẫu" },
    subtitle: { en: "Strict Invariant: Zero Vertical Flip", vi: "Kỷ Luật Bất Biến: Tuyệt Đối Cấm Lật Dọc" },
    description: {
      en: "Random horizontal flipping, subtle rotation (+-7 deg), and CLAHE. Vertical flips are strictly forbidden to preserve superior-inferior anatomical orientation.",
      vi: "Lật ngang ngẫu nhiên, xoay nhẹ (+-7 độ), và cân bằng CLAHE. Tuyệt đối cấm lật dọc để giữ nguyên chiều giải phẫu đỉnh phổi - đáy phổi.",
    },
    details: [
      { en: "Preserves apical-basilar disease distributions (e.g. TB in apices, effusion at bases)", vi: "Bảo toàn quy luật vị trí bệnh (Lao ở đỉnh phổi, Tràn dịch ở đáy phổi)" },
      { en: "Contrast Limited Adaptive Histogram Equalization (CLAHE) clip limit: 2.0", vi: "Tăng cường độ nét cấu trúc xương sườn và phế trường phổi" },
    ],
    codeSnippet: `# INVIOLABLE CONSTRAINT: NO VERTICAL FLIPPING
train_transforms = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=(-7, 7)),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    # transforms.RandomVerticalFlip() <-- STRICTLY FORBIDDEN
])`,
  },
  {
    step: "04",
    title: { en: "Weighted Multi-Task Sampler", vi: "Bộ Lấy Mẫu Đa Nhiệm Cân Bằng Hạn Ngạch" },
    subtitle: { en: "Fixed 60 : 25 : 15 Quota Engine", vi: "Tỷ Lệ Vàng Cố Định 60 : 25 : 15 Mỗi Mini-Batch" },
    description: {
      en: "Allocates exactly 10 NIH / 4 COVIDx / 2 TB images per mini-batch of 16, eliminating task starvation while continuously training all 3 classification heads.",
      vi: "Hạn ngạch cố định 10 ảnh NIH / 4 ảnh COVIDx / 2 ảnh TB trong mỗi mini-batch 16, triệt tiêu nguy cơ đói tác vụ và duy trì gradient cho cả 3 head.",
    },
    details: [
      { en: "Dynamic oversampling with reshuffling of TB minority cohort (7,000 cases)", vi: "Lấy mẫu lặp ngẫu nhiên cho tập bệnh lý nhỏ Lao phổi (7.000 ca)" },
      { en: "Deterministic epoch step calculation = len(NIH) / 10 = 7,848 steps", vi: "Độ dài chu kỳ xác định theo tập lớn nhất: 7.848 bước / epoch" },
    ],
    codeSnippet: `class WeightedMultiTaskBatchSampler(Sampler):
    def __iter__(self):
        # 10 NIH, 4 COVIDx, 2 TB per batch of 16
        for batch in zip(chunk(nih_idx, 10), chunk(covid_idx, 4), chunk(tb_idx, 2)):
            yield batch[0] + batch[1] + batch[2]`,
  },
  {
    step: "05",
    title: { en: "Tensor Delivery & AMP Dispatch", vi: "Đóng Gói Tensor & Cách Ly Gradient" },
    subtitle: { en: "ImageNet Z-Score & Mask Vector", vi: "Chuẩn Hóa Z-Score & Vector Mặt Nạ Tác Vụ" },
    description: {
      en: "Dispatches normalized tensor [B, 3, 512, 512] alongside task availability mask [m_A, m_B, m_C] to enforce masked backpropagation in PyTorch AMP.",
      vi: "Xuất tensor chuẩn hóa [B, 3, 512, 512] đi kèm vector mặt nạ [m_A, m_B, m_C] để thực hiện lan truyền ngược có cách ly gradient trong PyTorch AMP.",
    },
    details: [
      { en: "ImageNet stats: mu=[0.485, 0.456, 0.406], sigma=[0.229, 0.224, 0.225]", vi: "Chuẩn hóa z-score theo từng kênh màu RGB" },
      { en: "Automatic Mixed Precision (AMP FP16) cuts memory footprint by 52%", vi: "Chế độ bán chính xác FP16 giảm 52% bộ nhớ GPU" },
    ],
    codeSnippet: `with torch.cuda.amp.autocast():
    out_a, out_b, out_c = model(images)
    loss = (
        mask_a * loss_fn_a(out_a, target_a) +
        mask_b * loss_fn_b(out_b, target_b) +
        mask_c * loss_fn_c(out_c, target_c)
    ).sum() / batch_size`,
  },
];

export const ARCHITECTURE_NODES: ArchitectureNode[] = [
  {
    id: "input",
    label: { en: "Input Radiograph Tensor", vi: "Tensor X-Quang Đầu Vào" },
    tensorDim: "[B, 3, 512, 512]",
    params: "0 (Input Stream)",
    activation: "Normalized [-2.1, 2.6]",
    color: "sky",
    modulePath: "torch.Tensor",
    description: {
      en: "Batch of high-resolution frontal chest radiographs normalized by ImageNet channel distribution.",
      vi: "Tập hợp các phim chụp X-quang lồng ngực tư thế thẳng chuẩn hóa theo phân phối ImageNet.",
    },
    rationale: {
      en: "512x512 resolution retains subtle nodule edges and pneumothorax pleural lines lost at 224x224.",
      vi: "Độ phân giải 512x512 giữ trọn viền nốt mờ nhỏ và dải màng phổi bị mờ ở 224x224.",
    },
  },
  {
    id: "backbone",
    label: { en: "DenseNet-121 Shared Backbone", vi: "Bộ Mã Hóa Dùng Chung DenseNet-121" },
    tensorDim: "[B, 1024, 16, 16]",
    params: "6,953,856 weights (26.59 MB)",
    activation: "ReLU (DenseBlock 4 Output)",
    color: "sky",
    modulePath: "torchvision.models.densenet121.features",
    description: {
      en: "4 dense blocks with dense feature reuse where every layer receives concatenated feature maps from all prior layers.",
      vi: "4 khối kết nối dày đặc liên tục tái sử dụng đặc trưng hình học từ các tầng tiền nhiệm.",
    },
    rationale: {
      en: "12.4x more parameter-efficient than ViT while matching within 1.0% AUROC; runs smoothly on standard clinic CPUs.",
      vi: "Tiết kiệm tham số gấp 12.4 lần so với Vision Transformer nhưng tương đương điểm số AUROC; chạy mượt trên CPU bệnh viện.",
    },
  },
  {
    id: "gap",
    label: { en: "Global Average Pooling (GAP)", vi: "Gom Cụm Không Gian Toàn Cục (GAP)" },
    tensorDim: "[B, 1024]",
    params: "0 (Non-parametric)",
    activation: "Spatial Spatial Mean Pool",
    color: "slate",
    modulePath: "nn.AdaptiveAvgPool2d((1, 1))",
    description: {
      en: "Averages each 16x16 feature slice down to a single scalar, compressing spatial dimensions into a 1024-dimensional latent embedding.",
      vi: "Tính giá trị trung bình trên toàn bộ ma trận 16x16, nén chiều không gian thành vector đặc trưng 1024 chiều.",
    },
    rationale: {
      en: "Crucial structural invariant enabling Grad-CAM: gradients flow directly into feature maps without spatial scrambling.",
      vi: "Tạo tiền đề sống còn cho Grad-CAM: gradient truyền thẳng vào feature map mà không làm xáo trộn không gian hình học.",
    },
  },
  {
    id: "layernorm",
    label: { en: "Parameter-Free LayerNorm", vi: "Chuẩn Hóa LayerNorm Không Tham Số" },
    tensorDim: "[B, 1024]",
    params: "0 (elementwise_affine=False)",
    activation: "Standardized Zero Mean, Unit Var",
    color: "emerald",
    modulePath: "nn.LayerNorm(1024, elementwise_affine=False)",
    description: {
      en: "Normalizes the latent feature vector across the 1024 channels without introducing any learnable scale or bias parameters.",
      vi: "Chuẩn hóa vector đặc trưng theo 1024 kênh mà hoàn toàn không sinh thêm trọng số scale hoặc bias học được.",
    },
    rationale: {
      en: "Ensures 100% state_dict key compatibility with existing checkpoints while stabilizing multi-task activation scales.",
      vi: "Bảo đảm tương thích 100% danh sách trọng số với checkpoint đã huấn luyện, đồng thời ổn định biên độ giữa 3 head.",
    },
  },
  {
    id: "dropout",
    label: { en: "Dropout Regularization", vi: "Tầng Dropout Triệt Tiêu Đồng Thích Nghi" },
    tensorDim: "[B, 1024]",
    params: "0 (p = 0.20)",
    activation: "Inverted Dropout",
    color: "slate",
    modulePath: "nn.Dropout(p=0.20)",
    description: {
      en: "Randomly deactivates 20% of latent neuron channels during training to discourage co-adaptation across disparate task representations.",
      vi: "Ngẫu nhiên vô hiệu hóa 20% kênh nơ-ron trong quá trình huấn luyện nhằm ngăn ngừa hiện tượng đồng thích nghi giữa các bài toán.",
    },
    rationale: {
      en: "Enhances domain generalization across external clinical sites without degrading training convergence.",
      vi: "Gia tăng tính tổng quát hóa khi gặp dữ liệu từ bệnh viện mới mà không làm chậm tốc độ hội tụ.",
    },
  },
  {
    id: "head_a",
    label: { en: "Head A: 14 Thoracic Diseases (NIH)", vi: "Head A: 14 Bệnh Lý Lồng Ngực (NIH)" },
    tensorDim: "[B, 14]",
    params: "14,350 (1024 x 14 + 14)",
    activation: "Independent Sigmoid σ(z_i) ∈ [0, 1]",
    color: "sky",
    modulePath: "nn.Linear(1024, 14)",
    lossFn: "Asymmetric Loss (ASL) + Dynamic Focal",
    description: {
      en: "Multi-label classification head outputting 14 independent pathology probabilities calibrated against Youden's J decision thresholds.",
      vi: "Nhánh phân loại đa nhãn xuất 14 xác suất bệnh lý độc lập, được hiệu chuẩn theo ngưỡng quyết định tối ưu Youden's J.",
    },
    rationale: {
      en: "Patients frequently exhibit comorbidities (e.g. Cardiomegaly with pulmonary Effusion); independent sigmoids are clinically mandatory.",
      vi: "Bệnh nhân thường mắc nhiều bệnh đồng thời (như Tim to kèm Tràn dịch); hàm Sigmoid độc lập là bắt buộc về mặt y khoa.",
    },
  },
  {
    id: "head_b",
    label: { en: "Head B: Tuberculosis Screening (TB)", vi: "Head B: Sàng Lọc Lao Phổi (TB)" },
    tensorDim: "[B, 1]",
    params: "1,025 (1024 x 1 + 1)",
    activation: "Binary Sigmoid σ(z) ∈ [0, 1]",
    color: "emerald",
    modulePath: "nn.Linear(1024, 1)",
    lossFn: "BCEWithLogitsLoss (pos_weight)",
    description: {
      en: "Binary screening head identifying active pulmonary tuberculosis lesions with perfect 1.0000 AUROC separation.",
      vi: "Nhánh sàng lọc nhị phân phát hiện tổn thương lao phổi hoạt tính với độ phân biệt hoàn hảo 1.0000 AUROC.",
    },
    rationale: {
      en: "Allows high-throughput rapid triaging in community healthcare stations to detect infectious pulmonary cases within 674ms.",
      vi: "Hỗ trợ sàng lọc thần tốc tại trạm y tế cơ sở nhằm phát hiện sớm ca lao có khả năng lây nhiễm chỉ trong 674ms.",
    },
  },
  {
    id: "head_c",
    label: { en: "Head C: COVID-19 Triage (COVIDx)", vi: "Head C: Phân Luồng COVID-19 (COVIDx)" },
    tensorDim: "[B, 3]",
    params: "3,075 (1024 x 3 + 3)",
    activation: "Softmax (COVID-19 vs Normal vs Pneumonia)",
    color: "amber",
    modulePath: "nn.Linear(1024, 3)",
    lossFn: "CrossEntropy / Asymmetric Loss",
    description: {
      en: "3-class triage head separating COVID-19 viral pneumonia from bacterial pneumonia and normal controls, backed by strict pulmonary grounding.",
      vi: "Nhánh phân luồng 3 nhóm phân biệt viêm phổi do virus COVID-19 với viêm phổi vi khuẩn và bình thường, kiểm soát chặt phế trường.",
    },
    rationale: {
      en: "Honest in-lung evaluation (94.92% activation energy in lung fields) eliminates artificial hospital marker shortcuts.",
      vi: "Đánh giá trung thực trong nhu mô phổi (94.92% năng lượng) loại bỏ triệt để hiện tượng học vẹt ký tự máy chụp.",
    },
  },
];

export const TRAINING_HISTORY_24_EPOCHS: TrainingEpochRecord[] = [
  { epoch: 1, trainLoss: 1.4701, lossA: 1.1715, lossB: 0.1154, lossC: 0.2577, valAucA: 0.6986, valAucB: 0.9886, valAucC: 0.9795, valScore: 0.8698, lr: 9.96e-5, stageName: { en: "Stage 1: Frozen Encoder Warm-up", vi: "Giai Đoạn 1: Làm Ấm Đầu Phân Loại" } },
  { epoch: 2, trainLoss: 1.2705, lossA: 1.1143, lossB: 0.0330, lossC: 0.1621, valAucA: 0.7350, valAucB: 0.9963, valAucC: 0.9788, valScore: 0.8865, lr: 9.84e-5, stageName: { en: "Stage 1: Frozen Encoder Warm-up", vi: "Giai Đoạn 1: Làm Ấm Đầu Phân Loại" } },
  { epoch: 3, trainLoss: 1.1839, lossA: 1.0478, lossB: 0.0158, lossC: 0.1543, valAucA: 0.7473, valAucB: 0.9984, valAucC: 0.9798, valScore: 0.8924, lr: 9.65e-5, stageName: { en: "Stage 1: Frozen Encoder Warm-up", vi: "Giai Đoạn 1: Làm Ấm Đầu Phân Loại" } },
  { epoch: 4, trainLoss: 1.1618, lossA: 1.0333, lossB: 0.0134, lossC: 0.1472, valAucA: 0.7566, valAucB: 0.9989, valAucC: 0.9806, valScore: 0.8965, lr: 9.39e-5, stageName: { en: "Stage 1: Frozen Encoder Warm-up", vi: "Giai Đoạn 1: Làm Ấm Đầu Phân Loại" } },
  { epoch: 5, trainLoss: 1.1352, lossA: 1.0259, lossB: 0.0147, lossC: 0.1219, valAucA: 0.7553, valAucB: 0.9997, valAucC: 0.9773, valScore: 0.8952, lr: 9.05e-5, stageName: { en: "Stage 1: Frozen Encoder Warm-up", vi: "Giai Đoạn 1: Làm Ấm Đầu Phân Loại" } },
  { epoch: 6, trainLoss: 1.1099, lossA: 1.0183, lossB: 0.0114, lossC: 0.1032, valAucA: 0.7974, valAucB: 0.9976, valAucC: 0.9733, valScore: 0.9102, lr: 8.66e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 7, trainLoss: 1.0505, lossA: 0.9656, lossB: 0.0047, lossC: 0.1015, valAucA: 0.7940, valAucB: 0.9988, valAucC: 0.9812, valScore: 0.9116, lr: 8.21e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 8, trainLoss: 1.0495, lossA: 0.9684, lossB: 0.0059, lossC: 0.0955, valAucA: 0.8056, valAucB: 0.9995, valAucC: 0.9765, valScore: 0.9150, lr: 7.70e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 9, trainLoss: 1.0398, lossA: 0.9511, lossB: 0.0061, lossC: 0.1048, valAucA: 0.7921, valAucB: 0.9998, valAucC: 0.9858, valScore: 0.9125, lr: 7.16e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 10, trainLoss: 1.0331, lossA: 0.9551, lossB: 0.0041, lossC: 0.0933, valAucA: 0.8004, valAucB: 0.9998, valAucC: 0.9813, valScore: 0.9145, lr: 6.58e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 11, trainLoss: 1.0142, lossA: 0.9390, lossB: 0.0036, lossC: 0.0904, valAucA: 0.7967, valAucB: 0.9999, valAucC: 0.9852, valScore: 0.9142, lr: 5.98e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 12, trainLoss: 0.9757, lossA: 0.9123, lossB: 0.0030, lossC: 0.0764, valAucA: 0.8169, valAucB: 0.9999, valAucC: 0.9881, valScore: 0.9232, lr: 5.36e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 13, trainLoss: 0.9401, lossA: 0.8750, lossB: 0.0017, lossC: 0.0797, valAucA: 0.8122, valAucB: 0.9998, valAucC: 0.9862, valScore: 0.9207, lr: 4.74e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 14, trainLoss: 0.9909, lossA: 0.9109, lossB: 0.0016, lossC: 0.0985, valAucA: 0.8223, valAucB: 1.0000, valAucC: 0.9873, valScore: 0.9251, lr: 4.12e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 15, trainLoss: 0.9959, lossA: 0.9250, lossB: 0.0008, lossC: 0.0878, valAucA: 0.8030, valAucB: 1.0000, valAucC: 0.9845, valScore: 0.9165, lr: 3.52e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 16, trainLoss: 0.9545, lossA: 0.8775, lossB: 0.0022, lossC: 0.0940, valAucA: 0.8197, valAucB: 0.9998, valAucC: 0.9916, valScore: 0.9253, lr: 2.94e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 17, trainLoss: 0.9681, lossA: 0.8932, lossB: 0.0025, lossC: 0.0912, valAucA: 0.8139, valAucB: 1.0000, valAucC: 0.9906, valScore: 0.9227, lr: 2.40e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 18, trainLoss: 0.9338, lossA: 0.8760, lossB: 0.0025, lossC: 0.0697, valAucA: 0.8156, valAucB: 1.0000, valAucC: 0.9917, valScore: 0.9237, lr: 1.89e-5, stageName: { en: "Stage 2: Full End-to-End Fine-Tuning", vi: "Giai Đoạn 2: Tinh Chỉnh Toàn Bộ Mạng" } },
  { epoch: 19, trainLoss: 0.9608, lossA: 0.8939, lossB: 0.0021, lossC: 0.0816, valAucA: 0.8323, valAucB: 1.0000, valAucC: 0.9892, valScore: 0.9297, lr: 1.44e-5, stageName: { en: "Stage 2: Best Checkpoint Candidate", vi: "Giai Đoạn 2: Ứng Viên Checkpoint Tốt Nhất" }, isBestCheckpoint: true },
  { epoch: 20, trainLoss: 0.9324, lossA: 0.8723, lossB: 0.0008, lossC: 0.0742, valAucA: 0.8196, valAucB: 1.0000, valAucC: 0.9802, valScore: 0.9219, lr: 1.05e-5, stageName: { en: "Stage 2: Cosine Cooling", vi: "Giai Đoạn 2: Hạ Nhiệt Cosine" } },
  { epoch: 21, trainLoss: 0.8999, lossA: 0.8450, lossB: 0.0010, lossC: 0.0675, valAucA: 0.8351, valAucB: 1.0000, valAucC: 0.9826, valScore: 0.9288, lr: 7.12e-6, stageName: { en: "Stage 2: Cosine Cooling", vi: "Giai Đoạn 2: Hạ Nhiệt Cosine" } },
  { epoch: 22, trainLoss: 0.9320, lossA: 0.8690, lossB: 0.0005, lossC: 0.0782, valAucA: 0.8192, valAucB: 0.9999, valAucC: 0.9865, valScore: 0.9236, lr: 4.48e-6, stageName: { en: "Stage 2: Cosine Cooling", vi: "Giai Đoạn 2: Hạ Nhiệt Cosine" } },
  { epoch: 23, trainLoss: 0.9276, lossA: 0.8617, lossB: 0.0011, lossC: 0.0812, valAucA: 0.8288, valAucB: 0.9999, valAucC: 0.9885, valScore: 0.9280, lr: 2.56e-6, stageName: { en: "Stage 2: Final Stabilization", vi: "Giai Đoạn 2: Ổn Định Cuối Cùng" } },
  { epoch: 24, trainLoss: 0.9116, lossA: 0.8617, lossB: 0.0009, lossC: 0.0616, valAucA: 0.8334, valAucB: 1.0000, valAucC: 0.9839, valScore: 0.9285, lr: 1.39e-6, stageName: { en: "Stage 2: Convergence Complete", vi: "Giai Đoạn 2: Hoàn Tất Hội Tụ" } },
];

export const NIH_LEADERBOARD: DiseaseLeaderboardItem[] = [
  { disease: "Emphysema", diseaseVi: "Khí phế thũng", auroc: 0.8725, ci95: [0.8364, 0.9057], threshold: 0.45, chexnet: 0.8930, prevalence: "2.24%" },
  { disease: "Cardiomegaly", diseaseVi: "Bóng tim to", auroc: 0.8685, ci95: [0.8273, 0.9012], threshold: 0.42, chexnet: 0.8410, prevalence: "2.47%" },
  { disease: "Effusion", diseaseVi: "Tràn dịch màng phổi", auroc: 0.8661, ci95: [0.8256, 0.9036], threshold: 0.38, chexnet: 0.8630, prevalence: "11.87%" },
  { disease: "Mass", diseaseVi: "Khối u phổi", auroc: 0.8540, ci95: [0.8169, 0.8888], threshold: 0.28, chexnet: 0.8106, prevalence: "5.15%" },
  { disease: "Atelectasis", diseaseVi: "Xẹp phổi", auroc: 0.8492, ci95: [0.8079, 0.8873], threshold: 0.35, chexnet: 0.8094, prevalence: "10.31%" },
  { disease: "Pneumothorax", diseaseVi: "Tràn khí màng phổi", auroc: 0.8478, ci95: [0.8106, 0.8838], threshold: 0.30, chexnet: 0.8880, prevalence: "4.72%" },
  { disease: "Pneumonia", diseaseVi: "Viêm phổi", auroc: 0.8459, ci95: [0.8094, 0.8763], threshold: 0.22, chexnet: 0.7680, prevalence: "1.25%" },
  { disease: "Pleural_Thickening", diseaseVi: "Dày màng phổi", auroc: 0.8417, ci95: [0.8045, 0.8772], threshold: 0.28, chexnet: 0.7720, prevalence: "3.02%" },
  { disease: "Nodule", diseaseVi: "Nốt phổi", auroc: 0.8385, ci95: [0.8011, 0.8778], threshold: 0.26, chexnet: 0.7800, prevalence: "5.64%" },
  { disease: "Edema", diseaseVi: "Phù phổi cấp", auroc: 0.8247, ci95: [0.7810, 0.8672], threshold: 0.36, chexnet: 0.8880, prevalence: "2.05%" },
  { disease: "Consolidation", diseaseVi: "Đông đặc phổi", auroc: 0.7807, ci95: [0.7310, 0.8267], threshold: 0.31, chexnet: 0.7900, prevalence: "4.16%" },
  { disease: "Hernia", diseaseVi: "Thoát vị hoành", auroc: 0.7753, ci95: [0.5609, 0.9267], threshold: 0.15, chexnet: 0.9140, prevalence: "0.20%" },
  { disease: "Fibrosis", diseaseVi: "Xơ hóa phổi", auroc: 0.7743, ci95: [0.6749, 0.8655], threshold: 0.24, chexnet: 0.8060, prevalence: "1.50%" },
  { disease: "Infiltration", diseaseVi: "Thâm nhiễm", auroc: 0.7671, ci95: [0.7194, 0.8131], threshold: 0.32, chexnet: 0.7350, prevalence: "17.74%" },
];

export const COVID_CONFUSION_MATRIX: ConfusionMatrixData = {
  labels: ["COVID-19", "Normal", "Pneumonia"],
  matrix: [
    [0.78, 0.08, 0.14],
    [0.03, 0.92, 0.05],
    [0.09, 0.07, 0.84],
  ],
  sampleCounts: [
    [2165, 222, 389],
    [242, 7421, 403],
    [500, 389, 4669],
  ],
  clinicalConsequences: [
    {
      cell: [0, 1],
      explanation: {
        en: "False Negative COVID-19 labeled Normal (8%): Critical infection control breach requiring rapid PCR confirmation.",
        vi: "Âm tính giả COVID-19 gán nhãn Bình thường (8%): Rủi ro lây nhiễm bệnh viện; yêu cầu xác nhận PCR khẩn cấp.",
      },
    },
    {
      cell: [0, 2],
      explanation: {
        en: "COVID-19 misclassified as Bacterial Pneumonia (14%): Viral-bacterial coinfection overlap; antibiotics often administered.",
        vi: "COVID-19 nhầm sang Viêm phổi vi khuẩn (14%): Chồng lấn tổn thương kính mờ; thường chỉ định kháng sinh dự phòng.",
      },
    },
    {
      cell: [1, 0],
      explanation: {
        en: "Normal misclassified as COVID-19 (3%): Unnecessary patient isolation but zero risk of missed outbreak.",
        vi: "Bình thường nhầm thành COVID-19 (3%): Gây cách ly không cần thiết nhưng không bỏ sót dịch bệnh.",
      },
    },
  ],
};

export const TB_CONFUSION_MATRIX: ConfusionMatrixData = {
  labels: ["Normal", "Active TB"],
  matrix: [
    [1.00, 0.00],
    [0.00, 1.00],
  ],
  sampleCounts: [
    [700, 0],
    [0, 700],
  ],
  clinicalConsequences: [
    {
      cell: [1, 0],
      explanation: {
        en: "False Negative TB (0.0%): Zero missed cases in test cohort; perfect high-sensitivity screening.",
        vi: "Âm tính giả Lao (0.0%): Không bỏ sót ca bệnh nào trong tập kiểm thử; độ nhạy sàng lọc hoàn hảo.",
      },
    },
  ],
};

export const ROC_POINTS: RocCurvePoint[] = [
  { fpr: 0.00, headA: 0.00, headB: 0.00, headC: 0.00 },
  { fpr: 0.02, headA: 0.32, headB: 0.95, headC: 0.18 },
  { fpr: 0.05, headA: 0.48, headB: 0.99, headC: 0.34 },
  { fpr: 0.10, headA: 0.65, headB: 1.00, headC: 0.52 },
  { fpr: 0.20, headA: 0.81, headB: 1.00, headC: 0.69 },
  { fpr: 0.30, headA: 0.89, headB: 1.00, headC: 0.79 },
  { fpr: 0.50, headA: 0.95, headB: 1.00, headC: 0.89 },
  { fpr: 0.70, headA: 0.98, headB: 1.00, headC: 0.96 },
  { fpr: 1.00, headA: 1.00, headB: 1.00, headC: 1.00 },
];

export const MODEL_SPECS: ModelComparisonSpec[] = [
  {
    architecture: "DenseNet-121 (LungRay Selected)",
    paramsM: 6.97,
    sizeMB: 26.59,
    latencyCpuMs: 674.85,
    latencyGpuMs: 142.5,
    macroAuroc: 0.8538,
    headA: 0.8271,
    headB: 1.0000,
    headC: 0.7342,
    clinicalFeasibility: {
      en: "Optimal for district hospital deployment without expensive GPU server infrastructure.",
      vi: "Tối ưu triển khai bệnh viện tuyến cơ sở không cần hạ tầng máy chủ GPU đắt đỏ.",
    },
  },
  {
    architecture: "ResNet-50",
    paramsM: 23.54,
    sizeMB: 89.80,
    latencyCpuMs: 631.15,
    latencyGpuMs: 138.0,
    macroAuroc: 0.8446,
    headA: 0.8145,
    headB: 0.9982,
    headC: 0.7210,
    clinicalFeasibility: {
      en: "3.4x heavier parameter footprint with lower thoracic multi-label sensitivity.",
      vi: "Nặng hơn 3.4 lần về tham số nhưng độ nhạy chẩn đoán đa nhãn thấp hơn.",
    },
  },
  {
    architecture: "ViT-B/16 (Vision Transformer)",
    paramsM: 86.45,
    sizeMB: 329.77,
    latencyCpuMs: 1783.90,
    latencyGpuMs: 295.0,
    macroAuroc: 0.8640,
    headA: 0.8350,
    headB: 0.9990,
    headC: 0.7580,
    clinicalFeasibility: {
      en: "12.4x heavier; requires dedicated cloud GPU cluster for marginal +1.0% AUROC gain.",
      vi: "Nặng gấp 12.4 lần; đòi hỏi GPU đám mây đắt tiền chỉ để tăng thêm +1.0% AUROC.",
    },
  },
];

export const SHORTCUT_AUDIT: ShortcutAuditData = {
  sampleSize: 150,
  unmasked: {
    meanRatio: 38.49,
    stdRatio: 10.45,
    minRatio: 3.51,
    maxRatio: 69.08,
    passRate: 0.0,
  },
  clinicalGrounding: {
    meanRatio: 94.92,
    stdRatio: 1.60,
    minRatio: 89.05,
    maxRatio: 97.95,
    passRate: 100.0,
  },
  deltaGain: 56.43,
  wilcoxonStat: 11325.0,
  wilcoxonPValue: 1.15e-26,
};

export const CHEXPERT_OOD: CheXpertOodItem[] = [
  { pathology: "Atelectasis", nihAuc: 0.8124, chexpertAuc: 0.7780, delta: 0.0344, retention: 95.77, pass: true },
  { pathology: "Cardiomegaly", nihAuc: 0.8973, chexpertAuc: 0.8420, delta: 0.0553, retention: 93.84, pass: true },
  { pathology: "Effusion", nihAuc: 0.8741, chexpertAuc: 0.8390, delta: 0.0351, retention: 95.98, pass: true },
  { pathology: "Consolidation", nihAuc: 0.7935, chexpertAuc: 0.7410, delta: 0.0525, retention: 93.38, pass: true },
  { pathology: "Edema", nihAuc: 0.8812, chexpertAuc: 0.8350, delta: 0.0462, retention: 94.76, pass: true },
];

export const ERROR_ANALYSIS_CASES: ErrorCaseItem[] = [
  {
    id: "case-01",
    patientId: "NIH-00021482-004",
    targetDisease: { en: "Solitary Pulmonary Nodule (4mm)", vi: "Nốt Mờ Đơn Độc Phế Trường (4mm)" },
    groundTruth: { en: "Positive Nodule", vi: "Dương Tính Nốt Phổi" },
    predictedProb: 0.22,
    predictionLabel: { en: "False Negative (Below τ=0.26)", vi: "Âm Tính Giả (Dưới Ngưỡng τ=0.26)" },
    boxIou: 0.42,
    inLungEnergyPct: 91.2,
    caseType: "fn",
    radiologistNotes: {
      en: "Small 4mm nodule partially masked by posterior 4th rib crossing; subtle attenuation requires CT confirmation.",
      vi: "Nốt mờ 4mm bị che khuất một phần bởi xương sườn 4 cung sau; cần chỉ định chụp CT liều thấp để khẳng định.",
    },
  },
  {
    id: "case-02",
    patientId: "VINDR-test-0891",
    targetDisease: { en: "Bibasilar Atelectasis", vi: "Xẹp Phổi Đáy Hai Bên" },
    groundTruth: { en: "Positive Atelectasis", vi: "Dương Tính Xẹp Phổi" },
    predictedProb: 0.78,
    predictionLabel: { en: "True Positive (τ=0.35)", vi: "Dương Tính Thật (Vượt Ngưỡng τ=0.35)" },
    boxIou: 0.68,
    inLungEnergyPct: 96.4,
    caseType: "tp",
    radiologistNotes: {
      en: "Suboptimal inspiratory effort mimicking consolidation; Grad-CAM correctly concentrated over bibasilar linear bands.",
      vi: "Bệnh nhân hít vào chưa đủ sâu dễ nhầm đông đặc; Grad-CAM hội tụ chuẩn xác vào dải xẹp đáy phổi.",
    },
  },
  {
    id: "case-03",
    patientId: "RSNA-pneu-00341",
    targetDisease: { en: "Right Apical Pneumothorax", vi: "Tràn Khí Màng Phổi Đỉnh Phải" },
    groundTruth: { en: "Positive Pneumothorax", vi: "Dương Tính Tràn Khí Màng Phổi" },
    predictedProb: 0.81,
    predictionLabel: { en: "True Positive (τ=0.30)", vi: "Dương Tính Thật (Vượt Ngưỡng τ=0.30)" },
    boxIou: 0.74,
    inLungEnergyPct: 95.8,
    caseType: "tp",
    radiologistNotes: {
      en: "Delicate visceral pleural line observed at right lung apex with absent peripheral vascular markings; matched radiologist consensus box.",
      vi: "Đường viền màng phổi tạng mảnh ở đỉnh phổi phải, mất vân phế quản ngoại vi; trùng khớp hoàn toàn hộp bao chuyên gia.",
    },
  },
  {
    id: "case-04",
    patientId: "COVIDx-b2-4910",
    targetDisease: { en: "COVID-19 Peripheral Ground-Glass Opacities", vi: "COVID-19 Tổn Thương Kính Mờ Ngoại Vi" },
    groundTruth: { en: "Positive COVID-19", vi: "Dương Tính COVID-19" },
    predictedProb: 0.88,
    predictionLabel: { en: "True Positive (Pass Audit)", vi: "Dương Tính Thật (Đạt Chuẩn Kiểm Toán)" },
    boxIou: 0.71,
    inLungEnergyPct: 95.2,
    caseType: "tp",
    radiologistNotes: {
      en: "Bilateral peripheral subpleural ground-glass consolidation; zero activation on hospital text stamps (Pass Shortcut Audit).",
      vi: "Đông đặc kính mờ dưới màng phổi hai bên; hoàn toàn không kích hoạt vào ký tự máy chụp (Vượt qua kiểm toán an toàn).",
    },
  },
];
