---
name: academic-reporting
description: Quy trình biên soạn báo cáo khoa học, luận văn y khoa và xuất bản tệp PDF đơn sắc tuân thủ nghiêm ngặt tiêu chuẩn MICCAI/IEEE, Times New Roman, bảng Booktabs và không icon (Rule 9).
---

# 📄 SKILL: ACADEMIC REPORTING & MONOCHROME PDF PUBLISHING
## Quy Chuẩn Biên Soạn Báo Cáo Khoa Học, Thống Kê Bootstrap CI & Xuất Bản PDF Đơn Sắc Chuẩn Y Khoa

---

### 1. MỤC TIÊU & NGUYÊN TẮC BẮT BUỘC (RULE 9 ENFORCEMENT)
Kỹ năng này hướng dẫn việc tổng hợp số liệu thực nghiệm y tế, tính toán khoảng tin cậy khoa học Bootstrap 95% CI và xuất bản tài liệu nghiệm thu kỹ thuật, bài báo khoa học và luận án tốt nghiệp dưới định dạng PDF đạt chuẩn xuất bản của các hội nghị y khoa hàng đầu (MICCAI, IEEE TMI, RSNA):
1. **100% Không Icon, Emoji**: Tuyệt đối không sử dụng các biểu tượng đồ họa cảm xúc (như 🚀, 💡, ✅, ⚠️, ❌).
2. **Phông Chữ Chuẩn Mực**: Bắt buộc sử dụng phông chữ **Times New Roman** (hoặc Computer Modern), cỡ chữ 10–12pt trang trọng.
3. **Bảng Biểu Chuẩn Booktabs**: Bảng chỉ bao gồm đúng 3 đường kẻ ngang đen tuyền (`\toprule`, `\midrule`, `\bottomrule`), loại bỏ hoàn toàn các đường kẻ dọc và các màu nền xen kẽ sặc sỡ.
4. **Tone Màu Đơn Sắc (Monochrome)**: Toàn bộ bảng, văn bản và biểu đồ phải hiển thị tối ưu ở chế độ in ấn đen trắng. Biểu đồ đường sử dụng các kiểu nét khác biệt (nét liền, nét đứt, chấm gạch).

---

### 2. CÁC BƯỚC THỰC HIỆN CHI TIẾT

#### Bước 1: Tính Toán Thống Kê & Khoảng Tin Cậy Bootstrap (95% CI)
- Thực hiện phương pháp Resampling với lặp lại $B = 1,000$ lần trên tập test của mô hình:
  ```python
  import numpy as np

  def compute_bootstrap_ci(y_true, y_pred, metric_fn, n_bootstraps=1000, alpha=0.05):
      bootstrapped_scores = []
      rng = np.random.RandomState(42)
      for _ in range(n_bootstraps):
          indices = rng.randint(0, len(y_true), len(y_true))
          if len(np.unique(y_true[indices])) < 2:
              continue
          score = metric_fn(y_true[indices], y_pred[indices])
          bootstrapped_scores.append(score)
      sorted_scores = np.sort(bootstrapped_scores)
      lower = sorted_scores[int((alpha / 2.0) * len(sorted_scores))]
      upper = sorted_scores[int((1.0 - alpha / 2.0) * len(sorted_scores))]
      return float(np.mean(bootstrapped_scores)), (float(lower), float(upper))
  ```

#### Bước 2: Chuẩn Hóa Bảng Kết Quả Sang Định Dạng Booktabs
- Khi trình bày bảng kết quả trong văn bản Markdown hoặc tài liệu khoa học:
  ```markdown
  | Mô hình / Phân hệ | Số tham số | AUROC Head A (95% CI) | AUROC Head B | AUROC Head C | Độ trễ suy luận |
  |:---|:---:|:---:|:---:|:---:|:---:|
  | DenseNet-121 (Baseline) | 6.97M | 0.8271 (0.8110–0.8432) | 1.0000 | 0.7342 | 674 ms |
  | ResNet-50 | 23.51M | 0.8194 (0.8035–0.8353) | 0.9982 | 0.7280 | 812 ms |
  | Vision Transformer (ViT-B/16) | 86.40M | 0.8640 (0.8480–0.8800) | 1.0000 | 0.7815 | 1783 ms |
  ```

#### Bước 3: Xuất Bản Tệp PDF Luận Văn Bằng ReportLab
- Sử dụng script chính thức:
  ```powershell
  python scripts/generate_final_report_pdf.py
  ```
- Kiểm tra tệp xuất ra tại: `reports/output/pdf/LungRay_Final_Report.pdf`:
  - Dung lượng tệp: $\ge 1.0$ MB.
  - Số trang: 20–25 trang in chuẩn học thuật.
  - Bố cục trang bìa, mục lục, bảng số liệu, biểu đồ Grad-CAM định vị tổn thương và danh mục tài liệu tham khảo chuẩn IEEE.

