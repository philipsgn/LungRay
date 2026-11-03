# LungRay: Multi-Task CXR CADx & Weakly-Supervised Object Localization Platform

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Verification: 125 Tests PASS](https://img.shields.io/badge/verification-125%2F125%20PASS-emerald.svg)](scripts/verify.ps1)

> **Hệ thống Hỗ trợ Ra Quyết định Lâm sàng (Computer-Aided Diagnosis / Clinical Decision Support - CADx/CDS) & Định vị tổn thương lồng ngực có giám sát yếu (WSOL) trên ảnh X-quang với cơ chế kiểm toán Shortcut Learning và lớp phòng vệ Fail-Safe OOD.**

---

> [!IMPORTANT]
> **TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM LÂM SÀNG (CLINICAL DISCLAIMER)**  
> LungRay được nghiên cứu và phát triển như một **Hệ thống Hỗ trợ Tham vấn Chuyên môn Thứ hai (Second Reader / Triaging Assistant)** phục vụ nghiên cứu khoa học và thẩm định tiền lâm sàng. Hệ thống **tuyệt đối không thay thế** phán đoán chuyên môn độc lập của Bác sĩ Chẩn đoán Hình ảnh có chứng chỉ hành nghề. Khi phát hiện dữ liệu bất thường hoặc chất lượng phim chụp không đạt chuẩn giải phẫu, hệ thống sẽ kích hoạt chế độ khóa an toàn **Fail-Safe OOD Lockout** để từ chối đưa ra kết luận sơ bộ.

---

## 📑 Mục Lục
1. [Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
2. [Kiến trúc Kỹ thuật Multi-Task 3-Head](#2-kiến-trúc-kỹ-thuật-multi-task-3-head)
3. [9 Ràng buộc Kỹ thuật Sống còn](#3-9-ràng-buộc-kỹ-thuật-sống-còn)
4. [Danh mục 6 Bộ Dữ liệu Chuẩn Y tế](#4-danh-mục-6-bộ-dữ-liệu-chuẩn-y-tế)
5. [Lộ trình Triển khai 8 Giai đoạn & Kết quả Nghiệm thu](#5-lộ-trình-triển-khai-8-giai-đoạn--kết-quả-nghiệm-thu)
6. [Hướng dẫn Khởi chạy Hệ thống](#6-hướng-dẫn-khởi-chạy-hệ-thống)
7. [Hệ thống Kiểm thử Tự động](#7-hệ-thống-kiểm-thử-tự-động)
8. [Bản quyền & Giấy phép](#8-bản-quyền--giấy-phép)

---

## 1. Giới thiệu tổng quan

**LungRay** giải quyết 3 thách thức cấu trúc cốt lõi trong chẩn đoán hình ảnh lồng ngực:
1. **Phân mảnh tác vụ & Tốn kém bộ nhớ**: Tích hợp một mạng xương sống dùng chung (Shared DenseNet-121 Backbone, 6.97M tham số) để giải quyết đồng thời 3 bài toán: 14 bệnh lồng ngực (NIH ChestX-ray14), Sàng lọc Lao phổi (TB Database) và Phân luồng COVID-19 (COVIDx CXR-4).
2. **Hiện tượng Học đường tắt (Shortcut Learning - Nature MI 2021)**: Triệt tiêu sự phụ thuộc vào watermark, viền máy chụp hoặc ký hiệu R/L ngoài cơ thể thông qua giải thuật **Clinical Pulmonary Grounding** (nâng năng lượng trong phế trường từ baseline 38.49% lên 94.92%, $p = 1.15 \times 10^{-26}$).
3. **Định vị tổn thương có giám sát yếu (WSOL) được lượng hóa**: Binarize bản đồ nhiệt thích nghi và kiểm chứng trực tiếp với Bounding Box chuyên gia từ bác sĩ Việt Nam (VinDr-CXR: Box-IoU 0.6049) và quốc tế (RSNA: Box-IoU 0.7631) mà **không cần Bounding Box trong quá trình huấn luyện**.
4. **Lớp Phòng vệ An toàn Fail-Safe OOD (Phase 8)**: Tự động từ chối chẩn đoán (REJECT / LOCKOUT) trên ảnh nhiễu, ảnh đảo ngược hoặc ảnh ngoài miền thông qua Năng lượng Tự do Helmholtz ($S_E \ge 9.0421$) và Entropy Shannon ($H \le 0.6275$).

---

## 2. Kiến trúc Kỹ thuật Multi-Task 3-Head

```
                       [ Ảnh X-Quang Ngực Thẳng: 3 x 512 x 512 ]
                                         │
                              ┌──────────┴──────────┐
                              │    Shared Encoder   │
                              │    (DenseNet-121)   │
                              └──────────┬──────────┘
                                         │ Feature Maps: 1024 x 16 x 16
                                         ▼
                              [ Global Average Pooling ]
                                         │
                              [ Parameter-Free LayerNorm ] (1024-d, 0 new keys)
                                         │
                              [ Dropout Rate: p = 0.2 ]
                                         │
                     ┌───────────────────┼───────────────────┐
                     ▼                   ▼                   ▼
           ┌───────────────────┐┌───────────────────┐┌───────────────────┐
           │ Head A (NIH)      ││ Head B (TB)       ││ Head C (COVIDx)   │
           │ Linear(1024, 14)  ││ Linear(1024, 1)   ││ Linear(1024, 1)   │
           │ 14 Bệnh Lồng Ngực ││ Sàng lọc Lao Phổi ││ Phân luồng COVID  │
           │ Sigmoid (ASL/FL)  ││ Sigmoid (BCE)     ││ Sigmoid (BCE)     │
           │ Gắn mã WHO ICD-10 ││ Mã ICD-10: A15.0  ││ Mã ICD-10: U07.1  │
           └─────────┬─────────┘└─────────┬─────────┘└─────────┬─────────┘
                     └───────────────────┼───────────────────┘
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ Phase 8: Fail-Safe OOD Gatekeeper     │
                     │ - Helmholtz Free Energy S_E >= 9.0421 │
                     │ - Shannon Entropy H <= 0.6275         │
                     │ - ICD-10 Report Lockout if OOD        │
                     └───────────────────────────────────────┘
```

---

## 3. 9 Ràng buộc Kỹ thuật Sống còn

1. 🔴 **Kiến trúc Multi-Task 3-Head**: Dùng chung 1 backbone (DenseNet-121) cho đồng thời: Head A (14 bệnh NIH), Head B (Sàng lọc Lao TB), Head C (COVIDx CXR-4).
2. 🔴 **Zero Data Leakage**: Với NIH ChestX-ray14, **bắt buộc chia theo `Patient_ID` (70/10/20)**. Tuyệt đối cấm chia ngẫu nhiên theo ảnh ($Train \cap Test = \emptyset$).
3. 🔴 **Chống Shortcut Learning**: Với COVIDx CXR-4, **bắt buộc phân tầng theo nguồn gốc (`data_source`) kết hợp kiểm soát `patient_id`**.
4. 🔴 **Phân định vai trò Bounding Box**: Bounding Box **CHỈ** dùng cho tập kiểm định IoU (VinDr-CXR, RSNA). Tập huấn luyện **KHÔNG** cần Bounding Box vì WSOL học từ nhãn mức ảnh.
5. 🔴 **Cân bằng Batch Multi-Task**: Bắt buộc dùng `WeightedMultiTaskBatchSampler` cố định tỷ lệ 60% NIH : 25% COVID : 15% TB trong mỗi mini-batch để chống Task Starvation.
6. 🔴 **Kiểm toán bắt buộc cho Head C**: Thực hiện Shortcut Learning Audit bằng Grad-CAM; năng lượng kích hoạt trong phế trường phổi phải đạt $\ge 80\%$.
7. 🔴 **Chuẩn Nghiên cứu Thực nghiệm Sống**: Tuyệt đối cấm hiển thị ảnh tĩnh giả lập (`display(Image(...))`) trong notebooks; mọi kết quả phải được tính toán tương tác từ dữ liệu thực tế.
8. 🔴 **Không gian Dự án Tinh gọn (Lean Workspace)**: Toàn bộ script tạm thời, runner mồ côi hoặc cache phải được dọn dẹp sạch sẽ sau khi hoàn tất công việc.
9. 🔴 **Quy chuẩn Báo cáo Khoa học Đơn sắc**: Báo cáo học thuật và luận án bắt buộc dùng phông Times New Roman, bảng Booktabs 3 đường kẻ đen, đơn sắc, 100% không icon/emoji rườm rà.

---

## 4. Danh mục 6 Bộ Dữ liệu Chuẩn Y tế

| STT | Tên Bộ Dữ liệu | Quy mô | Vai trò trong Nền tảng | Ràng buộc Áp dụng |
|:---:|:---|:---:|:---|:---|
| 1 | **NIH ChestX-ray14** | 112,120 ảnh | Huấn luyện Head A (14 bệnh lồng ngực) | Phân chia chặt chẽ theo `Patient_ID` (70/10/20) |
| 2 | **Tuberculosis (TB) Dataset** | 7,000 ảnh | Huấn luyện Head B (Sàng lọc Lao) | Cố định hạt giống ngẫu nhiên; ghi rõ hạn chế nguồn Shenzhen |
| 3 | **COVIDx CXR-4 Benchmark** | 16,400+ ảnh | Huấn luyện Head C (Phân luồng COVID-19) | Phân tầng theo nguồn ảnh gốc (`data_source`) |
| 4 | **VinDr-CXR** | 3,000 ảnh test | **Chỉ dùng Test**: Đánh giá Box-IoU WSOL | Bounding Box chuyên gia Bác sĩ Chẩn đoán hình ảnh Việt Nam |
| 5 | **RSNA Pneumonia Detection** | 3,000 ảnh test | **Chỉ dùng Test**: Đánh giá Box-IoU WSOL | Bounding Box Viêm phổi chuẩn quốc tế |
| 6 | **CheXpert-small-v1** | 22,433 ảnh | **Chỉ dùng Test**: Đánh giá Ngoại vi (OOD) | Thử thách trôi dạt phân phối ngoại viện (Domain Shift) |

---

## 5. Lộ trình Triển khai 8 Giai đoạn & Kết quả Nghiệm thu

- **Phase 1**: Setup môi trường, cấu trúc repository, khảo sát y văn & 9 Ràng buộc sống còn.
- **Phase 2**: Pipeline xử lý ảnh 512x512, Leakage Audit & Weighted Multi-Task Batch Sampler (60:25:15).
- **Phase 3**: Huấn luyện Multi-Task 3-Head Baseline (DenseNet-121): Macro AUROC Head A = 0.8271, TB = 1.0000, COVID = 0.7342.
- **Phase 4**: Tối ưu hóa SOTA (Asymmetric Loss, Focal Loss pos_weight động) & Hiệu chuẩn ngưỡng Youden's J.
- **Phase 5**: Định lượng IoU WSOL (RSNA 0.7631, VinDr 0.6049) & Shortcut Learning Audit (In-lung 94.92%).
- **Phase 6**: Xây dựng Trạm đọc phim PACS chuyên dụng (FastAPI Port 8000 + Next.js 14 Port 3000).
- **Phase 7**: Hồ sơ Luận văn Khoa học 25 trang đơn sắc (`reports/FINAL_SCIENTIFIC_REPORT.pdf`) và Slide bảo vệ.
- **Phase 8**: Lớp Phòng vệ Lâm sàng Fail-Safe OOD (Helmholtz Energy, Shannon Entropy, Khóa báo cáo WHO ICD-10).

---

## 6. Hướng dẫn Khởi chạy Hệ thống

### Cách 1: Khởi động 1-Click Toàn Hệ Thống (Khuyến nghị)
Sử dụng script PowerShell tự động dọn dẹp cache và khởi động đồng thời Backend FastAPI và Frontend Next.js:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
```
- **Medical PACS Viewer**: `http://localhost:3000`
- **Clinical Monograph & Benchmark Report**: `http://localhost:3000/report`
- **FastAPI REST Microservice**: `http://localhost:8000/docs`

### Cách 2: Khởi động Thủ công từng Cấu phần

#### 1. Backend FastAPI Microservice
```powershell
# Kích hoạt môi trường ảo
python -m venv venv
venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt
pip install -e .

# Chạy server
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Next.js PACS Viewer
```powershell
cd app/frontend
npm install
npm run dev
```

---

## 7. Hệ thống Kiểm thử Tự động

Toàn bộ logic xử lý dữ liệu, mô hình toán học, ngưỡng quyết định và lớp an toàn Fail-Safe được bảo vệ bởi **125 Unit Tests** với tỷ lệ đạt 100%:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

---

## 8. Bản quyền & Đạo đức Nghiên cứu
Dự án được phân phối dưới giấy phép MIT License. Mọi nghiên cứu tuân thủ nghiêm ngặt bảo mật thông tin sức khỏe (PHI De-identification) và đạo đức y sinh.
