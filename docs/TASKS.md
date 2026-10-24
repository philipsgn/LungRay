# 📌 DANH SÁCH NHIỆM VỤ DỰ ÁN (docs/TASKS.md)
## Bảng Theo Dõi & Điều Phối Task Giữa Antigravity & CommandCode Go

---

| Task ID | Tiêu đề Nhiệm vụ | Trạng thái | Phụ thuộc | Tầng Model Đề xuất | Nhánh Git / Ghi chú |
|:---|:---|:---:|:---:|:---:|:---|
| **TASK-001** | Tạo script kiểm thử tự động `scripts/verify.ps1` và test runner | `DONE` | Không | S0 / T1 | `task/001-verify-script` |
| **TASK-002** | Dọn dẹp tàn dư Opencode và cấu hình rules cho CommandCode Go | `DONE` | Không | T1 | `task/002-cleanup-opencode` |
| **TASK-003** | Khởi tạo cấu trúc `docs/HANDOFF/` và file template chuẩn hóa | `DONE` | Không | S0 / T1 | `task/003-handoff-template` |
| **TASK-004** | Kiểm định & chuẩn hóa `WeightedMultiTaskBatchSampler` (tỷ lệ 60:25:15) | `DONE` | TASK-001 | T2 (Kimi K2.7 Code) | `src/data/sampler.py` (Đã tích hợp và kiểm thử) |
| **TASK-005** | Tối ưu hóa pipeline tiền xử lý Anti-Shortcut CLAHE/Crop cho COVIDx CXR-4 | `DONE` | TASK-004 | T2 (Kimi K2.7 Code) | `src/explainability/shortcut_audit.py` (Đạt 94.92%) |
| **TASK-006** | Hoàn thiện Unit Test cho Zero Data Leakage kiểm tra `Patient_ID` | `DONE` | TASK-001 | T1 (DeepSeek V4.1) | `tests/test_data_pipeline.py` (Pass 100%) |
| **TASK-007** | Tích hợp ngưỡng Youden's J threshold per-class vào module dự đoán | `DONE` | TASK-004 | T2 (GLM-5.3) | `task/007-youdens-j-threshold` |
| **TASK-008** | Hiện thực hóa Grad-CAM Energy Ratio Calculator cho phế trường phổi | `DONE` | TASK-004 | T2 (Kimi K2.7 Code) | `task/008-gradcam-inlung-energy` |
| **TASK-009** | Hiện thực hóa WSOL Adaptive Binarization & Đo đạc IoU trên RSNA & VinDr | `DONE` | TASK-008 | Antigravity Baseline | Ghi nhận Antigravity phác thảo mã nguồn |
| **TASK-010** | Xây dựng FastAPI Microservice Backend phục vụ suy luận 3-Head & Grad-CAM | `DONE` | TASK-009 | T2 (Kimi K2.7 Code) | `task/010-fastapi-backend` (CommandCode thực thi thành công) |
| **TASK-011** | Xây dựng Giao diện Next.js Medical PACS Viewer tương tác với Alpha Heatmap Slider | `DONE` | TASK-010 | T2 (Kimi K2.7 Code) | `task/011-nextjs-pacs-viewer` (CommandCode thực thi thành công) |
| **TASK-012** | Tối ưu hóa Trình Khởi chạy Cục bộ 1-Click Native PACS (`scripts/start_local.ps1`) | `DONE` | TASK-011 | S0 / T1 | Bỏ Docker nặng, 1-click kích hoạt FastAPI (8000) + Next.js (3000) |

---

### Quy ước Trạng thái:
- `TODO`: Đang chờ thực hiện, chưa tạo file handoff.
- `IN_PROGRESS`: Antigravity đã tạo `docs/HANDOFF/<ID>.md`, CommandCode đang thực thi trên nhánh git riêng.
- `REVIEW`: CommandCode đã chạy verify pass, điền Result, đang chờ Antigravity review `git diff`.
- `DONE`: Antigravity đã nghiệm thu và merge vào nhánh chính.
- `BLOCKED`: Tạm dừng do vướng phụ thuộc hoặc cần replan.
