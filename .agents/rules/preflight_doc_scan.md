# 🧭 AGENT RULE: PRE-FLIGHT DOCUMENTATION SCANNING & SCOPE ALIGNMENT
## Mã Quy Chuẩn: RULE-00-PREFLIGHT-DOCS-SCAN
## Dự án: Nền tảng LungRay
## Áp dụng cho: Toàn bộ Agent & Mọi phiên làm việc (Prompts)

---

### 1. NGUYÊN TẮC CỐT LÕI (MANDATORY ENFORCEMENT)
Trước khi đưa ra bất kỳ phản hồi, đề xuất giải pháp, thiết kế kiến trúc hoặc chỉnh sửa code nào, Agent **BẮT BUỘC** phải rà soát các tài liệu nền tảng trong dự án để đảm bảo tính nhất quán và tuân thủ các ràng buộc kỹ thuật đã được phê duyệt.

---

### 2. CHECKLIST 5 GIÂY TIỀN KIỂM TRƯỚC KHI THỰC THI (PRE-FLIGHT CHECKLIST)

```
[Nhận Prompt từ User]
          │
          ▼
[1. Quét Context Tài Liệu SSOT] ──► Đọc Root PRD.md & docs/EXECUTIVE_SUMMARY.md
          │
          ▼
[2. Đối Chiếu 9 Ràng Buộc] ─────► Kiểm tra 9 Inviolable Constraints của LungRay
          │
          ▼
[3. Xác Định Phạm Vi Task] ─────► Đối chiếu Root PHASES.md & Root PLAN.md
          │
          ▼
[4. Thực Thi Chính Xác & Tuân Thủ Tuyệt Đối]
```

#### Bước 1: Quét Context Tài Liệu Chuẩn Single-Source-of-Truth (SSOT)
| Nhóm tác vụ | Tài liệu bắt buộc phải quét/đọc lại |
|:---|:---|
| **Mọi tác vụ chung / Khởi tạo phiên** | [docs/EXECUTIVE_SUMMARY.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/docs/EXECUTIVE_SUMMARY.md) & [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/PRD.md) |
| **Xử lý Dữ liệu, Splits, DataLoader** | [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/PRD.md) (mục 3.1) & [TECH_ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/TECH_ARCHITECTURE.md) (mục 3.1) |
| **Mô hình, Losses, Training, Tuning** | [TECH_ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/TECH_ARCHITECTURE.md) (mục 3.2) & [PHASES.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/PHASES.md) (Phase 3 & 4) |
| **XAI, Grad-CAM, IoU, Shortcut Audit** | [TECH_ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/TECH_ARCHITECTURE.md) (mục 3.3) & [.agents/rules/xai_audit_rules.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/.agents/rules/xai_audit_rules.md) |
| **Deployment, API, Web PACS UI** | [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/PRD.md) (mục 3.5), [TECH_ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/TECH_ARCHITECTURE.md) (mục 4 & 6) |
| **Tiến độ, Milestone, Tiêu chí nghiệm thu** | [PLAN.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/PLAN.md) (Root) & [PHASES.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/PHASES.md) (Root) |
| **Phản biện lâm sàng & Bảo vệ luận án** | [docs/defense_faq.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/docs/defense_faq.md) |
| **Thực thi trên Kaggle GPU** | [docs/KAGGLE_EXECUTION_GUIDE.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/docs/KAGGLE_EXECUTION_GUIDE.md) |

#### Bước 2: 9 Ràng Buộc Sống Còn Của LungRay (The 9 Inviolable Constraints)
1. 🔴 **Multi-Task 3-Head**: 1 Shared Backbone (DenseNet-121 / ResNet-50 / ViT) + Head A (14 bệnh NIH) + Head B (Lao TB) + Head C (COVIDx CXR-4).
2. 🔴 **Patient-Level Split**: Với NIH ChestX-ray14, bắt buộc chia theo `Patient_ID` (70/10/20). Cấm chia ngẫu nhiên theo ảnh.
3. 🔴 **Source-Stratified Split**: Với COVIDx CXR-4 Benchmark, bắt buộc phân tầng theo nguồn ảnh gốc (`data_source`) và kiểm soát theo `patient_id`. Cấm chia ngẫu nhiên.
4. 🔴 **Bounding Box Vai Trò**: Bbox chỉ dùng cho tập test để tính IoU (VinDr-CXR, RSNA Pneumonia). Không yêu cầu bbox cho tập train.
5. 🔴 **Balanced Batch Sampler**: Bắt buộc dùng `WeightedMultiTaskBatchSampler` cố định 60% NIH : 25% COVID : 15% TB để tránh Task Starvation.
6. 🔴 **Shortcut Learning Audit**: Bắt buộc chạy Grad-CAM audit cho ca dương tính COVID-19 ($\ge 80\%$ trong phổi).
7. 🔴 **Chuẩn Nghiên cứu Sống & Cấm Tuyệt đối Fake/Display Ảnh Tĩnh**: Mọi phân tích EDA, training evaluation, Grad-CAM heatmap hay IoU trong Notebooks (`notebooks/*.ipynb`) **BẮT BUỘC dùng code tương tác sống 100%** (`pandas`, `seaborn`, `matplotlib`, `zipfile`, `cv2`, `PIL`), tính từ dữ liệu thật. Tuyệt đối cấm dùng `display(Image(...))` để giả lập kết quả.
8. 🔴 **Dọn dẹp Tệp Tạm & Tinh gọn Không gian Dự án**: Xóa sạch ngay lập tức các tệp tạm (scratch scripts, helper scripts, logs thử nghiệm) sau khi hoàn thành nhiệm vụ. Không để lại mã nguồn rác trong `scripts/`, `src/` hoặc thư mục gốc.
9. 🔴 **Chuẩn Báo Cáo Nghiên Cứu Khoa Học & Luận Án Đơn Sắc**: Mọi tài liệu báo cáo nghiệm thu, tài liệu kỹ thuật, bài báo khoa học và PDF (`reports/`, `results/*.md`, `results/*.pdf`) **BẮT BUỘC** tuân thủ [.agents/rules/academic_report_standards.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/.agents/rules/academic_report_standards.md): Tuyệt đối cấm icon/emoji, phông Times New Roman, bảng Booktabs 3 đường kẻ đen, tone màu đơn sắc đen trắng.

---

### 3. HẬU QUẢ VI PHẠM & CƠ CHẾ SỬA SAI
Nếu Agent phát hiện mã nguồn hoặc phương án đề xuất vi phạm bất kỳ ràng buộc nào ở trên:
- **DỪNG NGAY LẬP TỨC** hành động vi phạm.
- Thông báo rõ ràng lý do vi phạm điều khoản nào trong docs.
- Khôi phục lại đúng cấu hình chuẩn hóa của nền tảng LungRay.
