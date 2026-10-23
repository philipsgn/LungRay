# 🧐 CHECKLIST KIỂM DUYỆT CHẤT LƯỢNG CHO ANTIGRAVITY (docs/REVIEW.md)
## Tiêu Chuẩn Nghiệm Thu & Đánh Giá Git Diff Của Lead AI Architect

---

Mỗi khi CommandCode thông báo hoàn thành một task trên nhánh `task/<ID>-<slug>`, Antigravity **BẮT BUỘC** phải rà soát qua 7 cổng kiểm soát dưới đây trước khi đưa ra quyết định `APPROVE`:

### 1. Cổng Tiêu Chí Nghiệm Thu (Acceptance Criteria Gate)
- [ ] Mọi tiêu chí đánh dấu `[ ]` trong `docs/HANDOFF/<ID>.md` đều đã được giải quyết triệt để.
- [ ] Logic trả về đúng kiểu dữ liệu, đúng interface/chữ ký hàm đã cam kết.

### 2. Cổng Bằng Chứng Kiểm Thử Sống (Live Evidence Gate)
- [ ] CommandCode đã điền mục `## Result` kèm log chứng minh lệnh `powershell -File scripts/verify.ps1` chạy **xanh 100% (exit code 0)**.
- [ ] **Tuyệt đối không tin lời hứa suông**: Nếu không có log kết quả hoặc nghi ngờ, Antigravity yêu cầu chạy lại hoặc chạy xác thực độc lập.

### 3. Cổng Kiểm Soát Phạm Vi (Strict Scope Gate)
- [ ] Chạy `git diff --stat main..task/<ID>-<slug>` để xác nhận: **CHỈ CÓ** các file được phép trong mục `Scope` của handoff bị thay đổi.
- [ ] Không có bất kỳ file ngoài phạm vi (đặc biệt là config gốc, weights model, dữ liệu thô) bị chỉnh sửa ngầm.

### 4. Cổng Kiểm Soát Dependency & Môi Trường (Dependency Gate)
- [ ] Không tự tiện thêm thư viện mới vào `requirements.txt`, `pyproject.toml` hoặc `environment.yml` khi chưa có phê duyệt từ Antigravity.
- [ ] Không sử dụng các module không chuẩn hoặc thư viện bên ngoài không cần thiết.

### 5. Cổng Bảo Mật & Liêm Chính Dữ Liệu (Security & Privacy Gate)
- [ ] Không hardcode mật khẩu, token, API keys, credentials vào code.
- [ ] Đảm bảo tuân thủ `CMD_ZDR=1` cho các task đánh dấu sensitive.
- [ ] Không làm rò rỉ dữ liệu giữa tập Train và Test (bảo toàn nguyên tắc phân chia theo `Patient_ID`).

### 6. Cổng Độ Phức Tạp & Tiêu Chuẩn Mã Nguồn (Code Quality Gate)
- [ ] Mã nguồn tuân thủ nghiêm ngặt PEP 8, có đầy đủ Type Hints (`torch.Tensor`, `typing.Dict`, `typing.Optional`).
- [ ] Không lồng vòng lặp quá sâu, không viết code Spaghetti khó bảo trì.
- [ ] Đã xóa sạch 100% các file debug tạm thời, scratch logs hoặc test dumps.

### 7. Cổng Kiểm Thử Bổ Sung (Test Coverage Gate)
- [ ] Mọi logic mới hoặc nhánh rẽ thuật toán mới đều có ít nhất 1 Unit Test tương ứng trong thư mục `tests/`.

---

### Bảng Quyết Định (Decision Matrix):
- **APPROVE**: Thỏa mãn cả 7 cổng $\to$ Tiến hành `git merge task/<ID>-<slug>`, tạo commit chính thức và push.
- **CHANGES**: Rớt từ 1 đến 2 cổng nhỏ (ví dụ thiếu type hint hoặc test chưa pass) $\to$ Viết phản hồi cụ thể vào handoff yêu cầu sửa lại.
- **REPLAN**: Rớt cổng kiến trúc hoặc CommandCode sửa sai lệch hoàn toàn $\to$ Dừng nhánh, viết lại task hoặc điều chỉnh thiết kế.
