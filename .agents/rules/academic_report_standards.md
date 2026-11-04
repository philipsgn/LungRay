# QUY CHUẨN SOẠN THẢO BÁO CÁO NGHIÊN CỨU KHOA HỌC & LUẬN ÁN TỐT NGHIỆP
## Nền tảng LungRay: Tiêu Chuẩn Học Thuật Đơn Sắc (Academic Monochrome Standards)

---

| Thuộc tính | Quy chuẩn áp dụng |
|:---|:---|
| **Phạm vi áp dụng** | Toàn bộ tài liệu báo cáo nghiệm thu, báo cáo kỹ thuật, luận văn tốt nghiệp và các tệp kết xuất PDF trong `reports/`, `results/`, `docs/`. |
| **Phong cách trình bày** | Chuẩn bài báo y khoa quốc tế (Nature Digital Medicine, Radiology AI, IEEE Transactions) và Luận án Thạc sĩ/Kỹ sư. |
| **Bảng màu chủ đạo** | **Đơn sắc (Monochrome Grayscale)**: Chỉ sử dụng Đen (#000000), Xám đậm (#333333, #666666) và Nền trắng (#FFFFFF). Tuyệt đối không dùng màu mè trang trí. |
| **Phông chữ bắt buộc** | **Times New Roman** (hoặc Liberation Serif / Computer Modern). |
| **Biểu tượng cảm xúc (Emoji)**| **TUYỆT ĐỐI CẤM 100%**. Không sử dụng bất kỳ icon hay emoji nào trong văn bản chính thức. |

---

## 1. NGUYÊN TẮC CỐT LÕI (CORE PRINCIPLES)

### 1.1. Cấm Tuyệt Đối Emoji và Biểu Tượng Trang Trí
- Không sử dụng các emoji trang trí thường gặp trên mạng xã hội hoặc chat UI trong các báo cáo khoa học.
- Thay vì dùng các icon chỉ thị trạng thái, bắt buộc sử dụng chữ in hoa trang trọng:
  - Không dùng `[PASS]` kèm icon xanh lá $\to$ Sử dụng `ĐẠT TIÊU CHUẨN (PASS)`.
  - Không dùng icon cảnh báo màu vàng $\to$ Sử dụng `CẦN HOÀN THIỆN / ĐẠT CÓ ĐIỀU KIỆN (CONDITIONAL)`.
  - Không dùng icon lỗi màu đỏ $\to$ Sử dụng `KHÔNG ĐẠT (FAILED)`.

### 1.2. Phông Chữ & Căn Lề Chuẩn Mực Học Thuật
- **Phông chữ thân bài**: `Times New Roman`, kích thước 11pt - 12pt, độ giãn dòng 1.5.
- **Căn lề**: Căn đều hai bên (`text-align: justify;`).
- **Tiêu đề các cấp**:
  - `Heading 1`: 15pt - 16pt, IN HOA, đậm, căn giữa hoặc căn trái, màu đen (#000000).
  - `Heading 2`: 12pt - 13pt, Đậm, đánh số mục học thuật (1., 2., 3.,...), màu đen (#000000).
  - `Heading 3`: 11pt, Đậm hoặc nghiêng, đánh số mục phụ (1.1, 1.2,...), màu đen (#111111).

### 1.3. Chuẩn Trình Bày Bảng Biểu (Booktabs Style)
Mọi bảng số liệu khoa học trong bài báo cáo bắt buộc phải theo phong cách **Booktabs** (chuẩn mực xuất bản của Hội đồng Khoa học và các tạp chí uy tín):
- **Đường kẻ ngang trên cùng (Top Rule)**: Đường kẻ đen đậm `1.5pt solid #000000`.
- **Đường kẻ ngang dưới tiêu đề cột (Mid Rule)**: Đường kẻ đen mảnh `0.75pt solid #000000`.
- **Đường kẻ ngang đáy bảng (Bottom Rule)**: Đường kẻ đen đậm `1.5pt solid #000000`.
- **Tuyệt đối không có đường kẻ dọc (No Vertical Borders)**: `border-left: none; border-right: none;`.
- **Không có sọc vằn xen kẽ (No Zebra Striping)**: Nền bảng màu trắng đồng nhất, không dùng các màu nền xanh lam hay vàng.
- **Tiêu đề bảng**: Đặt phía trên bảng, đánh số rõ ràng: `Bảng X: [Mô tả nội dung ngắn gọn]`.

### 1.4. Trình Bày Hình Ảnh & Biểu Đồ
- Mọi hình ảnh phải có số thứ tự và chú thích đặt phía dưới: `Hình Y: [Mô tả ngắn gọn nội dung biểu đồ]`.
- Sơ đồ khối (Flowcharts / Architecture diagrams): Thiết kế tối giản theo dạng hình chữ nhật viền đen mảnh (1px), nền trắng, chữ đen, đường mũi tên màu đen rõ nét.

### 1.5. Văn Phong & Ngôn Ngữ Học Thuật
- Sử dụng đại từ nhân xưng khách quan, thể thụ động hoặc ngôi thứ ba trang trọng ("Nghiên cứu này thực hiện...", "Mô hình được huấn luyện...", "Dữ liệu được phân chia...").
- Tránh tuyệt đối các từ ngữ mang tính cảm thán, tiếp thị hoặc phóng đại ("thần thánh", "siêu đỉnh", "bất bại"). Trình bày trung thực, điềm tĩnh và dựa trên số liệu thực chứng.
