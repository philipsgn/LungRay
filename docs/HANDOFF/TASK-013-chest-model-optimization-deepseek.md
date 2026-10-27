# HANDOFF: TASK-013 - Tối Ưu Hóa Logic Mô Hình Y Tế Đa Nhiệm Lồng Ngực (DeepSeek Tactical Engine)
> Trạng thái: READY_FOR_DEV | Model: T1/DeepSeek V4.1 Flash hoặc T2/DeepSeek-Coder | Env: CMD_ZDR=1

---

## 1. Mục Tiêu (Goal)
Tối ưu hóa toàn diện logic toán học, hàm mất mát (loss functions), cấu trúc phân nhánh 3-Head và pipeline huấn luyện chuyên khoa lồng ngực (Chest X-ray) trên nền tảng **LungRay**. Đảm bảo thuật toán đạt hiệu năng lâm sàng tối đa, triệt tiêu xung đột gradient giữa các nhiệm vụ, và tuân thủ tuyệt đối 8 Ràng buộc sống còn của dự án.

---

## 2. Phạm Vi Cho Phép (Scope - File được phép sửa và tối ưu hóa)
- `src/models/losses.py` (Hàm mất mát đa nhiệm, Focal Loss, Asymmetric Loss, Masked Multi-Task Loss)
- `src/models/multi_task_net.py` (Kiến trúc mạng 3-Head, Shared Encoder DenseNet-121/ResNet-50/ViT, feature pooling & projection)
- `src/data/transforms.py` (Medical augmentation an toàn, cấm lật dọc, chuẩn hóa ảnh ngực 512x512)
- `kaggle/train_multitask_kaggle.py` (Production training loop trên Kaggle, AMP, Cosine Annealing, Early Stopping)
- `tests/test_model_architecture.py` & `tests/test_loss_functions.py` (Bổ sung/cập nhật tests tương ứng nếu có nâng cấp logic)

---

## 3. Ngoài Phạm Vi (Strictly Out of Bounds - CẤM ĐỤNG)
- Tuyệt đối cấm sửa logic phân chia tập dữ liệu `src/data/dataset.py` và `src/data/sampler.py` (đã được khóa chặt để bảo đảm Zero Patient Leakage và tỉ lệ 60:25:15).
- Tuyệt đối cấm sửa backend FastAPI `app/backend/` và frontend Next.js `app/frontend/` trừ khi có chỉ đạo riêng.
- Cấm thêm thư viện lạ ngoài `requirements.txt`.

---

## 4. Các Yêu Cầu Kỹ Thuật Chi Tiết (Technical Specifications)

### 4.1. Hàm Mất Mát Chuyên Sâu Cho Lồng Ngực (`src/models/losses.py`)
1. **Head A (14 Bệnh NIH ChestX-ray14 - Multi-label Imbalance)**:
   - Hiện thực hóa/hoàn thiện `FocalLoss` ($\alpha=0.25, \gamma=2.0$) kết hợp khả năng tiếp nhận `pos_weight` động theo từng lớp để khắc phục tình trạng nhãn cực hiếm (Hernia $0.2\%$, Pneumothorax $5\%$, Infiltration $17\%$).
   - Bổ sung tùy chọn `AsymmetricLoss` (ASL: $\gamma_- = 4.0, \gamma_+ = 1.0, \text{clip} = 0.05$) để triệt tiêu các gradient âm tính dễ (easy negatives), giúp mô hình tập trung vào các tổn thương mờ khó thấy.
2. **Head B (Sàng lọc Lao phổi TB - Binary Classification)**:
   - Sử dụng `BCEWithLogitsLoss` với cơ chế tính Youden's J statistic để tìm ngưỡng tối ưu $\tau_B$.
3. **Head C (COVIDx CXR-4 3-Class hoặc Binary)**:
   - Sử dụng `CrossEntropyLoss` có trọng số lớp hoặc `FocalLoss` chống overfitting vào watermark máy chụp.
4. **Masked Multi-Task Loss Engine**:
   - Đảm bảo cơ chế cách ly gradient: Khi một mẫu thuộc Head A, gradient chỉ lan truyền ngược về Head A và Shared Backbone; Head B và Head C phải nhận gradient bằng 0 tuyệt đối (Zero Gradient Leakage).

### 4.2. Kiến Trúc Mạng 3-Head (`src/models/multi_task_net.py`)
1. **Shared Encoder Backbone**:
   - Mặc định: DenseNet-121 (`features.denseblock4` cho feature map $16 \times 16$ tại đầu vào $512 \times 512$).
   - Hỗ trợ linh hoạt ResNet-50 và Vision Transformer (ViT-B/16 có nội suy bicubic positional embeddings).
2. **Phân Nhánh 3-Head Độc Lập**:
   - Tầng trung gian: Global Average Pooling (GAP) $\to$ LayerNorm / BatchNorm $\to$ Dropout ($p=0.2$).
   - Head A: Linear projection ra 14 logits.
   - Head B: Linear projection ra 1 logit.
   - Head C: Linear projection ra 3 logits (hoặc 1 logit tùy cấu hình nhị phân).
   - Hàm `forward(x, task_id=None)`: Phải hỗ trợ trả về dictionary chứa đầy đủ predictions của cả 3 heads khi inference, hoặc chỉ tính toán riêng cho 1 head được yêu cầu để tiết kiệm FLOPs.

### 4.3. Biến Đổi Tăng Cường Dữ Liệu Y Tế An Toàn (`src/data/transforms.py`)
1. **Quy định bất di bất dịch**: **TUYỆT ĐỐI CẤM `RandomVerticalFlip`** vì giải phẫu lồng ngực có định hướng trên-dưới (vòm hoành luôn ở đáy, đỉnh phổi luôn ở trên). Lật dọc sẽ làm biến dạng hoàn toàn tri thức giải phẫu.
2. Các phép biến đổi cho phép và khuyến nghị:
   - `RandomHorizontalFlip(p=0.5)` (chú ý: nếu học phân biệt Dextrocardia / Tim bên phải thì cần kiểm soát, nhưng với NIH đa số là đảo chiều tư thế chụp).
   - `RandomRotation(degrees=(-7, 7))` mô phỏng bệnh nhân hơi nghiêng khi chụp tại giường.
   - `RandomAffine(degrees=0, translate=(0.04, 0.04), scale=(0.96, 1.04))`.
   - Điều chỉnh độ tương phản nhẹ và chuẩn hóa theo Mean/Std của bộ dữ liệu y tế hoặc ImageNet.

---

## 5. Tiêu Chí Nghiệm Thu Bắt Buộc (Acceptance Criteria)
- [ ] Tất cả các file trong phạm vi không có lỗi cú pháp: `python -m compileall src kaggle tests`
- [ ] Chạy lệnh kiểm thử đơn nhất và đạt **100% PASS (Exit Code 0)**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
  ```
- [ ] Không làm phá vỡ bất kỳ bài test nào trong số 99 tests hiện tại của hệ thống.
- [ ] Bổ sung ít nhất 2 unit tests kiểm thử các tính năng mới trong `tests/test_loss_functions.py` hoặc `tests/test_model_architecture.py`.

---

## 7. Result (CommandCode điền mục này trước khi bàn giao cho Antigravity)

- **Tóm tắt thay đổi**:
  - `losses.py`: `FocalLoss` nhận `pos_weight` động theo từng lớp (xử lý Hernia 0.2% / Infiltration 17%) và `alpha` dạng vector theo lớp; bổ sung `AsymmetricLoss` ($\gamma_-=4.0, \gamma_+=1.0, clip=0.05$) triệt tiêu easy negatives; `MaskedMultiTaskLoss` hỗ trợ Head A `bce|focal|asl` và Head C `bce|ce (class-weighted)|focal|asl`; toàn bộ class weight được đăng ký dưới dạng buffer để `.to(device)` không gây lệch thiết bị khi train GPU; zero-gradient isolation được giữ nguyên cho cả 3 tiêu chí mới.
  - `multi_task_net.py`: bổ sung projection GAP → LayerNorm (parameter-free) → Dropout(0.2) trước 3 head; `forward(x, task_id=...)` hỗ trợ `head_a/head_b/head_c`, alias `a/b/c`, `0/1/2` và chỉ tính head được chọn để tiết kiệm FLOPs; hỗ trợ Head C 3 lớp Softmax.
  - `transforms.py`: affine $\pm 7^\circ$, scale 0.96–1.04, translate 4%, CLAHE; cấm tuyệt đối `VerticalFlip`.
  - `kaggle/train_multitask_kaggle.py`: entrypoint huấn luyện tối ưu (AMP, Cosine Annealing, early stopping, resume, balanced sampler tái sử dụng từ `train_kaggle.py`) + hiệu chuẩn ngưỡng quyết định bằng Youden's J statistic trên val split và xuất `configs/optimal_thresholds.json`.
  - Tests: bổ sung 15 unit tests (10 loss + 5 kiến trúc/transform), toàn bộ 99 tests cũ vẫn PASS.

- **Danh sách file đã sửa**:
  - `src/models/losses.py`
  - `src/models/multi_task_net.py`
  - `src/data/transforms.py`
  - `kaggle/train_multitask_kaggle.py` (tạo mới)
  - `tests/test_loss_functions.py` (tạo mới)
  - `tests/test_model_architecture.py`
  - `src/explainability/grad_cam.py` (chỉ sửa 2 dòng giảm chiều 4D của nhánh Grad-CAM++ bậc cao; xem mục lưu ý)

- **Kết quả kiểm thử**:
  ```
  [+] Running: Compileall (Python Syntax Check)... [PASS]
  [+] Running: Ruff Linting... [PASS]
  [+] Running: Pytest Unit Tests... [PASS]
  ======================= 114 passed in 64.45s (0:01:04) =======================
  >>> SUCCESS: ALL CHECKS PASSED - READY FOR GATEKEEPER REVIEW <<<
  ```
  Bổ sung: `python -m compileall src kaggle tests -q` → OK (bao gồm cả script Kaggle mới).

- **Điểm cần lưu ý cho Antigravity Gatekeeper**:
  1. **Checkpoint compatibility**: LayerNorm dùng `elementwise_affine=False` nên không sinh key mới trong `state_dict`; `checkpoints/best_model.pth` hiện tại vẫn load `strict=True` trong FastAPI backend (đã được test `test_parameter_free_feature_norm_preserves_state_dict` xác nhận).
  2. **Hợp đồng API loss cũ**: `pos_weight_a` tiếp tục bị từ chối khi `head_a_criterion` là `focal`/`asl` (để không phá test hiện hữu); dynamic positive weighting cho Focal Loss sử dụng tham số mới `focal_pos_weight_a`.
  3. **Ngoài scope ban đầu**: `src/explainability/grad_cam.py` buộc phải sửa 2 dòng (`dim=(1,2)` → `dim=(2,3)` và lấy `[0]` cho channel weights). Nguyên nhân: việc thêm LayerNorm làm nhánh Grad-CAM++ bậc cao được kích hoạt, lộ lỗi giảm chiều 4D tiềm ẩn khiến `F.interpolate` nhận tensor 3D. Không thay đổi public API; 17/17 test explainability PASS.
  4. **Ngưỡng quyết định**: `tau_B` cho Head B và `tau_C` cho Head C được sinh tự động bằng Youden's J trong `train_multitask_kaggle.py`; nếu chạy `--no-calibrate` thì dùng `configs/optimal_thresholds.json` hiện có.
  5. **Head C taxonomy**: loader COVIDx hiện cấu hình nhị phân (`num_classes_c=1`); engine đã sẵn sàng cho 3 lớp (`ce_weight_c`) khi pipeline dữ liệu chuyển sang bài toán 3 lớp.

