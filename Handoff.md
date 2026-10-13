# 🫁 LUNGRAY PLATFORM: PROJECT HANDOFF & MASTER SPECIFICATION (Handoff.md)
## Nền tảng Hỗ trợ Chẩn đoán & Định vị Tổn thương X-quang Ngực Đa nhiệm (CXR Multi-Task CADx + WSOL XAI)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Tên nền tảng** | **LungRay** (AI Chest X-ray Diagnostic & WSOL Grounding Platform) |
| **Mã dự án** | LUNGRAY-MULTITASK-WSOL-2026 |
| **Phiên bản** | v3.5 (SOTA Benchmark Synchronized) |
| **Kiến trúc cốt lõi** | Multi-Task 3-Head Shared Encoder + Masked Loss + Quantitative WSOL + FastAPI + Next.js |
| **Trạng thái** | ✅ BASELINE VALIDATED & READY FOR CLOUD EXECUTION |

---

## 1. TỔNG QUAN NỀN TẢNG & GIÁ TRỊ CỐT LÕI

**LungRay** là nền tảng phần mềm hỗ trợ chẩn đoán hình ảnh y tế (CADx) từ ảnh X-quang ngực thẳng (Chest X-ray PA/AP view). Nền tảng giải quyết triệt để 3 thách thức lớn nhất của AI y tế hiện nay:
1. **Phân mảnh bài toán (Task Fragmentation)**: Tích hợp 3 bài toán lâm sàng độc lập vào 1 mạng học sâu duy nhất với Shared Encoder (DenseNet-121 / ResNet-50 / ViT).
2. **Liêm chính khoa học & Chống học đường tắt (Scientific Integrity & Shortcut Learning Prevention)**: Ngăn chặn 100% rò rỉ dữ liệu theo bệnh nhân (Zero Patient Data Leakage) và kiểm toán rủi ro Shortcut Learning bằng năng lượng kích hoạt Grad-CAM trong phổi ($\ge 80\%$).
3. **Giải thích có thể định lượng (Quantitative WSOL Grounding)**: Không dừng lại ở việc xem heatmap định tính; hệ thống nhị phân hóa thích nghi và đo đạc chỉ số IoU so với Bounding Box chuyên gia từ bác sĩ y tế Việt Nam (VinDr-CXR) và RSNA Pneumonia.

---

## 2. 8 RÀNG BUỘC SỐNG CÒN CỦA DỰ ÁN (THE 8 INVIOLABLE CONSTRAINTS)

1. 🔴 **Kiến trúc 3-Head dùng chung 1 Shared Backbone**:
   Dùng chung 1 encoder (DenseNet-121, ResNet-50 hoặc ViT) cho đồng thời:
   - **Head A**: 14 bệnh lồng ngực NIH ChestX-ray14 ($C=14$, Sigmoid).
   - **Head B**: Sàng lọc Lao phổi TB ($C=1$, Sigmoid).
   - **Head C**: Chuẩn hóa theo benchmark quốc tế **COVIDx CXR-4** (=1$, Sigmoid: COVID-19 Positive vs Normal / Negative sàng lọc nhị phân, cân bằng mẫu 1:1 và Anti-Shortcut CLAHE/Crop). Bệnh Viêm phổi (Pneumonia) đã được giải quyết tại Head A và kiểm chứng trên RSNA/VinDr.
2. 🔴 **Zero Patient Data Leakage**:
   Với NIH ChestX-ray14, bắt buộc phân chia theo `Patient_ID` (70% Train / 10% Val / 20% Test). Tuyệt đối cấm chia ngẫu nhiên theo ảnh ($Train \cap Test = \emptyset$).
3. 🔴 **Chống Shortcut Learning**:
   Với COVIDx CXR-4, bắt buộc phân tầng theo nguồn ảnh gốc (`data_source`) và kiểm soát theo `patient_id`.
4. 🔴 **Phân định vai trò Bounding Box**:
   Bounding Box **CHỈ** dùng cho tập đánh giá để tính chỉ số IoU (VinDr-CXR, RSNA Pneumonia). Các tập huấn luyện (NIH, TB, COVIDx) **KHÔNG** cần Bounding Box vì WSOL học từ nhãn mức ảnh.
5. 🔴 **Cân bằng Batch Multi-Task**:
   Bắt buộc dùng `WeightedMultiTaskBatchSampler` cố định tỷ lệ 60% NIH : 25% COVIDx : 15% TB trong mỗi mini-batch để chống Task Starvation.
6. 🔴 **Kiểm toán bắt buộc cho Head C (Shortcut Audit)**:
   Bắt buộc thực hiện Shortcut Learning Audit bằng Grad-CAM trên các ca dương tính COVID-19; tỷ lệ năng lượng kích hoạt trong phế trường phổi phải đạt $\ge 80\%$.
7. 🔴 **Chuẩn Nghiên cứu Thực nghiệm Sống (Live Research Code)**:
   Mọi phân tích dữ liệu (EDA), đánh giá mô hình, ma trận nhầm lẫn (Confusion Matrix), Grad-CAM heatmap hay định vị IoU trong Jupyter Notebooks (`notebooks/*.ipynb`) bắt buộc phải viết bằng mã Python/PyTorch tương tác sống, tính toán trực tiếp từ dữ liệu thực tế. Tuyệt đối cấm nhúng ảnh tĩnh giả lập.
8. 🔴 **Dọn dẹp Tệp Tạm & Tinh gọn Không gian Dự án (Lean Workspace)**:
   Toàn bộ tệp tạm, scratch scripts phát sinh trong quá trình thực thi phải được dọn sạch ngay lập tức; không gian làm việc luôn ở chuẩn Enterprise.

---

## 3. DANH MỤC 6 BỘ DỮ LIỆU CHUẨN LÂM SÀNG

| STT | Bộ dữ liệu | Vai trò trong LungRay | Quy mô | Độ phân giải | Ràng buộc áp dụng |
|:---:|:---|:---|:---:|:---:|:---|
| 1 | **NIH ChestX-ray14** | Huấn luyện Head A (14 bệnh lồng ngực) | 112,120 ảnh | $1024 \times 1024$ | Phân chia nghiêm ngặt theo `Patient_ID` (70/10/20) |
| 2 | **TB Chest Radiography Database** | Huấn luyện Head B (Sàng lọc Lao phổi) | 7,000 ảnh | $512 \times 512$ | Stratified Split 70/10/20, Youden's J threshold |
| 3 | **COVIDx CXR-4 Benchmark** (ndyczhao/covidx-cxr2) | Huấn luyện Head C (Sàng lọc nhị phân COVID-19) | 16,400+ ảnh | $\ge 1024\text{px}$ | Mount tức thì trên Kaggle (0s), cân bằng 1:1, tiền xử lý Anti-Shortcut |
| 4 | **VinDr-CXR** | **Chỉ dùng Test**: Đánh giá IoU WSOL | 3,000 ảnh test | $\ge 2048\text{px}$ | Ground-truth Bounding Box từ bác sĩ Việt Nam |
| 5 | **RSNA Pneumonia Detection** | **Chỉ dùng Test**: Đánh giá IoU WSOL | Tập test | $1024 \times 1024$ | Bounding Box tổn thương Viêm phổi |
| 6 | **CheXpert-small-v1** | **Chỉ dùng Test**: External Generalization | 22,433 ảnh | $320 \times 320+$ | Đánh giá tổng quát hóa ngoài phân phối (OOD) |

---

## 4. THIẾT KẾ KIẾN TRÚC & MÃ NGUỒN (`src/`)

```
src/
├── data/
│   ├── dataset.py       # ChestXrayDataset hỗ trợ Dual-Mode, O(1) file_map lookup, COVIDx CXR-4 structure
│   ├── sampler.py       # WeightedMultiTaskBatchSampler (tỷ lệ chuẩn 60% NIH : 25% COVIDx : 15% TB)
│   ├── transforms.py    # Medical Augmentation (cấm flip dọc) & chuẩn hóa On-The-Fly 512x512
│   └── make_splits.py   # Pipeline sinh patient_splits.csv, covid_splits.csv, tb_splits.csv
├── models/
│   ├── backbones.py     # Shared Encoders: DenseNet-121, ResNet-50, ViT-B16 (resample_abs_pos_embed)
│   ├── multi_task_net.py# MultiTaskChestXrayNet: Head A (14), Head B (1), Head C (1) + Grad-CAM hook
│   ├── losses.py        # MaskedMultiTaskLoss (Zero Gradient Leakage), FocalLoss, pos_weight BCE
│   └── trainer.py       # MultiTaskTrainer: Mixed Precision AMP FP16, CosineAnnealingLR, Macro AUROC
└── explainability/
    ├── grad_cam.py      # Thuật toán Grad-CAM & Grad-CAM++ trích xuất activation maps
    ├── metrics.py       # Adaptive Binarization (alpha=0.3) & IoU so với Expert Bounding Box
    └── shortcut_audit.py# Shortcut Learning Audit Engine (tính tỷ lệ năng lượng trong phế trường phổi)
```

---

## 5. HỆ SINH THÁI JUPYTER NOTEBOOKS TRÊN KAGGLE CLOUD (`notebooks/`)

1. **`00_kaggle_dataset_audit_and_profiling.ipynb`**:
   - Tích hợp module *Deep Hierarchical Anatomizer* tự động bóc tách 3 bộ dữ liệu gắn trên Kaggle.
   - Kiểm toán độ phân giải thực tế, tỷ lệ ảnh $<512\text{px}$ và đưa ra phán quyết tự động (Clinical Verdict).
2. **`00_rescale_nih_512.ipynb`** (K?m script `scripts/rescale_nih_kaggle.py`):
   - ?a ti?n tr?nh 4 vCPUs (`ProcessPoolExecutor`) downscale to?n b? 112,120 ?nh NIH ($1024 \times 1024 \to 512 \times 512$) b?ng `cv2.INTER_AREA` (ch?ng r?ng c?a, b?o t?n t?n th??ng vi m?) trong ~25 ph?t.
   - Xu?t th? m?c ?nh n?n PNG m?c 4 (~13 GB) k?m `Data_Entry_2017.csv` v? `patient_splits.csv` (Zero Patient Leakage) ?? 1-click t?o Kaggle Dataset m?i: **`lungray-nih-512`**.
3. **`00_rescale_covidx_512.ipynb`** (K?m script `scripts/rescale_covidx_kaggle.py`):
   - ?p d?ng **Medical Letterboxing** (`LongestMaxSize(512)` + vi?n ?en ??i x?ng $512 \times 512$) cho 16,400+ ?nh trong `train/` v? `test/` c?a COVIDx CXR-4 trong ~3?5 ph?t. B?o to?n 100% t? l? h?nh h?c th?t c?a b?ng tim v? l?ng ng?c.
   - Xu?t th? m?c output (~2 GB) k?m `train.txt` v? `test.txt` ?? 1-click t?o Kaggle Dataset m?i: **`lungray-covidx-512`**.
   *(L?u ?: B? TB Chest Radiography 7,000 ?nh ?? chu?n $512 \times 512$ s?n c? n?n gi? nguy?n 100%, kh?ng c?n notebook resize).*
4. **`00a_nih_audit_baseline.ipynb`**:
   - Kiểm toán độc lập Head A (NIH ChestX-ray14): Bóc tách 12 chunks, kiểm tra Zero Patient Leakage, tính `pos_weight` cho 14 bệnh.
   - Huấn luyện DenseNet-121 baseline (3–5 epochs) xuất 14 đường cong ROC curves và Macro AUROC.
5. **`00b_covid_audit_baseline.ipynb`**:
   - Kiểm toán độc lập Head C (COVIDx CXR-4 Benchmark): Đọc 	rain.txt/	est.txt, cân bằng mẫu 1:1, tiền xử lý Anti-Shortcut (CLAHE + Inset Border Crop), huấn luyện baseline nhị phân với BCEWithLogitsLoss và Youden's J threshold.
   - Huấn luyện baseline DenseNet-121 3 lớp với `CrossEntropyLoss`, xuất Normalized Confusion Matrix và Macro AUROC.
6. **`00c_tb_audit_baseline.ipynb`**:
   - Kiểm toán độc lập Head B (Tuberculosis TB): Phân tích tỷ lệ mất cân bằng 5:1, tính `pos_weight=5.0`.
   - Huấn luyện baseline (3–5 epochs), tối ưu ngưỡng quyết định $\tau^*$ theo chỉ số **Youden's J statistic**, xuất AUROC, Sensitivity, Specificity.
7. **`01_exploratory_data_analysis.ipynb`**:
   - Phân tích và trực quan hóa chuyên sâu EDA: Phân bố bệnh lý, ma trận đồng xuất hiện (Co-occurrence Matrix), nhân khẩu học bệnh nhân và trực quan hóa ảnh X-quang thực tế.
8. **`02_multitask_baseline_training.ipynb`**:
   - Notebook huấn luyện toàn diện Multi-Task 3-Head Baseline trên Kaggle GPU (P100 / T4).
   - Tích hợp *Dataset Structure & Resolution Inspector*, On-the-Fly $512 \times 512$, nạp `WeightedMultiTaskBatchSampler` (60:25:15).
   - Đánh giá chuyên sâu trên tập Test độc lập cho cả 3 heads và xuất Delivery Gate 2 Scorecard.

---

## 6. HƯỚNG DẪN CHẠY TRÊN KAGGLE CLOUD (QUICK RUN GUIDE)

### Bước 1: Tạo Notebook mới trên Kaggle
- Môi trường: GPU P100 hoặc 2x T4.
- Gắn các Input Datasets:
  - NIH ChestX-ray14: `nih-chest-xrays` (hoặc `data/`).
  - TB Chest X-ray: `tawsifurrahman/tuberculosis-tb-chest-xray-dataset`.
  - COVIDx CXR-4: `andyczhao/covidx-cxr2` (Kaggle mount ngay trong 0s tại `/kaggle/input/covidx-cxr2/`).

### Bước 2: Huấn luyện Baseline
- Tải lên và thực thi notebook `notebooks/02_multitask_baseline_training.ipynb` (hoặc chạy script CLI `python kaggle/train_kaggle.py --epochs 25 --batch-size 16`).

### Bước 3: Nghiệm thu Delivery Gate 2
- Đối chiếu chỉ tiêu nghiệm thu:
  - Head A (NIH 14 bệnh): Macro AUROC $\ge 0.80$.
  - Head B (Lao phổi TB): AUROC $\ge 0.90$.
  - Head C (COVIDx CXR-4 Sàng lọc nhị phân): AUROC $\ge 0.90$, Sensitivity $\ge 0.88$, In-lung Activation Energy $\ge 80\%$.

---

## 7. KIỂM THỬ HỆ THỐNG & ĐỘ TIN CẬY

- **Unit Test Suite**: 19 automated tests trong `tests/` bảo đảm:
  - Zero Patient Data Leakage verification.
  - On-the-Fly 512x512 tensor shapes.
  - Multi-Task Batch Sampler fixed 60:25:15 ratios.
  - Masked Multi-Task Loss gradient isolation.
  - MultiTaskChestXrayNet forward / predict shapes across 3 heads.
  - 1-step dry-run training loop with Mixed Precision.
- **Kết quả kiểm thử**: `pytest tests/ -v` $\to$ **19/19 PASSED (100%)**.
