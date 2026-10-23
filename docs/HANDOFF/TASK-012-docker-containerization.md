# HANDOFF: TASK-012 - Docker & Docker-Compose Containerization (Phase 6 - Task 6.3)
> Trạng thái: READY_FOR_DEV | Model Đề Xuất: T1 / T2 (DeepSeek V4.1 Flash / Kimi K2.7 Code) | Env: CMD_ZDR=1

## 1. Mục Tiêu (Goal)
Container hóa toàn diện nền tảng y tế LungRay, tạo cấu hình `Dockerfile.backend`, `Dockerfile.frontend` và `docker-compose.yml` để khởi chạy đồng thời cả FastAPI Microservice Backend và Next.js PACS Viewer bằng 1 lệnh duy nhất.

## 2. Phạm Vi Cho Phép (Scope - File được phép tạo/sửa)
- `Dockerfile.backend` [NEW]
- `Dockerfile.frontend` [NEW]
- `docker-compose.yml` [NEW]
- `.dockerignore` [NEW]

## 3. Ngoài Phạm Vi (Strictly Out of Bounds - CẤM ĐỤNG)
- Không can thiệp vào logic Python trong `src/`, `app/backend/`.
- Không can thiệp vào mã nguồn TypeScript trong `app/frontend/app/`.

## 4. Đặc Tả Kỹ Thuật Containerization
1. **`Dockerfile.backend`**:
   - Base image: `python:3.10-slim` hoặc `python:3.11-slim`.
   - Cài đặt thư viện hệ thống cần thiết cho OpenCV (`libgl1`, `libglib2.0-0`).
   - Cài đặt `requirements.txt` với pip cache tối ưu.
   - Chạy lệnh: `uvicorn app.backend.main:app --host 0.0.0.0 --port 8000`.
2. **`Dockerfile.frontend`**:
   - Multi-stage build tối ưu kích thước image với `node:20-alpine`:
     - Stage 1 (deps): Cài đặt dependencies từ `package.json` và `package-lock.json`.
     - Stage 2 (builder): Build Next.js `npm run build` với biến môi trường `NEXT_PUBLIC_API_URL=http://localhost:8000`.
     - Stage 3 (runner): Chạy production server `npm start` trên cổng 3000.
3. **`docker-compose.yml`**:
   - Service `backend`: build `Dockerfile.backend`, ánh xạ cổng `8000:8000`, volume mounts cho checkpoints nếu có.
   - Service `frontend`: build `Dockerfile.frontend`, ánh xạ cổng `3000:3000`, depends_on `backend`.
   - Network bridge chung giữa 2 containers.

## 5. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] Chạy lệnh verify repo: `powershell -File scripts/verify.ps1` đạt 100% PASS (92/92 tests).
- [ ] File `docker-compose.yml` đúng cú pháp compose specification (hợp lệ không có lỗi thụt dòng).
- [ ] Dockerfiles có đầy đủ `.dockerignore` loại trừ `node_modules`, `.next`, `__pycache__`, `.git`, `dataset/` nặng.

## 6. Gợi Ý Model & Mức Nhạy Cảm
- **Mức nhạy cảm**: Sensitive (`$env:CMD_ZDR = "1"`).
- **Tầng model khuyến nghị**: T1 (`DeepSeek V4.1 Flash`) hoặc T2 (`Kimi K2.7 Code`).

---

## 7. Result (CommandCode CLI điền mục này sau khi hoàn thành)
- **Tóm tắt thay đổi**: [Điền tóm tắt sau khi hoàn thành]
- **Danh sách file đã tạo/sửa**: [Liệt kê files]
- **Kết quả kiểm thử**: [Dán log kiểm tra cú pháp / build docker]
- **Điểm chưa chắc / Cần review**: [Ghi chú nếu có]
