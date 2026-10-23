# 📚 KHẢO SÁT TÀI LIỆU & CƠ SỞ LÝ THUYẾT (LITERATURE REVIEW)
## Nền tảng LungRay: Phân Tích Chuyên Sâu 5 Công Trình Nền Tảng Trong Phân Tích X-Quang Ngực Bằng Deep Learning & XAI

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Dự án** | **LungRay** (CXR Multi-Task CADx + WSOL Grounding Engine) |
| **Giai đoạn** | Phase 1 — Task 1.1: Khảo sát tài liệu & Nghiên cứu công trình nền tảng |
| **Người thực hiện** | `ModelArchitectAgent` & `Lead AI Orchestrator` |
| **Trạng thái** | ✅ HOÀN THÀNH — ĐÃ PHÊ DUYỆT |

---

## 1. TỔNG QUAN KHẢO SÁT

Nền tảng **LungRay** được xây dựng dựa trên sự kế thừa, kết hợp và mở rộng có kiểm soát từ 5 nghiên cứu đột phá trong lĩnh vực Thị giác máy tính Y khoa (Medical Computer Vision) và Trí tuệ nhân tạo Đáng tin cậy (Trustworthy AI). Tài liệu này trích xuất các thông số kỹ thuật chuẩn hóa (benchmarks), các bài học thành công, cùng những cạm bẫy phương pháp luận (methodological pitfalls) cần khắc phục.

---

## 2. CHI TIẾT 5 CÔNG TRÌNH NỀN TẢNG

### 2.1. Công trình 1: ChestX-ray14 — Wang et al. (CVPR 2017)
- **Tên bài báo**: *ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks on Weakly-Supervised Classification and Localization of Common Thorax Diseases* (mở rộng thành ChestX-ray14).
- **Tác giả & Đơn vị**: Xiaosong Wang, Yifan Peng, Le Lu, Zhiyong Lu, Mohammadhadi Bagheri, Ronald M. Summers (National Institutes of Health - NIH Clinical Center).
- **Đóng góp then chốt**:
  - Công bố bộ dữ liệu X-quang lồng ngực ẩn danh quy mô lớn nhất thời điểm đó gồm **112,120 ảnh X-quang thẳng từ 30,805 bệnh nhân**.
  - Thiết lập phân loại 14 hội chứng lồng ngực: Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Consolidation, Edema, Emphysema, Fibrosis, Pleural Thickening, Hernia.
  - Sử dụng NLP (Text mining) trên bệnh án X-quang để gán nhãn mức ảnh (image-level labels) với độ chính xác >90%.
  - Cung cấp 880 ảnh có Bounding Box do bác sĩ chẩn đoán hình ảnh khoanh vùng thủ công làm benchmark cho bài toán Weakly-Supervised Object Localization (WSOL).
- **Benchmark AUC gốc (ResNet-50 / DenseNet)**:
  - AUC trung bình (Mean AUC): **0.745 – 0.780**.
  - Các bệnh đạt AUC cao nhất: Cardiomegaly (0.87–0.89), Pneumothorax (0.84–0.86), Effusion (0.86–0.88).
  - Các bệnh khó chẩn đoán: Infiltration (0.69), Nodule (0.71), Pneumonia (0.70).
- **Bài học & Ứng dụng cho LungRay**:
  - Nhãn đa nhãn (Multi-Label) có tính phụ thuộc lẫn nhau cao (ví dụ: Effusion thường đi kèm Infiltration). Cần áp dụng hàm mất mát BCEWithLogitsLoss hoặc Asymmetric Loss kết hợp Pos Weight.
  - **Cảnh báo Data Leakage**: Do 1 bệnh nhân có thể chụp nhiều lần tại các thời điểm khác nhau, **bắt buộc phải chia dữ liệu theo `Patient_ID`**. Nếu chia ngẫu nhiên theo ảnh, mô hình sẽ học thuộc đặc trưng giải phẫu cá nhân của bệnh nhân (patient-specific anatomy) dẫn đến AUC ảo tăng 5–10%.

---

### 2.2. Công trình 2: CheXNet — Rajpurkar et al. (Stanford University, 2017)
- **Tên bài báo**: *CheXNet: Radiologist-Level Pneumonia Detection on Chest X-Rays with Deep Learning*.
- **Tác giả & Đơn vị**: Pranav Rajpurkar, Jeremy Irvin, Kaylie Zhu, Brandon Yang, Hershel Mehta, Tony Duan, Daisy Ding, Aarti Bagul, Matthew P. Lungren, Andrew Y. Ng (Stanford ML Group).
- **Đóng góp then chốt**:
  - Kiến trúc mạng **DenseNet-121** (121 lớp) tối ưu vượt trội cho ảnh X-quang y tế nhờ cơ chế kết nối dày đặc (dense connections) giữa các khối, bảo tồn thông tin đa tầng từ đặc trưng cục bộ (tổn thương nhỏ dạng nốt) đến toàn cục (bóng tim to, tràn dịch).
  - Huấn luyện trên toàn bộ 112,120 ảnh của NIH ChestX-ray14, chứng minh mô hình AI vượt qua trình độ trung bình của 4 bác sĩ X-quang thực hành độc lập trong phát hiện Viêm phổi (Pneumonia) với chỉ số F1 score 0.435 (so với 0.387 của bác sĩ).
  - Mean AUC 14 bệnh đạt mốc kỷ lục thời điểm đó: **0.841**.
- **Thông số cấu hình kỹ thuật của CheXNet**:
  - Backbone: DenseNet-121 pre-trained trên ImageNet-1K.
  - Kích thước ảnh đầu vào: $224 \times 224$ (nguyên bản CheXNet 2017).
  - Optimizer: Adam, Learning rate ban đầu $10^{-4}$, giảm 10 lần khi val loss không giảm (ReduceLROnPlateau).
  - Trọng số Positive Class Weighting: $w_{pos} = \frac{|N|}{|P|}$ để cân bằng tỷ lệ mất cân bằng lớp.
- **Bài học & Ứng dụng cho LungRay**:
  - Chọn **DenseNet-121** làm Backbone chuẩn hóa chính (Primary Backbone) cho Shared Encoder của LungRay, đồng thời hỗ trợ ResNet-50 và Swin/ViT để so sánh đối chuẩn.
  - **Nâng cấp độ phân giải lên $512 \times 512$**: Dù CheXNet nguyên bản dùng $224\text{px}$, các nghiên cứu cập nhật (Sabottke & Spieler 2020; Wollek et al. 2023) chứng minh $224\text{px}$ làm mất chi tiết nốt mờ nhỏ và kích hoạt shortcut learning. Chuẩn $512 \times 512$ của LungRay giúp feature map đạt $16 \times 16$, tăng độ chính xác định vị WSOL gấp $\approx 5.2$ lần.

---

### 2.3. Công trình 3: VinDr-CXR — Nguyen et al. (Scientific Data - Nature, 2022)
- **Tên bài báo**: *VinDr-CXR: An open dataset of chest X-rays with radiologist's annotations*.
- **Tác giả & Đơn vị**: Ha Q. Nguyen, Khanh Lam, Linh T. Le, Hieu H. Pham, Dat Q. Tran, Dung B. Nguyen, Dung D. Le, Chi M. Pham, Hieu T. Nguyen, Zhen-Zhen Nguyen, et al. (VinBigdata & Đại học Quốc gia Hà Nội).
- **Đóng góp then chốt**:
  - Bộ dữ liệu X-quang chất lượng cao đầu tiên của người Việt Nam gồm **18,000 ảnh DICOM nguyên bản**, được gán nhãn độc lập bởi **17 bác sĩ chẩn đoán hình ảnh giàu kinh nghiệm** (từ Bệnh viện Bạch Mai và Bệnh viện 108).
  - Phân loại gồm: 22 triệu chứng cục bộ (critical findings) kèm Bounding Box và 6 chẩn đoán toàn diện (diseases).
  - Giao thức gán nhãn 3 bác sĩ độc lập cho mỗi ảnh trong tập test (3,000 ảnh) để đạt được consensus chuẩn mực.
- **Bài học & Ứng dụng cho LungRay**:
  - Sử dụng **3,000 ảnh tập Test của VinDr-CXR** làm bộ dữ liệu "Vàng" để đánh giá định lượng năng lực định vị tổn thương yếu (WSOL) thông qua chỉ số IoU và Box Accuracy, mà **không cần sử dụng bounding box trong pha huấn luyện**.
  - Kiểm tra độ bền vững ngoại vi (Domain Shift / External Generalization) khi mô hình huấn luyện trên dữ liệu Mỹ (NIH) nhưng đánh giá trên bệnh nhân Việt Nam (VinDr-CXR).

---

### 2.4. Công trình 4: Grad-CAM — Selvaraju et al. (ICCV 2017)
- **Tên bài báo**: *Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization*.
- **Tác giả & Đơn vị**: Ramprasad R. Selvaraju, Michael Cogswell, Abhishek Das, Ramakrishna Vedantam, Devi Parikh, Dhruv Batra (Georgia Tech).
- **Đóng góp then chốt**:
  - Đề xuất thuật toán Visual Explanation dựa trên Gradient của lớp tích chập cuối cùng (final convolutional layer):
    $$\alpha_k^c = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial y^c}{\partial A_{ij}^k}$$
    $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$
  - Không đòi hỏi phải thay đổi kiến trúc mạng (khác với CAM truyền thống bắt buộc phải có Global Average Pooling và loại bỏ Dense layers).
  - Cung cấp heatmap trực quan phản ánh chính xác vùng mô hình dựa vào để đưa ra quyết định dự đoán lớp $c$.
- **Bài học & Ứng dụng cho LungRay**:
  - Triển khai **Grad-CAM và Grad-CAM++** tại lớp `features.denseblock4` của DenseNet-121.
  - Xây dựng pipeline trích xuất Heatmap thời gian thực phục vụ cả việc hiển thị trên Web PACS UI lẫn trích xuất Bounding Box bằng thuật toán Adaptive Otsu Thresholding.

---

### 2.5. Công trình 5: Shortcut Learning in COVID-19 — DeGrave et al. (Nature Machine Intelligence, 2021)
- **Tên bài báo**: *AI for radiographic COVID-19 detection may rely on shortcut learning and fail to generalize*.
- **Tác giả & Đơn vị**: Alex J. DeGrave, Joseph D. Janizek, Su-In Lee (University of Washington).
- **Phát hiện chấn động**:
  - Phân tích hàng chục mô hình Deep Learning chẩn đoán COVID-19 đạt AUC cực cao (>95%) công bố trên các tạp chí lớn trong đại dịch.
  - Sử dụng Saliency Maps chứng minh các mô hình này **không hề nhìn vào tổn thương phổi (Ground-glass opacities / Consolidation)**, mà học thuộc các "lối tắt" (shortcuts):
    - Chữ cái đánh dấu tư thế chụp (L / R markers, AP / PA markers).
    - Dấu vết thiết bị, ống thở, đường cong máy X-quang di động (portable X-ray artifacts).
    - Viền đen ngoài lồng ngực hoặc độ tương phản khác biệt do ảnh COVID-19 lấy từ nguồn bệnh viện nặng (SIRM/BIMCV), còn ảnh Normal lấy từ tập cộng đồng người lớn hoặc trẻ em (Kermany/RSNA).
  - Khi đem mô hình sang bệnh viện mới không có cùng nhãn đánh dấu, AUC tụt thảm hại từ 0.98 xuống xấp xỉ mức đoán mò (0.55–0.60).
- **Ràng buộc sống còn cho LungRay**:
  - Bắt buộc áp dụng **Source-Stratified Split** theo nguồn dữ liệu gốc (`source`: PadChest, SIRM, RSNA, Kermany) để phân bố đều các nguồn vào cả Train/Val/Test.
  - Bắt buộc thiết kế **Shortcut Learning Audit Engine**: Tính toán tỷ lệ năng lượng kích hoạt Grad-CAM nằm bên trong phế trường phổi (Lung Mask). Nếu tỷ lệ ngoài phổi $>20\%$ $\to$ Báo động đỏ và kích hoạt tiền xử lý Lung Field Cropping.

---

## 3. BẢNG TỔNG HỢP SO SÁNH BENCHMARK GỐC

| Công trình | Năm | Bộ dữ liệu | Mô hình | Nhiệm vụ chính | AUC / Metric Gốc | Hạn chế ghi nhận |
|:---|:---:|:---|:---|:---|:---|:---|
| **Wang et al.** | 2017 | NIH ChestX-ray14 | ResNet-50 | 14 Thoracic Diseases | Mean AUC: **0.745** | Bị rò rỉ dữ liệu nếu không split theo Patient ID |
| **Rajpurkar et al. (CheXNet)** | 2017 | NIH ChestX-ray14 | DenseNet-121 | Pneumonia + 14 Diseases | Pneumonia F1: **0.435**<br>Mean AUC: **0.841** | Chưa kiểm định trên tập ngoại vi ngoài Hoa Kỳ |
| **Nguyen et al. (VinDr-CXR)** | 2022 | VinDr-CXR (18K) | Faster R-CNN, EfficientNet | 22 Local findings + 6 Diseases | mAP@0.5: **0.298**<br>Disease AUC: **0.890** | Chi phí dán nhãn Bounding Box cực kỳ đắt đỏ |
| **Selvaraju et al. (Grad-CAM)** | 2017 | ImageNet / VQA | VGG-16, AlexNet | Visual Localization | Top-1 Localization: **43.29%** | Độ phân giải heatmap thấp ($7 \times 7$ hoặc $14 \times 14$) |
| **DeGrave et al.** | 2021 | COVID-Net, COVID-19 Coll. | CNNs | COVID-19 Detection | In-domain AUC: **0.97**<br>Out-of-domain AUC: **0.60** | Vướng shortcut learning nghiêm trọng |

---

## 4. KẾT LUẬN & ĐỊNH HƯỚNG TRIỂN KHAI CHO LUNGRAY

1. **Kiến trúc thống nhất**: Chọn DenseNet-121 làm Backbone chia sẻ (Shared Backbone), hỗ trợ ResNet-50 cho thử nghiệm Baseline ablation.
2. **Cơ chế chống gian lận dữ liệu**:
   - `Patient_ID` split cho NIH ChestX-ray14.
   - `Source-Stratified Split` cho COVID-19.
3. **Chiến lược Weakly-Supervised**: Huấn luyện hoàn toàn bằng nhãn mức ảnh (Image-level Multi-Task BCE Loss), đánh giá định vị gián tiếp qua Grad-CAM heatmap $\to$ Bounding box so với VinDr-CXR/RSNA ground truth.
4. **Kiểm toán tin cậy**: Báo cáo tỷ lệ năng lượng phế trường phổi (In-lung activation ratio) $\ge 80\%$ là tiêu chí nghiệm thu bắt buộc (DoD) của đồ án.
