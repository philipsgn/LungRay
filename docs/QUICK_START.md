# 🚀 QUICK START GUIDE - Nền Tảng LungRay (Chest X-ray Deep Learning & WSOL)

## TL;DR - Khả Năng & Trọng Tâm Nền Tảng LungRay

| Khía cạnh | Đánh giá | Ghi chú quan trọng |
|:---|:---:|:---|
| **Dữ liệu** | ✅ MULTI-TASK 3-HEAD | • **Train Head A**: NIH ChestX-ray14 (112K ảnh, 14 bệnh lồng ngực)<br>• **Train Head B**: Tuberculosis (TB) Chest X-ray Database (3.500 TB + 3.500 Normal)<br>• **Train Head C**: COVID-19 Radiography Database (~21K ảnh, 4 lớp: COVID/Normal/Opacity/Viral)<br>• **Kiểm định XAI chính**: VinDr-CXR test set (BBox từ bác sĩ Việt Nam)<br>• **Kiểm định XAI bổ sung**: RSNA Pneumonia Detection (BBox, riêng Pneumonia)<br>• **External Generalization**: CheXpert-small-v1 (test-only, Head A)<br>• *Loại bỏ hoàn toàn MIMIC-CXR (~570GB)* |
| **Công nghệ** | ✅ TIÊU CHUẨN | Transfer learning (DenseNet-121 / ResNet-50 / ViT) + Grad-CAM/Grad-CAM++ |
| **Bài toán** | ✅ ĐẶC TẢ RÕ | Multi-Task 3-Head: Phân loại 14 bệnh + Sàng lọc Lao + Sàng lọc COVID-19 + WSOL IoU + Shortcut Audit |
| **Tiến độ** | ⚠️ CẦN KỶ LUẬT | 16 tuần khả thi nhưng Phase 4 (tuần 7–9) rất dốc |
| **Khả năng thành công** | ✅ **78–83%** | Có kiểm soát rủi ro chặt chẽ (Patient ID split, Source-stratified split và Shortcut Audit) |

---

## 🔴 6 ĐIỀU SỐNG CÒN (CRITICAL RULES - ĐỌC KỸ TRƯỚC KHI CODE)

### 1. DATA LEAKAGE - BẮT BUỘC CHIA THEO PATIENT ID (CHO NIH)!
❌ **SAI HOÀN TOÀN**: Chia ngẫu nhiên theo hàng/ảnh (ảnh của cùng 1 bệnh nhân nằm ở cả Train và Test). Kết quả AUC > 0.95 là kết quả giả do mô hình "nhớ mặt" cấu trúc xương/tim của bệnh nhân!  
✅ **ĐÚNG CHUẨN**: Nhóm theo `Patient_ID`, chia toàn bộ bệnh nhân vào 3 tập không giao nhau ($Train \cap Test = \emptyset$).

```python
# ✅ CHUẨN XÁC CHO NIH CHESTX-RAY14
patient_ids = np.array(list(set(df['Patient_ID'])))
np.random.seed(42)
np.random.shuffle(patient_ids)

n_total = len(patient_ids)
train_p = set(patient_ids[:int(0.7 * n_total)])
val_p   = set(patient_ids[int(0.7 * n_total):int(0.8 * n_total)])
test_p  = set(patient_ids[int(0.8 * n_total):])

assert len(train_p.intersection(test_p)) == 0, "Data leakage detected!"
```

### 2. SHORTCUT LEARNING - BẮT BUỘC CHIA THEO NGUỒN ẢNH GỐC & AUDIT (CHO COVID-19)!
Bộ COVID-19 Radiography Database tổng hợp từ 4 nguồn khác nhau (PadChest, SIRM, RSNA, Kermany). Nếu chia ngẫu nhiên, mô hình sẽ học đặc trưng nguồn ảnh (watermark, viền đen máy chụp, độ tương phản) thay vì tổn thương phổi thật (DeGrave et al., 2021).
- ❌ **TUYỆT ĐỐI KHÔNG chia ngẫu nhiên theo ảnh**.
- ✅ **BẮT BUỘC**: Phân chia Stratified Split theo nguồn ảnh gốc (`source`).
- ✅ **BẮT BUỘC**: Chạy **Shortcut Learning Audit** bằng Grad-CAM trên toàn bộ ca dương tính COVID-19 để kiểm tra vùng kích hoạt có nằm trong phế trường phổi hay không trước khi công bố kết quả.

### 3. MẤT CÂN BẰNG LỚP (CLASS IMBALANCE) - PHẢI DÙNG FOCAL LOSS!
14 bệnh lý của NIH có tần suất xuất hiện rất chênh lệch (Infiltration: ~18%, Hernia: ~0.2%). Nếu dùng BCE thông thường, mô hình sẽ dự đoán toàn bộ là 0.
- ✅ Sử dụng **Focal Loss** hoặc **BCEWithLogitsLoss(pos_weight=...)**.
- ✅ Đánh giá bằng **Macro AUC-ROC** và **Macro F1-Score**.
- ✅ Tối ưu ngưỡng quyết định $\tau_c$ riêng biệt cho từng bệnh (bằng Youden's Index, không mặc định cứng 0.5).

### 4. ĐỊNH LƯỢNG HÓA XAI - KHÔNG CHỈ NHÌN BẰNG MẮT!
Đừng chỉ hiển thị ảnh heatmap rực rỡ và tự kết luận mô hình giải thích tốt.
- ✅ Sinh Heatmap liên tục $M_c \in [0, 1]^{H \times W}$ bằng Grad-CAM.
- ✅ Nhị phân hóa thích nghi: $\hat{B}_c = \mathbb{I}(M_c \ge \alpha \cdot \max(M_c))$ với $\alpha \in [0.2, 0.4]$.
- ✅ Đo đạc IoU so với Bounding Box chuyên gia trên tập **VinDr-CXR** và **RSNA Pneumonia** (Mục tiêu: Mean IoU $\ge 0.35$).

### 5. BOUNDING BOX CHỈ CẦN CHO TẬP ĐÁNH GIÁ, KHÔNG CẦN CHO TẬP TRAIN
Bản chất "Weakly-Supervised" của WSOL là mô hình chỉ học từ **nhãn mức ảnh** (image-level labels).
- Tập Train (KHÔNG cần bbox): NIH ChestX-ray14, TB Database, COVID-19 Radiography Database.
- Tập Đánh giá IoU (BẮT BUỘC có bbox): VinDr-CXR (chính), RSNA Pneumonia (bổ sung).
- Head B (TB) và Head C (COVID) không có bbox phù hợp $\to$ đánh giá Grad-CAM định tính (minh bạch giới hạn).

### 6. MULTI-TASK LEARNING CẦN CÂN BẰNG BATCH (TRÁNH TASK STARVATION)
Quy mô dữ liệu chênh lệch lớn (NIH: 112K ảnh, COVID: ~21K ảnh, TB: 7K ảnh).
- ✅ Dùng **Weighted/Balanced Batch Sampler** — đảm bảo mỗi batch có tỷ lệ cố định (ví dụ 60% NIH, 25% COVID, 15% TB).
- ✅ **Masked Backpropagation**: Mỗi batch chỉ tính loss và cập nhật qua head tương ứng nguồn dữ liệu của batch đó.

---

## 📊 CHỈ TIÊU KỸ THUẬT MỤC TIÊU (TARGET BENCHMARKS)

| Chỉ số | Baseline (ResNet-50) | Mục tiêu tối ưu (DenseNet + Focal Loss) | Ghi chú |
|:---|:---:|:---:|:---|
| **Macro AUC-ROC (Head A - NIH)** | $0.78 - 0.80$ | **$\ge 0.82$** | Tiệm cận CheXNet trên 14 nhãn |
| **Macro F1-Score (Head A - NIH)** | $0.38 - 0.42$ | **$\ge 0.45$** | Đa nhãn mất cân bằng |
| **TB AUC-ROC (Head B)** | $0.90 - 0.93$ | **$\ge 0.95$** | Phân loại nhị phân TB/Normal |
| **COVID-19 Macro AUC (Head C)** | $0.88 - 0.90$ | **$\ge 0.92$** | Phân loại 4 lớp COVID Database |
| **COVID-19 Macro F1 (Head C)** | $0.80 - 0.82$ | **$\ge 0.85$** | 4 lớp |
| **WSOL Mean IoU** | $0.25 - 0.30$ | **$\ge 0.35$** | Trên tập VinDr-CXR & RSNA |
| **Shortcut Audit (Head C)** | $< 70\%$ | **$\ge 80\%$ trong phổi** | Không bám viền ảnh hay watermark |
| **Thời gian Web Demo** | $\le 3$ giây | **$\le 2$ giây/ảnh** | Cho cả 3 heads + render heatmap |
| **CheXpert External AUC (Head A)** | Giảm ~0.05-0.10 | Càng gần NIH test càng tốt | Đo lường độ tổng quát hóa ngoại vi |

---

## 🛠️ THIẾT LẬP MÔI TRƯỜNG PHÁT TRIỂN (TUẦN 1)

```bash
# 1. Tạo conda environment
conda create -n chest-xray python=3.10 -y
conda activate chest-xray

# 2. Cài đặt PyTorch với CUDA hỗ trợ
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 3. Cài đặt các thư viện ML, XAI & Vision
pip install timm pytorch-grad-cam opencv-python pillow scikit-learn pandas matplotlib seaborn albumentations

# 4. Cài đặt thư viện giao diện Web App
pip install streamlit

# 5. Kiểm tra thiết bị GPU
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN KHUYẾN NGHỊ

```
Chest X-rays/
├── docs/                        # Tài liệu đặc tả, đề cương, tracking
│   ├── PROPOSAL.md              # Đề cương chi tiết hoàn chỉnh
│   ├── EXECUTIVE_SUMMARY.md     # Tóm lược điều hành dự án (v3)
│   ├── FEASIBILITY_ASSESSMENT.md# Đánh giá tính khả thi kỹ thuật
│   ├── PROJECT_TRACKING.md      # Checklist 16 tuần
│   └── QUICK_START.md           # Hướng dẫn nhanh này
├── data/
│   ├── raw/
│   │   ├── nih_chestxray14/     # NIH ChestX-ray14 (Head A - train 14 bệnh)
│   │   ├── tb_chestxray/        # Tuberculosis Chest X-ray Database (Head B - train TB)
│   │   ├── covid19_radiography/ # COVID-19 Radiography Database (Head C - train 4 lớp)
│   │   ├── vindr_cxr/           # VinDr-CXR test set (WSOL/IoU chính)
│   │   ├── rsna_pneumonia/      # RSNA Pneumonia Detection (WSOL/IoU bổ sung)
│   │   └── chexpert_small/      # CheXpert-small-v1 (External Generalization test)
│   ├── processed/               # Ảnh đã resize chuẩn 512x512 (đồng nhất cho MỌI nguồn)
│   └── splits/                  # patient_splits.csv, tb_splits.csv, covid_splits.csv
├── src/
│   ├── data/
│   │   ├── dataset.py           # Multi-Task PyTorch Dataset cho CXR
│   │   ├── sampler.py           # WeightedBatchSampler giữa 3 nguồn
│   │   └── transforms.py        # Augmentation y tế an toàn
│   ├── models/
│   │   ├── multi_task_net.py    # Shared Backbone + 3 Heads (A, B, C)
│   │   └── losses.py            # Focal Loss, Masked Loss Engine
│   ├── explainability/
│   │   ├── grad_cam.py          # Module Grad-CAM / Grad-CAM++
│   │   ├── shortcut_audit.py    # Module Shortcut Learning Audit cho COVID
│   │   └── metrics.py           # Hàm tính IoU giữa Heatmap và BBox
│   └── utils/
│       └── metrics.py           # AUC-ROC, Macro F1, Threshold finder
├── app/
│   ├── main.py                  # Streamlit Web Application (hỗ trợ cả 3 heads)
│   └── assets/                  # Icon, CSS giao diện
├── checkpoints/                 # Lưu trữ file trọng số (.pth)
└── results/                     # Biểu đồ loss, bảng kết quả CSV, báo cáo audit
```

---

## 💡 LỜI KHUYÊN THEO GIAI ĐOẠN

1. **Tuần 1–4 (Dữ liệu là móng nhà):** Không vội train model phức tạp. Hãy dành thời gian phân tích phân bố nhãn, trích xuất metadata nguồn ảnh cho COVID-19 và viết hàm chia `patient_split` (NIH) và `source_split` (COVID) thật chuẩn.
2. **Tuần 5–6 (Baseline đa nhiệm vững chắc):** Huấn luyện DenseNet-121 với Masked Loss cho cả 3 heads. Đảm bảo vòng lặp Weighted Batch Sampler hoạt động trơn tru.
3. **Tuần 7–9 (Trọng tâm học thuật):** Áp dụng Focal Loss cho Head A. Thử nghiệm Vision Transformer để đưa vào bảng so sánh trong báo cáo tốt nghiệp.
4. **Tuần 10–11 (Điểm nhấn sáng tạo & Tính liêm chính khoa học):** 
   - Đo định lượng IoU giữa Heatmap và BBox trên VinDr-CXR.
   - Thực hiện kiểm toán Shortcut Learning Audit trên Head C để chứng minh AI nhìn vào tổn thương phổi thực tế. Đây là hai nội dung ghi điểm cao nhất trước Hội đồng!
5. **Tuần 12–13 (Trải nghiệm người dùng):** Hoàn thiện Web Demo hiển thị trực quan cả 3 heads và bản đồ nhiệt trong $\le 2$ giây/ảnh.

