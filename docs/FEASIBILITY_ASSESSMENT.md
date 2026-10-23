# 📋 ĐÁNH GIÁ TÍNH KHẢ THI & KẾ HOẠCH THỰC HIỆN
## Nền tảng LungRay: Hệ thống hỗ trợ chẩn đoán & định vị tổn thương X-quang ngực bằng Deep Learning có giải thích (Explainable AI / WSOL)

**Ngày cập nhật**: 27/09/2026 (v3 — mở rộng phổ bệnh theo Logic A, tái bổ sung COVID-19 với kiểm soát rủi ro)  
**Tên nền tảng**: **LungRay** (AI Chest X-ray Platform)  
**Trạng thái**: ✅ **APPROVED FOR EXECUTION (SPECIFIED & SCOPED — MULTI-TASK 3-HEAD)**  
**Khả năng thành công**: **78–83%** (điều chỉnh do mở rộng thêm 2 nhiệm vụ phụ + 1 thí nghiệm audit bắt buộc)

---

## 1️⃣ ĐÁNH GIÁ TÍNH KHẢ THI

### ✅ ĐIỂM MẠNH

| Khía cạnh | Đánh giá | Chi tiết |
|:---|:---:|:---|
| **Dữ liệu khả thi** | ✅ CÓ SẴN & TẬP TRUNG | • **Primary Training (Head A)**: NIH ChestX-ray14 (112.120 ảnh, 14 nhãn chuẩn).<br>• **Secondary Training (Head B)**: Tuberculosis (TB) Chest X-ray Database (3.500 TB + 3.500 Normal, Kaggle).<br>• **Tertiary Training (Head C)**: COVID-19 Radiography Database (~21.165 ảnh, 4 lớp) với Stratified Split theo nguồn ảnh gốc + Shortcut Learning Audit.<br>• **External Validation & WSOL chính**: VinDr-CXR (tập test có bounding box từ bác sĩ Việt Nam).<br>• **WSOL bổ sung**: RSNA Pneumonia Detection (bounding box riêng cho Pneumonia).<br>• **External Generalization Test**: CheXpert-small-v1 (test-only, không train).<br>• Loại bỏ hoàn toàn MIMIC-CXR (~570GB, thủ tục PhysioNet phức tạp). |
| **Công nghệ** | ✅ TRƯỞNG THÀNH | • Transfer learning (DenseNet-121, ResNet-50, ViT) là tiêu chuẩn được kiểm chứng.<br>• Grad-CAM / Grad-CAM++ được hỗ trợ mạnh bởi PyTorch.<br>• Tài nguyên GPU miễn phí (Google Colab T4/L4, Kaggle P100) đủ đáp ứng. |
| **Giá trị khoa học** | ✅ RÕ RÀNG & MỚI MẺ | • Kiến trúc Multi-Task 3-Head (14 bệnh NIH, Lao phổi, COVID-19 4 lớp) dùng chung 1 backbone.<br>• Định lượng hóa vùng giải thích bằng chỉ số IoU so với bounding box chuyên gia (VinDr-CXR & RSNA).<br>• Quy trình kiểm toán học đường tắt (Shortcut Learning Audit) minh chứng độ tin cậy của XAI trên dữ liệu đa nguồn.<br>• So sánh khách quan giữa CNN và Vision Transformer. |
| **Thực tiễn lâm sàng** | ✅ CAO | • Đóng vai trò hệ thống hỗ trợ ra quyết định (CDSS) sàng lọc sơ bộ tại cơ sở tuyến dưới cho các bệnh phổ biến, lao phổi và COVID-19.<br>• Có ứng dụng Web Demo tương tác trực quan cho bác sĩ tham khảo trong $\le 2$ giây. |

### ⚠️ THÁCH THỨC & RỦI RO KỸ THUẬT

| Rủi ro | Mức độ | Giải pháp kiểm soát |
|:---|:---:|:---|
| **Mất cân bằng nhãn nghiêm trọng (Head A)** | CAO | • Áp dụng **Focal Loss** kết hợp **Positive Class Weighting**.<br>• Đánh giá bằng Macro AUC-ROC và Macro F1 với ngưỡng $\tau_c$ tối ưu hóa theo từng lớp qua Youden's Index. |
| **Rò rỉ dữ liệu (Data Leakage)** | CAO | • **Bắt buộc phân chia train/val/test theo `Patient_ID`** cho NIH (không chia theo ảnh).<br>• Kiểm tra nghiêm ngặt: $Train \cap Test = \emptyset$ trên tập bệnh nhân. |
| **Rủi ro Shortcut Learning (Head C - COVID-19)** | CAO | • Do 4 lớp trong COVID-19 Radiography Database tổng hợp từ nhiều nguồn khác nhau (PadChest, SIRM, RSNA, Kermany) $\to$ **Bắt buộc Stratified Split theo nguồn ảnh gốc** (không chia ngẫu nhiên theo ảnh) kết hợp **Shortcut Learning Audit bằng Grad-CAM** (DeGrave et al., 2021) để chứng minh vùng chú ý nằm trong phổi chứ không học thuộc watermark/viền ảnh. |
| **Multi-task mất cân bằng (Task Starvation)** | TRUNG BÌNH | • NIH (112K ảnh) áp đảo COVID-19 (~21K ảnh) và TB (7K ảnh) $\to$ áp dụng **Weighted/Balanced Batch Sampling** giữa 3 task (ví dụ: 60% NIH, 25% COVID, 15% TB trong mỗi epoch).<br>• Theo dõi validation loss và early stopping RIÊNG cho từng head. |
| **Độ chính xác của Grad-CAM (Heatmap ≠ BBox)** | TRUNG BÌNH | • Grad-CAM sinh ra phân bố gradient liên tục. Cần chuẩn hóa ngưỡng nhị phân thích nghi $\tau_{mask} = \alpha \cdot \max(M)$ với $\alpha \in [0.2, 0.4]$ trước khi tính IoU.<br>• Đo đạc IoU trên tập True Positives của VinDr-CXR và RSNA Pneumonia. |
| **Phương sai cao ở các lớp hiếm trong NIH** | TRUNG BÌNH | • Hernia chỉ có 227 ảnh dương tính/112.120 ảnh (~0.2%) $\to$ sau patient-level split, tập test chỉ còn ~45 ảnh dương tính, khiến AUC dao động mạnh.<br>• Giải pháp: báo cáo Bootstrap Confidence Interval cho các lớp hiếm (Hernia, Fibrosis) thay vì chỉ 1 con số AUC duy nhất. |
| **Áp lực tiến độ 16 tuần** | CAO | • Tuần 7–9 rất dốc (vừa thử Focal Loss vừa thử ViT).<br>• Chuẩn bị sẵn template huấn luyện từ tuần 5–6; tận dụng checkpoint pretrained chuẩn từ torchvision/timm. |
| **Phần cứng tính toán** | THẤP | • Resize ảnh chuẩn hóa cố định $512 \times 512$ (tối ưu hóa độ phân giải không gian $16 \times 16$ cho WSOL).<br>• Sử dụng mixed precision training (`torch.cuda.amp`) để tiết kiệm VRAM và tăng tốc độ train 2x. |

### 🎯 KẾT LUẬN VỀ TÍNH KHẢ THI
**DỰ ÁN KHẢ THI (FEASIBLE)** với điều kiện:
- ✅ Giữ vững phạm vi trong chuyên khoa X-quang lồng ngực (không mở rộng sang cơ quan khác như não/bụng).
- ✅ Kiểm soát triệt để không để xảy ra rò rỉ dữ liệu (patient-level split cho NIH; source-stratified split cho COVID-19; stratified split cho TB).
- ✅ Thực hiện định lượng hóa XAI bằng chỉ số IoU cụ thể — **áp dụng cho các nhãn có bounding box** (8 lớp qua VinDr-CXR + Pneumonia qua RSNA); nhãn TB và COVID đánh giá Grad-CAM định tính.
- ✅ Bắt buộc thực hiện **Shortcut Learning Audit** bằng Grad-CAM trên Head C trước khi công bố kết quả.
- ✅ Triển khai đúng kiến trúc Multi-Task 3-Head với Weighted Batch Sampling để tránh task starvation.

> **📌 Ghi chú quan trọng về Bounding Box:** Bbox KHÔNG cần thiết để huấn luyện classifier (bản chất "Weakly-Supervised" của WSOL là học vị trí chỉ từ nhãn mức ảnh). Bbox CHỈ cần cho tập dữ liệu dùng để ĐÁNH GIÁ định lượng IoU (VinDr-CXR, RSNA Pneumonia). Do đó, NIH ChestX-ray14, Tuberculosis Chest X-ray Database và COVID-19 Radiography Database không cần có bbox khi huấn luyện — đây là thiết kế chuẩn xác.

---

## 2️⃣ PHÂN TÍCH CHI TIẾT TỪNG GIAI ĐOẠN (16 TUẦN)

### **Phase 1: Setup & Research (Tuần 1–2)** 
🟢 **Rủi ro: THẤP**
```
Tuần 1:
  □ Đọc 5 bài báo nền tảng: ChestX-ray14, CheXNet, CheXpert, ViT, Grad-CAM, Shortcut Learning (DeGrave et al., 2021).
  □ Thiết lập môi trường PyTorch 2.0+, CUDA, Jupyter, GitHub repo.
  □ Hiểu rõ bài toán Multi-Task 3-Head, Multi-label Classification và Weakly-Supervised Object Localization (WSOL).

Tuần 2:
  □ Hoàn thiện Đề cương chi tiết (PROPOSAL.md) với phát biểu bài toán Multi-Task 3-Head rõ ràng.
  □ Thiết kế sơ đồ kiến trúc hệ thống tổng thể (Shared Backbone + 3 Heads + Grad-CAM Pipeline).
  □ Lập kế hoạch chi tiết cho pipeline xử lý dữ liệu và chiến lược sampling.
```
**Sản phẩm bàn giao**: Đề cương chi tiết được duyệt, môi trường lập trình sẵn sàng.

---

### **Phase 2: Data Preparation, Patient-level & Source-level Split (Tuần 3–4)**
🟡 **Rủi ro: TRUNG BÌNH** (Trọng tâm: Chống data leakage & Shortcut split)
```
Tuần 3:
  □ Tải 6 nguồn dữ liệu: NIH ChestX-ray14, TB Database, COVID-19 Radiography, VinDr-CXR test set, RSNA test set, CheXpert-small.
  □ EDA: Phân tích phân bố 14 nhãn bệnh NIH, tỷ lệ cân bằng TB, phân bố 4 lớp COVID-19.
  □ Trích xuất metadata nguồn ảnh gốc (PadChest, SIRM, RSNA, Kermany) từ COVID-19 Radiography Database.
  □ Kiểm tra kích thước, chất lượng ảnh, missing values.

Tuần 4:
  □ Xây dựng pipeline tiền xử lý:
    • Resize ảnh chuẩn hóa cố định $512 \times 512$.
    • Chuẩn hóa pixel values theo ImageNet mean/std đồng nhất cho mọi nguồn.
    • Tăng cường dữ liệu y tế an toàn (xoay nhẹ ±10°, lật ngang; tuyệt đối không lật dọc).
  □ Phân chia train/val/test:
    • NIH ChestX-ray14: chia theo PATIENT_ID (70/10/20) chống data leakage.
    • COVID-19 Radiography: chia Stratified Split theo NGUỒN ẢNH GỐC chống shortcut learning.
    • TB Database: chia stratified split nhị phân.
  □ Lưu danh sách phân chia vào file splits (patient_splits.csv, covid_splits.csv, tb_splits.csv).
  □ Xây dựng PyTorch DataLoader hỗ trợ Weighted Batch Sampling giữa 3 task.
```
**Sản phẩm bàn giao**: Báo cáo EDA, bộ file chỉ mục phân chia, PyTorch Multi-Task DataLoader sẵn sàng.

---

### **Phase 3: Baseline Model Training (Multi-Task 3-Head) (Tuần 5–6)**
🟢 **Rủi ro: THẤP** (Quy trình chuẩn hóa)
```
Tuần 5:
  □ Xây dựng vòng lặp huấn luyện Multi-Task (Training Loop):
    • Load backbone pretrained DenseNet-121 và ResNet-50.
    • Thiết lập 3 classifier heads: Head A (14 đầu ra, BCE), Head B (1 đầu ra, BCE), Head C (4 đầu ra, CrossEntropy).
    • Triển khai Masked Backpropagation (chỉ tính loss và backprop qua head tương ứng nguồn ảnh của batch).
    • Triển khai Weighted Batch Sampling (ví dụ: 60% NIH, 25% COVID, 15% TB).
    • Optimizer: AdamW (lr=1e-3, weight_decay=1e-4), Scheduler: CosineAnnealingLR.
  □ Xây dựng validation loop riêng biệt cho từng head, early stopping độc lập.

Tuần 6:
  □ Huấn luyện mô hình đa nhiệm 20–30 epochs.
  □ Đánh giá trên tập test độc lập của từng nguồn: Head A (NIH test), Head B (TB test), Head C (COVID test).
  □ Lưu checkpoint baseline multi-task tốt nhất.
```
**Sản phẩm bàn giao**: Checkpoint baseline (`checkpoint_baseline_multitask.pth`), đường cong huấn luyện từng head, bảng điểm AUC sơ bộ (Mục tiêu: Head A Macro AUC $\ge 0.80$, Head B $\ge 0.90$, Head C $\ge 0.90$).

---

### **Phase 4: Model Enhancement & Architecture Comparison (Tuần 7–9)** 
🔴 **Rủi ro: CAO** (Giai đoạn dốc nhất của dự án)
```
Tuần 7: Xử lý mất cân bằng dữ liệu & Tối ưu hóa Loss
  □ Tính toán positive class weights cho 14 nhãn NIH.
  □ Triển khai Focal Loss / Asymmetric Loss cho Head A.
  □ Tinh chỉnh siêu tham số alpha và gamma.
  □ Huấn luyện chiến lược 2 giai đoạn (Freeze backbone → Unfreeze fine-tune toàn mạng với lr=1e-5).

Tuần 8: Thử nghiệm Vision Transformer
  □ Cấu hình mô hình Vision Transformer (ViT-B/16 hoặc Swin-T) từ thư viện timm.
  □ Fine-tune đa nhiệm trên tập dữ liệu X-quang.
  □ Tối ưu learning rate nhỏ (1e-4 đến 5e-5) và batch size.

Tuần 9: So sánh toàn diện & Lựa chọn mô hình tối ưu
  □ Lập bảng so sánh chi tiết: DenseNet-121 vs ResNet-50 vs ViT (AUC-ROC, F1, thời gian train/infer trên cả 3 heads).
  □ Tối ưu hóa ngưỡng phân loại riêng biệt tau_c cho từng lớp bằng Youden's J statistic.
  □ Chọn mô hình tốt nhất (thường là DenseNet-121 + Focal Loss).
  □ Báo cáo Bootstrap Confidence Interval cho các lớp hiếm (Hernia, Fibrosis).
```
**Sản phẩm bàn giao**: Bảng so sánh hiệu năng các kiến trúc, checkpoint mô hình tối ưu (`best_model.pth`), bảng ngưỡng quyết định $\tau_c$.

---

### **Phase 5: Explainability (XAI), Quantitative IoU & Shortcut Audit (Tuần 10–11)**
🟡 **Rủi ro: TRUNG BÌNH** (Đòi hỏi độ chính xác cao về mặt thuật toán)
```
Tuần 10: Tích hợp Grad-CAM & Grad-CAM++
  □ Trích xuất feature maps và gradients từ convolutional layer cuối cùng (hoặc attention maps từ ViT).
  □ Sinh bản đồ nhiệt kích hoạt (Grad-CAM heatmap) cho từng lớp có dự đoán dương tính.
  □ Trực quan hóa chồng lớp heatmap lên ảnh X-quang gốc (alpha-blending).

Tuần 11: Định lượng hóa IoU & Kiểm toán Shortcut Learning
  □ Chuẩn hóa bounding box ground-truth từ tập test VinDr-CXR và RSNA Pneumonia.
  □ Thiết lập hàm binarization heatmap thích nghi: B_hat = (M >= alpha * max(M)) với alpha in [0.2, 0.4].
  □ Tính chỉ số IoU giữa B_hat và Ground-truth BBox trên các mẫu True Positive (Mục tiêu: Mean IoU >= 0.35).
  □ Chạy Shortcut Learning Audit cho Head C (COVID-19): Kiểm tra tỷ lệ kích hoạt trong phế trường phổi so với viền/watermark trên toàn bộ ca dương tính COVID.
  □ Chạy Grad-CAM định tính cho Head B (TB).
  □ Kiểm tra Generalization của Head A trên CheXpert-small-v1 (test-only).
```
**Sản phẩm bàn giao**: Module Grad-CAM hoàn chỉnh, bảng kết quả định lượng IoU (VinDr-CXR & RSNA), báo cáo kiểm toán Shortcut Learning Audit cho Head C, báo cáo generalization CheXpert.

---

### **Phase 6: Web Demo Application (Tuần 12–13)**
🟡 **Rủi ro: TRUNG BÌNH** (Tập trung vào trải nghiệm người dùng)
```
Tuần 12: Xây dựng giao diện Web App
  □ Sử dụng Streamlit (hoặc Flask UI) với giao diện chuẩn y tế hiện đại, trực quan.
  □ Chức năng: Upload ảnh X-quang (DICOM/PNG/JPG), thanh điều chỉnh ngưỡng confidence.
  □ Backend tích hợp model checkpoint tối ưu và module Grad-CAM.

Tuần 13: Hoàn thiện tính năng & Kiểm thử
  □ Hiển thị đồng thời kết quả chẩn đoán cả 3 heads: 14 bệnh NIH, Lao phổi, COVID-19.
  □ Bảng xác suất có mã màu cảnh báo (đỏ: cao, vàng: nghi ngờ, xanh: bình thường).
  □ Tùy chọn bật/tắt hiển thị heatmap vùng tổn thương cho từng bệnh được chọn.
  □ Đo đạc và tối ưu thời gian suy luận (<= 2 giây/ảnh cho toàn bộ 3 heads + render heatmap).
```
**Sản phẩm bàn giao**: Ứng dụng Web Demo hoạt động mượt mà, tài liệu hướng dẫn sử dụng.

---

### **Phase 7: Báo cáo & Bảo vệ (Tuần 14–16)**
🟢 **Rủi ro: THẤP - TRUNG BÌNH**
```
Tuần 14–15: Hoàn thiện Báo cáo & Tài liệu
  □ Viết báo cáo tốt nghiệp 40–50 trang theo chuẩn quy định.
  □ Thiết kế Slide thuyết trình chuyên nghiệp (35–40 slides).
  □ Thiết kế Poster khoa học khổ A1 tóm tắt đề tài.
  □ Quay video demo quy trình hoạt động (2–3 phút).

Tuần 16: Bảo vệ đồ án tốt nghiệp
  □ Báo cáo thử nghiệm, chuẩn bị câu hỏi phản biện lâm sàng và kỹ thuật (đặc biệt phần XAI & Shortcut Audit).
  □ Bảo vệ chính thức trước Hội đồng chấm Đồ án.
```
**Mục tiêu**: Đạt điểm A/A+ (85–100%).

---

## 3️⃣ TIÊU CHUẨN NGHIỆM THU ĐỊNH LƯỢNG (TARGET METRICS)

| Tiêu chí | Ngưỡng mục tiêu | Cơ sở đối sánh / Phương pháp |
|:---|:---:|:---|
| **Macro AUC-ROC (Head A - NIH)** | $\ge 0.82$ | Tương đương benchmark công bố của CheXNet (Rajpurkar et al.) trên 14 nhãn |
| **Macro F1-Score (Head A - NIH)** | $\ge 0.45$ | F1 trung bình tại ngưỡng $\tau_c$ tối ưu hóa theo Youden's Index |
| **AUC-ROC (Head B - Tuberculosis)** | $\ge 0.90$ (tối ưu $\ge 0.95$) | Phân loại nhị phân trên TB Chest X-ray Database |
| **Macro AUC-ROC (Head C - COVID-19)** | $\ge 0.92$ | Phân loại 4 lớp trên COVID-19 Radiography Database |
| **Macro F1-Score (Head C - COVID-19)** | $\ge 0.85$ | F1 đa lớp trên COVID-19 Radiography Database |
| **WSOL Mean IoU** | $\ge 0.35$ | Độ trùng khớp giữa Binarized Grad-CAM và BBox trên VinDr-CXR & RSNA |
| **Shortcut Learning Audit (Head C)** | $\ge 80\%$ kích hoạt trong phổi | Kiểm toán vị trí heatmap trên ca dương tính COVID, không bám viền/watermark |
| **Thời gian suy luận Web Demo** | $\le 2$ giây/ảnh | Tổng thời gian tải ảnh $\to$ suy luận 3 heads $\to$ render bản đồ nhiệt |

---

## 4️⃣ CÁC NGUYÊN TẮC CỐT LÕI (GOLDEN RULES)

1. 🚫 **TUYỆT ĐỐI KHÔNG chia train/test theo ảnh:** Luôn luôn nhóm theo `patient_id` cho NIH để ngăn ngừa Data Leakage; với COVID-19, bắt buộc Stratified Split theo nguồn ảnh gốc.
2. 🎯 **KHÔNG dừng lại ở heatmap định tính:** Phải có bảng số liệu IoU cụ thể đối chiếu với VinDr-CXR + RSNA Pneumonia cho các lớp có bounding box.
3. ⚖️ **LUÔN xử lý mất cân bằng lớp:** Sử dụng Focal Loss và ngưỡng quyết định riêng biệt $\tau_c$; báo cáo Bootstrap CI cho các lớp hiếm (Hernia).
4. 🔍 **BẮT BUỘC kiểm toán Shortcut Learning cho Head C:** Chạy Grad-CAM audit trên ca dương tính COVID-19 để minh chứng mô hình học tổn thương phổi thật chứ không học đặc trưng máy chụp.
5. 🔀 **LUÔN cân bằng batch giữa các task:** Áp dụng Weighted Batch Sampling giữa 3 nguồn (NIH 112K, COVID 21K, TB 7K) để tránh task starvation.
6. 💾 **KHÔNG tải dữ liệu quá mức:** Giữ dung lượng ổ cứng gọn gàng (NIH, TB, COVID-19, VinDr-CXR, RSNA, CheXpert-small-v1; loại bỏ MIMIC-CXR 570GB).

