# 📋 PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Nền tảng: LungRay — Hệ Thống Hỗ Trợ Chẩn Đoán & Định Vị Tổn Thương X-Quang Ngực Đa Nhiệm (LungRay Multi-Task CADx + WSOL XAI)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Tên nền tảng** | **LungRay** (AI Chest X-ray Diagnostic & WSOL Platform) |
| **Mã dự án** | LUNGRAY-MULTITASK-WSOL-2026 |
| **Phiên bản** | v3.0 (Enterprise Specification) |
| **Tác giả** | Senior AI Engineer (10+ YOE) |
| **Trạng thái** | ✅ APPROVED FOR IMPLEMENTATION |
| **Mục tiêu hoàn thành** | 16 tuần (Quy chuẩn Đồ án Tốt nghiệp & Tiền Lâm sàng) |

---

## 1. TỔNG QUAN SẢN PHẨM & TẦM NHÌN (PRODUCT VISION)

### 1.1. Tuyên ngôn sản phẩm (Vision Statement)
Xây dựng **LungRay** — một hệ sinh thái nền tảng phần mềm hỗ trợ chẩn đoán hình ảnh y tế (Computer-Aided Diagnosis - CADx) từ ảnh X-quang ngực thẳng (Chest X-ray). Nền tảng LungRay ứng dụng học sâu đa nhiệm (Multi-Task Learning 3-Head) trên nền tảng encoder dùng chung, tích hợp trí tuệ nhân tạo có thể giải thích (Explainable AI - XAI) thông qua định vị tổn thương có giám sát yếu (Weakly-Supervised Object Localization - WSOL). Sản phẩm cam kết tính minh bạch khoa học thông qua quy trình kiểm toán học đường tắt (Shortcut Learning Audit) và giao diện hiển thị chuẩn PACS lâm sàng.

### 1.2. Đối tượng người dùng & Chân dung khách hàng (User Personas)
1. **Bác sĩ Chẩn đoán hình ảnh (Radiologist):**
   - *Nhu cầu*: Cần ý kiến tham vấn thứ hai (second opinion) độc lập, tốc độ xử lý nhanh, trực quan hóa vị trí nghi ngờ tổn thương dạng heatmap để tránh bỏ sót tổn thương nhỏ (nodule, pneumothorax sớm) trong ca trực đêm đông bệnh nhân.
   - *Điểm đau (Pain point)*: Quá tải phim chụp (100–200 ca/ca trực), mệt mỏi thị giác, không tin tưởng các mô hình AI dạng "hộp đen" chỉ đưa ra con số xác suất vô căn cứ.
2. **Bác sĩ Đa khoa Tuyến cơ sở / Bệnh viện dã chiến (General Practitioner):**
   - *Nhu cầu*: Công cụ sàng lọc phân luồng nhanh các bệnh truyền nhiễm cấp thiết (Lao phổi, COVID-19) và bệnh lý lồng ngực nguy cấp (Tràn khí màng phổi, Phù phổi cấp) để kịp thời hội chẩn hoặc chuyển viện.
   - *Điểm đau*: Thiếu chuyên gia X-quang tại chỗ, trang thiết bị đọc phim chưa chuyên sâu.
3. **Hội đồng Thẩm định & Giảng viên Hướng dẫn (Academic/Clinical Evaluators):**
   - *Nhu cầu*: Chứng minh được tính liêm chính học thuật, ngăn ngừa rò rỉ dữ liệu (data leakage) và chứng minh AI "học đúng bệnh" chứ không lợi dụng shortcut từ máy chụp/watermark nguồn ảnh.

---

## 2. BÀI TOÁN KỸ THUẬT & GIÁ TRỊ CỐT LÕI (VALUE PROPOSITION)

### 2.1. Phát biểu bài toán sản phẩm (Problem Statement)
- Hầu hết các ứng dụng AI chẩn đoán ảnh X-quang hiện nay chỉ tập trung vào một tập dữ liệu đơn lẻ hoặc một bệnh lý hẹp, dẫn đến tính khái quát kém và không đáp ứng được bức tranh bệnh học toàn diện tại phòng khám.
- Việc kết hợp dữ liệu đa nguồn từ nhiều bệnh viện tiềm ẩn nguy cơ **Shortcut Learning** (mô hình học thuộc đặc trưng biên máy chụp hoặc ký tự watermark để đưa ra chẩn đoán giả).
- Đa số đồ án chỉ hiển thị Grad-CAM định tính bằng mắt thường mà không có căn cứ định lượng (IoU) để chứng minh vùng chú ý trùng khớp với tổn thương thực tế.

### 2.2. Giải pháp kỹ thuật toàn diện
- **Kiến trúc Multi-Task 3-Head Shared Encoder**: Tận dụng một backbone duy nhất (DenseNet-121 / ResNet-50 / ViT) để giải quyết đồng thời 3 nhiệm vụ lâm sàng độc lập, tối ưu tài nguyên tính toán và bộ nhớ GPU.
- **Kiểm định định lượng IoU (WSOL Grounding)**: Binarize heatmap thích nghi và so sánh trực tiếp với Bounding Box chuyên gia từ bác sĩ Việt Nam (VinDr-CXR) và RSNA.
- **Shortcut Learning Audit Engine**: Cơ chế kiểm toán độc lập đo lường tỷ lệ năng lượng kích hoạt nằm trong phế trường phổi ($\ge 80\%$) cho nhánh COVID-19.
- **Trải nghiệm Full-stack Decoupled chuẩn PACS**: Tách rời Backend FastAPI (Docker containerized) và Frontend Next.js chuyên dụng cho ảnh y tế DICOM/PNG.

---

## 3. YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS - FR)

### FR1: Multi-Task Inference Engine (Lõi suy luận 3 nhánh)
- **FR1.1 — Head A (Phân loại đa nhãn 14 bệnh lý lồng ngực NIH)**:
  - Dự đoán đồng thời xác suất của 14 bệnh/bất thường: Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Consolidation, Edema, Emphysema, Fibrosis, Pleural Thickening, Hernia.
  - Phân loại qua ngưỡng động đa lớp $\tau_c$ được tinh chỉnh theo Youden's J statistic.
- **FR1.2 — Head B (Sàng lọc Lao phổi nhị phân - Tuberculosis)**:
  - Trả về xác suất nhị phân: Normal vs Tuberculosis.
  - Báo cáo chỉ số độ tin cậy và ngưỡng phân loại tối ưu.
- **FR1.3 — Head C (Phân loại 3 lớp COVIDx CXR-4 & Viêm phổi)**:
  - Phân loại đa lớp độc quyền (Softmax): COVID-19 (0), Normal (1), Pneumonia (2). Chuẩn hóa theo benchmark quốc tế COVIDx CXR-4 (Nature Scientific Reports).
- **FR1.4 — Masked Loss & Inference Decoupling**:
  - Hỗ trợ gọi suy luận riêng lẻ từng head hoặc gộp toàn diện cả 3 heads trong 1 lần forward pass.

### FR2: Explainable AI & Quantitative WSOL Heatmap Generator
- **FR2.1 — Sinh bản đồ nhiệt Grad-CAM & Grad-CAM++**:
  - Tự động sinh activation map tại tầng tích chập cuối cùng (hoặc cross-attention map của Transformer) cho từng lớp có xác suất vượt ngưỡng.
- **FR2.2 — Adaptive Heatmap Binarization**:
  - Tự động chuyển đổi heatmap liên tục sang mặt nạ nhị phân tổn thương với ngưỡng thích nghi: $\tau_{mask} = \alpha \cdot \max(M_c)$ ($\alpha \in [0.2, 0.4]$).
- **FR2.3 — Quantitative Grounding Validation**:
  - Tự động tính chỉ số IoU giữa mặt nạ nhị phân và Bounding Box chuyên gia trên tập kiểm thử (VinDr-CXR và RSNA Pneumonia Detection).

### FR3: Shortcut Learning Audit Engine
- **FR3.1 — Lung Field Masking**:
  - Tự động xác định vùng phế trường phổi ($P_{\text{lung}}$).
- **FR3.2 — Activation In-Lung Ratio Calculation**:
  - Tính toán tỷ lệ phần trăm gradient activation nằm trong phế trường phổi so với toàn bộ ảnh (đặc biệt là 4 góc chứa ký hiệu R/L, watermark máy chụp, mép viền ảnh).
- **FR3.3 — Cảnh báo vi phạm Shortcut**:
  - Gắn nhãn cảnh báo đỏ "High Shortcut Risk" nếu tỷ lệ kích hoạt trong phổi $< 75\%$.

### FR4: Ingestion & Tiền xử lý ảnh Y tế
- **FR4.1 — Hỗ trợ đa định dạng**: Tiếp nhận ảnh định dạng chuẩn y tế DICOM (`.dcm`), 16-bit / 8-bit Grayscale, PNG, JPG.
- **FR4.2 — Tiền xử lý chuẩn hóa**: Tự động áp dụng Windowing (HU) nếu là DICOM, chuẩn hóa kích thước cố định $512 \times 512$ cho toàn bộ pipeline huấn luyện và đánh giá, chuẩn hóa phân phối ImageNet.

### FR5: Giao diện Web PACS Viewer (Decoupled Frontend)
- **FR5.1 — Tải ảnh & Tương tác lâm sàng**: Kéo thả ảnh X-quang, hiển thị metadata ẩn (nếu có trong file DICOM).
- **FR5.2 — Dashboard chẩn đoán 3-Head**: Hiển thị thẻ xác suất trực quan với phân loại màu cảnh báo: Xanh (Bình thường), Vàng (Nghi ngờ), Đỏ (Nguy cơ cao tổn thương).
- **FR5.3 — Interactive Heatmap Overlay Viewer**:
  - Xem song song (Side-by-side) giữa ảnh gốc và ảnh chồng lớp Heatmap.
  - Thanh trượt điều chỉnh độ trong suốt (Alpha slider: $0\% \to 100\%$) của heatmap.
  - Cho phép click chọn từng bệnh lý cụ thể để chuyển đổi heatmap tương ứng.

---

## 4. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS - NFR)

### NFR1: Hiệu năng & Thời gian thực (Latency & Throughput)
- **Thời gian phản hồi đầu cuối (End-to-End Latency)**: $\le 2.0$ giây trên môi trường GPU cơ bản (T4/P100) hoặc máy cục bộ có card đồ họa RTX cho quy trình: Tải ảnh $\to$ Chuẩn hóa $\to$ Inference 3 Heads $\to$ Sinh Heatmap Grad-CAM $\to$ Trả kết quả JSON & Image Base64.
- **Thời gian suy luận thuần (Inference Only)**: $\le 200$ ms/ảnh với DenseNet-121 trên GPU.

### NFR2: Độ chính xác & Tiêu chuẩn lâm sàng (Model Performance KPIs)
- **Head A (NIH 14 pathologies)**: Macro AUC-ROC $\ge 0.82$, Macro F1-Score $\ge 0.45$.
- **Head B (Lao phổi)**: AUC-ROC $\ge 0.90$ (Mục tiêu: $\ge 0.95$).
- **Head C (COVIDx CXR-4 3 lớp)**: Macro AUC-ROC $\ge 0.92$, Macro F1-Score $\ge 0.85$.
- **WSOL Grounding Accuracy**: Mean IoU $\ge 0.35$ trên các mẫu True Positive của VinDr-CXR (8 lớp bệnh có bbox) và RSNA Pneumonia.
- **Shortcut Audit Pass Rate**: $\ge 80\%$ năng lượng kích hoạt tập trung trong nhu mô phổi trên tập kiểm thử COVID-19.

### NFR3: An toàn, Bảo mật & Liêm chính dữ liệu (Data Integrity & Safety)
- **Zero Data Leakage**: Tuyệt đối không để ảnh của cùng một bệnh nhân xuất hiện ở cả tập Train và Test (phân chia nghiêm ngặt theo `Patient_ID`).
- **Source Stratification**: Tách nguồn ảnh gốc đối với COVIDx CXR-4 (`data_source`) để kiểm soát rủi ro đa trung tâm.
- **De-identification**: Xóa bỏ toàn bộ thông tin định danh cá nhân (PII) nếu tải file DICOM trước khi đẩy vào pipeline suy luận.

### NFR4: Khả năng mở rộng & Đóng gói (Scalability & Packaging)
- Backend được container hóa bằng Docker (Docker Image $\le 4$GB tối ưu runtime PyTorch CPU/CUDA).
- Frontend Next.js độc lập, dễ dàng deploy lên Vercel hoặc chạy song song trong Docker-Compose.

---

## 5. CÁC ĐIỀU KIỆN NGOẠI LỆ & GIỚI HẠN (OUT OF SCOPE)

1. **Không can thiệp chẩn đoán điều trị pháp lý**: Hệ thống chỉ đóng vai trò hỗ trợ tham vấn (CDSS / Triaging tool), không thay thế bác sĩ chẩn đoán hình ảnh có chứng chỉ hành nghề.
2. **Không áp dụng trên ảnh CT Scanner hoặc MRI**: Chỉ xử lý ảnh chụp X-quang lồng ngực phẳng 2D tư thế thẳng (PA / AP view).
3. **Không tải toàn bộ dữ liệu MIMIC-CXR 570GB**: Giới hạn trong các tập dữ liệu mở khả thi đã phê duyệt (NIH ChestX-ray14, TB Chest Radiography Database, COVIDx CXR-4 Benchmark `andyczhao/covidx-cxr2`, VinDr-CXR, RSNA, CheXpert-small).
4. **Không tính IoU cho Head B và Head C**: Do các tập dữ liệu công khai của TB và COVID-19 không cung cấp bounding box chuẩn từ chuyên gia, hai nhánh này chỉ thực hiện đánh giá Grad-CAM định tính.

---

## 6. MA TRẬN PHÂN CHIA TRÁCH NHIỆM & TIÊU CHÍ NGHIỆM THU (DOD - DEFINITION OF DONE)

| Tính năng | Tiêu chí hoàn thành (DoD) | Người chịu trách nhiệm chính |
|:---|:---|:---:|
| **Data Ingestion & Splits** | • Có script sinh `patient_splits.csv` (NIH) và `covid_splits.csv` (Source-stratified)<br>• Unit test khẳng định $Train \cap Test = \emptyset$ về ID bệnh nhân | DataEngineerAgent |
| **Multi-Task 3-Head Model** | • Checkpoint `best_model.pth` đạt KPI phân loại cả 3 heads<br>• Masked backprop hoạt động đúng không gây rò rỉ gradient | ModelArchitectAgent |
| **XAI & Shortcut Audit** | • Module `grad_cam.py` xuất IoU $\ge 0.35$ trên VinDr-CXR<br>• Script audit xác nhận tỷ lệ trong phổi $\ge 80\%$ | XAIEvalAgent |
| **FastAPI Backend & Docker** | • Endpoint `/api/v1/predict` và `/api/v1/explain` phản hồi $\le 2$s<br>• Docker image build thành công, chạy ổn định | FullstackDeployAgent |
| **Next.js Medical UI** | • Hiển thị giao diện PACS, thanh trượt alpha, kết quả 3-head<br>• Thử nghiệm mượt mà trên trình duyệt | FullstackDeployAgent |
| **Báo cáo & Phản biện** | • Bộ bảng biểu metrics, biểu đồ loss, notebook demo hoàn chỉnh | QAReportAgent |
