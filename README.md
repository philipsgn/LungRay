# 🫁 LungRay: Multi-Task CADx & Weakly-Supervised Object Localization Platform

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Hệ thống chẩn đoán đa nhiệm (Multi-Task CADx) & Định vị tổn thương yếu (WSOL) trên ảnh X-quang lồng ngực với cơ chế kiểm toán Shortcut Learning phục vụ thực hành lâm sàng đáng tin cậy.**

---

## 📑 Mục lục
- [1. Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
- [2. Kiến trúc Multi-Task 3-Head](#2-kiến-trúc-multi-task-3-head)
- [3. Cấu trúc thư mục chuẩn Enterprise](#3-cấu-trúc-thư-mục-chuẩn-enterprise)
- [4. Hướng dẫn cài đặt & Thiết lập môi trường](#4-hướng-dẫn-cài-đặt--thiết-lập-môi-trường)
- [5. 6 Ràng buộc kỹ thuật sống còn](#5-6-ràng-buộc-kỹ-thuật-sống-còn)
- [6. Danh mục 6 Bộ Dữ liệu](#6-danh-mục-6-bộ-dữ-liệu)
- [7. Kế hoạch triển khai 7 Giai đoạn](#7-kế-hoạch-triển-khai-7-giai-đoạn)

---

## 1. Giới thiệu tổng quan

**LungRay** là nền tảng AI mã nguồn mở tiên tiến dành cho bài toán phân tích ảnh X-quang lồng ngực (CXR). Nền tảng kết hợp 3 trụ cột kỹ thuật:
1. **Kiến trúc Multi-Task 3-Head**: Sử dụng chung 1 Backbone (DenseNet-121 / ResNet-50 / ViT) để đồng thời phân loại 14 bệnh lồng ngực (NIH ChestX-ray14), sàng lọc Lao phổi (TB Database) và phân tầng 3 nhóm benchmark quốc tế COVIDx CXR-4.
2. **Định vị tổn thương yếu (WSOL)**: Khai thác Grad-CAM / Grad-CAM++ trích xuất bản đồ kích hoạt nhiệt (activation maps) và chuyển đổi thành Bounding Box mà **không cần bounding box trong quá trình huấn luyện**.
3. **Kiểm toán AI Đáng tin cậy (Trustworthy AI Audit)**: Thực hiện kiểm toán rủi ro Shortcut Learning đối với dữ liệu COVID-19 để đảm bảo mô hình ra quyết định dựa trên tổn thương phế trường thật sự ($\ge 80\%$ năng lượng trong phổi).

---

## 2. Kiến trúc Multi-Task 3-Head

```
                       [ Input CXR: 3 x 512 x 512 ]
                                    │
                         ┌──────────┴──────────┐
                         │   Shared Encoder    │
                         │   (DenseNet-121)    │
                         └──────────┬──────────┘
                                    │ Feature Maps: 1024 x 16 x 16
                 ┌──────────────────┼──────────────────┐
                 │ (Head A)         │ (Head B)         │ (Head C)
                 ▼                  ▼                  ▼
        ┌─────────────────┐┌─────────────────┐┌─────────────────┐
        │ 14 Bệnh NIH     ││ Sàng lọc Lao TB ││ COVID-19        │
        │ (Multi-Label)   ││ (Binary)        ││ (4-Class)       │
        │ Sigmoid         ││ Sigmoid         ││ Softmax         │
        └─────────────────┘└─────────────────┘└─────────────────┘
```

> **📌 Cơ sở khoa học của chuẩn độ phân giải $512 \times 512$**:
> - **Chống suy giảm hiệu năng vi tổn thương**: Theo Sabottke & Spieler (2020, *Radiology: AI*), các tổn thương dạng nốt nhỏ (*Nodule*) và giãn phế nang (*Emphysema*) trên NIH ChestX-ray14 bị suy giảm nghiêm trọng ở độ phân giải thấp ($224\text{px}$).
> - **Chống Shortcut Learning nội tại**: Wollek et al. (2023) chứng minh mô hình ở độ phân giải thấp buộc phải dựa vào các đặc trưng giả (*spurious features*); tăng kích thước ảnh nâng AUC từ 82.7% ($256\text{px}$) lên 84.2% ($1024\text{px}$). Chuẩn $512\text{px}$ là điểm cân bằng tối ưu giữa AUC lâm sàng và tốc độ xử lý.
> - **Độ phân giải không gian cho WSOL Grad-CAM**: Với hệ số downsample 32 lần của DenseNet/ResNet, ảnh $224\text{px}$ chỉ sinh feature map $7 \times 7$ (quá thô để định vị tổn thương); ảnh $512\text{px}$ sinh feature map $16 \times 16$, tăng độ phân giải không gian gấp **$\approx 5.2$ lần**, đáp ứng trực tiếp chỉ tiêu Mean IoU $\ge 0.35$.


---

## 3. Cấu trúc thư mục chuẩn Enterprise

```
Chest X-rays/
├── .agents/                    # Multi-Agent OS: Rules & Workflows
│   ├── rules/                  # Quy chuẩn: Pre-flight scan, Data integrity, XAI audit
│   └── workflows/              # Quy trình chuẩn: Data, Model, XAI, Deploy
├── configs/                    # File cấu hình thí nghiệm (YAML)
│   └── default_config.yaml     # Cấu hình mặc định
├── dataset/                    # Thư mục chứa dữ liệu liên kết (symlinks/Kaggle mounts)
├── docs/                       # Hồ sơ kỹ thuật học thuật & Nghiên cứu
│   ├── EXECUTIVE_SUMMARY.md    # Tóm lược dự án v3
│   ├── FEASIBILITY_ASSESSMENT.md
│   ├── literature_review.md    # Nghiên cứu 5 bài báo nền tảng
│   ├── PROJECT_TRACKING.md     # Bảng theo dõi tiến độ
│   └── PROPOSAL.md             # Đề cương chi tiết
├── kaggle/                     # Scripts & Notebooks thực thi trên Kaggle Cloud
│   ├── rescale_512.py          # Rescale đa luồng 112k ảnh sang 512x512
│   └── README.md               # Hướng dẫn thao tác trên Kaggle Kernel
├── notebooks/                  # Jupyter notebooks cho EDA và kiểm chứng
├── src/                        # Mã nguồn chính của package lungray
│   ├── data/                   # Dataset loaders, Samplers, Augmentation
│   ├── models/                 # Kiến trúc mạng 3-Head, Losses, Trainer
│   ├── explainability/         # Grad-CAM, IoU evaluation, Shortcut Audit
│   └── utils/                  # Metrics, Logging, Seeding
├── tests/                      # Bộ kiểm thử tự động (PyTest)
├── AGENTS.md                   # Multi-Agent Governance & Rule 0
├── PHASES.md                   # 7 Phases - 32 Tasks chi tiết
├── PLAN.md                     # Kế hoạch 16 tuần
├── PRD.md                      # Product Requirements Document
├── TECH_ARCHITECTURE.md        # Thiết kế kỹ thuật chi tiết
├── pyproject.toml              # Cấu hình gói cài đặt chuẩn PEP 517/518
├── requirements.txt            # Danh sách thư viện Python
└── environment.yml             # Môi trường Conda
```

---

## 4. Hướng dẫn cài đặt & Thiết lập môi trường

### Cách 1: Sử dụng Pip & Python 3.10
```bash
# 1. Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate # Linux/macOS

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Cài đặt package lungray ở chế độ Editable
pip install -e .

# 4. Kiểm tra cài đặt qua bộ test
pytest tests/
```

### Cách 2: Sử dụng Conda
```bash
conda env create -f environment.yml
conda activate lungray
pip install -e .
```

---

## 5. 6 Ràng buộc kỹ thuật sống còn

1. 🔴 **Kiến trúc Multi-Task 3-Head**: 1 Shared Backbone + 3 Heads chuyên biệt (NIH 14 lớp, Lao TB, COVIDx CXR-4 3 lớp).
2. 🔴 **Zero Data Leakage**: Với NIH ChestX-ray14, **bắt buộc chia train/val/test theo `Patient_ID` (70/10/20)**. Tuyệt đối cấm chia ngẫu nhiên theo ảnh.
3. 🔴 **Chống Shortcut Learning**: Với COVIDx CXR-4 Benchmark, **bắt buộc phân tầng theo nguồn ảnh gốc (`data_source`)**.
4. 🔴 **Phân định vai trò Bounding Box**: Bounding Box CHỈ dùng cho tập test để tính chỉ số IoU (VinDr-CXR, RSNA Pneumonia). Các tập huấn luyện (NIH, TB, COVID) KHÔNG cần Bounding Box vì WSOL học từ nhãn mức ảnh.
5. 🔴 **Cân bằng Batch Multi-Task**: Bắt buộc dùng `WeightedMultiTaskBatchSampler` cố định tỷ lệ 60% NIH : 25% COVID : 15% TB trong mỗi batch để chống Task Starvation.
6. 🔴 **Kiểm toán bắt buộc cho Head C**: Bắt buộc thực hiện Shortcut Learning Audit bằng Grad-CAM trên các ca dương tính COVID-19; năng lượng kích hoạt trong phế trường phổi phải đạt $\ge 80\%$.

---

## 6. Danh mục 6 Bộ Dữ liệu

| STT | Tên Bộ Dữ liệu | Quy mô | Vai trò trong LungRay | Ràng buộc áp dụng |
|:---:|:---|:---:|:---|:---|
| 1 | **NIH ChestX-ray14** | 112,120 ảnh | Huấn luyện Head A (14 bệnh) | Chia theo `Patient_ID` (70/10/20) |
| 2 | **Tuberculosis (TB) Dataset** | 7,000 ảnh | Huấn luyện Head B (Sàng lọc Lao) | Chia bệnh nhân / ngẫu nhiên cố định seed |
| 3 | **COVIDx CXR-4 Benchmark** | 16,400+ ảnh | Huấn luyện Head C (COVIDx 3 lớp) | **Source-Stratified Split** |
| 4 | **VinDr-CXR** | 3,000 ảnh test | **Chỉ dùng Test**: Đánh giá IoU WSOL | Bbox chuyên gia y tế Việt Nam |
| 5 | **RSNA Pneumonia Detection** | 3,000 ảnh test | **Chỉ dùng Test**: Đánh giá IoU WSOL | Bbox Viêm phổi |
| 6 | **CheXpert-small-v1** | 22,433 ảnh | **Chỉ dùng Test**: Đánh giá Tổng quát hóa | External Validation |

---

## 7. Kế hoạch triển khai 7 Giai đoạn

- **Phase 1**: Setup môi trường, cấu trúc repository, tài liệu đặc tả & Literature Review (Tuần 1–2).
- **Phase 2**: Ingestion dữ liệu, kiểm soát rò rỉ (Leakage Audit) & Source-stratified splits (Tuần 3–4).
- **Phase 3**: Huấn luyện Baseline Multi-Task 3-Head (DenseNet-121) (Tuần 5–7).
- **Phase 4**: Tối ưu hóa nâng cao, SOTA comparison & Threshold tuning (Tuần 8–10).
- **Phase 5**: Định lượng IoU WSOL trên VinDr-CXR & Kiểm toán Shortcut Learning (Tuần 11–12).
- **Phase 6**: Xây dựng Web PACS DICOM Demo (FastAPI + Next.js) (Tuần 13–14).
- **Phase 7**: Nghiệm thu đồ án, báo cáo học thuật & Defense slides (Tuần 15–16).

---

## 📜 Bản quyền & Giấy phép
Dự án được phân phối dưới giấy phép MIT License. Mọi kết quả nghiên cứu tuân thủ đạo đức nghiên cứu y khoa và an toàn dữ liệu y tế.
