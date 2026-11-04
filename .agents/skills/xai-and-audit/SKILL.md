---
name: xai-and-audit
description: Quy trình tích hợp Grad-CAM, đo lường định lượng chỉ số IoU so với Bounding Box chuyên gia trên VinDr-CXR/RSNA và kiểm toán rủi ro Shortcut Learning.
---

# 🔄 SKILL: EXPLAINABILITY (XAI), WSOL IOU & SHORTCUT AUDIT (LUNGRAY PLATFORM)
## Mã Quy Trình: SKILL-XAI-AND-AUDIT
## Dự án: Nền tảng LungRay
## Thực hiện bởi: `XAIEvalAgent`

---

## 1. MỤC ĐÍCH
Quy trình hướng dẫn tích hợp Grad-CAM, thực hiện đo lường định lượng chỉ số IoU so với Bounding Box chuyên gia trên VinDr-CXR/RSNA và kiểm toán rủi ro Shortcut Learning trên COVID-19.

---

## 2. CÁC BƯỚC THỰC THI (STEP-BY-STEP)

```
[Bước 1: Khởi tạo Grad-CAM Engine] ──► [Bước 2: Đo lường IoU VinDr-CXR & RSNA] ──► [Bước 3: Chạy Shortcut Audit COVID]
                                                                                               │
[Bước 5: Tổng hợp Báo cáo XAI]   ◄── [Bước 4: External Test CheXpert-small] ◄─────────────────┘
```

### Bước 1: Khởi tạo Module Grad-CAM
1. Nạp checkpoint `best_model.pth`.
2. Khởi tạo `GradCAMExplainer` nhắm vào tầng tích chập cuối cùng:
```python
from src.explainability.grad_cam import GradCAMExplainer
from src.models.multi_task_net import MultiTaskChestXrayNet

model = MultiTaskChestXrayNet.load_from_checkpoint("checkpoints/best_model.pth")
explainer = GradCAMExplainer(model=model, target_layer=model.backbone.features.denseblock4)
```

### Bước 2: Đo lường Định lượng IoU (WSOL Grounding)
1. Chạy script đánh giá IoU trên tập kiểm thử có Bounding Box:
   ```bash
   python scripts/evaluate_iou.py --checkpoint checkpoints/best_model.pth \
                                  --vindr-test data/raw/vindr_cxr/annotations_test.csv \
                                  --rsna-test data/raw/rsna/stage_2_train_labels.csv \
                                  --alpha 0.3 \
                                  --output results/iou_evaluation.csv
   ```
2. Kiểm tra kết quả trong `results/iou_evaluation.csv`:
   - Xác nhận **Mean IoU $\ge 0.35$** trên các mẫu True Positive cho 8 lớp bệnh của VinDr-CXR và nhãn Pneumonia của RSNA.

### Bước 3: Thực thi Kiểm toán Shortcut Learning Audit (Head C)
1. Chạy quy trình kiểm toán độc lập trên toàn bộ ca dương tính COVID-19 trong tập kiểm thử:
   ```bash
   python scripts/run_audit.py --checkpoint checkpoints/best_model.pth \
                               --covid-test data/splits/covid_splits.csv \
                               --output results/shortcut_learning_audit.csv
   ```
2. Thuật toán phân tích:
   - Trích xuất mặt nạ phổi $P_{\text{lung}}$.
   - Tính tỷ lệ năng lượng nhiệt Grad-CAM nằm trong phổi:
     $$\text{In-Lung Ratio} = \frac{\sum_{P_{\text{lung}}} M_{\text{COVID}}}{\sum_{\text{Total}} M_{\text{COVID}}}$$
3. **Tiêu chuẩn vượt qua**: Tỷ lệ trung bình $\ge 80\%$. Không có sự kích hoạt tập trung tại góc có watermark hoặc viền đen máy chụp.

### Bước 4: Kiểm định Tổng quát hóa Ngoại vi (External Generalization)
1. Đánh giá Head A trên tập `CheXpert-small-v1`:
   ```bash
   python scripts/evaluate_generalization.py --checkpoint checkpoints/best_model.pth \
                                            --chexpert-data data/raw/chexpert_small/ \
                                            --output results/chexpert_generalization_results.csv
   ```
2. Xác nhận mức suy giảm AUC $\le 0.10$ so với trên tập NIH test set.

### Bước 5: Tổng hợp Artifacts Báo cáo
Lưu trữ toàn bộ bảng số liệu và ảnh minh họa 30 ca tiêu biểu vào thư mục `results/`:
- `results/iou_evaluation.csv`
- `results/shortcut_learning_audit.csv`
- `results/chexpert_generalization_results.csv`
- `results/xai_sample_overlays.png`

