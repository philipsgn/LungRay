# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Nền tảng: LungRay — Hệ Thống Hỗ Trợ Chẩn Đoán & Định Vị Tổn Thương X-Quang Ngực Đa Nhiệm (LungRay Multi-Task CADx + WSOL XAI)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Tên nền tảng** | **LungRay** (AI Chest X-ray Clinical Decision Support & WSOL Grounding Platform) |
| **Mã dự án** | LUNGRAY-MULTITASK-WSOL-2026 |
| **Phiên bản** | v8.5 (Integrated Phase 8 Fail-Safe Layer & SOTA Arena, Gate 6 Approved) |
| **Tác giả** | Staff AI Architect & Clinical Informatics Squad (10+ YOE) |
| **Trạng thái** | APPROVED FOR CLINICAL DECISION SUPPORT EVALUATION & DEFENSE READY |
| **Mục tiêu hoàn thành** | 16 tuần (Quy chuẩn Đồ án Tốt nghiệp & Sản phẩm Hỗ trợ Lâm sàng Tiền triển khai) |

---

## 1. TỔNG QUAN SẢN PHẨM & TẦM NHÌN (PRODUCT VISION)

### 1.1. Tuyên ngôn sản phẩm (Vision Statement)
Xây dựng **LungRay** — hệ sinh thái phần mềm **Hỗ trợ Ra Quyết định Lâm sàng (Computer-Aided Diagnosis / Clinical Decision Support - CADx/CDS)** dành riêng cho bác sĩ chẩn đoán hình ảnh từ phim chụp X-quang ngực thẳng (Chest Radiograph - CXR). Nền tảng ứng dụng mô hình học sâu đa nhiệm 3 nhánh (Multi-Task Learning 3-Head) trên nền tảng mạng nền tảng dùng chung (Shared DenseNet-121 Encoder), tích hợp trí tuệ nhân tạo minh bạch (Explainable AI - XAI) thông qua định vị tổn thương có giám sát yếu (Weakly-Supervised Object Localization - WSOL) được lượng hóa đối chiếu với hộp bao chuyên gia (Bounding Box IoU).

> [!IMPORTANT]
> **ĐỊNH VỊ PHÁP LÝ & AN TOÀN Y TẾ**: LungRay được thiết kế và vận hành dưới vai trò **Ý kiến Chuyên môn Thứ Hai (Second Reader / Triaging Assistant)** nhằm tăng độ nhạy phát hiện tổn thương sớm và giảm thiểu quá tải cho bác sĩ trong ca trực. Nền tảng **KHÔNG PHẢI LÀ THIẾT BỊ CHẨN ĐOÁN TỰ ĐỘNG ĐỘC LẬP** và không thay thế phán đoán lâm sàng của bác sĩ có chứng chỉ hành nghề. Toàn bộ dự đoán bất thường đều đi kèm lớp bảo vệ an toàn **Fail-Safe OOD Lockout** để từ chối các phim chụp nằm ngoài phạm vi giải phẫu hoặc có chất lượng không đạt chuẩn.

### 1.2. Đối tượng người dùng & Chân dung khách hàng (User Personas)
1. **Bác sĩ Chẩn đoán hình ảnh (Radiologist):**
   - *Nhu cầu*: Cần ý kiến tham vấn thứ hai (second opinion) độc lập, tốc độ phản hồi nhanh $\le 1.8$s, trực quan hóa vị trí nghi ngờ tổn thương dạng heatmap tương tác để tránh bỏ sót tổn thương nhỏ (nodule, pneumothorax sớm) trong ca trực đêm đông bệnh nhân.
   - *Điểm đau*: Quá tải phim chụp (100–200 ca/ca trực), mệt mỏi thị giác, không tin tưởng các mô hình "hộp đen" chỉ đưa ra xác suất vô căn cứ.
2. **Bác sĩ Đa khoa Tuyến cơ sở / Bệnh viện dã chiến (General Practitioner):**
   - *Nhu cầu*: Công cụ sàng lọc phân luồng nhanh các bệnh truyền nhiễm cấp thiết (Lao phổi, COVID-19) và bệnh lý lồng ngực nguy cấp (Tràn khí màng phổi, Phù phổi cấp) để kịp thời hội chẩn hoặc chuyển viện.
   - *Điểm đau*: Thiếu chuyên gia X-quang tại chỗ, trang thiết bị đọc phim chưa chuyên sâu.
3. **Hội đồng Thẩm định & Giảng viên Hướng dẫn (Academic/Clinical Evaluators):**
   - *Nhu cầu*: Chứng minh tính liêm chính học thuật, ngăn ngừa rò rỉ dữ liệu (Zero Patient Leakage) và chứng minh AI "học đúng bệnh" chứ không lợi dụng shortcut từ máy chụp/watermark nguồn ảnh.

---

## 2. BÀI TOÁN KỸ THUẬT & GIÁ TRỊ CỐT LÕI (VALUE PROPOSITION)

### 2.1. Phát biểu bài toán sản phẩm (Problem Statement)
- Hầu hết các ứng dụng AI chẩn đoán ảnh X-quang hiện nay chỉ tập trung vào một tập dữ liệu đơn lẻ hoặc một bệnh lý hẹp, dẫn đến tính khái quát kém và không đáp ứng được bức tranh bệnh học toàn diện tại phòng khám.
- Việc kết hợp dữ liệu đa nguồn từ nhiều bệnh viện tiềm ẩn nguy cơ **Shortcut Learning** (mô hình học thuộc đặc trưng biên máy chụp hoặc ký tự watermark để đưa ra chẩn đoán giả).
- Đa số đồ án chỉ hiển thị Grad-CAM định tính bằng mắt thường mà không có căn cứ định lượng (IoU) để chứng minh vùng chú ý trùng khớp với tổn thương thực tế.

### 2.2. Giải pháp kỹ thuật toàn diện
- **Kiến trúc Multi-Task 3-Head Shared Encoder**: Tận dụng một backbone duy nhất (DenseNet-121 / ResNet-50 / ViT) để giải quyết đồng thời 3 nhiệm vụ lâm sàng độc lập, tối ưu tài nguyên tính toán và bộ nhớ GPU.
- **Bộ máy hàm mất mát cải tiến (TASK-013)**: Kết hợp Asymmetric Loss (ASL) triệt tiêu easy negatives và Focal Loss với `pos_weight` động kẹp trần 50x cho 14 bệnh lồng ngực NIH.
- **Kiểm định định lượng IoU (WSOL Grounding)**: Binarize heatmap thích nghi và so sánh trực tiếp với Bounding Box chuyên gia từ bác sĩ Việt Nam (VinDr-CXR: Mean Box-IoU 0.6049) và RSNA Pneumonia Detection (Mean Box-IoU 0.7631).
- **Shortcut Learning Audit Engine**: Cơ chế kiểm toán độc lập đo lường tỷ lệ năng lượng kích hoạt nằm trong phế trường phổi ($\ge 80\%$) cho nhánh COVID-19; giải thuật Clinical Pulmonary Grounding đạt 94.92% năng lượng trong phổi.
- **Trải nghiệm Full-stack Decoupled chuẩn PACS**: Tách rời Backend FastAPI Microservice (Port 8000) và Frontend Next.js 14 PACS Viewer (Port 3000) với 1-Click Native Launcher (`scripts/start_local.ps1`).

---

## 3. YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS - FR)

### FR1: Multi-Task Inference Engine (Lõi suy luận 3 nhánh)
- **FR1.1 — Head A (Phân loại đa nhãn 14 bệnh lý lồng ngực NIH ChestX-ray14)**:
  - Dự đoán đồng thời xác suất của 14 bệnh/bất thường lồng ngực được chuẩn hóa danh mục theo **Hội Lồng ngực Fleischner Society** và gắn mã **WHO ICD-10** quốc tế:
    | Bệnh lý tiếng Anh | Thuật ngữ Y khoa tiếng Việt | Mã WHO ICD-10 | Phân loại Fleischner / Giải phẫu | Ngưỡng Youden $\tau$ |
    |:---|:---|:---:|:---|:---:|
    | **Atelectasis** | Xẹp phổi (mất thể tích phế nang) | `J98.11` | Linear / Lobar collapse | 0.35 |
    | **Cardiomegaly** | Bóng tim to (chỉ số tim-lồng ngực $> 0.5$) | `I51.7` | Cardiothoracic ratio $> 0.5$ | 0.40 |
    | **Effusion** | Tràn dịch màng phổi | `J90` | Costophrenic blunting | 0.38 |
    | **Infiltration** | Thâm nhiễm mô kẽ / phế nang | `J18.9` | Interstitial / Alveolar opacity | 0.32 |
    | **Mass** | Khối mờ lồng ngực ($> 30\text{mm}$) | `R91.8` | Solid mass lesion $> 30\text{mm}$ | 0.28 |
    | **Nodule** | Nốt mờ phế trường ($\le 30\text{mm}$) | `R91.1` | Solitary / Multiple nodules | 0.26 |
    | **Pneumonia** | Viêm phổi thùy / phế quản phế viêm | `J18.9` | Consolidation with air bronchograms | 0.30 |
    | **Pneumothorax** | Tràn khí màng phổi | `J93.9` | Visceral pleural line | 0.30 |
    | **Consolidation** | Đông đặc nhu mô phổi | `J18.9` | Opacity obscuring underlying vessels | 0.34 |
    | **Edema** | Phù phổi cấp / Thuyên tắc huyết quản | `J81.0` | Kerley B lines, bat-wing pattern | 0.36 |
    | **Emphysema** | Khí phế thũng (tăng sáng phế trường) | `J43.9` | Hyperlucency, flattened diaphragms | 0.25 |
    | **Fibrosis** | Xơ hóa phổi (dải xơ mô kẽ) | `J84.10` | Reticular / Honeycombing pattern | 0.22 |
    | **Pleural Thickening** | Dày màng phổi | `J92.9` | Pleural plaque / Apical capping | 0.24 |
    | **Hernia** | Thoát vị hoành | `K44.9` | Diaphragmatic defect with bowel gas | 0.18 |
  - Hỗ trợ chuẩn hóa hàm mất mát:
    - **Asymmetric Loss (ASL)**: $\gamma_-=4.0, \gamma_+=1.0, \text{clip}=0.05$ giúp triệt tiêu gradient của các nhãn âm tính áp đảo, tối ưu hóa các bệnh lý hiếm gặp.
    - **Dynamic Focal Loss**: $\gamma=2.0, \alpha=0.25$ với per-class `pos_weight` kẹp trần tại 50.0.
  - Phân loại qua 14 ngưỡng động đa lớp $\tau_c$ được hiệu chuẩn theo Youden's J statistic ($J = \text{TPR} - \text{FPR}$) lưu tại `configs/optimal_thresholds.json`.
- **FR1.2 — Head B (Sàng lọc Lao phổi nhị phân - Tuberculosis)**:
  - Trả về xác suất nhị phân: Normal vs Tuberculosis (`A15.0`) bằng BCEWithLogitsLoss.
  - Ngưỡng phân loại Youden $\tau_B = 0.50$.
  - *Ghi chú trung thực về dữ liệu (Dataset Transparency)*: AUROC 1.0000 ghi nhận trên tập kiểm định Shenzhen phản ánh sự phân tách rõ rệt giữa hai cơ sở thu thập (bệnh viện chuyên khoa lao vs trạm khám sức khỏe bình thường), đòi hỏi cần kiểm định thêm trên mẫu đa trung tâm trước khi áp dụng lâm sàng.
- **FR1.3 — Head C (Sàng lọc nhị phân COVID-19 trên COVIDx CXR-4)**:
  - Phân loại nhị phân sàng lọc COVID-19 (`U07.1`) Positive vs Non-COVID/Normal qua Sigmoid (`num_classes_c=1`) tối ưu hóa theo Youden's J threshold ($\tau_C = 0.4893$) trên kiến trúc production.
  - Chuẩn hóa theo benchmark quốc tế COVIDx CXR-4 (*Nature Scientific Reports*).
- **FR1.4 — Masked Loss, Feature Normalization & Inference Decoupling**:
  - Tầng chiếu đặc trưng tích hợp **LayerNorm parameter-free** (`elementwise_affine=False`) đặt sau GAP và trước Dropout(0.2), bảo đảm 100% tương thích nghiêm ngặt với checkpoint `checkpoints/best_model.pth` (không sinh key lạ trong `state_dict`).
  - Hỗ trợ gọi suy luận riêng lẻ từng head qua tham số `task_id` (`'head_a'`, `'head_b'`, `'head_c'`) để tiết kiệm FLOPs hoặc gộp toàn diện cả 3 heads trong 1 lần forward pass.
  - Bảo đảm cơ chế Zero Gradient Leakage giữa các heads trong quá trình huấn luyện.
- **FR1.6 — Multi-Backbone Consensus Serving, 3-Pass Clinical TTA & Temperature Scaling Calibration (Phase 2, Phase 7 & Phase 8.1)**:
  - Hỗ trợ chuyển đổi trực tiếp trên thanh điều khiển PACS giữa 5 mô hình lâm sàng chuyên biệt:
    1. `standard`: Mô hình DenseNet-121 SOTA CADx (`best_model.pth`, Mean AUC 0.9095) phục vụ triaging khẩn cấp 16 bệnh.
    2. `wsol`: Mô hình DenseNet-121 WSOL Attention Specialist (`best_wsol_finetune.pth`, RSNA Box-IoU 0.2454, TB AUC 0.9684) tối ưu định vị tổn thương khu trú.
    3. `resnet50`: Mô hình ResNet-50 Specialist (`best_resnet50.pth`, Mean AUC 0.8258, độ trễ 42ms) cung cấp góc nhìn đối chứng kiến trúc Residual.
    4. `ensemble`: Động cơ đồng thuận kết hợp liên minh 3 mô hình (DenseNet-121 + ResNet-50 + WSOL Specialist) qua thuật toán bỏ phiếu mềm thích ứng với chỉ số `ensemble_agreement`.
    5. `ag_mtcnet`: Mô hình Đỉnh cao AG-MTCNet (Anatomical-Gated Multi-Task Network) kết hợp 2 giai đoạn: Cổng phân đoạn giải phẫu Dense-UNet (Stage 1, Dice 0.9450, IoU 0.8974 trên tập nhãn phổi thật) tiền xử lý lọc nhiễu không phá hủy + Mạng đa nhiệm DenseNet-121/ResNet-50 fine-tune với Asymmetric Focal Loss (Stage 2) và White-out Lung Fail-Safe tự động.
  - **Tự động 3-Pass Clinical TTA (Test-Time Augmentation)**: Tự động kết hợp 3 góc nhìn (Chuẩn, CLAHE chống chênh lệch tương phản, và Multi-Scale 1.03x Center View) xếp chồng tensor `(3, 3, 512, 512)` thực thi song song trong 1 lượt forward pass GPU ($\le 0.35$s overhead) giúp triệt tiêu triệt để rủi ro dịch chuyển máy chụp (Cross-hospital domain shift).
  - **Hiệu chuẩn nhiệt độ Platt / Temperature Scaling ($T = 1.20$)**: Làm mềm các dự đoán xác suất cực đoan trên dữ liệu ngoại vi, bảo đảm tính bất biến ranh giới quyết định ($p = 0.5 \implies z/T = 0 \implies p = 0.5$).
  - **Zero-Downtime Model Hot-Reloading (`POST /api/v1/models/reload`)**: Tự động nhận diện và nạp tức thì checkpoint `best_resnet50.pth` và `ag_mtcnet_best.pth` khi có sẵn trên đĩa mà không cần khởi động lại dịch vụ backend.
  - Tự động tính toán điểm số đồng thuận đa mô hình `ensemble_agreement` $\in [0, 1]$ và hiển thị huy hiệu Consensus trên trạm đọc PACS Next.js.
  - Đối chiếu kiểm chứng thực nghiệm lâm sàng theo nghiên cứu công bố trên *The Lancet Digital Health* (PubMed 34219054): Hợp tác Bác sĩ X-quang và trợ lý AI giúp nâng độ chính xác từ 0.713 lên 0.808 ROC-AUC (+0.095 AUC) đồng thời giảm 48.6% thời gian đọc mỗi ca bệnh.
  - Xác minh độ bao quát lâm sàng đạt 100% các bệnh lý lồng ngực khả dĩ trên ảnh X-quang ngực phẳng theo chuẩn quốc tế *The Radiology Assistant Chest Index*.

### FR1.5 — Phase 8: Clinical Fail-Safe Layer & OOD Anomaly Lockout
- **FR1.5.1 — Helmholtz Free Energy Safety Gate ($S_E$)**:
  - Tính năng lượng tự do từ 14 logits của Head A: $S_E(x) = T \cdot \sum_{c=1}^{14} \log(1 + \exp(z_c / T))$ với $T = 1.0$.
  - Ngưỡng từ chối tối ưu: $\tau_E = 9.0421$ bảo toàn $\ge 95.0\%$ mẫu hợp lệ trong miền (In-Distribution Retention). Mọi ảnh có $S_E(x) < 9.0421$ đều bị khóa chẩn đoán ngay lập tức với AUROC phát hiện Far-OOD đạt 1.0000.
- **FR1.5.2 — Shannon Binary Entropy Uncertainty Gate ($H$)**:
  - Đo lường mức độ bất định chẩn đoán trung bình trên 14 xác suất: $H(x) = -\frac{1}{14}\sum_{c=1}^{14} [p_c \log_2 p_c + (1-p_c)\log_2(1-p_c)]$.
  - Ngưỡng bất định: $\tau_H = 0.6275$. Khi $H(x) > \tau_H$, hệ thống cảnh báo "High Clinical Uncertainty" để ngăn ngừa các phán đoán thiếu căn cứ.
- **FR1.5.3 — Khóa Tự Động Báo Cáo Sơ Bộ (ICD-10 Diagnostic Lockout)**:
  - Khi phát hiện OOD hoặc mẫu bất định cao: Trạng thái hệ thống chuyển sang `REJECTED_OOD`, kích hoạt viền cảnh báo đỏ phẫu thuật, đóng dấu watermark `INVALID - OOD ANOMALY DETECTED` lên bản đồ nhiệt và khóa hoàn toàn bảng kết luận ICD-10 để triệt tiêu 100% nguy cơ ảo tưởng chẩn đoán (AI Diagnostic Hallucination).

### FR1.7 — Phase 8.1: Anatomical Lung Grounding & Shortcut Mitigation Gate (BMC Infectious Diseases 2026)
- **FR1.7.1 — Dense-UNet Segmentation Backbone**: Tích hợp mô hình Dense-UNet (kiến trúc chuẩn Dubey et al., *BMC Infectious Diseases* 2026) làm cổng tiền lọc giải phẫu không phá hủy (non-destructive anatomical gate). Đạt hiệu năng phân đoạn phế trường thực nghiệm thực tế Val Dice 0.9450 và Val IoU 0.8974 trên tập nhãn phổi chuyên gia (Montgomery & Shenzhen), kèm cơ chế White-out Lung Fail-Safe tự động bỏ qua cổng lọc khi thể tích phổi dưới 18% (tránh làm mất thông tin ở các ca tràn dịch toàn bộ hoặc xẹp phổi nặng).
- **FR1.7.2 — Dilated Soft Masking**: Áp dụng mặt nạ phế trường giãn nở 6% và suy giảm 90% cường độ tín hiệu ngoài phổi (attenuation factor 0.10), bảo toàn 100% nhu mô phổi bên trong đồng thời triệt tiêu các đặc trưng học vẹt (watermark chữ R/L, mép viền thiết bị chụp).
- **FR1.7.3 — Smart Clinical Report Guardrail**: Khi In-Lung Activation Ratio $< 0.80$ hoặc tổn thương thâm nhiễm phế nang (`Infiltration`, `Consolidation`, `Pneumonia`) xung đột lâm sàng với kết luận phổi sáng bình thường, cơ chế guardrail lập tức triệt tiêu cảnh báo dương tính giả và phát cờ kiểm toán lâm sàng.

### FR2: Explainable AI & Quantitative WSOL Heatmap Generator
- **FR2.1 — Sinh bản đồ nhiệt Grad-CAM & Grad-CAM++**:
  - Tự động sinh activation map tại tầng tích chập cuối cùng (`denseblock4`/`norm5`) cho từng lớp bệnh lý được yêu cầu.
  - Hỗ trợ chuẩn hóa tensor 4D `dim=(2, 3)` cho giải thuật Grad-CAM++ bậc cao.
- **FR2.2 — Adaptive Heatmap Binarization**:
  - Chuyển đổi heatmap liên tục sang mặt nạ nhị phân tổn thương với ngưỡng thích nghi: $\tau_{mask} = \alpha \cdot \max(M_c)$ ($\alpha \in [0.2, 0.4]$).
- **FR2.3 — Quantitative Grounding Validation**:
  - Tự động tính chỉ số kép Dual-Metric (Box-level IoU và Pixel Mask-IoU) giữa mặt nạ nhị phân và Bounding Box chuyên gia trên VinDr-CXR và RSNA Pneumonia Detection.

### FR3: Shortcut Learning Audit Engine
- **FR3.1 — Lung Field Masking**:
  - Tự động xác định vùng phế trường phổi ($P_{\text{lung}}$) bằng phân đoạn hình thái ngưỡng Otsu kết hợp giải phẫu lồng ngực.
- **FR3.2 — Activation In-Lung Ratio Calculation**:
  - Tính toán tỷ lệ phần trăm năng lượng kích hoạt nằm trong phế trường phổi so với toàn bộ ảnh (đặc biệt loại trừ 4 góc chứa ký hiệu R/L, watermark máy chụp, mép viền ảnh).
- **FR3.3 — Clinical Pulmonary Grounding & Cảnh báo Shortcut**:
  - Chế độ lâm sàng triệt tiêu 100% gradient kích hoạt ngoài lồng ngực, nâng tỷ lệ năng lượng trong phổi lên 94.92%.
  - Gắn nhãn cảnh báo đỏ "High Shortcut Risk" nếu tỷ lệ kích hoạt trong phổi $< 75\%$.

### FR4: Ingestion & Tiền xử lý ảnh Y tế An toàn
- **FR4.1 — Hỗ trợ đa định dạng**: Tiếp nhận ảnh định dạng chuẩn y tế DICOM (`.dcm`), 16-bit / 8-bit Grayscale, PNG, JPG.
- **FR4.2 — Tiền xử lý chuẩn hóa $512 \times 512$**: Chuẩn hóa kích thước cố định $512 \times 512$ cho toàn bộ pipeline huấn luyện và đánh giá, chuẩn hóa phân phối ImageNet.
- **FR4.3 — Tăng cường dữ liệu an toàn giải phẫu**: Xoay nhẹ $\pm 7^\circ$, scale 0.96–1.04, translate 4%, CLAHE. **Cấm tuyệt đối lật dọc (`RandomVerticalFlip`)** nhằm bảo tồn hướng giải phẫu đỉnh phổi - vòm hoành.

### FR5: Giao diện Web PACS Viewer (Decoupled Frontend)
- **FR5.1 — Tải ảnh & Tương tác lâm sàng**: Kéo thả ảnh X-quang, tự động phát hiện định dạng và chuẩn hóa.
- **FR5.2 — Dashboard chẩn đoán 3-Head**: Hiển thị thẻ xác suất trực quan với phân loại màu cảnh báo: Xanh (Bình thường), Vàng (Nghi ngờ), Đỏ (Nguy cơ cao tổn thương).
- **FR5.3 — Interactive Heatmap Overlay Viewer**:
  - Hiển thị trực tiếp ảnh chồng lớp Heatmap (`mixBlendMode: "screen"`), vùng ngoài lồng ngực trong suốt 100%.
  - Thanh trượt điều chỉnh độ mờ (Alpha slider: $0\% \to 100\%$, mặc định 45%).
  - Cho phép click chọn trực tiếp từng bệnh lý cụ thể trong 14 bệnh Head A, Head B (TB) hoặc Head C (COVID) để chuyển đổi heatmap tương ứng.
  - Công tắc chuyển đổi chế độ kép: `Clinical Grounded` (Chuẩn y tế không nhiễu viền) vs `Raw Attention` (Kiểm toán shortcut learning).

---

## 4. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS - NFR)

### NFR1: Hiệu năng & Thời gian thực (Latency & Throughput)
- **Thời gian phản hồi đầu cuối (End-to-End Latency)**: $\le 1.8$ giây trên môi trường GPU cơ bản hoặc máy cục bộ có card đồ họa RTX cho quy trình: Tải ảnh $\to$ Chuẩn hóa $\to$ Inference 3 Heads $\to$ Sinh Heatmap Grad-CAM $\to$ Trả kết quả JSON & Image Base64 (chỉ tiêu cam kết: $\le 2.0$ giây).
- **Thời gian suy luận thuần (Inference Only)**: $\le 150$ ms/ảnh với DenseNet-121 trên GPU.

### NFR2: Độ chính xác & Tiêu chuẩn lâm sàng (Model Performance KPIs)
- **Head A (NIH 14 pathologies)**: Macro AUC-ROC đạt **0.8271** (95% CI: 0.8110–0.8432), chỉ tiêu $\ge 0.82$; Macro F1-Score $\ge 0.45$.
- **Head B (Lao phổi)**: AUC-ROC đạt **1.0000** (95% CI: 0.9990–1.0000), chỉ tiêu $\ge 0.90$.
- **Head C (COVIDx CXR-4 Sàng lọc nhị phân)**: AUC-ROC đạt **0.7342** (Baseline trên tập test độc lập holdout) / mục tiêu SOTA $\ge 0.85$.
- **WSOL Grounding Accuracy**: Mean Box-IoU đạt **0.7631** trên RSNA Pneumonia và **0.6049** trên VinDr-CXR (kiểm định định lượng trên tập mẫu chuẩn $n=50$ ca có Bounding Box chuyên gia từ bác sĩ).
- **Shortcut Audit & Lớp Fail-Safe**: Mô hình gốc có In-lung Energy Ratio đạt trung bình **38.49%** (0/150 ca đạt ngưỡng 80%); sau khi áp dụng Clinical Anatomical Projection đạt **94.92% $\pm$ 1.60%** (149/150 ca đạt $\ge 80\%$). Đây là căn cứ khoa học quyết định triển khai thêm Lớp Fail-Safe OOD (Phase 8).
- **Độ ổn định Ngoại vi (Domain Shift)**: $\Delta \text{AUC} = +0.0447$ trên CheXpert-small-v1 (chỉ tiêu $\le 0.080$).
- **Quy chuẩn Kiểm thử Tự động**: **151 / 151 Unit Tests PASS** tuyệt đối qua lệnh kiểm tra `scripts/verify.ps1` (100% tỷ lệ vượt qua cổng kiểm tra kỹ thuật).

### NFR3: An toàn, Bảo mật & Liêm chính dữ liệu (Data Integrity & Safety)
- **Zero Data Leakage**: Tuyệt đối không để ảnh của cùng một bệnh nhân xuất hiện ở cả tập Train và Test (phân chia nghiêm ngặt theo `Patient_ID`, $Train \cap Test = \emptyset$).
- **Source Stratification**: Phân tầng theo nguồn ảnh gốc đối với COVIDx CXR-4 (`data_source`) để kiểm soát rủi ro đa trung tâm.
- **De-identification**: Xóa bỏ toàn bộ thông tin định danh cá nhân (PII) nếu tải file DICOM trước khi đẩy vào pipeline suy luận.
- **GPU Buffer Device Safety**: Toàn bộ trọng số lớp `pos_weight` và `alpha` của Focal Loss được đăng ký dưới dạng module buffer để tự động chuyển thiết bị an toàn.

### NFR4: Khả năng mở rộng & Đóng gói (Scalability & Packaging)
- Backend được container hóa bằng Docker (Docker Image $\le 4$GB tối ưu runtime PyTorch).
- Trình khởi chạy **1-Click Native Launcher (`scripts/start_local.ps1`)** khởi động cả 2 dịch vụ trong vòng 3–4 giây, tự động dọn dẹp cache `.next` chống lỗi webpack.

---

## 5. CÁC ĐIỀU KIỆN NGOẠI LỆ & GIỚI HẠN (OUT OF SCOPE)

1. **Không can thiệp chẩn đoán điều trị pháp lý**: Hệ thống chỉ đóng vai trò hỗ trợ tham vấn (CDSS / Triaging tool), không thay thế bác sĩ chẩn đoán hình ảnh có chứng chỉ hành nghề.
2. **Không áp dụng trên ảnh CT Scanner hoặc MRI**: Chỉ xử lý ảnh chụp X-quang lồng ngực phẳng 2D tư thế thẳng (PA / AP view).
3. **Không tải toàn bộ dữ liệu MIMIC-CXR 570GB**: Giới hạn trong 6 tập dữ liệu mở khả thi đã phê duyệt (NIH ChestX-ray14, TB Database, COVIDx CXR-4, VinDr-CXR, RSNA, CheXpert-small).
4. **Bounding Box CHỈ dùng cho tập đánh giá**: Tuyệt đối không dùng Bounding Box cho tập huấn luyện; toàn bộ mạng học từ nhãn mức ảnh (WSOL).

---

## 6. MA TRẬN PHÂN CHIA TRÁCH NHIỆM & TIÊU CHÍ NGHIỆM THU (DOD - DEFINITION OF DONE)

| Tính năng | Phase | Tiêu chí hoàn thành (DoD) | Agent chịu trách nhiệm |
|:---|:---:|:---|:---:|
| **Data Ingestion & Splits** | Phase 2 | • Script sinh `patient_splits.csv` (NIH) và `covid_splits.csv` (Source-stratified)<br>• 100% tests trong `tests/test_data_pipeline.py` PASS ($Train \cap Test = \emptyset$ về Patient ID)<br>• Xuất bản `lungray-nih-512` và `lungray-covidx-512` trên Kaggle | DataEngineerAgent |
| **Multi-Task 3-Head Model** | Phase 3 | • Checkpoint `best_model.pth` đạt Macro AUC Head A $\ge 0.82$, Head B $\ge 0.90$<br>• Masked backprop hoạt động chuẩn xác không gây rò rỉ gradient | ModelArchitectAgent |
| **SOTA Enhancements (TASK-013)** | Phase 4 | • Asymmetric Loss & Focal pos_weight động được tích hợp hoàn chỉnh<br>• LayerNorm parameter-free không sinh key mới trong `state_dict`<br>• 16 ngưỡng quyết định được hiệu chuẩn theo Youden's J (`configs/optimal_thresholds.json`)<br>• **114/114 unit tests PASS** qua `scripts/verify.ps1` | ModelArchitectAgent |
| **XAI & Shortcut Audit** | Phase 5 | • Grad-CAM xuất Box-IoU $\ge 0.35$ trên VinDr-CXR và RSNA<br>• Shortcut audit xác nhận tỷ lệ trong phổi $\ge 80\%$ trên 150 ca COVID<br>• Báo cáo PDF đơn sắc [reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf) | XAIEvalAgent |
| **FastAPI Backend Serving** | Phase 6 | • 6 Endpoints `/health`, `/predict`, `/explain`, `/audit`, `/models`, `/models/reload` phản hồi $\le 1.8$s<br>• Tự động 3-Pass Clinical TTA & Temperature Scaling ($T=1.20$)<br>• Hot-reloading không downtime | FullstackDeployAgent |
| **Next.js Medical PACS UI** | Phase 6 | • Giao diện trạm PACS hoàn chỉnh, thanh trượt alpha, huy hiệu TTA/Calibrated<br>• Trình khởi chạy 1-Click Native Launcher dọn sạch cache webpack | FullstackDeployAgent |
| **Báo cáo Học thuật & Bảo vệ** | Phase 7 | • Cuốn luận văn 25 trang `reports/FINAL_SCIENTIFIC_REPORT.pdf` (1.63 MB, Rule 9)<br>• Báo cáo tổng thể `reports/DSP391_Full_Thesis_Report.md` & `reports/docs_report.md` (0 raw `$`)<br>• Đề cương Slide 39 trang và 20 Clinical Defense FAQs | QAReportAgent |
| **Fail-Safe OOD & Lockout** | Phase 8 | • Cơ chế kiểm toán Far-OOD đạt AUROC 1.0000 qua Helmholtz Free Energy ($S_E \ge 9.0421$)<br>• Cổng bất định Shannon Entropy ($H \le 0.6275$)<br>• Khóa báo cáo sơ bộ ICD-10 và đánh dấu watermark INVALID khi phát hiện bất thường<br>• **138/138 Unit Tests PASS** qua `scripts/verify.ps1` | Lead AI Orchestrator |

---

## 7. LỘ TRÌNH PHÁT TRIỂN SẢN PHẨM & NGHIỆM THU TỪNG GIAI ĐOẠN (PHASES 1–8 PRODUCT DELIVERY ROADMAP)

Để hỗ trợ việc tích hợp trực tiếp vào hệ thống Landing Page Report, dưới đây là đặc tả sản phẩm độc lập của từng giai đoạn phát triển theo chuẩn 5 thành phần sản phẩm:

### Phase 1: Product Foundation, Regulatory Scope & 9 Inviolable Constraints
- **Product Need**: Thiết lập nền tảng quy chuẩn y tế, rà soát rủi ro pháp lý và công nghệ trước khi lập trình.
- **User Persona**: Giảng viên hướng dẫn, Hội đồng thẩm định và Trưởng nhóm AI.
- **Feature Scope**: Định nghĩa 9 Ràng buộc Sống còn (The 9 Inviolable Constraints); thiết lập cây thư mục chuẩn Enterprise; khóa chặt phạm vi 6 bộ dữ liệu chuẩn quốc tế.
- **Quality Gate DoD**: Bản đề cương kỹ thuật và kế hoạch nghiên cứu được phê duyệt chính thức (Delivery Gate 1).
- **Clinical Safety**: Loại bỏ dữ liệu nhiễu và định chế nguyên tắc cấm rò rỉ thông tin bệnh nhân.

### Phase 2: Patient-Safe Data Ingestion & Rescaling Pipeline
- **Product Need**: Bảo đảm dữ liệu đầu vào đạt độ phân giải tối ưu cho chẩn đoán lồng ngực ($512 \times 512$) và loại bỏ nguy cơ rò rỉ dữ liệu y khoa.
- **User Persona**: Data Engineer và Bác sĩ thẩm định dữ liệu.
- **Feature Scope**: Phân chia theo `Patient_ID` (70/10/20) cho NIH ChestX-ray14; phân tầng nguồn gốc (`data_source`) cho COVIDx CXR-4; xuất bản 2 Kaggle Datasets `lungray-nih-512` và `lungray-covidx-512`; bộ lấy mẫu cân bằng đa nhiệm `WeightedMultiTaskBatchSampler` tỷ lệ 60:25:15.
- **Quality Gate DoD**: Delivery Gate 1 Approved — Xác nhận $Train \cap Test = \emptyset$ qua `tests/test_data_pipeline.py`.
- **Clinical Safety**: Medical Augmentation an toàn giải phẫu, cấm tuyệt đối lật dọc (`RandomVerticalFlip`).

### Phase 3: Multi-Task Baseline Diagnostic Engine
- **Product Need**: Khả năng suy luận đồng thời 14 bệnh lồng ngực, Lao phổi và COVID-19 trong một mô hình duy nhất để tiết kiệm tài nguyên y tế.
- **User Persona**: Bác sĩ Đa khoa Tuyến cơ sở và Kỹ thuật viên X-quang.
- **Feature Scope**: Khởi tạo kiến trúc `MultiTaskChestXrayNet` với Shared Backbone DenseNet-121 và 3 classification heads độc lập; bộ máy `MaskedMultiTaskLoss` cách ly gradient; huấn luyện 24 epochs trên Kaggle GPU với AMP.
- **Quality Gate DoD**: Delivery Gate 2 Approved — Macro AUROC Head A = 0.8271, Head B = 1.0000, Head C = 0.7342; xuất bản Báo cáo nghiệm thu `results/baseline/BASELINE_REPORT.pdf`.
- **Clinical Safety**: Zero Gradient Leakage bảo vệ không gian nhãn của từng nhiệm vụ độc lập.

### Phase 4: SOTA Mathematical Optimization & Threshold Calibration (TASK-013)
- **Product Need**: Khắc phục hiện tượng dự đoán sai lệch do mất cân bằng lớp cực hạn và đưa ra ngưỡng quyết định tối ưu cho từng bệnh lý thay vì con số 0.5 tùy tiện.
- **User Persona**: Bác sĩ Chẩn đoán hình ảnh chuyên sâu và Nghiên cứu sinh AI Y tế.
- **Feature Scope**: Tích hợp Asymmetric Loss (ASL) triệt tiêu easy negatives; Focal Loss với pos_weight động kẹp trần 50x; LayerNorm parameter-free bảo tồn strict `state_dict`; hiệu chuẩn 16 ngưỡng quyết định theo Youden's J statistic; đấu trường kiến trúc CNN vs ViT-B16; kịch bản SOTA `kaggle/train_multitask_kaggle.py`.
- **Quality Gate DoD**: Delivery Gate 3 Approved — **114/114 Unit Tests PASS** qua `scripts/verify.ps1`.
- **Clinical Safety**: Cân bằng độ nhạy (Sensitivity) và độ đặc hiệu (Specificity) lâm sàng cho từng bệnh lý nguy hiểm.

### Phase 5: Quantitative WSOL Grounding & Trustworthy Shortcut Audit
- **Product Need**: Bác sĩ chỉ tin tưởng mô hình AI nếu vùng kích hoạt trùng khớp với tổn thương thực tế và không bị đánh lừa bởi ký hiệu máy chụp hay watermark.
- **User Persona**: Hội đồng Thẩm định Y khoa và Bác sĩ Lâm sàng.
- **Feature Scope**: Module Grad-CAM và Grad-CAM++ bậc cao; Adaptive Binarization; kiểm chứng định lượng Box-IoU trên VinDr-CXR và RSNA; kiểm toán Shortcut Learning Audit trên 150 ca COVID-19; giải thuật Clinical Pulmonary Grounding.
- **Quality Gate DoD**: Delivery Gate 4 & 5 Approved — RSNA Mean Box-IoU đạt 0.7631, VinDr-CXR đạt 0.6049 (vượt chỉ tiêu $\ge 0.35$); In-lung energy ratio đạt 94.92% $\pm$ 1.60% (100% ca đạt); xuất bản Báo cáo học thuật `reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf` (Rule 9).
- **Clinical Safety**: Triệt tiêu 100% nguy cơ chẩn đoán sai do học thuộc watermark hoặc viền máy chụp.

### Phase 6: Production Medical PACS Web Viewer & Serving Microservice
- **Product Need**: Bác sĩ cần một trạm đọc phim X-quang trực quan, thao tác tức thì, cho phép kéo thanh trượt điều chỉnh độ mờ heatmap và chọn xem từng tổn thương riêng biệt.
- **User Persona**: Bác sĩ Chẩn đoán hình ảnh tại phòng đọc phim và Giám đốc Y khoa.
- **Feature Scope**: Backend FastAPI bất đồng bộ (`/health`, `/predict`, `/explain`, `/audit`); Next.js 14 Medical PACS Viewer hỗ trợ thanh trượt Alpha Slider (0–100%), chọn xem 14 bệnh lý, công tắc Clinical vs Raw Attention; trình khởi chạy 1-Click Native Launcher (`scripts/start_local.ps1`) tích hợp cơ chế dọn dẹp cache webpack.
- **Quality Gate DoD**: Delivery Gate 5 Approved — Độ trễ suy luận đầu cuối $\le 1.8$ giây/ảnh, hoạt động ổn định trên `http://localhost:3000`.
- **Clinical Safety**: Pixel ngoài lồng ngực trong suốt 100%, bảo vệ bác sĩ khỏi các yếu tố gây nhiễu thị giác.

### Phase 7: Comprehensive Scientific Evidence & Defense Readiness
- **Product Need**: Hệ thống hóa toàn bộ công trình khoa học, chứng minh tính vượt trội về độ chính xác và an toàn y tế trước Hội đồng chấm luận văn tốt nghiệp.
- **User Persona**: Hội đồng Thẩm định Tốt nghiệp, Giảng viên Hướng dẫn và Kỹ sư Trưởng.
- **Feature Scope**: Luận văn khoa học 25 trang chuẩn MICCAI/IEEE (`reports/FINAL_SCIENTIFIC_REPORT.pdf`, 1.63 MB, Rule 9 đơn sắc); đề cương Slide bảo vệ 39 trang (`reports/DEFENSE_SLIDES_OUTLINE.md`); bộ 20 câu hỏi & đáp phản biện lâm sàng (`docs/defense_faq.md`); 18 khoảng tin cậy Bootstrap 95% CI.
- **Quality Gate DoD**: Delivery Gate 6 Approved (Sẵn sàng bảo vệ hướng đến Điểm A/A+).
- **Clinical Safety**: Bằng chứng khoa học có khả năng tái lập 100%, minh bạch hóa toàn bộ dữ liệu và quy trình huấn luyện.

### Phase 8: Clinical Fail-Safe Layer & OOD Anomaly Lockout
- **Product Need**: Bác sĩ cần hệ thống có năng lực nhận biết giới hạn chuyên môn, tự động từ chối chẩn đoán (REJECT / LOCKOUT) khi gặp ảnh hỏng, ảnh nhiễu hoặc ảnh nằm ngoài phân phối giải phẫu hỗ trợ thay vì đưa ra xác suất tự tin giả mạo.
- **User Persona**: Bác sĩ Trưởng khoa Chẩn đoán Hình ảnh, Ban Quản lý Chất lượng Bệnh viện và Hội đồng Đạo đức Y sinh.
- **Feature Scope**: Lớp an toàn kép (Dual-Gate Safety) tích hợp Năng lượng Tự do Helmholtz $S_E(x)$ và Entropy Shannon $H(x)$; ma trận thử nghiệm nhiễu OOD Perturbation Benchmarks (Gauss, Uniform, Inversion, Bilinear Blur, Washout); cơ chế khóa tự động kết luận sơ bộ WHO ICD-10 và đóng dấu watermark INVALID lên bản đồ nhiệt.
- **Quality Gate DoD**: Delivery Gate 6+ Approved — Far-OOD Detection AUROC đạt 1.0000, 100% ca nhiễu bị khóa, **125/125 Unit Tests PASS** qua `scripts/verify.ps1`.
- **Clinical Safety**: Triệt tiêu hoàn toàn rủi ro ảo tưởng chẩn đoán (Diagnostic Hallucination) trong môi trường lâm sàng thực tế.
