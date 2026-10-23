# 📋 LUNGRAY: KẾ HOẠCH & KIẾN TRÚC TỔNG THỂ (docs/PLAN.md)
## Mục Tiêu, Kiến Trúc Cốt Lõi & 8 Ràng Buộc Sống Còn

---

### 1. MỤC TIÊU DỰ ÁN
- **Hệ thống**: LungRay — Nền tảng CADx đa nhiệm lồng ngực kết hợp định vị tổn thương suy yếu (WSOL) trên ảnh X-quang ngực thẳng (PA/AP).
- **Stack công nghệ**: Python 3.10+, PyTorch, Torchvision/Timm, Albumentations, FastAPI, Next.js PACS Viewer.
- **3 Tác vụ lâm sàng song song**:
  - **Head A (NIH ChestX-ray14)**: Phân loại đa nhãn 14 bệnh lý lồng ngực ($C=14$, BCEWithLogits / Focal Loss).
  - **Head B (TB Radiography)**: Sàng lọc nhị phân Lao phổi ($C=1$, Binary Sigmoid).
  - **Head C (COVIDx CXR-4)**: Phân loại nhị phân COVID-19 vs Non-COVID/Normal ($C=1$, Anti-Shortcut CLAHE/Crop).
- **XAI & WSOL**: Trích xuất activation map bằng Grad-CAM/Grad-CAM++, nhị phân hóa thích nghi và đánh giá IoU định lượng trên VinDr-CXR và RSNA Pneumonia.

---

### 2. KIẾN TRÚC KỸ THUẬT CỐT LÕI (TECHNICAL ARCHITECTURE)
1. **Shared Backbone Network**: 1 encoder duy nhất (DenseNet-121 mặc định, tùy chọn ResNet-50 / ViT) sinh feature map chung $F \in \mathbb{R}^{B \times 1024 \times 7 \times 7}$.
2. **Multi-Head Pooling & Projection**:
   - Head A: Global Average Pooling $\to$ Linear(1024, 14)
   - Head B: Global Average Pooling $\to$ Linear(1024, 1)
   - Head C: Global Average Pooling $\to$ Linear(1024, 1)
3. **Masked Loss Engine**: Cô lập gradient giữa các head. Khi ảnh thuộc dataset của Head $k$, chỉ tính loss và backpropagation trên Head $k$; loss các head còn lại bị mask về 0.
4. **WeightedMultiTaskBatchSampler**: Cố định tỷ lệ mẫu trong mỗi mini-batch là **60% NIH : 25% COVIDx : 15% TB** để ngăn ngừa đói tác vụ (Task Starvation).

---

### 3. QUYẾT ĐỊNH ĐÃ CHỐT & 8 RÀNG BUỘC SỐNG CÒN (INVIOLABLE CONSTRAINTS)

| Ràng buộc | Nội dung bắt buộc | Cơ chế kiểm toán |
|:---|:---|:---|
| 🔴 **1. Kiến trúc 3-Head** | Dùng chung 1 backbone cho Head A, B, C; tách gradient bằng mask loss. | Code review & PyTorch Graph audit |
| 🔴 **2. Zero Data Leakage** | NIH ChestX-ray14 bắt buộc chia theo `Patient_ID` (70/10/20). Cấm chia theo ảnh. | `tests/test_data_leakage.py` |
| 🔴 **3. Chống Shortcut Learning** | COVIDx CXR-4 bắt buộc phân tầng theo `data_source` và kiểm soát theo `patient_id`. | Phân tích phân phối metadata nguồn |
| 🔴 **4. Phân vai trò Bounding Box** | Bounding Box CHỈ dùng cho tập test (VinDr-CXR, RSNA Pneumonia) để tính IoU. Train hoàn toàn nhãn mức ảnh. | Kiểm tra DataLoader huấn luyện |
| 🔴 **5. Cân bằng Batch Multi-Task** | Bắt buộc dùng `WeightedMultiTaskBatchSampler` tỷ lệ 60:25:15. | Unit test batch sampler distribution |
| 🔴 **6. Kiểm toán Shortcut Head C** | Năng lượng Grad-CAM trên ca dương tính COVID-19 trong phế trường phổi phải đạt $\ge 80\%$. | `src/explainability/shortcut_audit.py` |
| 🔴 **7. Chuẩn Nghiên cứu Sống** | Mọi kết quả, biểu đồ, Grad-CAM trong notebooks BẮT BUỘC sinh trực tiếp từ code Python thực tế. Cấm ảnh tĩnh giả lập. | Notebook execution inspection |
| 🔴 **8. Tinh gọn Workspace** | Tự động xóa sạch mọi file tạm/scratch scripts ngay sau khi thực thi. | Git status & Lean Workspace check |

---

### 4. QUY TRÌNH HỢP TÁC 2 TẦNG (ANTIGRAVITY + COMMANDCODE GO)
- **Kênh bàn giao**: Duy nhất qua Git và file Markdown `docs/HANDOFF/<ID>.md`.
- **Phân định**: Antigravity phụ trách kiến trúc, plan, handoff, code review `git diff` và git commit/push. CommandCode Go CLI phụ trách viết mã logic chi tiết, kiểm thử tự động `scripts/verify.ps1` và điền kết quả `Result`.
- **Ngân sách**: Bật `CMD_ZDR=1` cho code nghiên cứu cá nhân. Kiểm soát `/usage` sau mỗi phiên.
