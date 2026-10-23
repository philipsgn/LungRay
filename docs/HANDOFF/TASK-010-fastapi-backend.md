# HANDOFF: TASK-010 - FastAPI Microservice Backend Serving
> Trạng thái: READY_FOR_DEV | Model Đề Xuất: T2 (Kimi K2.7 Code / GLM-5.3) | Env: CMD_ZDR=1

## 1. Mục Tiêu (Goal)
Xây dựng microservice RESTful API bằng FastAPI (`app/backend/main.py`) phục vụ suy luận chẩn đoán 3-Head đồng thời, trích xuất bản đồ nhiệt Grad-CAM Base64 và kiểm toán Shortcut Learning trong thời gian $\le 1.8$ giây/ảnh.

## 2. Phạm Vi Cho Phép (Scope - File được phép tạo/sửa)
- `app/backend/main.py` [NEW]
- `app/backend/schemas.py` [NEW]
- `app/backend/services.py` [NEW]
- `tests/test_api_backend.py` [NEW]

## 3. Ngoài Phạm Vi (Strictly Out of Bounds - CẤM ĐỤNG)
- Tuyệt đối không sửa đổi `src/models/`, `src/data/`, `src/explainability/`.
- Không cài đặt thêm packages lạ ngoài FastAPI, Uvicorn, Pydantic, Pillow, Torch, OpenCV.

## 4. Interface / Endpoint Cần Tạo
```python
# 1. Health check
GET /health -> {"status": "healthy", "device": "cuda|cpu", "version": "v4.0"}

# 2. Suy luận đồng thời 3-Head
POST /api/v1/predict
Input: Multipart/form-data (file: UploadFile)
Output: JSON {
    "head_a_predictions": {disease_name: probability},
    "head_b_tb_screening": {"tb_probability": float, "is_positive": bool},
    "head_c_covidx": {"covid_probability": float, "is_positive": bool},
    "inference_time_ms": float
}

# 3. Trích xuất Grad-CAM
POST /api/v1/explain
Input: Multipart/form-data (file: UploadFile, target_head: str, target_class: int)
Output: JSON {
    "heatmap_base64": str,
    "overlay_base64": str,
    "target_head": str,
    "target_class": int
}

# 4. Kiểm toán Shortcut
POST /api/v1/audit
Input: Multipart/form-data (file: UploadFile)
Output: JSON {
    "in_lung_energy_ratio": float,
    "pass_80_percent": bool,
    "lung_mask_base64": str
}
```

## 5. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] Chạy lệnh verify repo: `powershell -File scripts/verify.ps1` đạt 100% PASS.
- [ ] Chạy `pytest tests/test_api_backend.py` pass 100% (test cả 4 endpoints với dummy tensor / TestClient).
- [ ] Không có ngoại lệ nào chưa được xử lý (unhandled exception) khi nạp ảnh hỏng.

## 6. Gợi Ý Model & Mức Nhạy Cảm
- **Mức nhạy cảm**: Sensitive (`$env:CMD_ZDR = "1"`).
- **Tầng model khuyến nghị**: T2 (`Kimi K2.7 Code` hoặc `GLM-5.3`).

---

## 7. Result (CommandCode CLI điền mục này sau khi hoàn thành)
- **Tóm tắt thay đổi**: Triển khai microservice FastAPI tại `app/backend/` phục vụ inference 3-Head (`/api/v1/predict`), sinh Grad-CAM (`/api/v1/explain`), và kiểm toán Shortcut Learning (`/api/v1/audit`). Code sử dụng singleton `LungRayService` để nạp `MultiTaskChestXrayNet`, xử lý ảnh 512x512, trả về JSON/Base64, và xử lý lỗi ảnh hỏng bằng HTTP 422.
- **Danh sách file đã tạo/sửa**:
  - `app/backend/main.py` [NEW]
  - `app/backend/schemas.py` [NEW]
  - `app/backend/services.py` [NEW]
  - `tests/test_api_backend.py` [NEW]
- **Kết quả kiểm thử**: Đã chạy `powershell -File scripts/verify.ps1` đạt 100% PASS (92/92 tests passed).
  ```
  [+] Running: Compileall (Python Syntax Check)...
  [PASS] Compileall (Python Syntax Check)

  [+] Running: Ruff Linting...
  [PASS] Ruff Linting

  [+] Running: Pytest Unit Tests...
  [PASS] Pytest Unit Tests

  >>> SUCCESS: ALL CHECKS PASSED - READY FOR GATEKEEPER REVIEW <<<

  Pytest summary: 92 passed, 1 warning in 30.70s
  ```
- **Điểm chưa chắc / Cần review**: Backend hiện fallback sang random weights khi chưa có `checkpoints/best_model.pth`; cần load checkpoint thực tế khi triển khai production. Không cài thêm package ngoài phạm vi cho phép.
