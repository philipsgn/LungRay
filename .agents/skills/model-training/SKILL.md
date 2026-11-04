---
name: model-training
description: Quy trình khởi tạo kiến trúc Multi-Task 3-Head, cấu hình Masked Loss, huấn luyện hai giai đoạn và tối ưu ngưỡng quyết định trên Kaggle GPU.
---

# 🔄 SKILL: MULTI-TASK MODEL TRAINING & TUNING (LUNGRAY PLATFORM)
## Mã Quy Trình: SKILL-MODEL-TRAINING
## Dự án: Nền tảng LungRay
## Thực hiện bởi: `ModelArchitectAgent`

---

## 1. MỤC ĐÍCH
Quy trình hướng dẫn khởi tạo kiến trúc Multi-Task 3-Head, cấu hình Masked Loss, chạy thử nghiệm cục bộ và triển khai huấn luyện chính thức trên Kaggle GPU kèm tinh chỉnh ngưỡng quyết định.

---

## 2. CÁC BƯỚC THỰC THI (STEP-BY-STEP)

```
[Bước 1: Thiết lập File Cấu hình YAML] ──► [Bước 2: Chạy Dry-Run Cục bộ] ──► [Bước 3: Đẩy lên Kaggle GPU]
                                                                                        │
[Bước 6: Tối ưu Ngưỡng Quyết định tau_c] ◄── [Bước 5: Đánh giá AUC & F1] ◄── [Bước 4: Huấn luyện 2 Giai đoạn]
```

### Bước 1: Thiết lập File Cấu hình Thí nghiệm
Tạo file cấu hình trong `configs/baseline_densenet.yaml`:
```yaml
model:
  backbone: "densenet121"
  pretrained: true
  dropout: 0.2
  num_classes_head_a: 14
  num_classes_head_b: 1
  num_classes_head_c: 4

training:
  batch_size: 32
  num_workers: 4
  epochs: 25
  lr_stage1: 1e-3
  lr_stage2: 1e-5
  weight_decay: 1e-4
  amp: true
  early_stopping_patience: 5

loss:
  head_a_type: "focal" # hoặc "bce"
  focal_gamma: 2.0
  focal_alpha: 0.25
```

### Bước 2: Chạy Dry-Run Cục bộ (Local Verification)
Trước khi gửi code lên Kaggle, bắt buộc chạy thử nghiệm trên tập mini-subset (100 mẫu) tại máy cá nhân:
```bash
python scripts/train.py --config configs/baseline_densenet.yaml --dry-run --epochs 1
```
Xác nhận:
- Mạng nạp đúng trọng số ImageNet.
- Masked Loss tính toán chính xác, không sinh NaN/Inf.
- Checkpoint test được ghi thành công vào `checkpoints/`.

### Bước 3: Huấn luyện chính thức trên Kaggle GPU
1. Mở Kaggle Kernel, bật GPU Accelerator (Tesla P100 hoặc 2x T4).
2. Chạy lệnh huấn luyện chính thức:
   ```bash
   python scripts/train.py --config configs/baseline_densenet.yaml
   ```
3. Theo dõi diễn biến huấn luyện qua đường cong Validation Loss và AUC trên giao diện Weights & Biases hoặc TensorBoard.

### Bước 4: Chiến lược Huấn luyện 2 Giai đoạn (Two-Stage)
1. **Giai đoạn 1 (Epoch 1–5)**: Đóng băng toàn bộ tham số của Shared Backbone, chỉ cập nhật 3 classification heads với learning rate $10^{-3}$.
2. **Giai đoạn 2 (Epoch 6–25)**: Mở khóa toàn bộ tham số, fine-tune toàn mạng với learning rate nhỏ $10^{-5}$ kết hợp Cosine Annealing LR Scheduler.

### Bước 5: Đánh giá Checkpoint Tối ưu
Tải checkpoint `best_model.pth` về và chạy đánh giá trên Test Set độc lập:
```bash
python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --config configs/baseline_densenet.yaml
```
**Chỉ tiêu nghiệm thu**:
- Head A (NIH): Macro AUC $\ge 0.82$
- Head B (TB): AUC $\ge 0.90$
- Head C (COVID): Macro AUC $\ge 0.92$

### Bước 6: Tối ưu hóa Ngưỡng Quyết định ($\tau_c$)
Chạy script tìm ngưỡng tối ưu theo Youden's Index trên tập Validation:
```bash
python -m src.utils.threshold_tuning --checkpoint checkpoints/best_model.pth --output configs/optimal_thresholds.json
```
Xác nhận file `optimal_thresholds.json` chứa 14 giá trị ngưỡng riêng biệt, nâng Macro F1-Score lên $\ge 0.45$.

