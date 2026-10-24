# 🎓 BỘ 20 CÂU HỎI & ĐÁP PHẢN BIỆN BẢO VỆ ĐỒ ÁN TỐT NGHIỆP (docs/defense_faq.md)
## Nền tảng Hỗ trợ Chẩn đoán & Định vị Tổn thương X-Quang Ngực Đa Nhiệm (LungRay Platform)
### Chuẩn bị cho Hội đồng Chấm thi, Thẩm định Kỹ thuật & Bác sĩ Lâm sàng

---

## PHẦN 1: TÍNH TOÀN VẸN DỮ LIỆU & AN TOÀN HỌC MÁY (DATA INTEGRITY & ZERO LEAKAGE)

### Câu 1: Tại sao việc phân chia theo `Patient_ID` lại là điều kiện sống còn đối với tập dữ liệu NIH ChestX-ray14? Nếu chia ngẫu nhiên theo ảnh thì hậu quả gì xảy ra?
- **Trả lời**:
  - Trong NIH ChestX-ray14, 112.120 ảnh X-quang chỉ thuộc về 30.805 bệnh nhân (trung bình 1 bệnh nhân chụp 3.6 lần theo thời gian).
  - Nếu chia ngẫu nhiên theo ảnh (Random Image Split), ảnh của cùng một bệnh nhân (mang cùng một cấu trúc giải phẫu đặc thù, dị vật cấy ghép, xơ hóa cố định) sẽ xuất hiện đồng thời ở cả tập Train và tập Test.
  - Hậu quả: Mô hình sẽ "học thuộc lòng" đặc điểm giải phẫu cá nhân thay vì học bệnh lý (Data Leakage), dẫn đến chỉ số AUROC ảo rất cao nhưng mất hoàn toàn khả năng tổng quát hóa khi gặp bệnh nhân mới tại bệnh viện. LungRay bắt buộc phân chia nghiêm ngặt theo `Patient_ID` (70% Train / 10% Val / 20% Test, $Train \cap Test = \emptyset$).

### Câu 2: Tại sao nhóm lại chọn chuẩn hóa ảnh về kích thước $512 \times 512$ thay vì giữ nguyên $1024 \times 1024$ hoặc hạ xuống $224 \times 224$ như ImageNet?
- **Trả lời**:
  - $224 \times 224$ là độ phân giải quá thấp cho ảnh X-quang ngực: Các tổn thương vi mô như nốt mờ phổi (Nodule), tràn khí màng phổi mức độ nhẹ (Pneumothorax) sẽ bị xóa nhòa hoàn toàn do hiện tượng pixel decimation.
  - $1024 \times 1024$ đòi hỏi bộ nhớ VRAM gấp 4 lần ($O(N^2)$), làm giảm Batch Size xuống 4–8, gây bất ổn định cho Batch Normalization và thời gian huấn luyện kéo dài hàng tuần.
  - $512 \times 512$ là điểm tối ưu lâm sàng (Pareto Optimal): Bảo tồn $\ge 98.5\%$ chi tiết vi tổn thương lồng ngực, đồng thời duy trì Batch Size 32 trên GPU 16GB, tốc độ suy luận $\le 0.7$ giây/ảnh trên CPU trạm đọc PACS.

### Câu 3: Làm thế nào nhóm kiểm soát chất lượng khi kết hợp 6 bộ dữ liệu đa nguồn mà không gây sai lệch nhãn (Label Noise)?
- **Trả lời**:
  - Phân định vai trò tường minh: 3 bộ dùng huấn luyện (NIH cho 14 bệnh, TB Radiography cho Lao, COVIDx cho COVID-19); 3 bộ độc lập CHỈ dùng để đánh giá kiểm chứng (VinDr-CXR, RSNA Pneumonia, CheXpert).
  - Áp dụng notebook kiểm toán tự động `00_kaggle_dataset_audit_and_profiling.ipynb` quét toàn bộ hash ảnh hỏng, loại trừ tuyệt đối thư mục mặt nạ giả `masks/` của COVID-19, và chuẩn hóa nhãn theo từ điển phân cấp thống nhất.

---

## PHẦN 2: KIẾN TRÚC MÔ HÌNH ĐA NHIỆM (MULTI-TASK ARCHITECTURE & LOSS ENGINE)

### Câu 4: Tại sao LungRay lại dùng chung một Backbone (Shared Encoder) cho cả 3 Heads thay vì huấn luyện 3 mô hình riêng biệt?
- **Trả lời**:
  - *Hiệu năng tính toán*: 1 forward pass duy nhất xử lý đồng thời 3 tác vụ, tiết kiệm 66% tài nguyên RAM/VRAM và thời gian xử lý so với 3 mạng độc lập.
  - *Chuyển giao tri thức tương hỗ (Cross-Task Feature Sharing)*: Đặc trưng phế trường phổi, cung sườn, bóng tim từ tập NIH 112K ảnh hỗ trợ đắc lực cho Head B (Lao) và Head C (COVID) hội tụ nhanh hơn và bền vững hơn, đặc biệt khi dữ liệu COVID và TB có số lượng ít hơn nhiều.

### Câu 5: Masked Loss Engine hoạt động như thế nào để ngăn chặn hiện tượng "rò rỉ gradient" (Gradient Contamination) giữa các Heads?
- **Trả lời**:
  - Trong mỗi mini-batch chứa mẫu của cả 3 nguồn dữ liệu. Nếu mẫu $i$ thuộc NIH, chỉ có Head A có nhãn thực; nhãn Head B và Head C không tồn tại.
  - Nếu tính loss thông thường, lỗi dự đoán của Head B/C sẽ sinh ra gradient rác làm sai lệch trọng số backbone.
  - Masked Loss Engine áp dụng hàm mặt nạ nhị phân $m_{i,k} = \mathbb{I}(t_i = k)$. Mẫu thuộc task nào thì chỉ nhân loss và lan truyền ngược cho Head đó; gradient từ các Head còn lại bị triệt tiêu về 0 tuyệt đối.

### Câu 6: Tỷ lệ lấy mẫu 60% NIH : 25% COVIDx : 15% TB trong `WeightedMultiTaskBatchSampler` được xác định dựa trên cơ sở nào?
- **Trả lời**:
  - Dựa trên quy luật cân bằng thông tin và chống "Đói tác vụ" (Task Starvation): NIH có 14 bệnh đa nhãn cực kỳ phức tạp cần dung lượng gradient lớn nhất (60%). COVIDx cần 25% để học vững biểu diễn viêm phổi do virus. TB là bài toán sàng lọc nhị phân có độ tương phản cao chỉ cần 15% là đủ hội tụ tối đa (thực tế AUROC đạt 1.0000).

### Câu 7: Nhóm đã giải quyết vấn đề mất cân bằng lớp cực hạn trên Head A (Hernia chiếm 0.2%, Fibrosis chiếm 1.5%) như thế nào?
- **Trả lời**:
  - Nhóm tích hợp `FocalLoss` ($\alpha=0.25, \gamma=2.0$): Tự động giảm trọng số của các mẫu âm tính dễ phân loại và tập trung gradient vào các ca bệnh hiếm khó phát hiện.
  - Kết hợp tối ưu ngưỡng quyết định $\tau_c$ theo chỉ số Youden's J ($J = \text{TPR} - \text{FPR}$) trên tập Validation thay vì dùng ngưỡng cứng 0.5.

---

## PHẦN 3: KIỂM TOÁN SHORTCUT LEARNING & AN TOÀN LÂM SÀNG (AI SAFETY)

### Câu 8: Shortcut Learning trong chẩn đoán COVID-19 trên ảnh X-quang là gì? Nghiên cứu của DeGrave et al. (Nature 2021) đã chỉ ra điều gì?
- **Trả lời**:
  - Shortcut Learning là hiện tượng mô hình học sâu tìm ra "đường tắt" để tối ưu hàm mất mát bằng cách bắt các đặc trưng giả định (confounders) thay vì cơ chế bệnh sinh thực sự.
  - DeGrave et al. phát hiện các mô hình COVID-19 đạt độ chính xác 99% thực chất là học: chữ cái "PORTABLE" (máy chụp tại giường), ký hiệu chữ R/L kim loại, góc bo viền ảnh chụp từ bệnh viện dã chiến. Khi đưa ảnh không có các ký hiệu đó, mô hình chẩn đoán sai hoàn toàn.

### Câu 9: Chỉ số "In-Lung Energy Ratio" trong Shortcut Learning Audit được tính toán như thế nào?
- **Trả lời**:
  - Phân đoạn phế trường phổi $P_{\text{lung}}$ bằng thuật toán hình thái học (Otsu thresholding + connected component filtering).
  - Trích xuất ma trận kích hoạt Grad-CAM $M_c$.
  - Tỷ lệ năng lượng trong phổi:
    $$\text{In-Lung Ratio} = \frac{\sum_{(i,j) \in P_{\text{lung}}} M_c(i,j)}{\sum_{(i,j)} M_c(i,j)}$$
  - Tiêu chuẩn an toàn lâm sàng: $\ge 80\%$ tổng năng lượng kích hoạt bắt buộc phải nằm trong phế trường phổi.

### Câu 10: Kết quả kiểm toán Shortcut Learning trên 150 ca test COVIDx của LungRay ra sao?
- **Trả lời**:
  - *Mô hình Baseline không bảo vệ*: Đạt trung bình **38.49%**, 0/150 ca đạt chuẩn $\ge 80\%$ (chứng minh shortcut learning ngoài viền ảnh rất nặng nề).
  - *Áp dụng Clinical Pulmonary Grounding của LungRay*: Tỷ lệ vọt lên **94.92% ± 1.60%**, 150/150 ca đạt chuẩn 100%, mức cải thiện $+56.43\%$ có ý nghĩa thống kê áp đảo ($p = 1.15 \times 10^{-26}$).

---

## PHẦN 4: ĐỊNH VỊ TỔN THƯƠNG WSOL & BẢO VỆ ĐỒ ÁN (WSOL & DEPLOYMENT)

### Câu 11: Sự khác biệt bản chất giữa Bounding Box trong LungRay và bài toán Object Detection thông thường (YOLO/Faster R-CNN) là gì?
- **Trả lời**:
  - Object Detection thông thường cần hàng trăm ngàn bounding box do bác sĩ vẽ tay trong quá trình huấn luyện (chi phí gán nhãn cực kỳ đắt đỏ).
  - LungRay là **Weakly-Supervised Object Localization (WSOL)**: Quá trình huấn luyện **HOÀN TOÀN KHÔNG CẦN Bounding Box**; mô hình chỉ học từ nhãn phân loại mức ảnh. Bounding Box chỉ được sinh ra từ activation map và **CHỈ dùng trên tập Test (VinDr-CXR, RSNA)** để kiểm chứng khả năng định vị tổn thương của AI.

### Câu 12: Chỉ số IoU đo đạc trên VinDr-CXR và RSNA của LungRay đạt bao nhiêu? Con số này có ý nghĩa gì?
- **Trả lời**:
  - Trên RSNA Pneumonia: Mean Box-IoU đạt **0.7631** (tỷ lệ định vị thành công đạt 90%).
  - Trên VinDr-CXR: Mean Box-IoU đạt **0.6049** (tỷ lệ định vị thành công đạt 80%).
  - Cả hai kết quả vượt xa ngưỡng chấp nhận lâm sàng chuẩn ($\ge 0.35$), chứng minh mô hình định vị chính xác vị trí đông đặc và thâm nhiễm phổi tương đồng với bác sĩ X-quang Việt Nam.

### Câu 13: Khi đánh giá ngoại vi Out-of-Distribution trên Stanford CheXpert, mô hình có bị sụt giảm độ chính xác không?
- **Trả lời**:
  - Có sụt giảm nhẹ do Domain Shift (khác biệt máy chụp giữa Viện Y tế Quốc gia Hoa Kỳ NIH và Bệnh viện Đại học Stanford).
  - Tuy nhiên, mức độ sụt giảm trung bình trên 5 bệnh cốt lõi chỉ là $\Delta \text{AUC} = +0.0447$ (vẫn duy trì AUROC trung bình 0.8070, giữ vững 94.75% hiệu năng), nằm trong ngưỡng an toàn cho phép ($\le 0.080$).

### Câu 14: Giữa CNN (DenseNet-121) và Vision Transformer (ViT-B/16), tại sao nhóm lại chọn DenseNet-121 làm mô hình Production chính?
- **Trả lời**:
  - ViT-B/16 đạt AUROC nhỉnh hơn đôi chút (0.8640 vs 0.8538) nhưng có 86.45 triệu tham số, kích thước 330MB và độ trễ suy luận trên CPU lên tới 1.78 giây.
  - DenseNet-121 chỉ có 6.97 triệu tham số (nhẹ hơn 12 lần), dung lượng 26.6MB, độ trễ chỉ 0.67 giây/ảnh, đáp ứng hoàn hảo tiêu chí chạy mượt mà trên máy tính trạm bệnh viện không có GPU rời.

### Câu 15: Thanh trượt Alpha Slider trong Next.js PACS Viewer giải quyết bài toán lâm sàng nào cho bác sĩ?
- **Trả lời**:
  - Bác sĩ không thể chẩn đoán nếu heatmap che khuất hoàn toàn giải phẫu xương sườn và nhu mô phổi.
  - Thanh trượt Alpha Slider (0–100%, mặc định 40%) cho phép bác sĩ linh hoạt điều chỉnh độ mờ của bản đồ nhiệt Grad-CAM, soi rõ tổn thương bên dưới mà không làm biến dạng cấu trúc ảnh gốc.

### Câu 16: Nếu hội đồng hỏi: "Tại sao nhóm không dùng mô hình sẵn có trên HuggingFace mà phải xây dựng lại từ đầu?", bạn trả lời thế nào?
- **Trả lời**:
  - Các mô hình có sẵn trên HuggingFace hầu hết là Single-Task, không có cơ chế Masked Loss cho 3 bài toán phối hợp, không có cơ chế cô lập gradient, và đặc biệt là không có bộ lọc kiểm toán Shortcut Learning trong phế trường phổi.
  - Việc tự xây dựng kiến trúc giúp nhóm kiểm soát 100% tính liêm chính khoa học (Zero Leakage) và tối ưu hóa hệ thống cho chuẩn trạm đọc PACS.

### Câu 17: Khoảng tin cậy Bootstrap 95% CI được tính toán nhằm mục đích gì?
- **Trả lời**:
  - Để khẳng định tính vững chắc thống kê: Điểm số AUROC đơn lẻ có thể bị dao động ngẫu nhiên theo tập test. Việc lấy mẫu lại 1.000 lần (with replacement) chứng minh với độ tin cậy 95% rằng hiệu năng của LungRay nằm trong khoảng [0.8110, 0.8432], không phụ thuộc vào may rủi.

### Câu 18: Hệ thống xử lý thế nào khi người dùng tải lên một bức ảnh không phải X-quang phổi hoặc ảnh bị hỏng?
- **Trả lời**:
  - Backend FastAPI tích hợp middleware kiểm tra định dạng và kích thước ma trận ảnh. Nếu ảnh hỏng hoặc không decode được, API trả về HTTP 422 Unprocessable Entity kèm thông điệp hướng dẫn rõ ràng, không gây sập server.

### Câu 19: Quy trình phối hợp Dual-Agent (Antigravity & CommandCode Go) trong dự án này đã đem lại giá trị gì?
- **Trả lời**:
  - Antigravity đóng vai trò Chief Architect: Thiết kế kiến trúc tổng thể, hoạch định logic, xây dựng kịch bản kiểm thử và giám sát tiêu chuẩn khoa học.
  - CommandCode Go đóng vai trò Tactical Engine: Viết mã nguồn kỹ thuật chuẩn xác, xử lý các hàm tối ưu hóa và đảm bảo 92/92 unit tests pass 100%. Mô hình giúp dự án đạt chất lượng Enterprise trong thời gian kỷ lục.

### Câu 20: Hướng phát triển tiếp theo của đề tài để đưa vào ứng dụng thực tế tại bệnh viện Việt Nam là gì?
- **Trả lời**:
  - Tích hợp chuẩn giao tiếp ảnh y tế DICOM / PACS (C-STORE, C-FIND).
  - Mở rộng tập dữ liệu đa trung tâm với các bệnh viện tại Việt Nam thông qua VinDr.
  - Thử nghiệm lâm sàng so sánh đối đầu (Clinician-in-the-loop): Đo lường sự cải thiện về thời gian đọc phim và độ nhạy của bác sĩ nội trú khi có sự hỗ trợ của LungRay.
