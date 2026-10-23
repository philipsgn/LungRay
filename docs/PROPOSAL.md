# ĐỀ CƯƠNG CHI TIẾT ĐỒ ÁN TỐT NGHIỆP
## NỀN TẢNG LUNGRAY: HỆ THỐNG HỖ TRỢ CHẨN ĐOÁN VÀ ĐỊNH VỊ TỔN THƯƠNG PHỔI TỪ ẢNH X-QUANG NGỰC DỰA TRÊN HỌC SÂU VÀ TRÍ TUỆ NHÂN TẠO CÓ GIẢI THÍCH (EXPLAINABLE AI)

---

### 1. LÝ DO CHỌN ĐỀ TÀI

Bệnh lý về phổi và lồng ngực (viêm phổi, lao phổi, tràn dịch màng phổi, xẹp phổi, u phổi...) là nhóm nguyên nhân gây tử vong hàng đầu trên thế giới và tại Việt Nam. X-quang ngực thẳng (Chest X-ray - CXR) là kỹ thuật chẩn đoán hình ảnh phổ biến, chi phí thấp và được chỉ định đầu tay trong hầu hết các quy trình khám chữa bệnh. Tuy nhiên, việc đọc và phân tích phim X-quang lồng ngực đòi hỏi bác sĩ chẩn đoán hình ảnh có chuyên môn cao và kinh nghiệm lâu năm, trong khi tình trạng quá tải tại các bệnh viện tuyến trung ương và sự thiếu hụt nhân lực chuyên môn sâu tại các cơ sở y tế tuyến dưới dẫn đến nguy cơ bỏ sót tổn thương hoặc chẩn đoán muộn.

Trong những năm gần đây, các mô hình học sâu (Deep Learning) đã đạt được hiệu năng ấn tượng trong phân loại ảnh y tế. Tuy nhiên, phần lớn các mô hình mạng nơ-ron tích chập (CNN) hay Vision Transformer (ViT) hoạt động như một “hộp đen” (black-box): chỉ xuất ra xác suất chẩn đoán mà không giải thích được cơ sở thị giác đằng sau kết luận đó. Trong y khoa lâm sàng, việc thiếu tính minh bạch là rào cản lớn nhất khiến bác sĩ không thể tin tưởng ứng dụng hệ thống AI vào hỗ trợ ra quyết định.

Hơn nữa, phần lớn các đồ án sinh viên trước đây chỉ dừng lại ở bài toán phân loại đơn giản, hoặc nếu có trực quan hóa bằng Grad-CAM thì chỉ dừng lại ở bước "đánh giá định tính bằng mắt thường" (qualitative visual check) mà thiếu sự kiểm chứng định lượng xem mô hình thực sự "nhìn đúng vùng bệnh" hay chỉ ngẫu nhiên trùng hợp với đặc trưng nhiễu.

Do đó, đề tài này được đề xuất nhằm phát triển nền tảng **LungRay** — giải quyết trọn vẹn bài toán từ **phân loại đa nhãn** đến **kiểm chứng định lượng vùng tổn thương có giải thích (Explainable AI - XAI)** trên dữ liệu X-quang ngực, với sự đối chiếu thực nghiệm trên bộ dữ liệu người Việt Nam (VinDr-CXR) có tọa độ tổn thương thực tế từ bác sĩ chuyên khoa.

---

### 2. MỤC TIÊU ĐỀ TÀI

#### 2.1. Mục tiêu tổng quát
Xây dựng nền tảng **LungRay** — một hệ thống học sâu hoàn chỉnh có khả năng hỗ trợ phân loại đồng thời 14 bất thường/bệnh lý lồng ngực phổ biến, sàng lọc Lao phổi và phân loại COVID-19 từ ảnh X-quang ngực thẳng theo kiến trúc đa nhiệm (Multi-Task 3-Head), đồng thời tích hợp cơ chế giải thích trực quan (XAI), kiểm toán rủi ro học đường tắt (Shortcut Learning Audit) và đánh giá định lượng độ chính xác của vùng giải thích so với tổn thương thực tế.

#### 2.2. Mục tiêu cụ thể
1. **Xử lý & Chuẩn hóa dữ liệu:** Xây dựng pipeline tiền xử lý ảnh X-quang lồng ngực, giải quyết bài toán rò rỉ dữ liệu (data leakage) theo mức bệnh nhân (patient-level cho NIH), phân chia tầng theo nguồn ảnh gốc (stratified split by source cho COVID-19) và xử lý hiện tượng mất cân bằng nhãn nghiêm trọng (class imbalance).
2. **Huấn luyện mô hình phân loại đa nhãn (Head A):** Huấn luyện và tối ưu hóa các kiến trúc mạng hiện đại (DenseNet-121, ResNet-50, Vision Transformer / Swin Transformer) với hàm mất mát chuyên biệt (Focal Loss, Asymmetric Loss) trên NIH ChestX-ray14 ($C=14$).
3. **Huấn luyện mô hình sàng lọc Lao phổi (Head B):** Mở rộng phổ bệnh trong cùng chuyên khoa hô hấp bằng một nhiệm vụ phân loại nhị phân (Tuberculosis/Normal) trên bộ Tuberculosis (TB) Chest X-ray Database, dùng chung backbone với Head A theo kiến trúc Multi-Task Learning (Masked Multi-Task).
4. **Huấn luyện mô hình sàng lọc & phân loại COVID-19 (Head C):** Tích hợp nhiệm vụ phân loại 4 lớp (COVID-19 / Normal / Lung Opacity / Viral Pneumonia) trên bộ COVID-19 Radiography Database, áp dụng quy trình kiểm soát rủi ro khoa học nghiêm ngặt: chia tập theo nguồn ảnh gốc để ngăn ngừa học thuộc nguồn và thực hiện kiểm toán giải thích.
5. **Định vị tổn thương có giám sát yếu (WSOL) qua XAI:** Áp dụng kỹ thuật Grad-CAM/Grad-CAM++ để trích xuất bản đồ kích hoạt (Activation Heatmap), binarize bản đồ nhiệt để tạo mặt nạ tổn thương và đo lường định lượng độ trùng khớp (IoU) với bounding box chuyên gia trên tập kiểm thử VinDr-CXR (chính) và RSNA Pneumonia Detection (bổ sung, riêng nhãn Pneumonia). Nhãn Tuberculosis và COVID-19 không có bounding box công khai phù hợp nên đánh giá Grad-CAM ở mức định tính.
6. **Kiểm toán học đường tắt (Shortcut Learning Audit cho Head C):** Kiểm tra Grad-CAM trên các ca dương tính COVID-19 nhằm xác thực vùng chú ý của mô hình tập trung đúng nhu mô phổi thay vì các đặc trưng ngoại lai/ký tự/watermark nguồn ảnh.
7. **Kiểm định tổng quát hóa ngoại vi (External Generalization):** Đánh giá Head A trên tập CheXpert-small-v1 (bệnh viện khác NIH) để đo mức độ suy giảm hiệu năng khi chuyển sang phân bố dữ liệu mới (domain shift) — chỉ dùng để kiểm thử, không dùng để huấn luyện.
8. **Phát triển ứng dụng thực nghiệm (Demo Prototype):** Xây dựng ứng dụng web giao diện thân thiện, cho phép tải ảnh X-quang, hiển thị kết quả chẩn đoán cả 3 head (14 nhãn NIH, Lao phổi, COVID-19) kèm bản đồ nhiệt trực quan hóa vùng tổn thương hỗ trợ bác sĩ tham khảo trong thời gian $\le 2$ giây.

#### 2.3. Phát biểu bài toán kỹ thuật (Problem Formulation)
Bài toán được mô hình hóa thành **hệ thống đa nhiệm 3 nhánh (Multi-Task 3-Head Framework)** dùng chung 1 backbone biểu diễn đặc trưng (shared encoder):

* **Không gian đầu vào (Input Space):**
  $$X \in \mathbb{R}^{H \times W \times C_{in}}$$
  Là ảnh chụp X-quang lồng ngực tư thế thẳng (ưu tiên chuẩn Posteroanterior - PA view), được tiền xử lý và chuẩn hóa kích thước cố định ($H = W = 512$, số kênh $C_{in} = 3$ hoặc $1$). Kích thước $512\text{px}$ là chuẩn mực lâm sàng tối ưu, tránh suy giảm vi tổn thương (Sabottke & Spieler, 2020) và hỗ trợ trích xuất bản đồ kích hoạt không gian $16 \times 16$ cho WSOL.

* **Không gian đầu ra (Output Spaces) theo từng nhánh:**
  1. **Head A — Multi-Label Thoracic Disease ($C = 14$):**
     $$Y_A = [y_1, y_2, \dots, y_{14}]^T \in \{0, 1\}^{14}$$
     Vector nhị phân đa nhãn đại diện cho sự hiện diện ($1$) hoặc vắng mặt ($0$) của 14 bất thường/bệnh lý lồng ngực trên NIH ChestX-ray14. Xác suất dự đoán $\hat{p}_c = \sigma(z_{A, c})$, quyết định nhị phân qua ngưỡng động $\hat{y}_c = \mathbb{I}(\hat{p}_c \ge \tau_c)$.
  2. **Head B — Tuberculosis Screening (Nhị phân):**
     $$y_B \in \{0, 1\} \quad (0: \text{Normal}, 1: \text{Tuberculosis})$$
     Xác suất dự đoán $\hat{p}_{TB} = \sigma(z_B)$ từ Tuberculosis (TB) Chest X-ray Database.
  3. **Head C — COVID-19 Screening (4 lớp):**
     $$y_C \in \{0, 1, 2, 3\} \quad (0: \text{Normal}, 1: \text{COVID-19}, 2: \text{Lung Opacity}, 3: \text{Viral Pneumonia})$$
     Phân phối xác suất qua hàm Softmax: $\hat{P}_C = \text{Softmax}(z_C) \in [0, 1]^4$ từ COVID-19 Radiography Database.

* **Cơ chế Masked Multi-Task Learning:**
  Mỗi mẫu hoặc mini-batch từ nguồn dữ liệu $k \in \{A, B, C\}$ chỉ tính hàm mất mát và cập nhật gradient qua classifier head tương ứng $\text{Head}_k$ và shared backbone:
  $$\mathcal{L} = \mathbb{I}_{k=A} \cdot \mathcal{L}_A + \mathbb{I}_{k=B} \cdot \mathcal{L}_B + \mathbb{I}_{k=C} \cdot \mathcal{L}_C$$

* **Nhiệm vụ định vị giải thích có giám sát yếu (WSOL) & Kiểm toán XAI:**
  Chỉ với nhãn mức ảnh trong quá trình huấn luyện, mô hình trích xuất bản đồ kích hoạt trực quan cho lớp bệnh $c$:
  $$M_c = \text{Grad-CAM}(f_\theta, X, c) \in [0, 1]^{H \times W}$$
  - **Grounding Validation (Head A):** Bản đồ $M_c$ được phân ngưỡng nhị phân thành mặt nạ dự đoán $\hat{B}_c = \mathbb{I}(M_c \ge \tau_{mask})$. Độ chính xác định vị được đánh giá định lượng qua chỉ số **Intersection over Union (IoU)** với bounding box ground-truth $B_c^{GT}$ từ tập dữ liệu VinDr-CXR và RSNA Pneumonia Detection:
    $$\text{IoU}(\hat{B}_c, B_c^{GT}) = \frac{|\hat{B}_c \cap B_c^{GT}|}{|\hat{B}_c \cup B_c^{GT}|}$$
  - **Shortcut Learning Audit (Head C):** Kiểm tra tỷ lệ kích hoạt của $M_{\text{COVID}}$ tập trung trong vùng mặt nạ phế trường phổi $P_{\text{lung}}$ so với vùng biên/ký hiệu góc ảnh:
    $$\text{Lung-Activation-Ratio} = \frac{\sum_{(x,y) \in P_{\text{lung}}} M_{\text{COVID}}(x,y)}{\sum_{(x,y)} M_{\text{COVID}}(x,y)}$$
    Đảm bảo mô hình phân loại dựa vào tổn thương kính mờ nhu mô phổi thật sự chứ không học thuộc watermark hay viền khung chụp.

---

### 3. ĐỐI TƯỢNG VÀ PHẠM VI NGHIÊN CỨU

#### 3.1. Đối tượng nghiên cứu
* Ảnh chụp X-quang lồng ngực người lớn dạng 2D (Posteroanterior - PA và Anteroposterior - AP view).
* Các mô hình học sâu nhận dạng ảnh y tế (Convolutional Neural Networks: DenseNet, ResNet; Vision Transformers: ViT, Swin-Transformer).
* Các kỹ thuật giải thích mô hình (Explainable AI): Grad-CAM, Grad-CAM++, Score-CAM.
* 14 tổn thương và bệnh lý lồng ngực phổ biến (Head A), bệnh Lao phổi (Head B), và nhóm bệnh COVID-19 / Viêm phổi mờ phổi (Head C):

| STT | Tên Tiếng Anh | Tên Tiếng Việt | Nhóm nhiệm vụ | Phân loại chuyên môn |
|:---:|:---|:---|:---:|:---|
| 1 | **Atelectasis** | Xẹp phổi | Head A | Dấu hiệu hình thái (Finding) |
| 2 | **Cardiomegaly** | Bóng tim to | Head A | Dấu hiệu hình thái (Finding) |
| 3 | **Effusion** (Pleural Effusion) | Tràn dịch màng phổi | Head A | Dấu hiệu hình thái (Finding) |
| 4 | **Infiltration** | Thâm nhiễm mô kẽ/phế nang | Head A | Dấu hiệu hình thái (Finding) |
| 5 | **Mass** | Khối mờ lớn ($\ge 3$ cm) | Head A | Dấu hiệu hình thái (Finding) |
| 6 | **Nodule** | Nốt mờ nhỏ ($< 3$ cm) | Head A | Dấu hiệu hình thái (Finding) |
| 7 | **Pneumonia** | Viêm phổi | Head A | Chẩn đoán bệnh lý (Disease) |
| 8 | **Pneumothorax** | Tràn khí màng phổi | Head A | Dấu hiệu cấp cứu (Finding/Disease) |
| 9 | **Consolidation** | Đông đặc nhu mô phổi | Head A | Dấu hiệu hình thái (Finding) |
| 10 | **Edema** (Pulmonary Edema) | Phù phổi | Head A | Dấu hiệu hình thái (Finding) |
| 11 | **Emphysema** | Khí phế thũng | Head A | Bệnh lý mạn tính (Disease) |
| 12 | **Fibrosis** | Xơ hóa phổi | Head A | Dấu hiệu hình thái (Finding) |
| 13 | **Pleural Thickening** | Dày màng phổi | Head A | Dấu hiệu hình thái (Finding) |
| 14 | **Hernia** | Thoát vị hoành | Head A | Bất thường giải phẫu (Disease) |
| 15 | **Tuberculosis** | Lao phổi | Head B | Bệnh lý truyền nhiễm hô hấp (Infection) |
| 16 | **COVID-19** | Viêm đường hô hấp cấp SARS-CoV-2 | Head C | Bệnh dịch truyền nhiễm cấp tính (Pandemic) |
| 17 | **Lung Opacity / Viral Pneumonia** | Mờ phổi / Viêm phổi virus | Head C | Dấu hiệu hình thái & nhiễm trùng |

#### 3.2. Phạm vi và Giới hạn nghiên cứu
* **Về loại ảnh:** Giới hạn ở ảnh X-quang ngực phẳng 2D (không mở rộng sang cắt lớp vi tính CT Scanner hoặc cộng hưởng từ MRI).
* **Về dữ liệu:** 
  * Sử dụng **NIH ChestX-ray14** làm bộ dữ liệu huấn luyện chính cho Head A (14 nhãn).
  * Sử dụng **Tuberculosis (TB) Chest X-ray Database** làm bộ dữ liệu huấn luyện phụ cho Head B (nhị phân TB/Normal).
  * Sử dụng **COVID-19 Radiography Database** (~21.165 ảnh) làm bộ dữ liệu huấn luyện cho Head C (4 lớp). **Quy định bắt buộc**: Thực hiện Stratified Split theo nguồn ảnh gốc (PadChest, SIRM, RSNA, Kermany) để ngăn ngừa rò rỉ nguồn và tiến hành Shortcut Learning Audit bằng Grad-CAM (khắc phục rủi ro được chỉ ra bởi DeGrave et al., 2021).
  * Sử dụng tập kiểm thử độc lập **VinDr-CXR** (chứa bounding box từ bác sĩ Việt Nam) làm nguồn WSOL/IoU-grounding chính, và **RSNA Pneumonia Detection** (có bounding box) làm nguồn bổ sung riêng cho nhãn Pneumonia.
  * Sử dụng **CheXpert-small-v1** làm tập kiểm định tổng quát hóa ngoại vi (external generalization test) cho Head A — chỉ dùng để test, không dùng để train, do khác biệt taxonomy nhãn với NIH.
  * *Bộ dữ liệu MIMIC-CXR:* Được khảo sát đối chiếu tài liệu lý thuyết, không tải toàn bộ dung lượng lớn (~570GB) về huấn luyện trong giới hạn tài nguyên của đồ án.
* **Về vai trò ứng dụng:** Hệ thống đóng vai trò hỗ trợ tham khảo (Clinical Decision Support System - CDSS), phục vụ sàng lọc sơ bộ, không thay thế chẩn đoán pháp lý của bác sĩ.
* **Về vai trò ứng dụng:** Hệ thống đóng vai trò hỗ trợ tham khảo (Clinical Decision Support System - CDSS), phục vụ sàng lọc sơ bộ, không thay thế chẩn đoán pháp lý của bác sĩ.

---

### 4. TỔNG QUAN TÌNH HÌNH NGHIÊN CỨU

#### 4.1. Nghiên cứu trên thế giới
* **Các bộ dữ liệu mở:** Năm 2017, Wang et al. (NIH Clinical Center) công bố bộ dữ liệu *ChestX-ray14* với 112.120 ảnh, mở đường cho kỷ nguyên ứng dụng deep learning quy mô lớn vào ảnh X-quang. Sau đó, Stanford giới thiệu *CheXpert* (2019) với quy trình trích xuất nhãn có độ tin cậy cao và nhãn bất định (uncertainty labels). MIT và Beth Israel Deaconess công bố *MIMIC-CXR* (2019) kết hợp ảnh với báo cáo lâm sàng tự do.
* **Kiến trúc mô hình:** Rajpurkar et al. (2017) công bố *CheXNet*, sử dụng DenseNet-121 đạt AUC vượt trội trên nhãn Viêm phổi. Các nghiên cứu sau đó phát triển theo hướng áp dụng EfficientNet, ResNeSt và gần đây là Vision Transformers (ViT, Swin Transformer) nhằm tận dụng khả năng mô hình hóa mối quan hệ không gian tầm xa (long-range dependencies) giữa các thùy phổi.
* **Explainable AI trong y tế:** Kỹ thuật Grad-CAM (Selvaraju et al., 2017) đã trở thành tiêu chuẩn de-facto trong hiển thị heatmap của mạng CNN. Tuy nhiên, các bài báo gần đây (như Arun et al., 2021 trên *Nature Machine Intelligence*) chỉ ra rằng heatmap của Grad-CAM có thể xuất hiện sai lệch và không phản ánh đúng vị trí bệnh lý nếu không được kiểm chứng định lượng với bounding box hoặc segmentation mask thực tế.

#### 4.2. Nghiên cứu tại Việt Nam
* Viện Nghiên cứu Dữ liệu lớn (VinBigData) đã công bố bộ dữ liệu *VinDr-CXR* (Nguyen et al., 2022) gồm 18.000 ảnh X-quang được gán nhãn chi tiết bởi các bác sĩ chẩn đoán hình ảnh hàng đầu tại Việt Nam, đặc biệt cung cấp bounding box tọa độ thực tế cho các tổn thương. Đây là tiền đề cực kỳ giá trị để thực hiện kiểm chứng định lượng XAI trên đặc thù hình thái bệnh học của người Việt.

#### 4.3. Khoảng trống nghiên cứu đồ án hướng đến
1. Phần lớn các đồ án sinh viên chỉ dừng ở việc huấn luyện phân loại và hiển thị heatmap định tính (chụp ảnh minh họa). Đề tài này giải quyết bài toán: **Đo đạc định lượng mức độ trùng khớp giữa vùng chú ý của AI và tổn thương thực tế bằng IoU trên tập VinDr-CXR**.
2. Thực nghiệm so sánh khách quan giữa mạng tích chập sâu (DenseNet/ResNet) và kiến trúc Transformer (ViT) trên cùng một pipeline xử lý dữ liệu và tiêu chí đánh giá.

---

### 5. PHƯƠNG PHÁP NGHIÊN CỨU VÀ GIẢI PHÁP KỸ THUẬT

#### 5.1. Chiến lược dữ liệu (Data Strategy)
| Tên Dataset | Số lượng ảnh | Vai trò trong đồ án | Ghi chú kỹ thuật |
|:---|:---:|:---|:---|
| **NIH ChestX-ray14** | 112.120 ảnh | **Train Head A (14 nhãn) & Benchmark** | Chia train/val/test theo Patient ID (70/10/20). Cần Bbox? KHÔNG (chỉ cần nhãn mức ảnh). |
| **Tuberculosis (TB) Chest X-ray Database** | 3.500 TB + 3.500 Normal | **Train Head B (nhị phân TB/Normal)** | Kaggle: `tawsifurrahman/tuberculosis-tb-chest-xray-dataset`. Chia bằng random stratified split (không có Patient_ID công khai). Cần Bbox? KHÔNG. |
| **COVID-19 Radiography Database** | ~21.165 ảnh | **Train Head C (4 lớp: COVID/Normal/Lung Opacity/Viral Pneumonia)** | ⚠️ **Bắt buộc**: Stratified Split theo nguồn ảnh gốc (PadChest, SIRM, RSNA, Kermany) + Shortcut Learning Audit bằng Grad-CAM (DeGrave et al., 2021). Cần Bbox? KHÔNG. |
| **VinDr-CXR** | ~3.000 ảnh test có BBox | **External Validation & WSOL Grounding (chính)** | Dữ liệu người Việt, đo đạc chỉ số IoU giữa Heatmap và Bounding Box cho 8 lớp bệnh có ground-truth. |
| **RSNA Pneumonia Detection** | Tập test có BBox | **WSOL Grounding (bổ sung, riêng Pneumonia)** | Bounding box thật cho nhãn Pneumonia, bổ trợ cho VinDr-CXR. |
| **CheXpert-small-v1** | Đã tải sẵn | **External Generalization Test (Head A)** | Test-only, KHÔNG train, do taxonomy nhãn khác NIH (cần xử lý nhãn uncertainty riêng nếu dùng cho phân tích sâu hơn). Không có Bbox. |

> **Nguyên tắc phân vai trò Bounding Box:** Bbox không cần thiết để huấn luyện classifier (đúng bản chất "Weakly-Supervised" của WSOL — mô hình học vị trí tổn thương chỉ từ nhãn mức ảnh). Bbox chỉ bắt buộc đối với các bộ dữ liệu đóng vai trò **đánh giá định lượng IoU** (VinDr-CXR, RSNA). Với Head B (TB) và Head C (COVID-19), do không có bounding box công khai phù hợp, phần XAI được đánh giá Grad-CAM ở mức định tính; riêng Head C bắt buộc thực hiện thêm bước **Shortcut Learning Audit** để kiểm tra tính trung thực của vùng kích hoạt.

#### 5.2. Tiền xử lý và Xử lý mất cân bằng dữ liệu
1. **Kiểm soát rò rỉ dữ liệu (No Data Leakage):** Phân chia tập dữ liệu nghiêm ngặt theo `Patient_ID` (đối với NIH). Với TB dataset dùng random stratified split. Với COVID-19 Radiography Database, **bắt buộc phân tầng theo nguồn ảnh gốc** (source-stratified split) để đảm bảo mô hình không học thuộc đặc trưng của máy chụp/nguồn cấp.
2. **Chuẩn hóa ảnh:** Chuyển đổi định dạng, resize về kích thước chuẩn cố định $512 \times 512$ cho cả 3 heads và test sets, chuẩn hóa mean/std theo ImageNet.
3. **Tăng cường dữ liệu có kiểm soát (Medical Data Augmentation):** Áp dụng xoay nhẹ ($\pm 10^\circ$), lật ngang (horizontal flip), biến đổi nhẹ độ tương phản/độ sáng. Tuyệt đối không lật dọc (vertical flip) vì vi phạm cấu trúc giải phẫu lồng ngực.
4. **Giải quyết mất cân bằng lớp:** Do các bệnh như Hernia, Pneumothorax có tỷ lệ xuất hiện cực thấp ($< 2\%$), sử dụng **Focal Loss** kết hợp **Positive Class Weighting**:
   $$FL(p_t) = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$

#### 5.3. Kiến trúc mô hình đề xuất (Multi-Task 3-Head Learning)
* **Backbone dùng chung (Shared Encoder):** DenseNet-121 và ResNet-50 pretrained trên ImageNet (so sánh thêm Vision Transformer ViT-B/16 hoặc Swin-T để đối chiếu khả năng trích xuất đặc trưng toàn cục).
* **Head A (NIH ChestX-ray14):** Linear Layer ($14$ đầu ra) + Sigmoid Activation (Multi-label).
* **Head B (Tuberculosis):** Linear Layer ($1$ đầu ra nhị phân) + Sigmoid Activation.
* **Head C (COVID-19 Radiography):** Linear Layer ($4$ đầu ra) + Softmax Activation (Multiclass).
* **Chiến lược Masked Multi-Task:** Mỗi batch chỉ tính loss và backprop qua head tương ứng với nguồn dữ liệu của batch đó:
  - Batch từ NIH $\to$ tính Binary Cross Entropy / Focal Loss qua Head A.
  - Batch từ TB $\to$ tính BCE qua Head B.
  - Batch từ COVID-19 $\to$ tính Cross Entropy qua Head C.
  Tránh triệt để việc xung đột taxonomy nhãn giữa 3 nguồn dữ liệu độc lập.
* **Weighted/Balanced Batch Sampling:** Do quy mô dữ liệu chênh lệch lớn (NIH: 112K ảnh, COVID: ~21K ảnh, TB: 7K ảnh), áp dụng cơ chế lấy mẫu theo tỷ lệ cố định (ví dụ: 60% NIH, 25% COVID, 15% TB trong mỗi epoch) để ngăn ngừa hiện tượng "Task Starvation" khiến các head nhỏ bị áp đảo.
* **Training Policy:** Chiến lược 2 giai đoạn:
  * Giai đoạn 1: Đóng băng (freeze) backbone, chỉ huấn luyện 3 classifier head với learning rate $10^{-3}$.
  * Giai đoạn 2: Mở khóa toàn bộ mạng, fine-tune toàn diện với learning rate nhỏ $10^{-5}$ đi kèm Cosine Annealing Learning Rate Scheduler.

#### 5.4. Quy chuẩn định lượng XAI, Đo lường IoU & Shortcut Audit
1. **Trích xuất Heatmap:** Tính gradient của score dự đoán lớp $c$ đối với feature map của lớp tích chập cuối cùng để tạo bản đồ Grad-CAM $M_c$.
2. **Nhị phân hóa (Binarization):** Tạo mặt nạ nhị phân từ heatmap liên tục bằng ngưỡng thích nghi:
   $$\hat{B}_c(x, y) = \begin{cases} 1 & \text{nếu } M_c(x, y) \ge \alpha \cdot \max(M_c) \\ 0 & \text{ngược lại} \end{cases}$$
   với hệ số $\alpha \in [0.2, 0.4]$ được hiệu chỉnh thực nghiệm.
3. **Đo độ trùng khớp IoU:** Tính IoU giữa mặt nạ $\hat{B}_c$ và Bounding box chuẩn $B_c^{GT}$ trên tập VinDr-CXR (8 lớp bệnh) và RSNA Pneumonia Detection (riêng Pneumonia).
4. **Kiểm toán rủi ro học đường tắt (Shortcut Learning Audit cho Head C):**
   - Chạy Grad-CAM trên toàn bộ các ca dự đoán dương tính COVID-19.
   - Phân tích vị trí vùng kích hoạt: Kiểm tra mức độ tập trung trong phế trường phổi so với viền mép ảnh, góc đặt dấu chỉ thị hoặc watermark.
   - Đảm bảo tỷ lệ kích hoạt trong phổi đạt $\ge 80\%$, chứng minh mô hình phân loại dựa trên đặc trưng tổn thương thực tế chứ không lợi dụng shortcut từ nguồn ảnh.

#### 5.5. Tiêu chuẩn đánh giá và Tiêu chí nghiệm thu (Acceptance Criteria)
* **Chỉ số phân loại (Head A - NIH):**
  * **Macro AUC-ROC:** Trung bình AUC trên 14 nhãn đạt $\ge 0.82$ (báo cáo kèm Bootstrap CI riêng cho các lớp hiếm như Hernia, Fibrosis do cỡ mẫu nhỏ).
  * **Macro F1-Score:** Đạt $\ge 0.45$ (mức tiêu chuẩn đối với bài toán mất cân bằng nhãn y tế đa nhãn 14 lớp).
* **Chỉ số phân loại (Head B - Tuberculosis):**
  * **AUC-ROC:** Đạt $\ge 0.90$ (mục tiêu tối ưu $\ge 0.95$).
* **Chỉ số phân loại (Head C - COVID-19):**
  * **Macro AUC-ROC:** Đạt $\ge 0.92$.
  * **Macro F1-Score:** Đạt $\ge 0.85$ (cho 4 lớp phân loại).
* **Chỉ số định vị giải thích (WSOL):**
  * **Mean IoU:** Đạt $\ge 0.35$ trên các mẫu dự đoán dương tính đúng (True Positives) có bounding box, đo trên VinDr-CXR (8 lớp) và RSNA Pneumonia Detection (riêng Pneumonia).
  * Head B (TB) và Head C (COVID): đánh giá Grad-CAM định tính.
* **Shortcut Learning Audit (Head C):**
  * Bản đồ nhiệt Grad-CAM tập trung đúng phế trường phổi, không bị lệch sang viền hoặc watermark nguồn ảnh.
* **Chỉ số tổng quát hóa ngoại vi (External Generalization):**
  * AUC của Head A trên CheXpert-small-v1 không suy giảm quá 0.10 so với AUC trên NIH test set.
* **Hiệu năng hệ thống (Web Demo):**
  * Thời gian phản hồi dự đoán (cả 3 head) + sinh heatmap $\le 2$ giây/ảnh.

---

### 6. Ý NGHĨA KHOA HỌC VÀ THỰC TIỄN

* **Ý nghĩa khoa học:**
  * Cung cấp đánh giá thực nghiệm đa chiều giữa hai trường phái kiến trúc (CNN vs Vision Transformer) trên bài toán phân loại ảnh y tế đa nhãn và đa nhiệm phức tạp.
  * Đóng góp quy trình đánh giá định lượng chất lượng của Explainable AI kết hợp quy trình kiểm toán học đường tắt (Shortcut Learning Audit), góp phần xây dựng các hệ thống AI y tế có thể kiểm chứng được (Verifiable & Trustworthy AI).
* **Ý nghĩa thực tiễn:**
  * Hỗ trợ sàng lọc sơ bộ đồng thời các bệnh lý lồng ngực phổ biến, lao phổi và COVID-19 tại các phòng khám, bệnh viện tuyến cơ sở thiếu bác sĩ chuyên khoa chẩn đoán hình ảnh.
  * Giảm tải áp lực cho bác sĩ đọc phim trong các ca trực đông bệnh nhân, đóng vai trò như một ý kiến tham vấn thứ hai (second opinion) tin cậy với bằng chứng thị giác rõ ràng.

---

### 7. KẾ HOẠCH THỰC HIỆN CHI TIẾT (16 TUẦN)

| Giai đoạn | Tuần | Nội dung công việc cụ thể | Sản phẩm / Kết quả bàn giao |
|:---|:---:|:---|:---|
| **Phase 1: Chuẩn bị & Đề cương** | 1–2 | • Khảo sát tài liệu, nghiên cứu 5 bài báo nền tảng.<br>• Thiết lập môi trường PyTorch, Git, GPU Colab/Kaggle.<br>• Hoàn thiện đề cương chi tiết bảo vệ đề tài (Multi-Task 3-Head). | • Đề cương chi tiết được duyệt.<br>• Repository mã nguồn chuẩn hóa. |
| **Phase 2: Xử lý Dữ liệu** | 3–4 | • Tải tập dữ liệu NIH ChestX-ray14, TB Database, COVID-19 Radiography, VinDr-CXR, RSNA, CheXpert-small.<br>• Thực hiện EDA, trích xuất metadata nguồn ảnh gốc của COVID-19 dataset.<br>• Viết script chia train/val/test theo Patient ID (NIH) và Stratified Split theo nguồn (COVID-19).<br>• Xây dựng DataLoader hỗ trợ Weighted Batch Sampling giữa 3 task. | • Báo cáo phân tích dữ liệu EDA.<br>• Bộ file chỉ mục phân chia (`patient_splits.csv`, `tb_splits.csv`, `covid_splits.csv`).<br>• Module DataLoader multi-task kiểm thử hoàn chỉnh. |
| **Phase 3: Baseline Model** | 5–6 | • Xây dựng pipeline huấn luyện Multi-Task 3-Head (DenseNet-121 / ResNet-50).<br>• Cấu hình hàm mất mát riêng cho từng head và optimizer AdamW.<br>• Huấn luyện 20–30 epochs với Masked Backpropagation.<br>• Đánh giá AUC-ROC sơ bộ cho cả 3 head. | • Model checkpoint baseline multi-task.<br>• Đường cong huấn luyện (Loss, AUC riêng từng head).<br>• Bảng kết quả AUC sơ bộ (Head A $\ge 0.80$, Head B $\ge 0.90$, Head C $\ge 0.90$). |
| **Phase 4: Cải tiến & So sánh** | 7–9 | • Triển khai Focal Loss & Class Weighting cho Head A xử lý mất cân bằng.<br>• Huấn luyện và fine-tune mô hình Vision Transformer (ViT / Swin-T).<br>• Tối ưu siêu tham số và ngưỡng phân loại $\tau_c$ theo Youden's J statistic.<br>• So sánh toàn diện hiệu năng CNN vs ViT. | • Checkpoint mô hình tối ưu nhất (`best_model.pth`).<br>• Bảng so sánh chi tiết hiệu năng các kiến trúc.<br>• Bảng ngưỡng quyết định tối ưu $\tau_c$. |
| **Phase 5: Tích hợp XAI, Đo đạc IoU & Shortcut Audit** | 10–11 | • Hiện thực thuật toán Grad-CAM và Grad-CAM++.<br>• Thiết lập hàm binarization heatmap thích nghi.<br>• Chạy kiểm thử trên tập VinDr-CXR và RSNA Pneumonia có bounding box để tính IoU.<br>• Thực hiện kiểm toán Shortcut Learning Audit trên Head C (COVID-19).<br>• Kiểm định ngoại vi Head A trên CheXpert-small-v1. | • Module sinh bản đồ nhiệt Grad-CAM.<br>• Báo cáo định lượng độ chính xác giải thích (IoU).<br>• Báo cáo kiểm toán rủi ro Shortcut Learning cho Head C.<br>• Báo cáo tổng quát hóa ngoại vi CheXpert. |
| **Phase 6: Xây dựng Ứng dụng Demo** | 12–13 | • Xây dựng Web App giao diện y tế hiện đại hỗ trợ cả 3 head chẩn đoán.<br>• Tích hợp pipeline suy luận ảnh và render heatmap trực tiếp.<br>• Tối ưu thời gian xử lý ($\le 2$ giây/ảnh) và kiểm thử người dùng. | • Ứng dụng Web Demo hoạt động hoàn chỉnh. |
| **Phase 7: Viết Báo cáo & Bảo vệ** | 14–16 | • Tổng hợp kết quả thực nghiệm, viết báo cáo tốt nghiệp 40–50 trang.<br>• Chuẩn bị slide thuyết trình, video demo.<br>• Bảo vệ trước Hội đồng chấm Đồ án. | • Cuốn báo cáo tốt nghiệp hoàn chỉnh.<br>• Slide, Poster và Video demo bảo vệ. |

---

### 8. SẢN PHẨM BÀN GIAO CỦA ĐỒ ÁN

1. **Báo cáo chuyên môn:** Báo cáo đồ án tốt nghiệp bản in và PDF theo quy chuẩn của Khoa/Trường.
2. **Mã nguồn hệ thống:** Mã nguồn toàn bộ pipeline (Data Loader multi-task, Training Loop 3-head, Evaluation, Grad-CAM, Shortcut Audit, Web App) được tổ chức khoa học, có tài liệu README hướng dẫn cài đặt và tái tạo kết quả.
3. **Mô hình học máy:** Các file trọng số mô hình đã huấn luyện tối ưu (`best_checkpoint.pth`), kèm bảng thông số siêu tham số và kết quả đo lường 3 head.
4. **Báo cáo thực nghiệm XAI & Audit:** Bảng kết quả định lượng IoU trên tập kiểm thử VinDr-CXR và RSNA, kèm báo cáo kiểm toán Shortcut Learning Audit trên COVID-19, minh chứng tính minh bạch và độ tin cậy khoa học.
5. **Ứng dụng Demo (Web App):** Ứng dụng web cho phép người dùng upload ảnh X-quang, nhận danh sách xác suất bệnh (14 nhãn NIH, Lao phổi, COVID-19) và hiển thị trực quan bản đồ nhiệt vùng tổn thương tương ứng trong $\le 2$ giây.
6. **Tài liệu thuyết trình:** Slide báo cáo, Poster tóm tắt và Video ghi hình quy trình hoạt động của hệ thống.

---

### 9. TÀI LIỆU THAM KHẢO

1. **Wang, X., Peng, Y., Lu, L., Lu, Z., Bagheri, M., & Summers, R. M.** (2017). ChestX-ray8: Hospital-scale chest X-ray database and benchmarks on weakly-supervised classification and localization of common thorax diseases. *IEEE CVPR*, 2097–2106.
2. **Rajpurkar, P., Irvin, J., Zhu, K., Yang, B., Mehta, H., Duan, T., ... & Ng, A. Y.** (2017). CheXNet: Radiologist-level pneumonia detection on chest X-rays with deep learning. *arXiv preprint arXiv:1711.05225*.
3. **Irvin, J., Rajpurkar, P., Ko, M., Yu, Y., Ciurea-Ilcus, S., Chute, C., ... & Ng, A. Y.** (2019). CheXpert: A large chest radiograph dataset with uncertainty labels and expert comparison. *AAAI Conference on Artificial Intelligence*, 33(01), 590–597.
4. **Nguyen, H. Q., Lam, K., Le, L. T., Pham, H. H., Tran, D. Q., Nguyen, D. B., ... & Vu, V.** (2022). VinDr-CXR: An open dataset of chest X-rays with radiologist's annotations. *Scientific Data*, 9(1), 429.
5. **Selvaraju, R. R., Cogswell, M., Das, A., Vedaldi, A., Parikh, D., & Batra, D.** (2017). Grad-CAM: Visual explanations from deep networks via gradient-based localization. *IEEE ICCV*, 618–626.
6. **Dosovitskiy, A., Beyer, L., Kolesnikov, A., Weissenborn, D., Zhai, X., ... & Houlsby, N.** (2021). An image is worth 16x16 words: Transformers for image recognition at scale. *ICLR*.
7. **Arun, N., Gaw, N., Singh, P., Chang, K., Aggarwal, M., Chen, B., ... & Kalpathy-Cramer, J.** (2021). Assessing the trustworthiness of saliency maps for localizing abnormalities in medical imaging. *Nature Machine Intelligence*, 3(1), 28–34.
8. **DeGrave, A. J., Janizek, J. D., & Lee, S. I.** (2021). AI for radiographic COVID-19 detection selects shortcuts over signal. *Nature Machine Intelligence*, 3(7), 610–619. *(Cơ sở lý thuyết bắt buộc thực hiện Stratified Split theo nguồn ảnh gốc và quy trình Shortcut Learning Audit bằng Grad-CAM cho Head C nhằm đảm bảo tính trung thực khoa học.)*
