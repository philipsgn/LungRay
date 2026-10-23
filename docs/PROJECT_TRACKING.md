# 📊 TRACKING & CHECKLIST - Nền tảng LungRay (Chest X-ray Deep Learning & WSOL Multi-Task 3-Head)

## Tuần 1-2: Setup, Research & Đề cương
- [x] Đọc các bài báo nền tảng (ChestX-ray14, CheXNet, CheXpert, Grad-CAM, ViT, DeGrave et al. 2021 về Shortcut Learning) — Báo cáo tại `docs/literature_review.md`
- [x] Setup môi trường PyTorch 2.0+, cấu hình dependencies (`requirements.txt`, `environment.yml`, `pyproject.toml`) và cài đặt package `lungray` editable
- [x] Nắm vững bài toán Multi-Task 3-Head: Multi-label Classification (Head A) + Binary TB Screening (Head B) + 3-class COVIDx CXR-4 Screening (Head C) + WSOL qua IoU & Shortcut Audit
- [x] Vẽ sơ đồ kiến trúc hệ thống (Shared Backbone + 3 Classification Heads + Grad-CAM Pipeline) trong `README.md` và `TECH_ARCHITECTURE.md`
- [x] Hoàn thiện đề cương chi tiết (PROPOSAL.md) với phát biểu bài toán cụ thể cho cả 3 heads
- **Status**: ✅ COMPLETED (GIAI ĐOẠN 1 NGHIỆM THU - DELIVERY GATE 1 PASSED)
- **Deliverables hoàn tất**: 
  - Tài liệu Literature Review 5 bài báo: `docs/literature_review.md`
  - Cấu trúc mã nguồn Enterprise: `src/data`, `src/models`, `src/explainability`, `src/utils`, `configs/`, `tests/`, `notebooks/`
  - Cấu hình quản lý môi trường: `requirements.txt`, `environment.yml`, `pyproject.toml`
  - Bộ kiểm thử tự động khởi tạo: `tests/test_environment.py` (3/3 passed)
  - Tài liệu dự án: `README.md` chuẩn hóa đầy đủ thông số kiến trúc và ràng buộc kỹ thuật

## Tuần 3-4: Data Preparation, Patient-Level & Source-Level Split
- [x] Tải dữ liệu Head A: NIH ChestX-ray14 (~112.120 ảnh, 14 nhãn bệnh) — xác nhận file `Data_Entry_2017.csv` có đầy đủ thông tin
- [x] Tải dữ liệu Head B: Tuberculosis (TB) Chest X-ray Database (3.500 TB + 3.500 Normal, Kaggle `tawsifurrahman/tuberculosis-tb-chest-xray-dataset`)
- [x] Tải dữ liệu Head C: Chuẩn hóa benchmark quốc tế COVIDx CXR-4 (~16.400+ ảnh: COVID-19, Normal, Pneumonia) — Kaggle: `andyczhao/covidx-cxr2` (0s mount, native resolution $\ge 1024$px)
- [x] Tải tập dữ liệu kiểm định vị trí tổn thương chính: VinDr-CXR (tập test có bounding box từ bác sĩ Việt Nam)
- [x] Tải tập dữ liệu kiểm định vị trí tổn thương bổ sung: RSNA Pneumonia Detection Challenge (bounding box, riêng nhãn Pneumonia)
- [x] Xác nhận CheXpert-small-v1 đã tải đúng phiên bản (dùng làm External Generalization test cho Head A, KHÔNG dùng để train)
- [x] Phân tích EDA: Phân bố 14 nhãn NIH, tỷ lệ cân bằng TB, phân bố 3 lớp COVIDx CXR-4 — Notebook `notebooks/01_exploratory_data_analysis.ipynb` & 6 biểu đồ `results/eda/`
- [x] **BẮT BUỘC CHO HEAD C**: Trích xuất metadata nguồn ảnh gốc (`data_source`) và ID bệnh nhân (`patient_id`) của COVIDx CXR-4 từ `train.txt` và `test.txt`
- [x] Pipeline tiền xử lý: Resize chuẩn hóa cố định $512 \times 512$, chuẩn hóa ImageNet mean/std đồng nhất cho mọi nguồn (`src/data/transforms.py`)
- [x] Data augmentation y tế an toàn (xoay nhẹ ±10°, flip ngang; tuyệt đối không flip dọc)
- [x] **CHỐNG DATA LEAKAGE**: Chia train/val/test theo `patient_id` cho NIH (70/10/20) - Cam kết Zero Data Leakage!
- [x] **CHỐNG SHORTCUT LEARNING**: Chia train/val/test cho COVID-19 Radiography Database theo **Source-Stratified Split** (độ lệch nguồn < 0.1%)
- [x] Chia train/val/test cho TB dataset bằng random stratified split
- [x] Lưu các file chỉ mục phân chia: `patient_splits.csv` (112,120 ảnh), `covid_splits.csv` (21,165 ảnh), `tb_splits.csv` (4,200 ảnh)
- [x] Thiết kế Dataset/DataLoader hỗ trợ **Multi-Task Weighted Batch Sampling** cố định tỷ lệ 60:25:15 (`src/data/sampler.py`)
- **Status**: ✅ COMPLETED (GIAI ĐOẠN 2 NGHIỆM THU - HỆ SINH THÁI 3 NOTEBOOKS 00a, 00b, 00c ĐÃ HOÀN TẤT & VERIFIED 100%)
- **Deliverables hoàn tất**: 
  - Notebook Kiểm toán Chất lượng Dataset Kaggle Độc lập: `notebooks/00_kaggle_dataset_audit_and_profiling.ipynb`
  - Hệ sinh thái Notebooks Chuyên sâu & Baseline Thực nghiệm (16 cells/notebook):
    - `notebooks/00a_nih_audit_baseline.ipynb` (Head A: 12 Chunks, Zero Patient Leakage, 14 Pathologies pos_weight, 3-5 Epoch Baseline)
    - `notebooks/00b_covid_audit_baseline.ipynb` (Head C: COVIDx CXR-4 3 Classes, Zero Patient Leakage, Source Stratification, 3-5 Epoch Baseline)
    - `notebooks/00c_tb_audit_baseline.ipynb` (Head B: 2 Classes, Imbalance Ratio, Youden's J threshold, 3-5 Epoch Baseline)
  - Notebook EDA toàn diện: `notebooks/01_exploratory_data_analysis.ipynb`
  - 6 biểu đồ EDA độ phân giải cao: `results/eda/`
  - Bộ 3 file chỉ mục phân chia cố định: `dataset/splits/patient_splits.csv`, `covid_splits.csv`, `tb_splits.csv`
  - Module nạp dữ liệu đa nhiệm & Dual-Mode: `src/data/dataset.py`, `src/data/transforms.py`, `src/data/sampler.py`
  - Bộ kiểm thử tự động đạt 19/19 passed: `tests/test_data_pipeline.py` (Zero Data Leakage, Mask Exclusion, Sampler Ratio 60:25:15)

## Tuần 5-6: Baseline Model Training (Multi-Task 3-Head)
- [x] Xây dựng kiến trúc `MultiTaskChestXrayNet` (`src/models/multi_task_net.py`): Shared DenseNet-121 backbone + 3 Classification Heads (Head A 14 outputs, Head B 1 output, Head C 3 outputs) + `predict()` xuất xác suất chuẩn xác và Grad-CAM layer hooks
- [x] Hiện thực `MaskedMultiTaskLoss` & `FocalLoss` (`src/models/losses.py`): Cô lập gradient tuyệt đối giữa các heads (Zero Gradient Leakage), tích hợp BCE + positive class weights (`pos_weight`) cho Head A
- [x] Xây dựng `MultiTaskTrainer` (`src/models/trainer.py`): Mixed Precision AMP FP16, CosineAnnealingLR, Early Stopping, Validation đa nhiệm tính Macro AUROC độc lập và lưu checkpoint theo $S_{\text{val}} = 0.40 \cdot \text{AUC}_A + 0.30 \cdot \text{AUC}_B + 0.30 \cdot \text{AUC}_C$
- [x] Xây dựng kịch bản huấn luyện độc lập Kaggle Cloud (`kaggle/train_kaggle.py`) tự động hóa phát hiện dataset mounts và huấn luyện 25 epochs trên P100 / T4 GPU
- [x] Xây dựng notebook thực nghiệm sống `notebooks/02_multitask_baseline_training.ipynb` chuẩn hóa cho Kaggle GPU, tích hợp module **Dataset Structure & Resolution Inspector**, Smart Recursive Path Indexer ($O(1)$ lookup), chuẩn hóa On-The-Fly 512x512, 25 epoch train loop, đánh giá 14 bệnh lồng ngực, vẽ live ROC curves và Confusion Matrix
- [x] Xây dựng bộ kiểm thử kiến trúc tự động (`tests/test_model_architecture.py`): Kiểm tra shape outputs, xác suất kích hoạt, cô lập gradient tuyệt đối và 1-step dry run
- [x] Chạy kiểm thử tự động toàn diện: **19/19 Unit Tests PASSED** (100% tỷ lệ vượt qua, bao gồm kiểm định loại trừ thư mục masks)
- **Status**: ✅ COMPLETED (NOTEBOOK & TOÀN BỘ MÃ NGUỒN HUẤN LUYỆN PHASE 3 ĐÃ HOÀN TẤT VỚI DATASET INSPECTOR & KIỂM THỬ XÁC MINH 100%)
- **Deliverables hoàn tất**: 
  - Module kiến trúc: `src/models/multi_task_net.py` (✅)
  - Module hàm mất mát: `src/models/losses.py` (✅)
  - Bộ máy huấn luyện: `src/models/trainer.py` (✅)
  - Kịch bản Kaggle Cloud: `kaggle/train_kaggle.py` (✅)
  - Notebook thực nghiệm sống: `notebooks/00_kaggle_dataset_audit_and_profiling.ipynb` (✅ Deep Hierarchical Anatomizer & Live CXR Image Inspector)
  - Notebook huấn luyện sống: `notebooks/02_multitask_baseline_training.ipynb` (✅ 24 cells sống tích hợp Kaggle Resolution Profiler, Smart Indexer & On-the-Fly 512x512)
  - Bộ kiểm thử unit tests: `tests/test_model_architecture.py` (✅ 6/6 tests passed)
  - Regression test suite: `tests/` (✅ 19/19 tests passed)
  - **Chỉ tiêu kỳ vọng Gate 2**: Head A Macro AUC $\ge 0.80$, Head B AUC $\ge 0.90$, Head C Macro AUC $\ge 0.90$ (khi chạy 25 epochs trên Kaggle GPU để export `best_model.pth`)

## Tuần 7-9: Model Enhancement & Architecture Comparison (⚠️ GIAI ĐOẠN DỐC!)
### Tuần 7: Xử lý mất cân bằng dữ liệu & Tinh chỉnh Loss
- [ ] Tính toán trọng số các lớp (Positive Class Weights) cho Head A
- [ ] Triển khai Focal Loss / Asymmetric Loss cho Head A
- [ ] Tinh chỉnh siêu tham số: $\alpha \in \{0.25, 0.5\}$, $\gamma \in \{2, 3\}$
- [ ] Chiến lược huấn luyện 2 giai đoạn: Freeze backbone lớp đầu $\to$ Unfreeze fine-tune toàn mạng với lr nhỏ ($10^{-5}$)

### Tuần 8: Thử nghiệm Vision Transformer (ViT)
- [ ] Tải mô hình ViT-B/16 hoặc Swin-Transformer từ thư viện `timm`
- [ ] Fine-tune đa nhiệm trên tập dữ liệu X-quang với learning rate nhỏ ($10^{-4}$ đến $5 \times 10^{-5}$)
- [ ] So sánh tốc độ huấn luyện và lượng tài nguyên VRAM tiêu thụ so với DenseNet

### Tuần 9: So sánh toàn diện & Lựa chọn mô hình tốt nhất
- [ ] So sánh 3 kiến trúc: ResNet-50, DenseNet-121, ViT-Base trên cả 3 heads
- [ ] Đo lường: AUC-ROC, F1-score, Precision, Recall cho từng nhãn bệnh
- [ ] Báo cáo khoảng tin cậy Bootstrap CI cho các lớp hiếm (Hernia, Fibrosis)
- [ ] Tối ưu hóa ngưỡng quyết định $\tau_c$ riêng cho từng lớp theo Youden's J statistic
- [ ] Chọn mô hình tối ưu (thường là DenseNet-121 + Focal Loss)
- [ ] Lưu checkpoint tối ưu `best_model.pth`
- **Status**: ⏳ PENDING
- **Deliverable**: 
  - Bảng so sánh các mô hình `comparison_table.csv`
  - File trọng số tối ưu `best_model.pth`
  - Bảng ngưỡng quyết định tối ưu `optimal_thresholds.csv`

## Tuần 10-11: Explainability (XAI), Định lượng IoU & Shortcut Audit
### Tuần 10: Tích hợp Grad-CAM & Grad-CAM++
- [ ] Hiện thực Grad-CAM trích xuất gradients từ convolutional layer cuối cùng (hoặc attention maps từ ViT)
- [ ] Thử nghiệm biến thể Grad-CAM++
- [ ] Sinh bản đồ nhiệt kích hoạt (Heatmap) trên các mẫu dương tính
- [ ] Trực quan hóa chồng lớp (overlay) heatmap lên ảnh X-quang gốc

### Tuần 11: Đánh giá định lượng IoU & Kiểm toán Shortcut Learning
- [ ] Nạp tập kiểm thử VinDr-CXR có tọa độ bounding box ground-truth
- [ ] Nạp tập kiểm thử RSNA Pneumonia Detection có bounding box (bổ sung, riêng nhãn Pneumonia)
- [ ] Áp dụng ngưỡng nhị phân thích nghi: $\hat{B}_c = \mathbb{I}(M_c \ge \alpha \cdot \max(M_c))$ với $\alpha \in [0.2, 0.4]$
- [ ] Tính chỉ số IoU giữa $\hat{B}_c$ và Bounding Box chuyên gia trên các ca True Positive (VinDr-CXR + RSNA, mục tiêu Mean IoU $\ge 0.35$)
- [ ] **BẮT BUỘC: Shortcut Learning Audit cho Head C (COVID-19)**:
  - Chạy Grad-CAM trên toàn bộ ca dương tính COVID-19
  - Kiểm tra xem vùng kích hoạt có nằm trong phế trường phổi hay bị lệch sang viền ảnh/watermark/ký hiệu nguồn
  - Đảm bảo tỷ lệ kích hoạt trong phổi $\ge 80\%$, chứng minh độ tin cậy khoa học trước khi công bố kết quả
- [ ] Chạy Grad-CAM định tính cho Head B (TB) — trực quan hóa minh họa ca bệnh tiêu biểu
- [ ] Chạy Head A trên tập test CheXpert-small-v1 để đo External Generalization xuyên bệnh viện
- **Status**: ⏳ PENDING
- **Deliverable**: 
  - Module mã nguồn `grad_cam.py`
  - Báo cáo định lượng `iou_evaluation.csv` (VinDr-CXR + RSNA)
  - Báo cáo kiểm toán `shortcut_learning_audit.csv` (Head C)
  - Báo cáo generalization `chexpert_external_test.csv`
  - Notebook trực quan hóa 30+ ca bệnh tiêu biểu (cả 3 heads)

## Tuần 12-13: Xây dựng ứng dụng Demo (Web App)
### Tuần 12: Phát triển Backend & Giao diện người dùng
- [ ] Chọn framework: Streamlit (hoặc Flask/FastAPI)
- [ ] Xây dựng UI: Tải ảnh X-quang (PNG/JPG/DICOM), thanh trượt điều chỉnh ngưỡng tự tin
- [ ] Tích hợp inference pipeline: Nạp `best_model.pth` và tự động suy luận đồng thời cả 3 heads

### Tuần 13: Hoàn thiện tính năng & Đánh giá trải nghiệm
- [ ] Hiển thị dashboard chẩn đoán:
  - Bảng xác suất 14 bệnh lồng ngực (Head A) phân nhóm màu cảnh báo
  - Kết quả sàng lọc Lao phổi (Head B)
  - Kết quả sàng lọc COVID-19 (Head C: COVID / Normal / Opacity / Viral)
- [ ] Cho phép bác sĩ click vào từng bệnh để xem bản đồ nhiệt Grad-CAM tổn thương tương ứng
- [ ] Tối ưu hóa tốc độ: Đảm bảo thời gian phản hồi $\le 2$ giây/ảnh cho toàn bộ pipeline
- [ ] Viết tài liệu hướng dẫn sử dụng và cài đặt README
- **Status**: ⏳ PENDING
- **Deliverable**: 
  - Mã nguồn Web App hoạt động hoàn chỉnh
  - Bộ ảnh test mẫu kèm kết quả kỳ vọng

## Tuần 14-15: Viết Báo cáo & Chuẩn bị Bảo vệ
### Tuần 14: Soạn thảo Báo cáo Đồ án tốt nghiệp
- [ ] Phần 1: Giới thiệu & Phát biểu bài toán cụ thể (Multi-Task 3-Head Framework)
- [ ] Phần 2: Tổng quan nghiên cứu & Cơ sở lý thuyết (CNN, ViT, XAI, WSOL, Shortcut Learning)
- [ ] Phần 3: Phương pháp đề xuất (Pipeline dữ liệu, Weighted Sampling, Kiến trúc 3-Head, Thuật toán binarize IoU, Quy trình Audit)
- [ ] Phần 4: Thực nghiệm & Kết quả chi tiết (Baseline, Cải tiến, So sánh ViT, Bảng điểm IoU, Kết quả Audit COVID)
- [ ] Phần 5: Thảo luận, hạn chế và hướng phát triển
- [ ] Thiết kế Slide báo cáo (35–45 slides khoa học)

### Tuần 15: Thiết kế Poster & Thuyết trình thử nghiệm
- [ ] Thiết kế Poster khoa học khổ A1
- [ ] Quay video demo hoạt động của hệ thống (2–3 phút)
- [ ] Thuyết trình thử nghiệm trước giảng viên hướng dẫn / bạn học
- [ ] Chuẩn bị bộ câu hỏi phản biện lâm sàng và kỹ thuật (đặc biệt phần rủi ro đa nguồn & audit)
- **Status**: ⏳ PENDING
- **Deliverable**: 
  - Báo cáo đồ án hoàn chỉnh (PDF 40–50 trang)
  - Slide thuyết trình PowerPoint / PDF
  - Poster khoa học A1
  - Video demo hệ thống

## Tuần 16: Bảo vệ Đồ án tốt nghiệp
- [ ] Chuẩn bị máy móc, kiểm tra kết nối demo trực tiếp
- [ ] Báo cáo trước Hội đồng chấm Đồ án tốt nghiệp
- [ ] Trả lời câu hỏi phản biện của Hội đồng
- **Mục tiêu**: Điểm A hoặc A+ ($\ge 85\%$)

---

## 🎯 CÁC CHỈ TIÊU NGHIỆM THU ĐỊNH LƯỢNG (MILESTONES)

| Mục tiêu | Thời điểm | Chỉ tiêu bắt buộc (Must-Have) | Chỉ tiêu nâng cao (Nice-to-Have) |
|:---|:---:|:---|:---|
| **Môi trường & Đề cương** | Tuần 2 | ✅ Đề cương chi tiết được duyệt (Multi-Task 3-Head) | Sơ đồ kiến trúc LaTeX/Draw.io hoàn chỉnh |
| **Pipeline dữ liệu** | Tuần 4 | ✅ Chia dữ liệu theo Patient ID (NIH) & Nguồn gốc (COVID) | Pipeline tự động hóa lưu cache đa nhiệm |
| **Baseline Model** | Tuần 6 | ✅ Head A Macro AUC $\ge 0.80$, Head B $\ge 0.90$, Head C $\ge 0.90$ | So sánh ResNet vs DenseNet |
| **Mô hình tối ưu** | Tuần 9 | ✅ Head A Macro AUC $\ge 0.82$, F1 $\ge 0.45$; Head C AUC $\ge 0.92$ | Thử nghiệm thành công ViT / Swin-T |
| **Định lượng XAI & Audit** | Tuần 11 | ✅ Mean IoU $\ge 0.35$ (VinDr-CXR) + Shortcut Audit $\ge 80\%$ trong phổi | Thử nghiệm cả Grad-CAM++ & Score-CAM |
| **Web Demo App** | Tuần 13 | ✅ Suy luận 3 heads và render heatmap $\le 2$s | Hỗ trợ đọc trực tiếp định dạng DICOM |
| **Báo cáo & Bảo vệ** | Tuần 16 | ✅ Báo cáo 40–50 trang, bảo vệ A/A+ | Công bố bài báo hội nghị SV |

