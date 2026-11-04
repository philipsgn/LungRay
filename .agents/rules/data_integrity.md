# 🛡️ AGENT RULE: DATA INTEGRITY & CLINICAL SAFETY (LUNGRAY PLATFORM)
## Mã Quy Chuẩn: RULE-02-DATA-INTEGRITY
## Dự án: Nền tảng LungRay
## Áp dụng cho: `DataEngineerAgent`, `ModelArchitectAgent`

---

### 1. NGUYÊN TẮC VÀNG CHỐNG DATA LEAKAGE (BẮT BUỘC)
- **Cấm hoàn toàn chia tách ngẫu nhiên theo ảnh (Row/Image Random Split) trên NIH ChestX-ray14**:
  Ảnh X-quang của cùng một bệnh nhân chụp ở các thời điểm khác nhau có cấu trúc khung xương sườn, bóng tim và dấu vết phẫu thuật giống nhau. Chia theo ảnh sẽ dẫn đến việc mô hình nhận diện bệnh nhân thay vì nhận diện bệnh lý, tạo ra AUC giả lập $\ge 0.95$.
- **Quy chuẩn chia tách theo `Patient_ID`**:
  ```python
  # Danh sách bệnh nhân duy nhất
  unique_patients = np.array(list(set(df['Patient_ID'])))
  # Phân bổ 70% Train, 10% Val, 20% Test
  ```
- **Ràng buộc kiểm thử bắt buộc (Assertion Rule)**:
  Mọi pipeline trước khi huấn luyện BẮT BUỘC phải vượt qua assertion:
  ```python
  assert len(set(train_patients).intersection(set(test_patients))) == 0, "FATAL: Data leakage detected between Train and Test!"
  assert len(set(train_patients).intersection(set(val_patients))) == 0, "FATAL: Data leakage detected between Train and Val!"
  ```

---

### 2. NGUYÊN TẮC CHỐNG SHORTCUT LEARNING TRÊN COVID-19 DATABASE
- **Không chia ngẫu nhiên trên COVID-19 Radiography Database**:
  Bộ dữ liệu này được hợp nhất từ 4 nguồn khác nhau. Nếu chia ngẫu nhiên, mô hình sẽ học thuộc độ phân giải, phông chữ watermark hoặc viền đen máy chụp của nguồn dữ liệu (DeGrave et al., 2021).
- **Quy tắc phân tầng theo nguồn (Source-Stratified Split)**:
  Mỗi phân nhóm nguồn con (PadChest, SIRM, RSNA, Kermany) phải được chia đều theo tỷ lệ 70/10/20 vào cả 3 tập Train, Val và Test.
- Mọi kết quả của Head C BẮT BUỘC phải đi kèm báo cáo **Shortcut Learning Audit** trước khi được công nhận.

---

### 3. QUY CHUẨN TĂNG CƯỜNG DỮ LIỆU Y TẾ AN TOÀN (AUGMENTATION CONSTRAINTS)

| Phép biến đổi | Trạng thái | Giới hạn kỹ thuật | Lý do y khoa lâm sàng |
|:---|:---:|:---|:---|
| **Lật dọc (Vertical Flip)** | ❌ **NGHIÊM CẤM** | Tuyệt đối không dùng | Đầu người không thể chúc xuống dưới; vi phạm hoàn toàn giải phẫu học lồng ngực. |
| **Xoay ảnh (Rotation)** | ⚠️ Hạn chế | Tối đa $\pm 10^\circ$ | Tư thế chụp X-quang chuẩn chỉ cho phép sai lệch góc đứng rất nhỏ. |
| **Phóng to/Thu nhỏ (Scale/Crop)** | ⚠️ Hạn chế | Tỷ lệ $0.95 - 1.05$ | Giữ nguyên tỷ lệ tim-lồng ngực (Cardiothoracic ratio) để chẩn đoán bóng tim to (Cardiomegaly). |
| **Lật ngang (Horizontal Flip)** | ⚠️ Cân nhắc | $p \le 0.5$ | Tim người bình thường nằm lệch trái. Chỉ dùng nếu không gây nhiễu nhãn Cardiomegaly hoặc dùng chung nhãn đảo ngược phủ tạng. |
| **Biến đổi độ sáng/độ tương phản** | ✅ Được phép | $\pm 10\%$ | Mô phỏng sự sai khác về liều chiếu tia X (mAs) giữa các máy chụp. |

---

### 4. QUY CHUẨN XỬ LÝ ẢNH DICOM & DẢI ĐỘNG (DYNAMIC RANGE)
- Khi đọc file DICOM (`.dcm`), phải chuyển đổi từ giá trị thô sang đơn vị Hounsfield Unit (HU) hoặc Rescale Slope & Intercept:
  `hu_image = raw_pixel * RescaleSlope + RescaleIntercept`
- Áp dụng Windowing thích hợp cho cửa sổ phổi (Lung Window: Level $\approx -600$, Width $\approx 1500$) hoặc cửa sổ trung thất (Mediastinum Window) trước khi chuẩn hóa về khoảng $[0, 255]$ hoặc $[0, 1]$.
