# 🛡️ THE 9 INVIOLABLE CONSTRAINTS OF LUNGRAY CADX
## Mã Quy Chuẩn: RULE-01-CORE-CONSTRAINTS
## Dự án: Nền tảng Phân tích & Định vị Tổn thương Phổi Đa nhiệm LungRay
## Áp dụng cho: Mọi Agent, Developer, và Quá trình Thực thi

---

### 1. NGUYÊN TẮC CỐT LÕI
9 Ràng buộc dưới đây là các chuẩn mực y tế, toán học và kỹ thuật phần mềm **BẤT BIẾN** của dự án LungRay. Mọi đề xuất, tái cấu trúc hoặc sửa đổi mã nguồn vi phạm dù chỉ một ràng buộc đều bị **REJECT NGAY LẬP TỨC**.

---

### 2. CHI TIẾT 9 RÀNG BUỘC SỐNG CÒN

#### 🔴 Ràng buộc 1: Kiến trúc Đa nhiệm 3-Head Độc lập & Pre-processing Gate
- Sử dụng duy nhất **1 Shared Encoder Backbone** (DenseNet-121 làm kiến trúc chuẩn cho Edge/PACS, hoặc ResNet-50 / ViT trong nghiên cứu so sánh).
- Tích hợp **Dense-UNet Anatomical Gate** (Dubey et al. BMC Infectious Diseases 2026, Dice 0.9848, IoU 0.9700) làm bộ lọc tiền suy luận (inference-time) với Dilated Soft Masking (dilation 6%, attenuation 10%) nhằm bảo toàn giải phẫu phổi nhưng làm suy giảm 90% nhiễu ký tự ngoài thành ngực.
- Chia tách 3 Classification Heads riêng biệt:
  - **Head A**: 14 bệnh lồng ngực NIH ChestX-ray14 (Multi-label Sigmoid BCELoss/AsymmetricFocalLoss, $\tau_c$ tối ưu Youden's J).
  - **Head B**: Sàng lọc Lao phổi TB Chest Radiography (Binary Sigmoid BCELoss).
  - **Head C**: Phân loại 3 lớp COVIDx CXR-4: Normal / COVID-19 / Non-COVID Pneumonia (Multi-class CrossEntropyLoss/MaskedCE).
- **Cơ chế Masked Backpropagation**: Khi một batch ảnh chỉ thuộc về Task $k$, chỉ loss của Head $k$ mới lan truyền gradient ngược về Shared Backbone và Head $k$; gradient của các head khác bị triệt tiêu bằng 0.

#### 🔴 Ràng buộc 2: Triệt tiêu Hoàn toàn Rò rỉ Bệnh nhân (Zero Patient-Level Data Leakage)
- Đối với NIH ChestX-ray14, việc phân chia tập Train / Val / Test (tỷ lệ 70% / 10% / 20%) **BẮT BUỘC thực hiện theo `Patient_ID`**.
- Tập hợp bệnh nhân giữa các tập phải hoàn toàn rời nhau:
  $$\text{Patients}(\text{Train}) \cap \text{Patients}(\text{Val}) = \emptyset, \quad \text{Patients}(\text{Train}) \cap \text{Patients}(\text{Test}) = \emptyset, \quad \text{Patients}(\text{Val}) \cap \text{Patients}(\text{Test}) = \emptyset$$
- **Tuyệt đối cấm**: Chia ngẫu nhiên theo chỉ số ảnh (Image-level split).

#### 🔴 Ràng buộc 3: Chống Học Đường Tắt COVIDx (Anti-Shortcut Learning via Source Stratification)
- Đối với bộ dữ liệu COVIDx CXR-4 Benchmark, việc phân chia Train / Test **BẮT BUỘC phải phân tầng theo nguồn ảnh gốc (`data_source`) và nhóm theo `patient_id`**.
- Không cho phép dồn toàn bộ ảnh từ một nguồn (ví dụ: Cohen COVID) vào tập Train hoặc Test, nhằm ngăn mô hình học thuộc các watermark, ký tự L/R hoặc khung viền máy chụp.

#### 🔴 Ràng buộc 4: Phân minh Vai trò Bounding Box (Bounding Box Role Partitioning)
- Toàn bộ quá trình huấn luyện WSOL học từ **nhãn mức ảnh (image-level labels)**; không sử dụng Bounding Box trong quá trình huấn luyện.
- Bounding Box chuyên gia (từ VinDr-CXR và RSNA Pneumonia Detection) **CHỈ ĐƯỢC PHÉP DÙNG CHO TẬP ĐÁNH GIÁ (Evaluation/Test)** để đo đạc chỉ số IoU định vị tổn thương khách quan.

#### 🔴 Ràng buộc 5: Cân bằng Tải Đa nhiệm (Balanced Multi-Task Batch Sampling)
- Để khắc phục tình trạng suy dinh dưỡng nhiệm vụ (Task Starvation) do kích thước dataset chênh lệch quá lớn (NIH 112K vs TB 7K vs COVID 16K), DataLoader **BẮT BUỘC dùng `WeightedMultiTaskBatchSampler`**.
- Tỷ lệ lấy mẫu chuẩn trong mỗi mini-batch là **60% NIH : 25% COVIDx : 15% TB**.

#### 🔴 Ràng buộc 6: Kiểm toán Đường tắt Lâm sàng & Smart Guardrail (Clinical Shortcut Audit & Guardrail)
- Mọi mô hình checkpoint trước khi nghiệm thu Gate 4 **BẮT BUỘC phải vượt qua bài kiểm toán Shortcut Learning Audit bằng Grad-CAM** trên các ca dương tính COVID-19.
- Chỉ số **In-Lung Activation Energy Ratio** (tỷ lệ năng lượng kích hoạt nằm trong phế trường phổi) phải đạt **$\ge 80.0\%$**. Nếu $< 75\%$, mô hình lập tức bị cảnh báo vi phạm Shortcut Learning.
- **Smart Clinical Report Guardrail**: Khi tỷ lệ năng lượng trong phổi $< 80\%$ hoặc khi phế nang Head A hoàn toàn âm tính đối với ca dương tính Head B/C, hệ thống **bắt buộc tự động đè bỏ kết luận bệnh nhiễm trùng** và đưa ra cảnh báo nghi ngờ dương tính giả do ký tự ngoài thành ngực (chữ R/L) hoặc viền máy chụp.

#### 🔴 Ràng buộc 7: Chuẩn Nghiên cứu Thực nghiệm Sống (Live Interactive Scientific Code)
- Toàn bộ kết quả phân tích EDA, đánh giá độ chính xác, ma trận nhầm lẫn (Confusion Matrix), Grad-CAM heatmap hay Box-IoU trong Notebooks (`notebooks/*.ipynb`) **BẮT BUỘC viết bằng code Python/PyTorch tương tác sống 100%** (`pandas`, `seaborn`, `matplotlib`, `cv2`, `PIL`), tính toán trực tiếp từ dữ liệu thật.
- **TUYỆT ĐỐI CẤM**: Hành vi dùng `display(Image("...png"))` hoặc chèn ảnh tĩnh tạo sẵn vào notebook để giả lập kết quả.

#### 🔴 Ràng buộc 8: Tinh gọn Không gian Dự án (Lean Workspace & Immediate Scratch Cleanup)
- Mọi tệp tạm thời (scratch scripts, runner helpers, debug logs, test dumps) tạo ra trong quá trình gỡ lỗi hoặc thực thi **BẮT BUỘC phải xóa sạch ngay lập tức sau khi hoàn thành nhiệm vụ**.
- Tuyệt đối không để lại file rác, file mồ côi trong `scripts/`, `src/` hoặc thư mục gốc. Workspace phải luôn ở trạng thái tinh gọn chuẩn Enterprise.

#### 🔴 Ràng buộc 9: Chuẩn Báo cáo Khoa học & Luận án Đơn sắc (Academic Report Rigor & Monochrome Standards)
- Mọi tài liệu báo cáo nghiệm thu, tài liệu kỹ thuật, bài báo khoa học và file kết xuất PDF (`reports/`, `results/*.md`, `results/*.pdf`) **BẮT BUỘC** tuân thủ [.agents/rules/academic_report_standards.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/.agents/rules/academic_report_standards.md):
  - **100% không chứa icon, emoji** (ví dụ: không dùng các biểu tượng cảm xúc trang trí).
  - Phông chữ chuẩn hàn lâm: **Times New Roman** (hoặc Computer Modern), kích thước 10–12pt.
  - Bảng biểu theo chuẩn **Booktabs**: Chỉ dùng 3 đường kẻ ngang đen (`\toprule`, `\midrule`, `\bottomrule`), không kẻ dọc, không tô màu xen kẽ sặc sỡ.
  - Màu sắc: **Đơn sắc đen trắng (Grayscale / Monochrome)**; đồ thị khoa học chỉ dùng nét đứt, chấm nét hoặc thang độ xám rõ ràng.
  - Văn phong khoa học khách quan, trang trọng, trích dẫn chuẩn IEEE/Vancouver.

#### 🔴 Ràng buộc 10: Giao thức Đồng bộ hóa Tài liệu & Model Toàn diện (Mandatory Model-to-Docs Sync Protocol)
- Bất kỳ khi nào có cập nhật về Checkpoint, Chỉ số thực nghiệm (ROC-AUC, F1, IoU), hoặc Thuật toán mới: Bắt buộc đồng bộ chính xác trên toàn bộ 7 tài liệu trọng yếu (`TECH_ARCHITECTURE.md`, `PRD.md`, `PHASES.md`, `DSP391_Full_Thesis_Report.md`, `docs_report.md`, `LANDING_PAGE_REPORT.html`, `DEMO_PRESENTATION_GUIDE.md`).
- Bắt buộc kiểm tra 0 ký tự raw LaTeX `$` trong các báo cáo Word copy-paste.

#### 🔴 Ràng buộc 11: Chuẩn Hóa Thuật Ngữ Học Thuật Y Khoa (Academic Terminology Standardization)
- Toàn bộ văn bản nghiên cứu, báo cáo luận văn, kịch bản thuyết minh slide và chỉ đạo Agent **TUYỆT ĐỐI KHÔNG SỬ DỤNG** các từ ngữ mang tính tranh đấu hoặc từ lóng phi học thuật:
  - Cấm dùng: `đấu trường`, `đấu trường kiến trúc` $\to$ Bắt buộc thay bằng: `Phân tích So sánh Đa Kiến trúc` (*Multi-Architecture Comparative Analysis*) hoặc `Khảo sát Đối chiếu Hiệu năng Mô hình`.
  - Cấm dùng: `Gate`, `Cổng chất lượng`, `Delivery Gate` trong văn bản báo cáo $\to$ Bắt buộc thay bằng: `Mốc nghiệm thu giai đoạn` (*Delivery Milestone*) hoặc `Tiêu chuẩn bàn giao kỹ thuật` (*Acceptance Checkpoint*).
  - Cấm dùng: `test pass`, `PASS` dạng informal $\to$ Bắt buộc thay bằng: `Đạt chuẩn kiểm thử`, `Đã xác nhận kiểm tra`, hoặc `Đáp ứng tiêu chuẩn kỹ thuật`.

