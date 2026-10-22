# 🗓️ MASTER ENGINEERING PLAN (PLAN.md)
## Nền tảng LungRay: Hệ Thống Hỗ Trợ Chẩn Đoán & Định Vị Tổn Thương X-Quang Ngực Đa Nhiệm (LungRay Multi-Task CADx + WSOL XAI)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Nền tảng** | **LungRay** (AI Chest X-ray Multi-Task Diagnostic Platform) |
| **Tài liệu** | Kế Hoạch Kỹ Thuật Tổng Thể (Master Engineering Plan) |
| **Thời lượng** | 16 Tuần (Quy chuẩn Đồ án Tốt nghiệp & Sản phẩm Tiền Lâm sàng) |
| **Mục tiêu điểm số** | Điểm A/A+ ($\ge 85\%$) & Chuẩn bị công bố nghiên cứu |
| **Phê duyệt bởi** | Senior AI Engineer (10+ YOE) |

---

## 1. MỤC TIÊU CHIẾN LƯỢC & NGUYÊN TẮC QUẢN TRỊ DỰ ÁN

### 1.1. Mục tiêu chiến lược (Strategic Objectives)
1. **Hoàn thành đúng hạn 16 tuần** với kết quả nghiệm thu vượt benchmark công bố của các nghiên cứu nền tảng (CheXNet, Rajpurkar et al.; VinDr-CXR, Nguyen et al.).
2. **Minh bạch hóa liêm chính khoa học (Scientific Integrity)**: Đảm bảo 100% không xảy ra rò rỉ dữ liệu (zero data leakage) theo bệnh nhân và chứng minh mô hình vượt qua kiểm toán Shortcut Learning trên dữ liệu benchmark quốc tế COVIDx CXR-4.
3. **Định lượng hóa giá trị giải thích (Quantitative WSOL)**: Đạt Mean IoU $\ge 0.35$ trên tập VinDr-CXR, tạo sự khác biệt vượt trội so với các đồ án chỉ chụp ảnh heatmap định tính.
4. **Sản phẩm bàn giao hoàn chỉnh (Production-grade Deliverable)**: Hệ thống Full-stack Decoupled gồm FastAPI Backend containerized và Next.js PACS Viewer chạy mượt mà trước Hội đồng chấm thi trong thời gian $\le 2$ giây/ảnh.

### 1.2. 6 Cổng Kiểm Soát Chất Lượng Bắt Buộc (Quality Delivery Gates)
- [x] 🚪 **Gate 1 (Tuần 4) [HOÀN THÀNH XUẤT SẮC]**: Dữ liệu phân chia hoàn tất ($Train \cap Test = \emptyset$ theo `Patient_ID`). Chuẩn hóa 512x512 toàn diện: Xuất bản thành công 2 bộ Kaggle Datasets chất lượng cao: `lungray-nih-512` (112,120 ảnh, 100% Zero Leakage) và `lungray-covidx-512` (76.3k ảnh, Letterbox bảo tồn giải phẫu).
- [x] 🚪 **Gate 2 (Tuần 6) [HOÀN THÀNH — CONDITIONAL PASS]**: Checkpoint Baseline Multi-Task 3-Head đạt:
  - Head A (NIH 14 bệnh): Macro AUROC = **0.8271** (Chỉ tiêu $\ge 0.80$, **PASS**).
  - Head B (Lao phổi TB): AUROC = **1.0000** (Chỉ tiêu $\ge 0.90$, **PASS**).
  - Head C (COVIDx CXR-4): Test AUROC = **0.7342** (**CONDITIONAL PASS**, đề xuất rebalancing $w_{pos}=0.185$ & Focal Loss ở Phase 4).
  - Xuất bản Báo cáo nghiệm thu y khoa chuẩn mực: [results/baseline/BASELINE_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/results/baseline/BASELINE_REPORT.pdf).
- 🚪 **Gate 3 (Tuần 9) [MỤC TIÊU TIẾP THEO]**: Mô hình tối ưu hóa với Focal Loss + Threshold tuning đạt Macro AUC $\ge 0.82$, Macro F1 $\ge 0.45$. So sánh toàn diện CNN vs Vision Transformer.
- 🚪 **Gate 4 (Tuần 11)**: Module Grad-CAM xuất IoU $\ge 0.35$ trên VinDr-CXR & RSNA. Báo cáo Shortcut Learning Audit đạt tỷ lệ kích hoạt trong phổi $\ge 80\%$.
- 🚪 **Gate 5 (Tuần 13)**: Hệ thống Full-stack Dockerized hoạt động end-to-end; thời gian phản hồi $\le 2.0$ giây.
- 🚪 **Gate 6 (Tuần 16)**: Hoàn tất toàn bộ báo cáo 40–50 trang, slide 35–45 trang, poster A1 và video demo. Bảo vệ thành công trước Hội đồng.

---

## 2. LỘ TRÌNH TỔNG THỂ & PHÂN BỔ THỜI GIAN (16 TUẦN — TIẾN ĐỘ HIỆN TẠI: 50%)

```
[x] Tuần 01-02 [Phase 1]: Nghiên cứu lý thuyết, Đặc tả kiến trúc, Thiết lập môi trường (DONE)
[x] Tuần 03-04 [Phase 2]: Tải dữ liệu, EDA, Phân chia Patient-ID, Rescaling 512x512 Kaggle (DONE)
[x] Tuần 05-06 [Phase 3]: Huấn luyện Multi-Task 3-Head Baseline (DenseNet-121) (DONE - GATE 2 PASSED)
[▶] Tuần 07-09 [Phase 4]: Cải tiến mô hình: Focal Loss, ViT Transformer, Tuning ngưỡng (IN PROGRESS)
[ ] Tuần 10-11 [Phase 5]: Tích hợp XAI Grad-CAM, Đo đạc định lượng IoU, Shortcut Audit
[ ] Tuần 12-13 [Phase 6]: Xây dựng ứng dụng Web Full-stack (FastAPI + Next.js PACS Viewer)
[ ] Tuần 14-15 [Phase 7A]: Viết báo cáo đồ án, thiết kế slide thuyết trình, quay video demo
[ ] Tuần 16    [Phase 7B]: Tổng duyệt thử nghiệm, Bảo vệ đồ án chính thức trước Hội đồng
```

---

## 3. CHIẾN LƯỢC QUẢN TRỊ TÀI NGUYÊN TÍNH TOÁN (COMPUTE BUDGET)

### 3.1. Phân bổ phần cứng huấn luyện trên Kaggle Cloud
- **Hạn mức GPU Kaggle**: ~30 giờ GPU (NVIDIA P100 hoặc 2x T4) mỗi tuần cho mỗi tài khoản.
- **Chiến lược tối ưu hóa thời gian chạy**:
  1. *Local Prototyping (Dry Run)*: Toàn bộ code PyTorch, DataLoader, Loss Engine và Grad-CAM được chạy thử trên tập mini-subset (100 ảnh) tại máy local trước khi đẩy lên Kaggle.
  2. *Mixed Precision (FP16)*: Sử dụng `torch.cuda.amp` giúp giảm 50% thời gian huấn luyện mỗi epoch (ước tính 25-35 phút/epoch cho 112K ảnh với DenseNet-121).
  3. *Early Stopping & Checkpoint Pruning*: Dừng sớm sau 5 epochs nếu Validation Loss không cải thiện, chỉ lưu lại file trọng số tốt nhất `best_model.pth`.
- **Tổng ngân sách thời gian GPU dự kiến**:
  - Phase 3 (Baseline 25 epochs): ~12 giờ GPU.
  - Phase 4 (Focal Loss tuning + ViT fine-tune): ~20 giờ GPU.
  - Phase 5 (IoU Grounding & Audit runs): ~5 giờ GPU.
  - Tổng cộng: ~37 giờ GPU (phân bổ rải đều trong 3–4 tuần, hoàn toàn nằm trong hạn ngạch miễn phí).

---

## 4. MA TRẬN QUẢN TRỊ RỦI RO KỸ THUẬT (RISK MANAGEMENT MATRIX)

| Rủi ro kỹ thuật | Mức độ | Khả năng xảy ra | Biện pháp phòng ngừa chủ động | Kế hoạch xử lý khi phát sinh (Fallback) |
|:---|:---:|:---:|:---|:---|
| **Data Leakage giữa Train và Test** | CỰC KỲ CAO | TRUNG BÌNH | Bắt buộc gom nhóm theo `Patient_ID` từ Tuần 3, viết test assert $Train \cap Test = \emptyset$. | Nếu phát hiện rò rỉ, hủy toàn bộ checkpoint cũ, chia lại split và train lại từ đầu. |
| **Shortcut Learning trên COVIDx CXR-4** | CAO | CAO | Thực hiện Stratified Split theo nguồn ảnh gốc (`data_source`), cấm chia ngẫu nhiên theo ảnh. | Chạy Grad-CAM audit: Nếu kích hoạt bám viền/watermark $\to$ áp dụng Lung Masking tiền xử lý để cắt bỏ viền ngoài phổi. |
| **Task Starvation trong Multi-Task** | TRUNG BÌNH | CAO | Triển khai Weighted Batch Sampler cố định tỷ lệ 60:25:15 giữa NIH, COVIDx và TB trong mỗi batch. | Theo dõi Validation Loss riêng biệt; nếu một task không hội tụ, tăng trọng số sampling cho task đó. |
| **Mất cân bằng lớp cực hạn (Hernia 0.2%)** | CAO | CHẮC CHẮN | Áp dụng Focal Loss ($\gamma=2.0$) kết hợp Positive Class Weights và Youden's Index tuning. | Báo cáo khoảng tin cậy Bootstrap Confidence Interval thay vì con số AUC điểm đơn lẻ. |
| **Hết hạn mức GPU Kaggle hàng tuần** | TRUNG BÌNH | TRUNG BÌNH | Sử dụng 2 tài khoản Kaggle dự phòng hoặc chuyển đổi sang Google Colab T4/L4 khi cần. | Lưu checkpoint thường xuyên lên Kaggle Output / Google Drive để có thể tiếp tục train bất kỳ lúc nào. |
| **Thời gian suy luận Web Demo quá chậm** | TRUNG BÌNH | THẤP | Sử dụng TorchScript / Torch JIT tracing hoặc ONNX Runtime cho backend FastAPI với mixed precision FP16 ở kích thước $512 \times 512$. | Sử dụng mô hình DenseNet-121 gọn nhẹ kết hợp suy luận bất đồng bộ và bộ đệm tensor cache. |

---

## 5. CHIẾN LƯỢC KIỂM THỬ & ĐẢM BẢO CHẤT LƯỢNG (QA & TESTING PYRAMID)

```
        ▲
       / \     [Level 4: Clinical Sanity Checks & Defense Dry-Run]
      /   \    - 30 ca bệnh thực tế được bác sĩ/hội đồng thẩm định
     /-----\   [Level 3: XAI IoU Grounding & Shortcut Audit]
    /       \  - IoU >= 0.35 trên VinDr-CXR & RSNA; In-Lung Ratio >= 80%
   /---------\ [Level 2: ML Regression & Metric Benchmarks]
  /           \- Macro AUC >= 0.82; Macro F1 >= 0.45; Inference <= 2s
 /-------------\ [Level 1: Unit Tests & Data Integrity Assertions]
/               \- test_no_data_leakage(), test_batch_sampler(), test_masked_loss()
-----------------
```

1. **Unit Tests (Tự động hóa pytest)**:
   - `tests/test_data_leakage.py`: Kiểm tra tính độc lập tuyệt đối giữa các tập dữ liệu.
   - `tests/test_multi_task_sampler.py`: Kiểm tra tỷ lệ lấy mẫu giữa các nguồn trong mỗi batch.
   - `tests/test_masked_loss.py`: Kiểm tra gradient chỉ truyền qua head có mẫu tương ứng.
2. **Integration Tests**:
   - `tests/test_api_endpoints.py`: Kiểm tra phản hồi `/api/v1/predict`, `/api/v1/explain`, `/api/v1/audit`.
3. **Clinical Grounding & Audit**:
   - Chạy tự động script `scripts/run_audit.py` và `scripts/evaluate_iou.py` sinh báo cáo định lượng CSV.

---

## 6. QUY TẮC PHỐI HỢP GIT & PHÁT TRIỂN MÃ NGUỒN

- **Git Branching Model**:
  - `main`: Chỉ chứa mã nguồn ổn định, đã qua kiểm thử và sẵn sàng báo cáo.
  - `develop`: Nhánh tích hợp chính của dự án.
  - `feat/data-pipeline`: Công việc liên quan đến tải dữ liệu, EDA, splits, transforms.
  - `feat/model-training`: Mã nguồn kiến trúc mạng, loss, training loops.
  - `feat/xai-evaluation`: Mã nguồn Grad-CAM, IoU evaluation, Shortcut audit.
  - `feat/web-application`: Mã nguồn FastAPI backend và Next.js PACS frontend.
- **Commit Convention**: Chuẩn Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- **Mã nguồn đóng gói chuẩn Module**:
  Toàn bộ mã nguồn nằm trong package `src/`, cài đặt dưới dạng editable package: `pip install -e .`.
