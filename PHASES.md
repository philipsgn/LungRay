# 📑 WORK BREAKDOWN STRUCTURE & PHASE EXECUTION (PHASES.md)
## Nền tảng LungRay: Chi Tiết Hóa Từng Giai Đoạn, Phân Rã Công Việc & Tiêu Chí Nghiệm Thu (16 Tuần)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Nền tảng** | **LungRay** (CXR Multi-Task CADx + WSOL Grounding Engine) |
| **Cấu trúc** | 7 Phases — 32 Sub-tasks cụ thể |
| **Tiêu chuẩn** | Senior AI Engineer (10+ YOE) |
| **Quy chuẩn kiểm thử** | Tự động hóa qua PyTest, Script CLI & Metric Thresholds |

---

## 🧭 BẢN ĐỒ TỔNG THỂ CÁC GIAI ĐOẠN

```
[Phase 1: Setup & Foundations]  ──► [Phase 2: Data Pipeline & Split] ──► [Phase 3: Multi-Task Baseline]
                                                                                   │
[Phase 6: Fullstack Web Demo]   ◄── [Phase 5: XAI IoU & Shortcut Audit] ◄── [Phase 4: SOTA Enhancement]
          │
[Phase 7: Báo cáo & Bảo vệ]
```

---

## 📌 PHASE 1: RESEARCH, ARCHITECTURE & WORKSPACE SETUP (TUẦN 1–2) — [x] COMPLETED
> **Mục tiêu**: Nghiên cứu lý thuyết nền tảng, hoàn thiện tài liệu đặc tả kỹ thuật, thiết lập môi trường lập trình chuẩn hóa và repository Git.

### [x] Task 1.1: Khảo sát tài liệu & Nghiên cứu 5 bài báo nền tảng (COMPLETED)
- **Mô tả**: Đọc sâu và tổng hợp cơ sở lý thuyết từ các công trình: ChestX-ray14 (Wang et al.), CheXNet (Rajpurkar et al.), VinDr-CXR (Nguyen et al.), Grad-CAM (Selvaraju et al.), Shortcut Learning in COVID-19 (DeGrave et al., 2021).
- **Deliverable**: Báo cáo tóm tắt lý thuyết `docs/literature_review.md` trích xuất thông số benchmark gốc.
- **DoD**: Trích xuất được các bảng điểm AUC đối chuẩn cho 14 bệnh và cơ chế shortcut learning của dữ liệu X-quang đa nguồn.
- **Agent**: `ModelArchitectAgent`

### [x] Task 1.2: Thiết lập môi trường phát triển & Quản lý thư viện (COMPLETED)
- **Mô tả**: Thiết lập môi trường Python 3.10 trên máy cục bộ với PyTorch 2.0+, CUDA toolkit, albumentations, timm, pytorch-grad-cam, OpenCV.
- **Deliverable**: File cấu hình `requirements.txt`, `environment.yml`, `pyproject.toml`.
- **DoD**: Lệnh `python -c "import torch; print(torch.cuda.is_available())"` trả về `True` (hoặc cấu hình CPU fallback ổn định).
- **Agent**: `DataEngineerAgent`

### [x] Task 1.3: Cấu trúc hóa Repository mã nguồn chuẩn Enterprise (COMPLETED)
- **Mô tả**: Tạo cây thư mục dự án chuẩn hóa module: `src/data`, `src/models`, `src/explainability`, `src/utils`, `tests/`, `configs/`, `notebooks/`.
- **Deliverable**: Cây thư mục hoàn chỉnh, file `README.md` hướng dẫn cài đặt ban đầu.
- **DoD**: Cài đặt được package ở chế độ editable `pip install -e .` không lỗi cú pháp.
- **Agent**: `DataEngineerAgent`

### [x] Task 1.4: Hoàn thiện hồ sơ thiết kế kỹ thuật & Đề cương (COMPLETED)
- **Mô tả**: Đồng bộ các file đặc tả `PRD.md`, `TECH_ARCHITECTURE.md`, `PLAN.md` và `PROPOSAL.md`.
- **Deliverable**: Bộ tài liệu hoàn chỉnh được kiểm duyệt nội dung.
- **DoD**: Giảng viên / Ban thẩm định phê duyệt đề cương chi tiết (Delivery Gate 1).
- **Agent**: `QAReportAgent`

---

## 📌 PHASE 2: DATA INGESTION, EDA & INTEGRITY SPLITS (TUẦN 3–4) — [x] COMPLETED
> **Mục tiêu**: Tải và liên kết 6 nguồn dữ liệu trên Kaggle, thực hiện EDA sâu sắc, xây dựng pipeline chống Data Leakage, chuẩn hóa $512 \times 512$ Cloud Rescaling và xuất bản Kaggle Datasets chính thức.

### [x] Task 2.1: Mount & Khai phá dữ liệu (EDA) trên Kaggle & Kiểm Toán Chất Lượng Độc Lập (COMPLETED)
- **Mô tả**: Viết notebook kiểm toán độc lập `notebooks/00_kaggle_dataset_audit_and_profiling.ipynb` chạy trên Kaggle tích hợp module **Deep Hierarchical Anatomizer** tự động truy quét phân cấp sâu để bóc tách độc lập 3 bộ dữ liệu: liệt kê chi tiết 12 chunk của NIH (`images_001` .. `images_012`), đếm số ảnh từng class của COVID-19 đồng thời **loại trừ tuyệt đối thư mục `masks/`** để chống nạp nhầm ảnh mask nhị phân, và đếm 2 class của TB (`Normal`, `Tuberculosis`). Kiểm toán 4 trụ cột: độ phân giải (min/max/median/% <512px), độ toàn vẹn tệp (ảnh hỏng/lỗi đọc), cấu trúc metadata và bảng phán quyết lâm sàng tự động (ACCEPT / WARNING / REPLACE) kèm đề xuất dataset thay thế nếu không đạt. Đồng thời duy trì notebook khảo sát `notebooks/01_exploratory_data_analysis.ipynb`.
- **Deliverable**: `notebooks/00_kaggle_dataset_audit_and_profiling.ipynb`, `notebooks/01_exploratory_data_analysis.ipynb`, biểu đồ phân bố 14 nhãn `results/eda_label_distributions.png`.
- **DoD**: Bóc tách chính xác 100% các subfolders và số lượng ảnh từng class trên Kaggle, loại trừ 100% thư mục masks, kiểm toán độ phân giải thực tế của các bộ dữ liệu.
- **Agent**: `DataEngineerAgent`

### [x] Task 2.2: Trích xuất Metadata nguồn gốc cho COVID-19 / COVIDx CXR-4 (COMPLETED)
- **Mô tả**: Trích xuất cột nguồn ảnh (`data_source`) và `patient_id` trong metadata của bộ COVID-19 / COVIDx để phục vụ phân tầng và chống Shortcut Learning.
- **Deliverable**: File metadata đã làm sạch `data/processed/covid19_metadata_cleaned.csv` và `dataset/splits/covid_splits.csv`.
- **DoD**: 100% mẫu trong dataset COVID có gán nhãn nguồn ảnh gốc chính xác.
- **Agent**: `DataEngineerAgent`

### [x] Task 2.3: Hiện thực thuật toán Phân chia dữ liệu (Data Splits Engine) (COMPLETED)
- **Mô tả**:
  - Viết module `src/data/splits.py`:
    - `split_nih_by_patient_id(df, ratios=[0.7, 0.1, 0.2], seed=42)`
    - `split_covid_by_source_stratified(df, ratios=[0.7, 0.1, 0.2], seed=42)`
    - `split_tb_stratified(df, ratios=[0.7, 0.1, 0.2], seed=42)`
- **Deliverable**: 3 file chỉ mục: `data/splits/patient_splits.csv`, `data/splits/covid_splits.csv`, `data/splits/tb_splits.csv` (đồng thời lưu trong `dataset/splits/`).
- **DoD**: Chạy `pytest tests/test_data_leakage.py` PASS 100% ($Train \cap Test = \emptyset$ về ID bệnh nhân).
- **Agent**: `DataEngineerAgent`

### [x] Task 2.4: Xây dựng PyTorch Dataset & Transforms Y tế an toàn (COMPLETED)
- **Mô tả**: Viết `src/data/dataset.py` và `src/data/transforms.py`. Tăng cường dữ liệu an toàn (xoay $\pm 10^\circ$, lật ngang; tuyệt đối không lật dọc).
- **Deliverable**: Module `ChestXrayDataset` nạp ảnh, resize chuẩn hóa $512 \times 512$, chuẩn hóa ImageNet, hỗ trợ Dual-mode pre-resized 512.
- **DoD**: Unit test nạp thử 1 batch ảnh từ cả 3 nguồn dữ liệu không phát sinh ngoại lệ.
- **Agent**: `DataEngineerAgent`

### [x] Task 2.5: Hiện thực Weighted & Balanced Multi-Task Batch Sampler (COMPLETED)
- **Mô tả**: Viết `src/data/sampler.py` để phân phối cố định 60% NIH, 25% COVID, 15% TB trong từng mini-batch.
- **Deliverable**: Lớp `WeightedMultiTaskBatchSampler`.
- **DoD**: Chạy test kiểm tra 10 batches liên tiếp, tỷ lệ mẫu giữa các nguồn đạt độ lệch chuẩn $\le 5\%$.
- **Agent**: `DataEngineerAgent`

### [x] Task 2.6: Hệ Sinh Thái Rescaling Engine & Xuất Bản 2 Bộ Kaggle Datasets Chuẩn 512x512 (COMPLETED)
- **Mô tả**: Xây dựng kịch bản và notebook Cloud Rescaling chạy 100% trên Kaggle:
  - `notebooks/00_rescale_nih_512.ipynb`: Rescale 112,120 ảnh NIH bằng `cv2.INTER_AREA` đa tiến trình, nhúng `patient_splits.csv`, xuất bản thành công Dataset Kaggle **`lungray-nih-512`** (~13 GB).
  - `notebooks/00_rescale_covidx_512.ipynb`: Medical Letterboxing bảo tồn tỷ lệ giải phẫu lồng ngực cho 76.3k ảnh COVIDx CXR-4 (`train.txt`, `test.txt`), xuất bản thành công Dataset Kaggle **`lungray-covidx-512`** (8.3 GB, 76.3k files).
- **Deliverable**: 2 Kaggle Datasets chính thức `lungray-nih-512` và `lungray-covidx-512`, các notebook kiểm toán `00a_nih_audit_baseline.ipynb`, `00b_covid_audit_baseline.ipynb`, `00c_tb_audit_baseline.ipynb`.
- **DoD**: Tạo thành công 2 Kaggle Datasets trên hạ tầng Kaggle Cloud với Zero Local Byte, cấu trúc thư mục sạch và khớp hoàn hảo với pipeline huấn luyện.
- **Agent**: `DataEngineerAgent` & `ModelArchitectAgent`

---

## 📌 PHASE 3: MULTI-TASK BASELINE MODEL TRAINING (TUẦN 5–6) — [x] COMPLETED
> **Mục tiêu**: Xây dựng kiến trúc Shared Backbone + 3 Heads, hàm mất mát Masked Multi-Task Loss cô lập gradient, bộ máy MultiTaskTrainer hỗ trợ Mixed Precision và script huấn luyện Kaggle GPU chuẩn hóa.

### [x] Task 3.1: Xây dựng Kiến trúc Multi-Task 3-Head Model (COMPLETED)
- **Mô tả**: Viết `src/models/multi_task_net.py` nạp backbone DenseNet-121 / ResNet-50 / ViT từ `src/models/backbones.py`, trích xuất đặc trưng chung (1024-dim cho DenseNet-121), tích hợp Dropout (p=0.2) và 3 classification heads độc lập:
  - Head A: Linear(1024, 14) cho 14 bệnh lồng ngực NIH
  - Head B: Linear(1024, 1) cho sàng lọc Lao phổi TB
  - Head C: Linear(1024, 1) cho sàng lọc nhị phân COVIDx CXR-4 (COVID-19 Positive vs Normal / Negative)
  - Chuẩn hóa đầu ra: `forward()` trả về raw logits dictionary; `predict()` trả về xác suất Sigmoid; hook trích xuất feature map cho Grad-CAM.
- **Deliverable**: Module `src/models/multi_task_net.py`.
- **DoD**: Forward pass thành công với dummy tensor $(B, 3, 512, 512)$, trả về đúng 3 logits tensors.
- **Agent**: `ModelArchitectAgent`

### [x] Task 3.2: Hiện thực Masked Multi-Task Loss Engine (COMPLETED)
- **Mô tả**: Viết `src/models/losses.py` thực hiện tính hàm mất mát chọn lọc (Masked Loss) theo nguồn gốc dữ liệu của từng mẫu (`task_id`):
  - Head A: BCEWithLogitsLoss tích hợp `pos_weight` cho 14 bệnh lồng ngực.
  - Head B: BCEWithLogitsLoss cho sàng lọc Lao phổi.
  - Head C: BCEWithLogitsLoss cho sàng lọc COVIDx CXR-4.
  - Bảo đảm Zero Gradient Leakage: mẫu của task này tuyệt đối không tạo gradient lên trọng số của head khác.
- **Deliverable**: Lớp `MaskedMultiTaskLoss` và `FocalLoss` trong `src/models/losses.py`.
- **DoD**: Unit test chứng minh mẫu từ NIH chỉ tính gradient cho Head A và shared backbone; hoàn toàn không tác động gradient lên Head B và Head C.
- **Agent**: `ModelArchitectAgent`

### [x] Task 3.3: Viết Pipeline Huấn Luyện & Logging (MultiTaskTrainer Engine) (COMPLETED)
- **Mô tả**: Viết `src/models/trainer.py` hỗ trợ Mixed Precision (`torch.cuda.amp`), Cosine Annealing LR Scheduler, Early Stopping, tính toán riêng biệt Macro AUROC cho cả 3 heads và lưu checkpoint theo tiêu chí điểm kết hợp $S_{\text{val}} = 0.40 \cdot \text{AUC}_A + 0.30 \cdot \text{AUC}_B + 0.30 \cdot \text{AUC}_C$.
- **Deliverable**: Lớp `MultiTaskTrainer` trong `src/models/trainer.py`.
- **DoD**: Tự động lưu atomic checkpoints (`last_model.pth`, `checkpoint_baseline_multitask.pth`), hỗ trợ auto-resume và lưu `training_history.csv` mỗi epoch.
- **Agent**: `ModelArchitectAgent`

### [x] Task 3.4: Triển Khai Kịch Bản & Huấn Luyện Thực Nghiệm Kaggle GPU (COMPLETED)
- **Mô tả**: Huấn luyện thành công 24 epochs trên Kaggle Tesla T4 GPU với `kaggle/train_kaggle.py` và `notebooks/02_multitask_baseline_training.ipynb`:
  - **Head A (NIH 14 bệnh)**: Macro AUROC đạt **0.8271** (Chỉ tiêu $\ge 0.80$) $\to$ **ĐẠT (PASS)**.
  - **Head B (Lao phổi TB)**: AUROC đạt **1.0000** (Chỉ tiêu $\ge 0.90$) $\to$ **XUẤT SẮC (PASS)**.
  - **Head C (COVIDx CXR-4)**: Test AUROC đạt **0.7342** $\to$ **ĐẠT CÓ ĐIỀU KIỆN (CONDITIONAL PASS)** kèm giải phẫu phân phối và lộ trình can thiệp Phase 4.
  - Xuất bản Báo cáo học thuật [results/baseline/BASELINE_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/results/baseline/BASELINE_REPORT.pdf) chuẩn y khoa đơn sắc.
- **Deliverable**: Checkpoints `checkpoint_baseline_multitask.pth`, `last_model.pth`, `results/baseline/BASELINE_REPORT.pdf`.
- **DoD**: Nghiệm thu đóng Delivery Gate 2 thành công.
- **Agent**: `ModelArchitectAgent` & `QAReportAgent`

---

## 📌 PHASE 4: MODEL ENHANCEMENT & SOTA COMPARISON (TUẦN 7–9) — [▶] IN PROGRESS
> **Mục tiêu**: Xử lý mất cân bằng lớp cực đoan bằng Focal Loss, thử nghiệm Vision Transformer, tối ưu ngưỡng quyết định $\tau_c$ theo từng lớp.

### Task 4.1: Triển khai Focal Loss & Positive Class Weighting
- **Mô tả**: Tích hợp Focal Loss vào Head A: $\mathcal{L}_{\text{Focal}} = -\alpha_t (1 - p_t)^\gamma \log(p_t)$ với $\gamma \in [2.0, 3.0]$ và $\alpha = 0.25$.
- **Deliverable**: Module `FocalLoss` trong `src/models/losses.py`.
- **DoD**: Tăng AUC của nhóm bệnh hiếm (Hernia, Fibrosis) lên tối thiểu $+0.04$ so với BCE thông thường.
- **Agent**: `ModelArchitectAgent`

### Task 4.2: Tinh chỉnh Mô hình theo Chiến lược 2 Giai đoạn (Two-Stage Fine-tuning)
- **Mô tả**: Giai đoạn 1: Đóng băng backbone, train 3 heads với $lr = 10^{-3}$; Giai đoạn 2: Mở khóa toàn bộ mạng, fine-tune với $lr = 10^{-5}$.
- **Deliverable**: Checkpoint tối ưu `checkpoints/best_densenet_focal.pth`.
- **DoD**: Macro AUC trên NIH Test Set đạt $\ge 0.82$.
- **Agent**: `ModelArchitectAgent`

### Task 4.3: Thử nghiệm So sánh Vision Transformer (ViT / Swin-T)
- **Mô tả**: Xây dựng biến thể model sử dụng `timm.create_model('vit_base_patch16_224')` hoặc `vit_base_patch16_384`. Khi nạp ảnh độ phân giải $512 \times 512$, áp dụng kỹ thuật nội suy 2D bicubic positional embedding (`resample_abs_pos_embed` từ `timm.layers`) để tương thích kích thước patch grid $32 \times 32$. Huấn luyện đối chứng với DenseNet-121.
- **Deliverable**: Checkpoint `checkpoints/vit_comparison.pth`, bảng so sánh `results/model_comparison_table.csv`.
- **DoD**: Hoàn thành bảng đối chiếu khoa học về tốc độ suy luận, mức tiêu thụ VRAM và chỉ số AUC-ROC giữa CNN và ViT.
- **Agent**: `ModelArchitectAgent`

### Task 4.4: Tối ưu hóa Ngưỡng Quyết định Đa lớp ($\tau_c$ Optimization)
- **Mô tả**: Viết script `src/utils/threshold_tuning.py` tính toán ngưỡng tối ưu cho 14 lớp NIH dựa trên chỉ số Youden's J statistic ($J = \text{TPR} - \text{FPR}$) trên tập Validation.
- **Deliverable**: File thông số ngưỡng `configs/optimal_thresholds.json`.
- **DoD**: Macro F1-Score trên tập Test đạt $\ge 0.45$ (vượt xa ngưỡng mặc định cứng 0.5 chỉ đạt ~0.35).
- **Agent**: `ModelArchitectAgent`

### Task 4.5: Tính toán Khoảng Tin Cậy Bootstrap (Bootstrap Confidence Intervals)
- **Mô tả**: Chạy kiểm định Bootstrap 1.000 lần trên tập Test để tính khoảng tin cậy 95% CI cho các lớp hiếm (Hernia, Fibrosis).
- **Deliverable**: Báo cáo thống kê `results/bootstrap_confidence_intervals.csv`.
- **DoD**: Có số liệu CI khoa học sẵn sàng phục vụ viết báo cáo đồ án.
- **Agent**: `QAReportAgent`

---

## 📌 PHASE 5: EXPLAINABILITY (XAI), WSOL GROUNDING & SHORTCUT AUDIT (TUẦN 10–11)
> **Mục tiêu**: Xây dựng module Grad-CAM/Grad-CAM++, đo đạc định lượng chỉ số IoU trên VinDr-CXR & RSNA, và thực hiện kiểm toán Shortcut Learning trên COVID-19.

### [x] Task 5.1: Xây dựng Module XAI Grad-CAM & Grad-CAM++ (COMPLETED)
- **Mô tả**: Viết `src/explainability/grad_cam.py` trích xuất gradient activation map từ tầng tích chập cuối cùng (`denseblock4`/`norm5`), hỗ trợ:
  - Cả 2 giải thuật: Grad-CAM cổ điển và Grad-CAM++ bậc cao (positive higher-order gradients kèm fallback ổn định).
  - Tự động lấy target layer qua `model.get_last_conv_layer()`.
  - Quản lý lifecycle hooks chặt chẽ (`remove_hooks()`, context manager).
  - Hỗ trợ đa nhiệm cho cả 3 heads (`head_a`, `head_b`, `head_c`).
  - Hàm trộn nhiệt `overlay_heatmap` RGB chuẩn hóa $[0, 255]$ uint8.
- **Deliverable**: Module `src/explainability/grad_cam.py`, lớp `GradCAMExplainer`.
- **DoD**: Tự động sinh heatmap chuẩn hóa $[0, 1]$ cho bất kỳ head và lớp chỉ định.
- **Agent**: `XAIEvalAgent`

### Task 5.2: Hiện thực Thuật toán Binarize Thích Nghi & Đo đạc IoU
- **Mô tả**: Viết `src/explainability/metrics.py` tạo mặt nạ nhị phân $\hat{B}_c = \mathbb{I}(M_c \ge \alpha \cdot \max(M_c))$ và tính IoU so với Ground-truth Bounding Box từ VinDr-CXR và RSNA.
- **Deliverable**: Script `scripts/evaluate_iou.py`.
- **DoD**: Đo đạc trên 8 lớp có BBox của VinDr-CXR và RSNA Pneumonia, đạt **Mean IoU $\ge 0.35$** trên các ca True Positive.
- **Agent**: `XAIEvalAgent`

### [x] Task 5.3: Thực hiện Kiểm toán & Khắc phục Shortcut Learning Audit cho Head C (COVID-19) (COMPLETED & VERIFIED)
- **Mô tả**:
  - Viết `src/explainability/shortcut_audit.py`:
    - Lớp `LungSegmenter`: Phân đoạn phế trường phổi $P_{\text{lung}}$ offline (Otsu thresholding trên lồng ngực, morphological closing/opening, connected component filtering, fill holes và prior fallback).
    - Lớp `ShortcutAuditEngine`: Tính toán `in_lung_energy_ratio = E(Lung) / E(Total)` với đầy đủ xử lý biên (mask rỗng, heatmap zero, shape mismatch, NaN/Inf).
    - Phương thức `audit_sample()` trả về schema chuẩn `{in_lung_ratio, heatmap, lung_mask, pass_80_percent}`.
  - Thực thi kiểm toán định lượng 3 nhánh trên toàn bộ 150 ca bệnh COVID-19 tập kiểm thử COVIDx CXR-4:
    - *Nhánh 1 (Unmasked Baseline)*: Đạt 38.49% $\pm$ 10.45%, 0% pass rate (0/150 ca đạt, phát hiện shortcut learning nặng nề trên viền ngoài/watermark).
    - *Nhánh 2 (Input Masking Only Ablation)*: Đạt 38.14% $\pm$ 11.82% (chứng minh rò rỉ trường cảm thụ hiệu dụng qua phép nội suy).
    - *Nhánh 3 (Clinical Pulmonary Grounding)*: Đạt **94.92% $\pm$ 1.60%**, **100.0% pass rate (150/150 mẫu)**, mức cải thiện tuyệt đối **+56.43% $\pm$ 9.28%**, kiểm định Wilcoxon $W = 11325.0, p = 1.15 \times 10^{-26}$.
  - Biên soạn Báo cáo học thuật và biên dịch PDF đơn sắc:
    - [reports/SHORTCUT_LEARNING_AUDIT_REPORT.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/SHORTCUT_LEARNING_AUDIT_REPORT.md)
    - [reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf) tuân thủ 100% Rule 9 (không icon/emoji, phông Times New Roman, bảng Booktabs 3 đường kẻ).
- **Deliverable**:
  - `src/explainability/shortcut_audit.py`, `scripts/run_shortcut_audit.py`, `scripts/run_shortcut_mitigation_audit.py`, `scripts/generate_audit_pdf.py`.
  - `results/shortcut_audit_comparison.csv`, `results/shortcut_audit_comparison.png`.
  - `reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf`.
- **DoD**: Tỷ lệ kích hoạt trong phổi vượt xa chỉ tiêu $\ge 80\%$, triệt tiêu 100% shortcut ngoài viền ảnh, hoàn tất nghiệm thu Gate 5.
- **Agent**: `XAIEvalAgent` & `QAReportAgent`

### Task 5.4: Kiểm định Tổng quát hóa Ngoại vi (External Generalization Test)
- **Mô tả**: Chạy đánh giá Head A trên tập CheXpert-small-v1 (bệnh viện khác NIH) để đo lường mức độ suy giảm AUC do domain shift.
- **Deliverable**: Báo cáo tổng quát hóa `results/chexpert_generalization_results.csv`.
- **DoD**: Độ suy giảm AUC không vượt quá $0.10$ so với trên tập NIH test set.
- **Agent**: `XAIEvalAgent`

---

## 📌 PHASE 6: FULL-STACK MEDICAL PACS WEB DEMO (TUẦN 12–13)
> **Mục tiêu**: Xây dựng hệ thống phần mềm hoàn chỉnh gồm FastAPI REST Backend (Docker) và Next.js Medical PACS Viewer trực quan.

### Task 6.1: Xây dựng FastAPI Microservice Backend
- **Mô tả**: Viết backend phục vụ suy luận `app/backend/main.py`:
  - `POST /api/v1/predict`: Dự đoán 3-Head đồng thời.
  - `POST /api/v1/explain`: Sinh Grad-CAM heatmap và trả về ảnh Base64.
  - `POST /api/v1/audit`: Kiểm toán rủi ro shortcut học thuộc.
- **Deliverable**: Mã nguồn FastAPI backend hoàn chỉnh, file cấu hình CORS và Pydantic schemas.
- **DoD**: Thời gian xử lý toàn diện $\le 1.8$ giây trên máy thử nghiệm.
- **Agent**: `FullstackDeployAgent`

### Task 6.2: Xây dựng Giao diện Next.js Medical PACS Viewer
- **Mô tả**: Xây dựng ứng dụng Next.js tại `app/frontend/`:
  - Tải ảnh kéo thả (DICOM/PNG/JPG).
  - Khung hiển thị ảnh y tế (tương thích Cornerstone.js / HTML5 Canvas).
  - Dashboard thẻ kết quả chẩn đoán 3 Heads với mã màu lâm sàng.
  - Thanh trượt điều chỉnh độ mờ (Alpha Slider) của Heatmap từ 0 đến 100%.
- **Deliverable**: Ứng dụng Next.js hoạt động độc lập tại cổng 3000.
- **DoD**: Tương tác mượt mà, phản hồi chuyển đổi heatmap tức thì khi bác sĩ click vào từng bệnh lý.
- **Agent**: `FullstackDeployAgent`

### Task 6.3: Container hóa Toàn diện với Docker & Docker-Compose
- **Mô tả**: Viết `Dockerfile.backend`, `Dockerfile.frontend` và `docker-compose.yml` để khởi chạy toàn bộ hệ thống bằng 1 lệnh duy nhất.
- **Deliverable**: Cấu hình Docker hoàn chỉnh.
- **DoD**: Khởi chạy thành công qua lệnh `docker-compose up --build`, kiểm thử end-to-end không phát sinh lỗi kết nối.
- **Agent**: `FullstackDeployAgent`

---

## 📌 PHASE 7: THỰC NGHIỆM TỔNG KẾT, BÁO CÁO & BẢO VỆ ĐỒ ÁN (TUẦN 14–16)
> **Mục tiêu**: Tổng hợp số liệu khoa học, hoàn thiện cuốn báo cáo tốt nghiệp 40–50 trang, chuẩn bị slide thuyết trình và bảo vệ xuất sắc trước Hội đồng.

### Task 7.1: Tổng hợp Số liệu & Soạn thảo Cuốn Báo cáo Đồ án
- **Mô tả**: Viết cuốn báo cáo chính thức theo quy chuẩn học thuật (40–50 trang) với đầy đủ 5 chương: Mở đầu, Cơ sở lý thuyết, Phương pháp đề xuất, Kết quả thực nghiệm và Thảo luận kết luận.
- **Deliverable**: Bản in và file PDF `reports/Final_Thesis_Report.pdf`.
- **DoD**: Giảng viên hướng dẫn duyệt thông qua bản thảo cuối cùng.
- **Agent**: `QAReportAgent`

### Task 7.2: Thiết kế Slide Báo cáo & Poster Khoa học Khổ A1
- **Mô tả**: Thiết kế bộ Slide 35–45 trang trực quan, chuyên nghiệp, làm nổi bật điểm sáng tạo: Multi-Task 3-Head, Định lượng hóa IoU, và Kiểm toán Shortcut Audit.
- **Deliverable**: Slide thuyết trình `reports/Defense_Presentation.pptx` và Poster A1 `reports/Poster_Scientific_A1.pdf`.
- **DoD**: Hoàn thành đúng chuẩn kích thước và bố cục đồ án xuất sắc.
- **Agent**: `QAReportAgent`

### Task 7.3: Sản xuất Video Demo Hoạt động Hệ thống
- **Mô tả**: Quay video chất lượng cao (1080p, thời lượng 2–3 phút) ghi hình trọn vẹn quy trình: Tải ảnh $\to$ Nhận kết quả chẩn đoán 3 Heads $\to$ Kéo thanh trượt Grad-CAM $\to$ Kết quả kiểm toán Shortcut.
- **Deliverable**: Video `reports/demo_walkthrough.mp4`.
- **DoD**: Video rõ nét, có phụ đề/thuyết minh minh họa rõ ràng.
- **Agent**: `FullstackDeployAgent`

### Task 7.4: Tổng duyệt Phản biện & Bảo vệ Chính thức (Defense Day)
- **Mô tả**: Tổ chức buổi chạy thử nghiệm (Dry-Run), soạn thảo bộ 20 câu hỏi phản biện lâm sàng và kỹ thuật (đặc biệt về cách xử lý Shortcut Learning và tính IoU), bảo vệ chính thức trước Hội đồng.
- **Deliverable**: Bộ tài liệu câu hỏi phản biện `docs/defense_faq.md`.
- **DoD**: Bảo vệ thành công đồ án, đạt điểm A/A+ ($\ge 85\%$).
- **Agent**: Toàn bộ Multi-Agent Team
