# ⚡ COMMANDCODE CLI GO: QUICK OPERATING CHEATSHEET
<!-- VERIFY: Đối chiếu cú pháp lệnh mới nhất tại https://commandcode.ai/docs -->

Tài liệu này tóm tắt các lệnh tác chiến nhanh dành cho nhà phát triển khi sử dụng CommandCode CLI trong dự án LungRay:

## 1. Khởi Đầu Mỗi Phiên Làm Việc (Start Session Trên Nhánh Main)
```powershell
# 1. Bật chế độ Zero Data Retention cho code nghiên cứu nhạy cảm
$env:CMD_ZDR = "1"

# 2. Khởi chạy CommandCode CLI trực tiếp trên nhánh chính
cmd
```

## 2. Các Lệnh Nội Bộ Trong CommandCode CLI
- `/usage`: Xem số dư hạn mức credit Go (chạy ở đầu và cuối phiên).
- `/model`: Chuyển đổi model (theo bảng `docs/MODEL_ROUTING.md`):
  - Ví dụ: `/model kimi-k2.7-code` hoặc `/model deepseek-v4.1-flash`
- `/clear`: Xóa sạch ngữ cảnh khi bắt đầu một module hoàn toàn khác để tiết kiệm token; nếu 2 task liên tiếp kế thừa nhau (ví dụ: Frontend gọi Backend vừa viết), bạn có thể giữ nguyên session để model nhớ ngữ cảnh.

## 3. Câu Lệnh Mẫu Dán Cho CommandCode
```text
Đọc docs/HANDOFF/<ID>.md, làm đúng phạm vi cho phép, không sửa ngoài danh sách file, chạy scripts/verify.ps1 đạt 100% pass, rồi điền mục Result.
```

## 4. Nghiệm Thu & Đóng Phiên
```powershell
# Sau khi verify thành công và CommandCode điền Result:
git add .
git commit -m "feat(<ID>): <mô tả ngắn>"
# Quay lại Antigravity trong IDE để Review git diff
```
