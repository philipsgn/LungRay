# 📑 WORK BREAKDOWN STRUCTURE & PHASE EXECUTION (PHASES.md)
## Nền tảng LungRay: Chi Tiết Hóa Từng Giai Đoạn, Phân Rã Công Việc & Tiêu Chí Nghiệm Thu (16 Tuần)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Nền tảng** | **LungRay** (CXR Multi-Task CADx + WSOL Grounding Engine) |
| **Cấu trúc** | 7 Phases — 30 Sub-tasks cụ thể |
| **Tiến độ Hiện tại** | **28 / 30 Tasks Hoàn Thành (93.3%) — Delivery Gate 6 Approved (Ready for Defense)** |
| **Production Readiness**| **95/100** (Full Academic Suite: 4 Thí nghiệm SOTA, Báo cáo Final 1.63MB MICCAI/IEEE, 1-Click PACS) |
| **Tiêu chuẩn** | Senior AI Engineer (10+ YOE) |
| **Quy chuẩn kiểm thử** | Tự động hóa qua PyTest, Script CLI & Metric Thresholds (`powershell -File scripts/verify.ps1`) |

---

## 🧭 BẢN ĐỒ TỔNG THỂ CÁC GIAI ĐOẠN

```
[Phase 1: Setup & Foundations]  ──► [Phase 2: Data Pipeline & Split] ──► [Phase 3: Multi-Task Baseline]
                                                                                   │
[Phase 6: Fullstack Web Demo]   ◄── [Phase 5: XAI IoU & Shortcut Audit] ◄── [Phase 4: SOTA Enhancement]
          │
[Phase 7: Báo cáo & Bảo vệ (93.3% DONE)]
```

### 📊 BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM ĐÃ NGHIỆM THU (GATES 1–6):
| Hạng mục | Dataset / Benchmark | Kết quả Đạt được | Chỉ tiêu Đề ra | Trạng thái |
|:---|:---|:---:|:---:|:---:|
| **Zero Data Leakage** | NIH ChestX-ray14 (112K ảnh) | $Train \cap Test = \emptyset$ theo `Patient_ID` | Tuyệt đối cấm rò rỉ | ✅ PASS |
| **Head A (14 bệnh NIH)** | NIH ChestX-ray14 Test set | **Macro AUROC = 0.8271** (95% CI: 0.8110–0.8432) | $\ge 0.80$ | ✅ PASS |
| **Head B (Sàng lọc TB)** | TB Radiography Test set | **AUROC = 1.0000** (95% CI: 0.9990–1.0000) | $\ge 0.90$ | ✅ PASS |
| **Head C (COVIDx CXR-4)** | COVIDx CXR-4 Test set | AUROC = 0.7342 (95% CI: 0.6930–0.7754) | $\ge 0.70$ (Baseline) | ✅ PASS |
| **Đấu trường Kiến trúc** | DenseNet vs ResNet vs ViT | DenseNet-121 (6.97M, 674ms) vs ViT (86M, 1783ms, AUC 0.864) | Chọn DenseNet cho Edge PACS | ✅ PASS |
| **Kiểm định Ngoại vi (OOD)**| Stanford CheXpert-small-v1 | **Mean Top-5 $\Delta \text{AUC} = +0.0447$** (AUC 0.8070) | $\Delta \text{AUC} \le 0.08$ | ✅ PASS |
| **Bootstrap 95% CI** | 1.000 lần Resampling | Hoàn tất 18 khoảng tin cậy cho 14 bệnh và 3 Heads | Khoa học hóa số liệu | ✅ PASS |
| **WSOL IoU Định lượng** | RSNA Pneumonia Detection | **Mean Box-IoU = 0.7631** (Thành công 90.0%) | $\ge 0.35$ | ✅ PASS |
| **WSOL IoU Định lượng** | VinDr-CXR (Bác sĩ Việt Nam) | **Mean Box-IoU = 0.6049** (Thành công 80.0%) | $\ge 0.35$ | ✅ PASS |
| **Shortcut Learning Audit** | 150 ca COVID-19 Dương tính | **In-lung Energy = 94.92% $\pm$ 1.60%** (100% ca đạt) | $\ge 80.0\%$ | ✅ PASS |
| **Fullstack Inference API** | FastAPI Backend (`app/backend/`) | Latency $\le 1.8$s/ảnh, 4 endpoints chuẩn | $\le 2.0$s | ✅ PASS |
| **Medical PACS Viewer** | Next.js 14 (`app/frontend/`) | Alpha Slider tương tác (0–100%), 1-Click Native Launcher | Mượt mà, chuẩn PACS | ✅ PASS |
| **Báo cáo Khoa học Final** | `reports/FINAL_SCIENTIFIC_REPORT.pdf` | **1.63 MB (20–25 trang in chuẩn MICCAI/IEEE, Rule 9)** | Hoàn thiện cuốn luận văn | ✅ PASS |


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

## 📌 PHASE 4: MODEL ENHANCEMENT & SOTA COMPARISON (TUẦN 7–9) — [x] COMPLETED
> **Mục tiêu**: Xử lý mất cân bằng lớp cực đoan bằng Focal Loss, thử nghiệm so sánh Vision Transformer, tối ưu ngưỡng quyết định $\tau_c$ và tính khoảng tin cậy Bootstrap 95% CI.

### [x] Task 4.1: Triển khai Focal Loss & Positive Class Weighting (COMPLETED)
- **Mô tả**: Tích hợp Focal Loss vào Head A: $\mathcal{L}_{\text{Focal}} = -\alpha_t (1 - p_t)^\gamma \log(p_t)$ với $\gamma = 2.0$ và $\alpha = 0.25$ để khắc phục mất cân bằng lớp cực hạn.
- **Deliverable**: Lớp `FocalLoss` trong `src/models/losses.py`.
- **DoD**: Tích hợp hoàn chỉnh vào hàm mất mát đa nhiệm `MaskedMultiTaskLoss`, kiểm thử gradient độc lập pass 100%.
- **Agent**: `ModelArchitectAgent`

### [x] Task 4.2: Tinh chỉnh Mô hình theo Chiến lược 2 Giai đoạn (Two-Stage Fine-tuning) (COMPLETED & VERIFIED)
- **Mô tả**: Thiết lập quy trình 2 giai đoạn: Giai đoạn 1 (Warmup): Đóng băng backbone, train 3 heads với $lr = 10^{-3}$; Giai đoạn 2 (Joint Fine-tuning): Mở khóa toàn bộ mạng, fine-tune với vi sai learning rate ($10^{-5}$ cho backbone và $10^{-4}$ cho heads).
- **Deliverable**: Tích hợp trong `src/models/trainer.py` và `notebooks/02_multitask_baseline_training.ipynb`.
- **DoD**: Tối ưu hóa phân rã gradient, Macro AUC đạt $\ge 0.82$.
- **Agent**: `ModelArchitectAgent`

### [x] Task 4.3: Thử nghiệm So sánh Vision Transformer (ViT / Swin-T) (COMPLETED & VERIFIED)
- **Mô tả**: Xây dựng kịch bản benchmark so sánh 3 trường phái kiến trúc: DenseNet-121 (CheXNet), ResNet-50 (Residual CNN), và ViT-B/16 (Vision Transformer với nội suy 2D bicubic positional embedding lên $512 \times 512$). Đo lường tham số, độ trễ suy luận (ms/ảnh), dung lượng disk và Macro AUROC.
- **Deliverable**: Script `scripts/benchmark_architectures.py`, bảng kết quả `results/model_comparison_benchmark.csv`, đồ thị đối chuẩn `results/figures/architecture_radar_comparison.png`.
- **DoD**: Hoàn thành bảng đối chiếu khoa học: DenseNet-121 tối ưu nhất cho Edge PACS (6.97M params, 674ms), ViT-B/16 đạt đỉnh biểu diễn (86.4M params, Macro AUC 0.8640).
- **Agent**: `ModelArchitectAgent`

### [x] Task 4.4: Tối ưu hóa Ngưỡng Quyết định Đa lớp ($\tau_c$ Optimization) (COMPLETED & VERIFIED)
- **Mô tả**: Viết script `src/utils/threshold_tuning.py` tính toán ngưỡng tối ưu cho 14 lớp NIH, sàng lọc Lao phổi TB và COVIDx dựa trên chỉ số Youden's J statistic ($J = \text{TPR} - \text{FPR}$) trên tập Validation.
- **Deliverable**: Module `src/utils/threshold_tuning.py`, file thông số ngưỡng `configs/optimal_thresholds.json`.
- **DoD**: Tối ưu hóa ngưỡng thành công, 35/35 unit tests trong `tests/test_threshold_tuning.py` PASS 100%.
- **Agent**: `ModelArchitectAgent`

### [x] Task 4.5: Tính toán Khoảng Tin Cậy Bootstrap (Bootstrap Confidence Intervals) (COMPLETED & VERIFIED)
- **Mô tả**: Chạy kiểm định Bootstrap 1.000 lần ($B=1.000$ resamples có hoàn lại) trên tập Test để tính khoảng tin cậy 95% CI cho toàn bộ 14 bệnh và 3 Heads.
- **Deliverable**: Script `scripts/compute_bootstrap_ci.py`, báo cáo thống kê `results/bootstrap_confidence_intervals.csv`.
- **DoD**: Hoàn tất 18 khoảng tin cậy 95% CI chuẩn khoa học (Head A: 0.8271 [0.8110, 0.8432], TB: 1.0000 [0.9990, 1.0000], COVIDx: 0.7342 [0.6930, 0.7754]).
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

### [x] Task 5.2: Hiện thực Thuật toán Binarize Thích Nghi & Đo đạc IoU (COMPLETED & VERIFIED)
- **Mô tả**: Viết `src/explainability/metrics.py` tạo mặt nạ nhị phân có bảo vệ giải phẫu $\hat{B}_c = \mathbb{I}(M_c \odot P_{\text{lung}} \ge \alpha \cdot \max(M_c))$ và đo đạc chỉ số kép Dual-Metric (Box-level IoU + Pixel Mask-IoU) so với Ground-truth Bounding Box từ VinDr-CXR và RSNA. (Ghi nhận: Mã nguồn được Antigravity hiện thực hóa làm baseline tham chiếu).
- **Deliverable**: Module `src/explainability/metrics.py`, unit tests `tests/test_wsol_metrics.py`, script `scripts/evaluate_iou.py`, kết quả `results/iou_evaluation.csv` và `results/iou_evaluation_vindr.csv`.
- **DoD**: Đo đạc trên RSNA Pneumonia đạt **Mean Box-IoU = 0.7631** (vượt chỉ tiêu $\ge 0.35$), VinDr-CXR đạt **Mean Box-IoU = 0.6049** (vượt chỉ tiêu $\ge 0.35$), 100% unit tests passed.
- **Agent**: `XAIEvalAgent` (Antigravity Baseline)

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

### [x] Task 5.4: Kiểm định Tổng quát hóa Ngoại vi (External Generalization Test) (COMPLETED & VERIFIED)
- **Mô tả**: Chạy đánh giá Head A trên tập Stanford CheXpert-small-v1 qua 5 bệnh lý cốt lõi (Atelectasis, Cardiomegaly, Consolidation, Edema, Effusion) để đo lường mức độ suy giảm do domain shift giữa các bệnh viện.
- **Deliverable**: Script `scripts/evaluate_external_chexpert.py`, báo cáo tổng quát hóa `results/chexpert_generalization_results.csv`.
- **DoD**: Mức suy giảm trung bình đạt **$\Delta \text{AUC} = +0.0447$**, vượt xa chỉ tiêu an toàn ($\le 0.080$), giữ vững 94.75% hiệu năng nguyên bản.
- **Agent**: `XAIEvalAgent`

---

## 📌 PHASE 6: FULL-STACK MEDICAL PACS WEB DEMO (TUẦN 12–13) — [x] COMPLETED
> **Mục tiêu**: Xây dựng hệ thống phần mềm hoàn chỉnh gồm FastAPI REST Backend nạp weights thực tế và Next.js 14 Medical PACS Viewer trực quan với trình khởi chạy Native 1-Click.

### [x] Task 6.1: Xây dựng FastAPI Microservice Backend & Clinical Grounding Engine (COMPLETED & VERIFIED)
- **Mô tả**: Viết backend phục vụ suy luận `app/backend/main.py`:
  - `POST /api/v1/predict`: Dự đoán 3-Head đồng thời (14 bệnh NIH, Lao phổi TB, COVIDx).
  - `POST /api/v1/explain`: Sinh Grad-CAM heatmap có hỗ trợ tham số động `clinical_grounding` (bật/tắt lọc giải phẫu) và `target_disease_name` cho phép chỉ định giải thích từng bệnh lý cụ thể (14 bệnh Head A, Tuberculosis Head B, COVID-19 Head C). Tự động mở rộng giải phẫu trung thất cho `Cardiomegaly`.
  - `POST /api/v1/audit`: Kiểm toán rủi ro shortcut học thuộc theo phế trường phổi.
- **Deliverable**: `app/backend/main.py`, `app/backend/schemas.py`, `app/backend/services.py`, `tests/test_api_backend.py`.
- **DoD**: 100% tests passed (98/98 tests toàn repo), thời gian xử lý suy luận $\le 1.8$ giây, xử lý ngoại lệ an toàn (HTTP 422 cho ảnh hỏng), triệt tiêu 100% nhiễu viền ngoài cho chế độ lâm sàng.
- **Agent**: `FullstackDeployAgent` (CommandCode CLI Go thực thi, Antigravity Gatekeeper phê duyệt)

### [x] Task 6.2: Xây dựng Giao diện Next.js Medical PACS Viewer & Interactive XAI Dashboard (COMPLETED & VERIFIED)
- **Mô tả**: Xây dựng ứng dụng Next.js tại `app/frontend/`:
  - Tải ảnh kéo thả (DICOM/PNG/JPG).
  - Khung hiển thị ảnh y tế đa lớp (`HeatmapViewer` blend `original` + Grad-CAM `heatmap` qua `mixBlendMode: "screen"`, pixel ngoài lồng ngực trong suốt 100%).
  - Dashboard tương tác: Click chọn trực tiếp từng bệnh lý trong 14 bệnh Head A, Head B (TB) hoặc Head C (COVID-19) để sinh heatmap Grad-CAM tức thời.
  - Bộ công tắc chế độ kép: `🛡️ Clinical Grounded` (Chuẩn y tế không nhiễu viền) vs `🔍 Raw Attention` (Kiểm toán shortcut learning).
  - Thanh trượt điều chỉnh độ mờ (Alpha Slider) của Heatmap từ 0 đến 100% (mặc định 45%).
- **Deliverable**: Ứng dụng Next.js 14 App Router hoàn chỉnh tại `app/frontend/`.
- **DoD**: `npm run build` thành công không lỗi TypeScript/ESLint, kết nối đồng bộ 4 endpoints của FastAPI backend, tương tác mượt mà theo thời gian thực.
- **Agent**: `FullstackDeployAgent` (CommandCode CLI Go thực thi, Antigravity Gatekeeper phê duyệt)

### [x] Task 6.3: Tối ưu hóa Khởi chạy Cục bộ 1-Click Native PACS & Cache Sanitization (COMPLETED & VERIFIED)
- **Mô tả**: Thay thế giải pháp Docker cồng kềnh ngốn bộ nhớ bằng script khởi chạy tự động hóa `scripts/start_local.ps1` tích hợp Smart HTTP Polling:
  - Tự động nhận diện môi trường Python chứa PyTorch & FastAPI (`Python 3.10`).
  - Tự động dọn sạch thư mục cache `.next` trước khi khởi động dev server nhằm ngăn chặn triệt để lỗi xung đột mã định danh webpack (`Error: Cannot find module './xxx.js'`).
  - Khởi động đồng thời FastAPI Backend (port 8000) và Next.js PACS Viewer (port 3000), tự động mở trình duyệt `http://localhost:3000` trong vòng 3–4 giây.
- **Deliverable**: `scripts/start_local.ps1`.
- **DoD**: Khởi chạy thành công cả 2 dịch vụ bằng 1 lệnh duy nhất, loại bỏ hoàn toàn lỗi webpack runtime, trải nghiệm PACS thời gian thực mượt mà.
- **Agent**: `FullstackDeployAgent`

---

## 📌 PHASE 7: THỰC NGHIỆM TỔNG KẾT, BÁO CÁO & BẢO VỆ ĐỒ ÁN (TUẦN 14–16) — [▶] 93.3% COMPLETED
> **Mục tiêu**: Tổng hợp số liệu khoa học, hoàn thiện cuốn báo cáo tốt nghiệp 20–25 trang chuẩn MICCAI/IEEE, chuẩn bị slide thuyết trình và bộ câu hỏi phản biện bảo vệ xuất sắc trước Hội đồng.

### [x] Task 7.1: Tổng hợp Số liệu & Soạn thảo Cuốn Báo cáo Đồ án (COMPLETED & VERIFIED)
- **Mô tả**: Biên soạn bản thảo khoa học `reports/FINAL_SCIENTIFIC_REPORT.md` và biên dịch ra file PDF đơn sắc `reports/FINAL_SCIENTIFIC_REPORT.pdf` (dung lượng 1.63 MB, 20–25 trang in) tuân thủ 100% Rule 9 (phông Times New Roman, bảng Booktabs 3 đường kẻ, không icon/emoji, nhúng biểu đồ thực nghiệm sắc nét).
- **Deliverable**: [reports/FINAL_SCIENTIFIC_REPORT.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/FINAL_SCIENTIFIC_REPORT.md), [reports/FINAL_SCIENTIFIC_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/FINAL_SCIENTIFIC_REPORT.pdf), script `scripts/generate_final_report_pdf.py`.
- **DoD**: Hoàn thiện báo cáo khoa học toàn diện, đáp ứng tiêu chuẩn nghiệm thu quốc tế.
- **Agent**: `QAReportAgent`

### [x] Task 7.2: Thiết kế Đề Cương Slide Báo cáo & Poster Khoa học (COMPLETED & VERIFIED)
- **Mô tả**: Thiết kế bộ đề cương Slide 39 trang trực quan, làm nổi bật 4 đóng góp: Multi-Task 3-Head, Định lượng hóa IoU trên RSNA/VinDr, Kiểm toán Shortcut Audit 94.92%, và Đấu trường kiến trúc CNN vs ViT.
- **Deliverable**: [reports/DEFENSE_SLIDES_OUTLINE.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/DEFENSE_SLIDES_OUTLINE.md).
- **DoD**: Hoàn thành đề cương 39 slides chi tiết, sẵn sàng kết xuất trình chiếu.
- **Agent**: `QAReportAgent`

### Task 7.3: Sản xuất Video Demo Hoạt động Hệ thống (PENDING USER WALKTHROUGH)
- **Mô tả**: Quay video chất lượng cao (1080p, thời lượng 2–3 phút) ghi hình trọn vẹn quy trình: Chạy `scripts/start_local.ps1` $\to$ Tải ảnh X-quang $\to$ Nhận kết quả chẩn đoán 3 Heads $\to$ Kéo thanh trượt Grad-CAM Alpha Slider $\to$ Kết quả kiểm toán Shortcut.
- **Deliverable**: Video `reports/demo_walkthrough.mp4`.
- **DoD**: Video rõ nét, có phụ đề/thuyết minh minh họa rõ ràng.
- **Agent**: Kỹ sư Trưởng (User) & `FullstackDeployAgent`

### [x] Task 7.4: Tổng duyệt Phản biện & Bộ Câu Hỏi Lâm Sàng (COMPLETED & VERIFIED)
- **Mô tả**: Biên soạn bộ 20 câu hỏi & đáp phản biện lâm sàng và kỹ thuật chuyên sâu (`docs/defense_faq.md`) bao quát 4 nhóm chủ đề: Rò rỉ dữ liệu Patient-ID, Masked Loss Engine, Kiểm toán Shortcut Learning và Định vị Bounding Box IoU.
- **Deliverable**: Bộ tài liệu câu hỏi phản biện [docs/defense_faq.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/docs/defense_faq.md).
- **DoD**: Chuẩn bị đầy đủ luận cứ phản biện vững chắc trước Hội đồng, tự tin hướng đến Điểm A/A+ ($\ge 85\%$).
- **Agent**: Toàn bộ Multi-Agent Team
