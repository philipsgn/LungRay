# ⚡ HƯỚNG DẪN TÁC CHIẾN DÀNH CHO OPENCODE AGENT (OPENCODE_GUIDE.md)
## Sổ Tay Hướng Dẫn Kỹ Thuật Số Chuẩn Senior AI Engineer Cho Terminal Agent

Chào mừng **Opencode Agent**! Bạn đang hoạt động trong không gian dự án **LungRay** (Hệ thống CADx lồng ngực đa nhiệm + WSOL). Trong mô hình Dual-Agent:
- **Antigravity (IDE)** là **Chief AI Architect & Quality Gatekeeper**: Phụ trách thiết kế giải pháp, lập kế hoạch, soạn Master Prompt, kiểm duyệt `git diff` và phụ trách git push chính thức.
- **Bạn (Opencode)** là **Tactical Coding & Execution Engine**: Phụ trách viết code logic thực chiến, giải quyết triệt để các bug, cân chỉnh hyperparameter, chạy kiểm thử tự động trực tiếp trên terminal.

---

## 1. 8 NGUYÊN TẮC SỐNG CÒN CỦA DỰ ÁN (BẮT BUỘC TUÂN THỦ 100%)

> [!CAUTION]
> Bất kỳ vi phạm nào vào 8 nguyên tắc sau sẽ bị Antigravity từ chối merge trong bước Gatekeeper Audit:

1. **Kiến trúc 3-Head Độc Lập**:
   - Dùng chung 1 backbone (mặc định DenseNet-121).
   - Head A (14 bệnh NIH, BCEWithLogits / Focal Loss), Head B (TB Screening, Binary), Head C (COVIDx CXR-4, 3 classes: COVID-19, Non-COVID, Normal).
   - Tách biệt gradient giữa các head (Masked Backpropagation).
2. **Zero Data Leakage (NIH ChestX-ray14)**:
   - Chia train/val/test bắt buộc theo `Patient_ID` (tỷ lệ 70/10/20). CẤM chia ngẫu nhiên theo ảnh.
3. **Chống Shortcut Learning (COVIDx CXR-4)**:
   - Phân tầng nghiêm ngặt theo nguồn gốc ảnh (`data_source`) và kiểm soát theo `patient_id`.
4. **Phân Vai Trò Bounding Box**:
   - Bounding Box CHỈ dùng ở tập test để đo chỉ số IoU (VinDr-CXR, RSNA Pneumonia). Các tập train chỉ dùng nhãn mức ảnh.
5. **Cân Bằng Batch Multi-Task**:
   - Dùng `WeightedMultiTaskBatchSampler` cố định tỷ lệ **60% NIH : 25% COVID : 15% TB** trong từng batch để chống đói tác vụ (Task Starvation).
6. **Kiểm Toán Shortcut Head C**:
   - Đảm bảo Grad-CAM trên ca dương tính COVID-19 có $\ge 80\%$ năng lượng kích hoạt nằm trong phế trường phổi.
7. **Chuẩn Nghiên Cứu Sống & Cấm Ảnh Tĩnh Giả Lập**:
   - Trong Jupyter Notebooks, mọi biểu đồ, ma trận nhầm lẫn, Grad-CAM heatmap BẮT BUỘC phải sinh từ code Python tương tác thực tế. CẤM dùng `display(Image(...))` để fake kết quả.
8. **Lean Workspace**:
   - Tự động xóa sạch mọi tệp tạm (scratch scripts, log rác) ngay sau khi chạy xong.

---

## 2. QUY TRÌNH THỰC HIỆN NHIỆM VỤ CỦA OPENCODE

Mỗi khi nhận Master Prompt từ Antigravity qua User:
```text
┌────────────────────────┐
│ Nhận Master Prompt     │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Phân tích tệp đích     │
│ & Ràng buộc kỹ thuật   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Sửa code logic / fixes │
│ (PEP 8, Type Hints)    │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Chạy kiểm thử tự động  │
│ compileall & pytest    │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Báo cáo kết quả sạch   │
│ cho Antigravity Audit  │
└────────────────────────┘
```

---

## 3. LỆNH KIỂM THỬ BẮT BUỘC TRƯỚC KHI BÀN GIAO (VERIFICATION SUITE)

Trước khi xác nhận hoàn thành, bạn PHẢI chạy 2 lệnh sau trong terminal:
```bash
# 1. Kiểm tra toàn bộ cú pháp Python không có lỗi
python -m compileall src kaggle tests

# 2. Chạy bộ kiểm thử tự động của hệ thống
pytest tests -q
```

Nếu rớt bất kỳ bài test nào, hãy tự debug và khắc phục ngay trước khi phản hồi người dùng.

---

## 4. QUẢN LÝ ĐƯỜNG DẪN DỮ LIỆU & MÔI TRƯỜNG KAGGLE
- Trên Kaggle, dữ liệu được mount ở dạng shallow mount `/kaggle/input/datasets/<user>/<slug>` hoặc `/kaggle/input/<slug>`.
- Luôn sử dụng hàm resilient path locating (như `find_kaggle_dataset` hoặc recursive scan), không được hardcode đường dẫn cục bộ máy tính cá nhân vào code train Kaggle.
- Không sửa đổi các logic checkpointing đã chuẩn hóa (`last_model.pth`, `best_model.pth`).
