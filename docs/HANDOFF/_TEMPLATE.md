# HANDOFF: [TASK-ID] - [Tên Task Ngắn Gọn]
> Trạng thái: READY_FOR_DEV | Model: [T1/T2/SENSITIVE] | Env: CMD_ZDR=1

## 1. Mục Tiêu (Goal)
[Mô tả cụ thể nhiệm vụ cần làm trong đúng 1 phiên CommandCode duy nhất]

## 2. Phạm Vi Cho Phép (Scope - File được phép sửa/tạo)
- `src/...`
- `tests/...`

## 3. Ngoài Phạm Vi (Strictly Out of Bounds - CẤM ĐỤNG)
- Tuyệt đối cấm sửa các file ngoài danh sách trên.
- Không sửa kiến trúc 3-Head, không thêm packages ngoài `requirements.txt`.

## 4. Interface / Chữ Ký Hàm Cần Tạo
```python
def example_function(param1: torch.Tensor, ratio: float = 0.8) -> dict:
    """Đặc tả input/output và kiểu dữ liệu bắt buộc."""
    pass
```

## 5. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] Chạy lệnh verify bắt buộc phải pass: `powershell -File scripts/verify.ps1`
- [ ] [Tiêu chí bổ sung cụ thể nếu có]

## 6. Gợi Ý Model & Mức Nhạy Cảm
- **Mức nhạy cảm**: [Sensitive (CMD_ZDR=1) | Public/Open]
- **Tầng model khuyến nghị**: [T1: DeepSeek V4.1 Flash (giờ thấp điểm) | T2: Kimi K2.7 Code / GLM-5.3]

---

## 7. Result (CommandCode điền mục này trước khi báo xong)
- **Tóm tắt thay đổi**: [Điền ngắn gọn 2-3 câu]
- **Danh sách file đã sửa**: [Liệt kê các file]
- **Kết quả kiểm thử**: [Paste output hoặc trạng thái chạy `scripts/verify.ps1`]
- **Điểm chưa chắc / Cần review kỹ**: [Ghi chú nếu có vấn đề phát sinh]
