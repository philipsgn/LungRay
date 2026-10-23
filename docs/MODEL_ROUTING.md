# 🧭 CHIẾN LƯỢC ĐỊNH TUYẾN MODEL CHO COMMANDCODE GO (docs/MODEL_ROUTING.md)
## Tối Ưu Hóa Chi Phí ($1/Go), Quản Lý Quota & Bảo Vệ Dữ Liệu Nghiên Cứu

---

## 1. BẢNG ĐỊNH TUYẾN THEO TẦNG CÔNG VIỆC

| Tầng | Định nghĩa & Tình huống sử dụng | Model Được Chỉ Định | Chi phí & Ghi chú |
|:---:|:---|:---|:---|
| **S0** | **Code công khai / Không nhạy cảm**: Tạo boilerplate, khung skeleton, test fixtures đơn giản, tài liệu Markdown. | **Beam 1.0**, **Laguna S 2.1** | **Miễn phí** (Glyph Cluster giới hạn 100 req/ngày). CẤM dùng cho code nhạy cảm. |
| **T1** | **Khối lượng lớn, việc lặp lại, sửa nhanh**: Sửa lỗi cú pháp nhỏ, refactor tên biến, cập nhật schema, viết unit tests chuẩn. | **DeepSeek V4.1 Flash** | Chi phí rẻ. Dồn tác vụ nặng vào khung giờ thấp điểm. |
| **T2** | **Logic phức tạp, thuật toán, state, bug khó**: Huấn luyện Multi-Task, Masked Loss, Grad-CAM IoU, Batch Sampler. | **Kimi K2.7 Code**, **GLM-5.3** | Cân bằng hoàn hảo giữa khả năng code PyTorch và credit Go. |
| **T3** | **Dự phòng khẩn cấp**: Chỉ kích hoạt khi model T2 thất bại 2 lần liên tiếp. | **Qwen 3.8 Max**, **Kimi K3** | Model đắt, giới hạn số lượng request. Dùng chắt chiu. |
| **SENSITIVE** | **Code cá nhân / Y tế / Học thuật có tính bảo mật**: Mọi mã nguồn thuật toán lõi của LungRay. | **Chỉ dùng T1 hoặc T2** kèm biến môi trường **`CMD_ZDR=1`** | **TUYỆT ĐỐI CẤM** dùng tầng S0 (Beam/Laguna vì có thể bị lưu/train lại dữ liệu). |

---

## 2. QUY TẮC NGÂN SÁCH & KHUNG GIỜ VÀNG (BUDGET & PEAK HOURS RULES)

### 2.1. Khung giờ giá cao điểm của DeepSeek V4.1 Flash (Giờ Việt Nam - GMT+7):
- ⏰ **Giờ Cao Điểm (Giá x2)**: `08:00 - 11:00` và `13:00 - 17:00` (Thứ Hai đến Thứ Sáu).
- 🌙 **Giờ Thấp Điểm (Giá Rẻ Chuẩn)**: `18:00 - 08:00 sáng hôm sau` và toàn bộ các ngày **Thứ Bảy, Chủ Nhật**.
- 👉 **Chiến lược**: Dồn các đợt refactor mã nguồn lớn hoặc chạy kiểm thử lặp lại bằng DeepSeek vào khung giờ tối/đêm hoặc cuối tuần.

### 2.2. Kiểm soát Quota & Giữ Ngữ Cảnh Tinh Gọn:
1. **Kiểm tra đầu & cuối phiên**: Luôn gõ `/usage` ngay khi mở CommandCode CLI và trước khi đóng để theo dõi chính xác lượng credit tiêu thụ.
2. **Dọn dẹp ngữ cảnh (`/clear`)**: Luôn gõ `/clear` giữa 2 task. Phiên chat dài sẽ tốn credit theo cấp số cộng vì mỗi lượt phản hồi model phải nạp lại toàn bộ lịch sử trò chuyện.
3. **Tham chiếu bằng đường dẫn**: Không copy-paste cả file code dài vào chat; chỉ gửi đường dẫn `docs/HANDOFF/<ID>.md` và tên file đích.

---

## 3. NGUYÊN TẮC BẬC THANG NÂNG CẤP (ESCALATION LADDER)
```text
[Task Bắt đầu]
       │
       ▼
 [Thử với T1 hoặc T2] ──(Lỗi lần 1)──> Sửa prompt handoff ngắn gọn
       │
   (Lỗi lần 2)
       ▼
 [Nâng cấp lên T2 hoặc T3]
       │
   (Lỗi lần 3)
       ▼
 🛑 [HARD STOP] Dừng phiên CommandCode ngay lập tức.
     Báo cáo Antigravity để xem xét lại kiến trúc / chia nhỏ task.
```
