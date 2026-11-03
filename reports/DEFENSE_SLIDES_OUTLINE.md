# 🖥️ ĐỀ CƯƠNG BỘ SLIDE BÁO CÁO BẢO VỆ ĐỒ ÁN TỐT NGHIỆP (40 SLIDES)
## Nền tảng LungRay: CADx X-Quang Ngực Đa Nhiệm, Định Vị Tổn Thương WSOL & Lớp Phòng Vệ Fail-Safe Ngoại Lai

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Đồ án** | **LungRay** (CXR Multi-Task CADx + WSOL Grounding + Clinical Fail-Safe Workstation) |
| **Quy mô** | **40 Slides Thuyết Trình Toàn Diện** |
| **Thời lượng Báo cáo** | 20–25 phút thuyết trình + 10–15 phút phản biện |
| **Tiêu chuẩn Học thuật** | MICCAI / IEEE Trans. Med. Imaging — Không icon/emoji, Bảng số liệu Booktabs, Chuẩn y khoa WHO ICD-10 |
| **Trạng thái** | ✅ 100% HOÀN THIỆN & SẴN SÀNG CHO HỘI ĐỒNG BẢO VỆ |

---

### PHẦN I: TỔNG QUAN ĐỀ TÀI & TÍNH CẤP THIẾT LÂM SÀNG (SLIDES 01 – 06)
- **Slide 01**: Trang tiêu đề Đồ án, Tác giả: Nguyễn Tấn Phát, Giảng viên Hướng dẫn, Đơn vị đào tạo.
- **Slide 02**: Bối cảnh thực tế: Áp lực đọc phim X-quang lồng ngực tại các bệnh viện tuyến đầu & Thực trạng thiếu hụt bác sĩ chẩn đoán hình ảnh.
- **Slide 03**: Ba nghịch lý & "nút thắt cổ chai" của AI y tế hiện nay:
  1. *Phân mảnh tác vụ*: Mỗi bệnh 1 mô hình riêng biệt $\to$ tốn RAM/VRAM, chậm trễ.
  2. *Học đường tắt (Shortcut Learning)*: Bắt các đặc trưng giả định (watermark, chữ R/L, viền ảnh) thay vì tổn thương phổi.
  3. *Giải thích mù (Qualitative-only XAI)*: Chỉ xem heatmap màu mè, không có thước đo định lượng so với bác sĩ.
- **Slide 04**: Nghịch lý thứ tư: *"Ảo tưởng tự tin" (Overconfident OOD)* — AI chẩn đoán tự tin ngay trên ảnh nhiễu hoặc ảnh ngoài lồng ngực.
- **Slide 05**: Tóm tắt 5 đóng góp đột phá của đề tài LungRay (Shared Backbone, Masked Loss, WSOL IoU, Shortcut Audit, Phase 8 Fail-Safe Layer).
- **Slide 06**: Khung phương pháp luận & Sơ đồ tổng thể hệ thống (System Architecture Pipeline).

---

### PHẦN II: DỮ LIỆU ĐA NGUỒN & NGUYÊN TẮC LIÊM CHÍNH KHOA HỌC (SLIDES 07 – 12)
- **Slide 07**: Danh mục 6 bộ dữ liệu chuẩn lâm sàng (NIH ChestX-ray14, TB Radiography, COVIDx CXR-4, VinDr-CXR, RSNA Pneumonia, CheXpert).
- **Slide 08**: Nguyên tắc sống còn 1: **Zero Patient Data Leakage** trên NIH ChestX-ray14 ($Train \cap Test = \emptyset$ theo `Patient_ID`).
- **Slide 09**: Nguyên tắc sống còn 2: Phân tầng nguồn gốc (`data_source`) trên COVIDx CXR-4 chống shortcut learning máy chụp.
- **Slide 10**: Quy chuẩn phân định vai trò Bounding Box: Chỉ dùng để đánh giá kiểm chứng trên tập Test (VinDr, RSNA), không dùng trong huấn luyện.
- **Slide 11**: Chuẩn hóa độ phân giải Pareto $512 \times 512$ Cloud Rescaling bảo tồn giải phẫu.
- **Slide 12**: Kết quả kiểm toán dữ liệu độc lập (Data Profiling & Audit).

---

### PHẦN III: THIẾT KẾ KIẾN TRÚC MÔ HÌNH ĐA NHIỆM (SLIDES 13 – 19)
- **Slide 13**: Kiến trúc Shared Backbone Multi-Task 3-Head (DenseNet-121 / ResNet-50 / ViT):
  - *Head A*: 14 bệnh lồng ngực NIH (Multi-label Sigmoid).
  - *Head B*: Sàng lọc Lao phổi TB (Binary Sigmoid).
  - *Head C*: Sàng lọc Cấp cứu COVID-19 Triage (Binary Sigmoid, `num_classes_c=1`).
- **Slide 14**: Thuật toán **Masked Loss Engine**: Cô lập gradient giữa các Heads, chống nhiễm độc tham số.
- **Slide 15**: Giải quyết mất cân bằng lớp cực đoan: Multi-Label **Focal Loss** ($\alpha=0.25, \gamma=2.0$) & Positive Class Weights.
- **Slide 16**: Cơ chế lấy mẫu cân bằng **WeightedMultiTaskBatchSampler** (60% NIH : 25% COVID : 15% TB).
- **Slide 17**: Tối ưu hóa 16 ngưỡng phân loại $\tau_c$ theo Youden's J statistic trên Validation.
- **Slide 18**: Chiến lược Two-Stage Fine-tuning với Differential Learning Rates & Hướng mở rộng Asymmetric Loss (SOTA ASL).
- **Slide 19**: Tóm tắt thông số siêu tham số huấn luyện (Mixed Precision FP16, AdamW, Cosine Annealing).

---

### PHẦN IV: ĐỊNH LƯỢNG HÓA WSOL & KIỂM TOÁN SHORTCUT LEARNING (SLIDES 20 – 26)
- **Slide 20**: Thuật toán trích xuất Grad-CAM & Grad-CAM++ từ tầng tích chập cuối cùng (`denseblock4`).
- **Slide 21**: Kỹ thuật nhị phân hóa thích nghi bảo vệ phế trường phổi $\hat{B}_c$.
- **Slide 22**: Định lượng hóa chỉ số IoU so với Bounding Box chuyên gia từ bác sĩ Việt Nam (VinDr-CXR: 0.6049) và RSNA (0.7631).
- **Slide 23**: Thử nghiệm Kiểm toán Shortcut Learning Audit trên 150 ca bệnh COVID-19 đa nguồn.
- **Slide 24**: Phát hiện thực tế: **Grad-CAM thô thất bại** với In-Lung Ratio trung bình chỉ đạt **38.49%** (0/150 ca đạt ngưỡng an toàn $\ge 80\%$) do bám vào text marker và viền chụp.
- **Slide 25**: Giải pháp Phòng vệ Đa tầng (Defense-in-Depth): Cơ chế **Anatomical Post-hoc Safety Gatekeeper (Clinical Projection)** nâng tỷ lệ năng lượng lên **94.92% ± 1.60%** (149/150 ca đạt chuẩn).
- **Slide 26**: Bằng chứng trực quan: So sánh đối đầu trước và sau Clinical Projection, triệt tiêu kích hoạt ngoài viền ảnh để bảo vệ bác sĩ khỏi chẩn đoán sai lệch.

---

### PHẦN V: KẾT QUẢ THỰC NGHIỆM ĐỘT PHÁ & ĐỐI CHUẨN KHOA HỌC (SLIDES 27 – 32)
- **Slide 27**: Bảng điểm hiệu năng AUROC tổng thể trên cả 3 Heads:
  - *Head A (NIH-14)*: AUROC Macro **0.8271** (Đạt mục tiêu $\ge 0.82$).
  - *Head B (Lao TB)*: AUROC **1.0000** (Phân tách hoàn hảo trên benchmark; thảo luận thẳng thắn về nguy cơ domain bias).
  - *Head C (COVID)*: AUROC **0.7342** (Đạt conditional pass sàng lọc cấp cứu nhị phân).
- **Slide 28**: Phân tích khoảng tin cậy thống kê **Bootstrap 95% CI** (1.000 lần resample).
- **Slide 29**: Đấu trường kiến trúc: So sánh chi tiết **DenseNet-121 vs ResNet-50 vs ViT-B/16** (Tham số, Độ trễ, VRAM, Macro AUC).
- **Slide 30**: Lý giải quyết định chọn DenseNet-121 làm động cơ Production tối ưu cho bệnh viện (nhẹ 26.6MB, độ trễ 674ms trên CPU).
- **Slide 31**: Kiểm định tổng quát hóa ngoại vi (External OOD Test) trên Stanford CheXpert ($\Delta \text{AUC} = 0.0447 \le 0.080$).
- **Slide 32**: Đối sánh với các nghiên cứu công bố quốc tế (CheXNet, VinDr-CXR Benchmark).

---

### PHẦN VI: LỚP PHÒNG VỆ FAIL-SAFE LAYER & CHUẨN HÓA Y KHOA WHO ICD-10 (SLIDES 33 – 36)
- **Slide 33**: Lớp Phòng Vệ Ngoại Lai Phase 8: Phát hiện ảnh OOD bằng **Năng lượng tự do Helmholtz (Sigmoid Free Energy $S_E$)** và **Shannon Entropy ($H$)**.
- **Slide 34**: Cơ chế Khóa Cảnh Báo An Toàn (Safety Reject Policy & Lockout): Hiệu chuẩn ngưỡng $\tau_E = 9.0421$, $\tau_H = 0.6275$; tự động kích hoạt `is_rejected = true` và khóa bản đồ nhiệt khi tiếp nhận ảnh dị thường.
- **Slide 35**: Chuẩn hóa Y khoa & Bảng Mã Định danh Quốc tế **WHO ICD-10**: Tích hợp 16 mã bệnh lý (`J98.11`, `I51.7`, `J90`, `J18.9`, `A15.0`, `U07.1`...) loại bỏ hoàn toàn các mô tả tự do sai lệch.
- **Slide 36**: Động cơ Sinh Báo Cáo Lâm Sàng Xác Định (Grounded Clinical Report Generator): Kết hợp định vị không gian 6 vùng phổi với ICD-10 và cơ chế tự động khóa `BLOCKED` khi phát hiện ca bệnh OOD.

---

### PHẦN VII: TRIỂN KHAI PHẦN MỀM TRẠM ĐỌC PACS & KẾT LUẬN (SLIDES 37 – 40)
- **Slide 37**: Kiến trúc phần mềm Full-Stack Y tế: FastAPI REST Microservice + Next.js 14 Medical PACS Viewer phòng tối (`#070B12`) và Chuyên khảo Báo cáo (`/report`).
- **Slide 38**: Trình diễn Demo vận hành thực tế hệ thống: Phân tích 16 bệnh trong $\le 1.8$s, Alpha Slider mượt mà, kiểm chứng Fail-Safe Lockout Banner.
- **Slide 39**: Đánh giá mức độ hoàn thiện đồ án: **Hoàn thành 100% WBS (36/36 Tasks), 125/125 Unit Tests Đạt PASS Tuyệt Đối**.
- **Slide 40**: Kết luận, Giá trị chuyển giao tiền lâm sàng & Phiên Hỏi - Đáp (Q&A Session).
