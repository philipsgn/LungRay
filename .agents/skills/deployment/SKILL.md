---
name: deployment
description: Quy trình đóng gói FastAPI backend, giao diện Next.js PACS Viewer và container hóa toàn bộ hệ thống bằng Docker Compose cho nền tảng LungRay.
---

# 🔄 SKILL: FULL-STACK DEPLOYMENT & CONTAINERIZATION (LUNGRAY PLATFORM)
## Mã Quy Trình: SKILL-DEPLOYMENT
## Dự án: Nền tảng LungRay
## Thực hiện bởi: `FullstackDeployAgent`

---

## 1. MỤC ĐÍCH
Quy trình hướng dẫn đóng gói backend FastAPI, xây dựng giao diện Next.js PACS Viewer và container hóa toàn bộ hệ thống bằng Docker Compose sẵn sàng phục vụ trình diễn trước Hội đồng chấm Đồ án.

---

## 2. CÁC BƯỚC THỰC THI (STEP-BY-STEP)

```
[Bước 1: Hiện thực FastAPI Backend] ──► [Bước 2: Xây dựng Next.js PACS UI] ──► [Bước 3: Viết Cấu hình Docker]
                                                                                        │
[Bước 6: Tổng duyệt Demo Bảo vệ]  ◄── [Bước 5: Kiểm thử Đo độ trễ Latency] ◄── [Bước 4: Chạy Docker Compose]
```

### Bước 1: Hiện thực Lõi Dịch vụ Backend FastAPI
1. Viết `app/backend/main.py` triển khai các endpoints:
   - `GET /api/v1/health`: Kiểm tra trạng thái GPU/CPU và nạp mô hình.
   - `POST /api/v1/predict`: Nhận file ảnh (DICOM/PNG/JPG), tiền xử lý và trả về xác suất 3-Head.
   - `POST /api/v1/explain`: Nhận file ảnh và nhãn chỉ định, trả về ảnh Heatmap Base64.
   - `POST /api/v1/audit`: Kiểm tra tỷ lệ kích hoạt trong phổi cho các ca COVID-19.
2. Kiểm thử API cục bộ:
   ```bash
   uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Truy cập Swagger UI tại `http://localhost:8000/docs` để kiểm tra các request mẫu.

### Bước 2: Xây dựng Giao diện Next.js Medical PACS Viewer
1. Khởi tạo và thiết lập ứng dụng Next.js tại `app/frontend/`:
   ```bash
   cd app/frontend
   npm install
   npm run dev
   ```
2. Các thành phần giao diện bắt buộc:
   - **Upload & DICOM Ingestion**: Kéo thả ảnh trực tiếp, hỗ trợ xem thông tin metadata.
   - **Multi-Task Dashboard**: Hiển thị bảng xác suất 14 bệnh NIH, kết quả sàng lọc Lao phổi và phân loại COVID-19.
   - **Interactive Heatmap Viewer**: Xem ảnh gốc song song với ảnh nhiệt, có thanh trượt Alpha điều chỉnh độ mờ $(0\% \to 100\%)$.
   - **Audit Badge**: Huy hiệu xác nhận "Vượt qua kiểm toán Shortcut Learning" hiển thị bên cạnh kết quả COVID-19.

### Bước 3: Đóng gói Docker & Docker-Compose
1. Cấu hình `Dockerfile.backend`:
   ```dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY src/ ./src/
   COPY app/backend/ ./app/backend/
   COPY checkpoints/ ./checkpoints/
   CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. Cấu hình `docker-compose.yml` liên kết 2 dịch vụ tại cổng 8000 (Backend) và cổng 3000 (Frontend).

### Bước 4: Kiểm thử Tự động & Đo lường Độ trễ (Latency Benchmark)
1. Khởi chạy toàn bộ hệ thống:
   ```bash
   docker-compose up --build -d
   ```
2. Chạy script kiểm thử tải và đo thời gian phản hồi:
   ```bash
   python scripts/benchmark_latency.py --samples 50 --host http://localhost:8000
   ```
3. **Tiêu chuẩn nghiệm thu**:
   - Thời gian phản hồi trung bình $\le 1.8$ giây/ảnh.
   - Bộ nhớ RAM tiêu thụ $\le 3.5$ GB.

### Bước 5: Kịch bản Trình diễn Trực tiếp (Defense Live Demo Script)
Chuẩn bị sẵn 3 ca bệnh mẫu trong thư mục `demo_samples/`:
1. *Sample 1*: Ca tràn dịch màng phổi + bóng tim to (Head A dương tính Effusion & Cardiomegaly $\to$ Heatmap tập trung đúng đáy phổi và bóng tim).
2. *Sample 2*: Ca lao phổi dương tính (Head B Tuberculosis $\to$ Grad-CAM vùng đỉnh phổi).
3. *Sample 3*: Ca COVID-19 dương tính (Head C COVID-19 $\to$ Shortcut Audit Pass $\ge 85\%$ trong phế trường phổi).

