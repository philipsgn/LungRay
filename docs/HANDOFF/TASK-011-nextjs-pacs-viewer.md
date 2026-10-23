# HANDOFF: TASK-011 - Next.js Medical PACS Viewer Web Demo
> Trạng thái: READY_FOR_DEV | Model Đề Xuất: T2 (Kimi K2.7 Code / GLM-5.3) | Env: CMD_ZDR=1

## 1. Mục Tiêu (Goal)
Xây dựng giao diện Web Next.js mô phỏng trạm đọc phim y tế PACS hiện đại (`app/frontend/`) kết nối trực tiếp với FastAPI backend (`http://localhost:8000`), hỗ trợ kéo thả ảnh X-quang ngực, hiển thị thẻ chẩn đoán 3 Heads và thanh trượt điều chỉnh độ mờ (Alpha Slider) của Grad-CAM Heatmap tức thì.

## 2. Phạm Vi Cho Phép (Scope - File được phép tạo/sửa)
- `app/frontend/**` [NEW] (Cấu trúc ứng dụng Next.js, components, styles, package.json)

## 3. Ngoài Phạm Vi (Strictly Out of Bounds - CẤM ĐỤNG)
- Tuyệt đối không chỉnh sửa `app/backend/`, `src/`, `tests/`, `dataset/`.
- Không thay đổi các cổng API đã định nghĩa tại FastAPI.

## 4. Giao Diện & Tính Năng Yêu Cầu (PACS UI Components)
1. **Header PACS Viewer**: Tên nền tảng LungRay, trạng thái kết nối backend API, nút chuyển đổi chế độ xem.
2. **Khu Vực Tải Ảnh (Upload Dropzone)**: Kéo-thả ảnh PNG/JPG/DICOM hoặc chọn từ máy tính, xem trước ảnh sắc nét.
3. **Thanh Trượt Alpha Heatmap (Heatmap Opacity Slider)**:
   - Slider mượt mà từ 0% (chỉ thấy ảnh gốc) đến 100% (chỉ thấy heatmap), mặc định 40% blend y khoa.
4. **Bảng Kết Quả Chẩn Đoán 3-Head (Clinical Diagnosis Dashboard)**:
   - **Head A (14 Bệnh NIH)**: Thanh tiến trình xác suất từng bệnh lý, cảnh báo đỏ/vàng theo ngưỡng tối ưu Youden's J.
   - **Head B (Lao Phổi TB)**: Huy hiệu trạng thái Sàng lọc Lao phổi (Negative / Positive).
   - **Head C (COVIDx CXR-4)**: Huy hiệu chẩn đoán COVID-19 và tỷ lệ năng lượng phế trường phổi Shortcut Audit ($\ge 80\%$).

## 5. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] Chạy lệnh build hoặc dev server: `npm run build` hoặc `npm run dev` không phát sinh lỗi cú pháp hay TypeScript/ESLint.
- [ ] Giao diện tương thích API FastAPI: gọi thành công `GET /health`, `POST /api/v1/predict`, `POST /api/v1/explain`, `POST /api/v1/audit`.
- [ ] Thao tác kéo thanh trượt Alpha Heatmap phản hồi tức thì mà không bị giật lag.

## 6. Gợi Ý Model & Mức Nhạy Cảm
- **Mức nhạy cảm**: Sensitive (`$env:CMD_ZDR = "1"`).
- **Tầng model khuyến nghị**: T2 (`Kimi K2.7 Code` hoặc `GLM-5.3`).

---

## 7. Result (CommandCode CLI điền mục này sau khi hoàn thành)
- **Tóm tắt thay đổi**: Khởi tạo ứng dụng Next.js 14 App Router tại `app/frontend/` gồm Header PACS, Upload Dropzone, Alpha Heatmap Slider, Heatmap Viewer, và Clinical Diagnosis Dashboard 3-Head. Các component kết nối với FastAPI backend qua client API tập trung (`app/lib/api.ts`), gọi đồng bộ các endpoint `/health`, `/api/v1/predict`, `/api/v1/explain`, `/api/v1/audit`. UI dùng Tailwind CSS với tone màu y khoa đơn sắc.
- **Danh sách file đã tạo/sửa**:
  - `app/frontend/package.json` [MODIFY]
  - `app/frontend/next.config.mjs` [MODIFY]
  - `app/frontend/app/globals.css` [MODIFY]
  - `app/frontend/app/layout.tsx` [MODIFY]
  - `app/frontend/app/page.tsx` [NEW]
  - `app/frontend/app/types.ts` [NEW]
  - `app/frontend/app/lib/api.ts` [NEW]
  - `app/frontend/app/components/PacsHeader.tsx` [NEW]
  - `app/frontend/app/components/UploadDropzone.tsx` [NEW]
  - `app/frontend/app/components/AlphaSlider.tsx` [NEW]
  - `app/frontend/app/components/HeatmapViewer.tsx` [NEW]
  - `app/frontend/app/components/DiagnosisDashboard.tsx` [NEW]
  - `app/frontend/public/sample_cxr.png` [NEW - ảnh demo]
- **Kết quả kiểm thử**:
  - `npm run build` trong `app/frontend` thành công, không lỗi TypeScript/ESLint:
    ```
    ▲ Next.js 14.2.35
       Creating an optimized production build ...
     ✓ Compiled successfully
       Linting and checking validity of types ...
       Collecting page data ...
       Generating static pages (5/5)
     ✓ Generating static pages (5/5)
       Finalizing page optimization ...

    Route (app)                              Size     First Load JS
    ┌  /                                    9.07 kB        96.4 kB
    └ ○ /_not-found                          873 B          88.2 kB

    ○  (Static)  prerendered as static content
    ```
  - Backend FastAPI chạy tại `http://localhost:8000`, các endpoint được gọi thành công:
    - `GET /health` → `{"status":"healthy","device":"cpu","version":"v4.0"}`
    - `POST /api/v1/predict` → trả về `head_a_prediction`, `head_b_tb_screening`, `head_c_covidx`, `inference_time_ms`
    - `POST /api/v1/explain` → trả về `heatmap_base64`, `overlay_base64`, `target_head`, `target_class`
    - `POST /api/v1/audit` → trả về `in_lung_energy_ratio`, `pass_80_percent`, `lung_mask_base64`
- **Điểm chưa chắc / Cần review**: Backend hiện sử dụng random weights do chưa có `checkpoints/best_model.pth`; kết quả dự đoán chỉ mang tính demo. Khi có checkpoint thực, frontend sẽ hiển thị đúng xác suất lâm sàng. Cần chạy `npm run dev` và mở `http://localhost:3000` để kiểm tra tương tác Alpha Slider trực tiếp.
