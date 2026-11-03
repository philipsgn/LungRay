# MASTER ENGINEERING PLAN (PLAN.md)
## Nền tảng LungRay: Hệ Thống Hỗ Trợ Chẩn Đoán & Định Vị Tổn Thương X-Quang Ngực Đa Nhiệm (LungRay Multi-Task CADx + WSOL XAI)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Nền tảng** | **LungRay** (AI Chest X-ray Multi-Task Diagnostic Platform) |
| **Tài liệu** | Kế Hoạch Kỹ Thuật Tổng Thể (Master Engineering Plan) |
| **Phiên bản** | **v8.5 (Delivery Gate 6 Approved — 100.0% Progress — Final Defense Ready)** |
| **Thời lượng** | 18 Tuần (Quy chuẩn Đồ án Tốt nghiệp & Sản phẩm Tiền Lâm sàng) |
| **Mục tiêu điểm số** | Điểm A/A+ ($\ge 85\%$) & Chuẩn bị công bố nghiên cứu quốc tế |
| **Phê duyệt bởi** | Senior AI Engineer / Staff AI Architect (10+ YOE) & Quality Gatekeeper |

---

## 1. MỤC TIÊU CHIẾN LƯỢC & NGUYÊN TẮC QUẢN TRỊ DỰ ÁN

### 1.1. Mục tiêu chiến lược (Strategic Objectives)
1. **Hoàn thành đúng hạn 18 tuần** với kết quả nghiệm thu vượt benchmark công bố của các nghiên cứu nền tảng (CheXNet, Rajpurkar et al.; VinDr-CXR, Nguyen et al.).
2. **Minh bạch hóa liêm chính khoa học (Scientific Integrity)**: Đảm bảo 100% không xảy ra rò rỉ dữ liệu (zero data leakage) theo bệnh nhân và chứng minh mô hình vượt qua kiểm toán Shortcut Learning trên dữ liệu benchmark quốc tế COVIDx CXR-4.
3. **Định lượng hóa giá trị giải thích (Quantitative WSOL)**: Đạt Mean IoU $\ge 0.35$ trên tập VinDr-CXR (thực tế đạt 0.6049) và RSNA (thực tế đạt 0.7631), tạo sự khác biệt vượt trội so với các đồ án chỉ chụp ảnh heatmap định tính.
4. **Lớp phòng vệ an toàn lâm sàng (Fail-Safe Defense Layer)**: Phát hiện và từ chối (REJECT) các ảnh bất thường ngoại lai (OOD) bằng Năng lượng tự do Helmholtz ($S_E \ge 9.0421$) và Shannon Entropy ($H \le 0.6275$), ngăn chặn chẩn đoán tự tin giả tạo.
5. **Sản phẩm bàn giao hoàn chỉnh (Production-grade Deliverable)**: Hệ thống Full-stack Decoupled gồm FastAPI Backend và Next.js PACS Viewer phòng tối (`#070B12`) chạy mượt mà trước Hội đồng chấm thi trong thời gian $\le 1.8$ giây/ảnh.

### 1.2. 6 Cổng Kiểm Soát Chất Lượng Bắt Buộc (Quality Delivery Gates)
- **Gate 1 (Tuần 4) [HOÀN THÀNH XUẤT SẮC]**: Dữ liệu phân chia hoàn tất ($Train \cap Test = \emptyset$ theo `Patient_ID`). Chuẩn hóa 512x512 toàn diện: Xuất bản thành công 2 bộ Kaggle Datasets chất lượng cao: `lungray-nih-512` (112,120 ảnh, 100% Zero Leakage) và `lungray-covidx-512` (76.3k ảnh, Letterbox bảo tồn giải phẫu).
- **Gate 2 (Tuần 6) [HOÀN THÀNH — CONDITIONAL PASS]**: Checkpoint Baseline Multi-Task 3-Head đạt:
  - Head A (NIH 14 bệnh): Macro AUROC = **0.8271** (Chỉ tiêu $\ge 0.80$, **PASS**).
  - Head B (Lao phổi TB): AUROC = **1.0000** (Chỉ tiêu $\ge 0.90$, **PASS**).
  - Head C (COVIDx CXR-4): Test AUROC = **0.7342** (**CONDITIONAL PASS**, đề xuất rebalancing $w_{pos}=0.185$ & Focal Loss ở Phase 4).
  - Xuất bản Báo cáo nghiệm thu y khoa chuẩn mực: [results/baseline/BASELINE_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/results/baseline/BASELINE_REPORT.pdf).
- **Gate 3 (Tuần 9) [HOÀN THÀNH & VERIFIED — UPGRADED VIA TASK-013]**: Tích hợp Focal Loss ($\alpha=0.25, \gamma=2.0$) với `pos_weight` động và Asymmetric Loss (ASL $\gamma_-=4.0, \gamma_+=1.0, \text{clip}=0.05$) triệt tiêu easy negatives cho Head A; tích hợp parameter-free LayerNorm projection và per-task forward execution trên `MultiTaskChestXrayNet`; tối ưu hóa 16 ngưỡng quyết định $\tau_c$ theo Youden's J statistic (`configs/optimal_thresholds.json`).
- **Gate 4 (Tuần 11) [HOÀN THÀNH XUẤT SẮC]**: Module Grad-CAM trích xuất chuẩn xác. Đo đạc IoU định lượng đạt **RSNA Mean Box-IoU = 0.7631** và **VinDr-CXR Mean Box-IoU = 0.6049** (vượt xa chỉ tiêu $\ge 0.35$). Báo cáo Shortcut Learning Audit đạt **In-lung energy ratio = 94.92% $\pm$ 1.60%** (100% ca bệnh đạt, triệt tiêu shortcut ngoài viền ảnh). Xuất bản [reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/reports/SHORTCUT_LEARNING_AUDIT_REPORT.pdf).
- **Gate 5 (Tuần 13) [HOÀN THÀNH & VERIFIED]**: FastAPI Microservice Backend 4 endpoints (`/health`, `/predict`, `/explain`, `/audit`) nạp trọng số thật từ `checkpoints/best_model.pth` tích hợp giải thuật Clinical Pulmonary Grounding; Next.js 14 Medical PACS Viewer phòng tối (`#070B12`) tương tác mượt mà cho phép chọn giải thích từng bệnh lý cụ thể (14 bệnh NIH, Lao phổi TB, COVID-19), chuyển đổi chế độ kép Clinical/Raw Attention, Alpha Heatmap Slider và trình khởi chạy 1-Click Native Launcher.
- **Gate 6 (Tuần 16–18) [HOÀN THÀNH XUẤT SẮC — FINAL CLOSURE]**:
  - Xuất bản Báo cáo Khoa học Final chuẩn MICCAI/IEEE `reports/FINAL_SCIENTIFIC_REPORT.pdf` (1.63 MB, 20–25 trang in, Rule 9).
  - Hoàn thiện Đề cương Slide Bảo vệ 40 trang `reports/DEFENSE_SLIDES_OUTLINE.md`.
  - Bộ 25 câu hỏi phản biện lâm sàng `docs/defense_faq.md`.
  - Đóng gói Task 7.3 qua Kịch bản Video Demo Song ngữ 180s `reports/DEMO_WALKTHROUGH_SCRIPT.md` và gói 4 ảnh mẫu `demo_samples/`.
  - **125 / 125 Unit Tests toàn hệ sinh thái đạt PASS 100%**.

---

## 2. MA TRẬN ĐIỀU HÀNH 8 GIAI ĐOẠN & ÁNH XẠ DELIVERY GATES (TIẾN ĐỘ: 100.0%)

Bảng tổng hợp chi tiết lộ trình thực hiện 18 tuần, ánh xạ trực tiếp sang các Cổng kiểm soát chất lượng và sản phẩm bàn giao:

| Giai đoạn | Tên Giai Đoạn | Khoảng Thời Gian | Cổng Nghiệm Thu | Tiến Độ Thực Tế | Sản Phẩm Bàn Giao Cốt Lõi |
|:---|:---|:---:|:---:|:---:|:---|
| **Phase 1** | Research, Architecture & Workspace Setup | Tuần 01–02 | Preparation for Gate 1 | 100% COMPLETED | PRD v8.5, TECH_ARCHITECTURE, 9 Ràng buộc Sống còn, Môi trường PyTorch |
| **Phase 2** | Data Ingestion, Leakage Splits & 512 Rescaling | Tuần 03–04 | **Delivery Gate 1 Approved** | 100% COMPLETED | `patient_splits.csv` (70/10/20), `lungray-nih-512`, `lungray-covidx-512`, Batch Sampler 60:25:15 |
| **Phase 3** | Multi-Task Baseline Model Training | Tuần 05–06 | **Delivery Gate 2 Approved** | 100% COMPLETED | Checkpoint DenseNet-121 baseline, `BASELINE_REPORT.pdf`, Macro AUC A: 0.8271, B: 1.0000 |
| **Phase 4** | SOTA Optimization, ASL & Tuning (TASK-013) | Tuần 07–09 | **Delivery Gate 3 Approved** | 100% COMPLETED | Asymmetric Loss, Focal Loss pos_weight động, LayerNorm parameter-free, Youden's J JSON |
| **Phase 5** | XAI Grad-CAM, IoU Grounding & Shortcut Audit | Tuần 10–11 | **Delivery Gate 4 & 5 Approved**| 100% COMPLETED | RSNA IoU: 0.7631, VinDr IoU: 0.6049, In-lung ratio: 94.92%, `SHORTCUT_LEARNING_AUDIT_REPORT.pdf` |
| **Phase 6** | Full-Stack Medical PACS Web & FastAPI Serving | Tuần 12–13 | **Delivery Gate 5 Approved** | 100% COMPLETED | FastAPI microservice, Next.js 14 PACS UI Darkroom (`#070B12`), 1-Click Launcher, Latency $\le 1.8$s |
| **Phase 7** | Comprehensive Reports, Thesis & Defense Prep | Tuần 14–16 | **Delivery Gate 6 Approved** | 100% COMPLETED | `FINAL_SCIENTIFIC_REPORT.pdf`, Slide 40 trang, 25 FAQs, Demo Script Song Ngữ 180s & `demo_samples/` |
| **Phase 8** | Clinical Fail-Safe Layer, OOD & Grounded Report| Tuần 17–18 | **Safety Gate Approved** | 100% COMPLETED | Sigmoid Free Energy, Shannon Entropy, Reject Policy Lockout, Báo cáo ICD-10, 125 Unit Tests |

---

## 3. CHIẾN LƯỢC QUẢN TRỊ TÀI NGUYÊN TÍNH TOÁN (COMPUTE BUDGET)

### 3.1. Phân bổ phần cứng huấn luyện trên Kaggle Cloud
- **Hạn mức GPU Kaggle**: ~30 giờ GPU (NVIDIA P100 hoặc 2x T4) mỗi tuần cho mỗi tài khoản.
- **Chiến lược tối ưu hóa thời gian chạy**:
  1. *Local Prototyping (Dry Run)*: Toàn bộ code PyTorch, DataLoader, Loss Engine và Grad-CAM được chạy thử trên tập mini-subset (100 ảnh) tại máy local trước khi đẩy lên Kaggle.
  2. *Mixed Precision (FP16)*: Sử dụng `torch.amp.autocast("cuda")` giúp giảm 50% thời gian huấn luyện mỗi epoch.
  3. *Early Stopping & Atomic Checkpointing*: Dừng sớm sau 5 epochs nếu Validation Loss không cải thiện, chỉ lưu lại file trọng số tốt nhất `best_model.pth`.
- **Tổng ngân sách thời gian GPU thực tế**:
  - Phase 3 (Baseline 25 epochs): ~12 giờ GPU.
  - Phase 4 (Focal Loss / ASL tuning + ViT benchmark): ~20 giờ GPU.
  - Phase 5 (IoU Grounding & Audit runs): ~5 giờ GPU.
  - Tổng cộng: ~37 giờ GPU (hoàn toàn nằm trong hạn ngạch miễn phí).

---

## 4. MA TRẬN QUẢN TRỊ RỦI RO KỸ THUẬT (RISK MANAGEMENT MATRIX)

| Rủi ro kỹ thuật | Mức độ | Khả năng xảy ra | Biện pháp phòng ngừa chủ động | Kế hoạch xử lý khi phát sinh (Fallback) |
|:---|:---:|:---:|:---|:---|
| **Data Leakage giữa Train và Test** | CỰC KỲ CAO | TRUNG BÌNH | Bắt buộc gom nhóm theo `Patient_ID` từ Tuần 3, viết test assert $Train \cap Test = \emptyset$. | Nếu phát hiện rò rỉ, hủy toàn bộ checkpoint cũ, chia lại split và train lại từ đầu. |
| **Shortcut Learning trên COVIDx CXR-4** | CAO | CAO | Thực hiện Stratified Split theo nguồn ảnh gốc (`data_source`), cấm chia ngẫu nhiên theo ảnh. | Chạy Grad-CAM audit: Áp dụng Clinical Pulmonary Grounding triệt tiêu gradient ngoài lồng ngực. |
| **Task Starvation trong Multi-Task** | TRUNG BÌNH | CAO | Triển khai Weighted Batch Sampler cố định tỷ lệ 60:25:15 giữa NIH, COVIDx và TB trong mỗi batch. | Theo dõi Validation Loss riêng biệt; nếu một task không hội tụ, tăng trọng số sampling cho task đó. |
| **Mất cân bằng lớp cực hạn (Hernia 0.2%)** | CAO | CHẮC CHẮN | Áp dụng Asymmetric Loss ($\gamma_-=4.0$) kết hợp Focal Loss positive weights động và Youden's J threshold tuning. | Báo cáo khoảng tin cậy Bootstrap Confidence Interval thay vì con số AUC điểm đơn lẻ. |
| **Ảo tưởng tự tin trên ảnh ngoại lai (OOD)**| CAO | CAO | Xây dựng Phase 8 Fail-Safe Layer tính toán năng lượng Helmholtz và Shannon Entropy hậu nghiệm. | Tự động kích hoạt cờ REJECT LOCKOUT và khóa sinh báo cáo khi $S_E < 9.0421$ hoặc $H > 0.6275$. |

---

## 5. CHIẾN LƯỢC KIỂM THỬ & ĐẢM BẢO CHẤT LƯỢNG (QA & TESTING PYRAMID)

```
        ▲
       / \     [Level 5: Clinical Sanity Checks & Defense Dry-Run]
      /   \    - 30 ca bệnh thực tế được bác sĩ thẩm định, 25 FAQs, Demo Walkthrough Script
     /-----\   [Level 4: OOD Fail-Safe Detection & Rejection Policy]
    /       \  - Helmholtz Energy (AUROC 1.0000); Shannon Entropy <= 0.6275
   /---------\ [Level 3: XAI IoU Grounding & Shortcut Audit]
  /           \- IoU >= 0.35 trên VinDr & RSNA; In-Lung Ratio >= 80% (94.92%)
 /-------------\ [Level 2: ML Regression & Metric Benchmarks]
/               \- Macro AUC >= 0.82; Macro F1 >= 0.45; Latency <= 1.8s
----------------- [Level 1: Automated Unit Tests (125 pytest items)]
                  - test_data_pipeline, test_loss_functions, test_ood_safety...
```

### Danh Mục 11 Modules Kiểm Thử Thực Tế Trong `tests/` (125 Test Items)
Toàn bộ danh mục test được kiểm chứng thực tế trên ổ đĩa, loại bỏ hoàn toàn các tệp tham chiếu ảo:

1. **`tests/test_data_pipeline.py` (8 items)**:
   Xác thực thuật toán phân chia Zero Patient Leakage ($Train \cap Test = \emptyset$), phân tầng nguồn gốc COVIDx CXR-4, stratified split cho TB, và tỷ lệ phân bổ $60:25:15$ của `WeightedMultiTaskBatchSampler`.
2. **`tests/test_model_architecture.py` (11 items)**:
   Kiểm tra kích thước tensor đầu ra $(B, 14)$, $(B, 1)$, $(B, 1/3)$; xác suất Sigmoid/Softmax; tính bảo tồn `state_dict` của LayerNorm parameter-free (`elementwise_affine=False`); thực thi per-task forward; và kiểm tra transforms y tế an toàn (cấm lật dọc).
3. **`tests/test_loss_functions.py` (10 items)**:
   Xác thực cơ chế triệt tiêu easy negatives của Asymmetric Loss; dynamic `pos_weight` buffer và vector $\alpha$ của Focal Loss; cô lập gradient tuyệt đối (Zero Gradient Leakage) của `MaskedMultiTaskLoss`.
4. **`tests/test_threshold_tuning.py` (35 items)**:
   Kiểm tra thuật toán cực đại hóa chỉ số Youden's J ($J = \text{TPR} - \text{FPR}$), tối ưu hóa F1 score, hiệu chuẩn ngưỡng đa nhãn, nạp/lưu file JSON `configs/optimal_thresholds.json` và xử lý biên đơn lớp.
5. **`tests/test_explainability.py` (17 items)**:
   Kiểm tra vòng đời hooks Grad-CAM và Grad-CAM++ bậc cao, trích xuất activation maps cho cả 3 heads, và tạo ảnh hòa trộn RGB overlay.
6. **`tests/test_wsol_metrics.py` (10 items)**:
   Xác thực thuật toán Adaptive Binarization, chỉ số Box-level IoU, Pixel Mask-IoU so với Bounding Box chuyên gia trên VinDr-CXR và RSNA Pneumonia.
7. **`tests/test_ood_safety.py` (11 items)**:
   Kiểm tra tính đơn điệu của Sigmoid Free Energy, biên giá trị Shannon Entropy, Max-Sigmoid confidence, chính sách ACCEPT/REJECT của SafetyPolicy, trích xuất 6 vùng giải phẫu phổi, và cơ chế khóa cứng BLOCKED của ClinicalReportGenerator.
8. **`tests/test_api_backend.py` (8 items)**:
   Kiểm tra các endpoints FastAPI (`/health`, `/predict`, `/explain`, `/audit`), công tắc lọc giải phẫu Clinical Pulmonary Grounding và chế độ Raw Attention.
9. **`tests/test_ingestion.py` (6 items)**:
   Kiểm tra cơ chế tự động dò tìm đường dẫn dataset trên Kaggle `/kaggle/input/` và ổ đĩa cục bộ, xử lý thư mục lồng nhau và tính toàn vẹn metadata.
10. **`tests/test_production_experiments.py` (4 items)**:
    Đánh giá đối chuẩn kiến trúc (DenseNet vs ResNet vs ViT), kiểm định Bootstrap 1.000 lần 95% CI và tổng quát hóa ngoại vi trên Stanford CheXpert-small-v1.
11. **`tests/test_environment.py` (5 items)**:
    Kiểm tra môi trường thực thi Python 3.10, PyTorch, CUDA, albumentations, timm và OpenCV dependencies.

**Quy chuẩn nghiệm thu**: Chạy MỘT lệnh duy nhất đạt 100% PASS:
```powershell
powershell -File scripts/verify.ps1
```

---

## 6. QUY TẮC PHỐI HỢP GIT & PHÁT TRIỂN MÃ NGUỒN

- **Git Branching Model**:
  - `main`: Chỉ chứa mã nguồn ổn định, đã qua kiểm thử và sẵn sàng báo cáo.
  - `develop`: Nhánh tích hợp chính của dự án.
- **Commit Convention**: Chuẩn Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- **Mã nguồn đóng gói chuẩn Module**:
  Toàn bộ mã nguồn nằm trong package `src/`, cài đặt dưới dạng editable package: `pip install -e .`.
