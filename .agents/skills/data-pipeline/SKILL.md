---
name: data-pipeline
description: Quy trình chuẩn bị dữ liệu X-quang lồng ngực, phân chia tập dữ liệu chống rò rỉ (Zero Patient Leakage), kiểm định metadata và khởi tạo Multi-Task DataLoader cho LungRay.
---

# 🔄 SKILL: DATA PIPELINE & INTEGRITY SPLITTING (LUNGRAY PLATFORM)
## Mã Quy Trình: SKILL-DATA-PIPELINE
## Dự án: Nền tảng LungRay
## Thực hiện bởi: `DataEngineerAgent`

---

## 1. MỤC ĐÍCH
Quy trình hướng dẫn từng bước chuẩn bị dữ liệu từ các nguồn trên Kaggle, thực hiện phân tích EDA, phân chia tập dữ liệu chống rò rỉ và khởi tạo PyTorch Multi-Task DataLoader.

---

## 2. CÁC BƯỚC THỰC THI (STEP-BY-STEP)

```
[Bước 1: Mount/Khảo sát Dữ liệu] ──► [Bước 2: Trích xuất Metadata Nguồn] ──► [Bước 3: Chạy Split Engine]
                                                                                        │
[Bước 5: Khởi tạo Multi-Task DataLoader] ◄── [Bước 4: Chạy Unit Test Chống Leakage] ◄──┘
```

### Bước 1: Khảo sát cấu trúc thư mục dữ liệu
1. Kiểm tra sự tồn tại của các file metadata:
   - NIH ChestX-ray14: `Data_Entry_2017.csv`
   - TB Database: Thư mục ảnh `Tuberculosis/` và `Normal/`
   - COVID-19 Radiography: File `COVID-19.metadata.xlsx` hoặc CSV tương ứng.
2. Kiểm tra tính toàn vẹn của file ảnh (kích thước, định dạng, corrupt images).

### Bước 2: Chuẩn hóa & Trích xuất Metadata
1. Làm sạch danh sách nhãn NIH (tách chuỗi nhãn phân cách bởi ký tự `|` thành 14 cột nhị phân one-hot).
2. Trích xuất nhãn nguồn gốc (`source`) cho bộ COVID-19 Radiography Database.
3. Lưu metadata chuẩn hóa vào `data/processed/`.

### Bước 3: Phân chia tập dữ liệu (Splits Generation)
1. Chạy script phân chia tập dữ liệu:
   ```bash
   python -m src.data.splits --nih-meta data/raw/nih/Data_Entry_2017.csv \
                             --covid-meta data/raw/covid19/COVID.metadata.csv \
                             --tb-dir data/raw/tb/ \
                             --output-dir data/splits/ \
                             --seed 42
   ```
2. Kiểm tra 3 file đầu ra được tạo:
   - `data/splits/patient_splits.csv`
   - `data/splits/covid_splits.csv`
   - `data/splits/tb_splits.csv`

### Bước 4: Kiểm thử rò rỉ dữ liệu tự động (Verification Test)
1. Thực thi PyTest:
   ```bash
   pytest tests/test_data_leakage.py -v
   ```
2. **Tiêu chuẩn vượt qua**: 100% tests Passed. Không có bất kỳ `Patient_ID` nào xuất hiện đồng thời ở 2 tập.

### Bước 5: Kiểm tra DataLoader & Weighted Batch Sampler
1. Chạy script kiểm thử mini-batch:
   ```bash
   python -m src.data.sampler --test-batch-size 32
   ```
2. Xác nhận tỷ lệ mẫu trong batch xấp xỉ: ~19 ảnh NIH (60%), ~8 ảnh COVID (25%), ~5 ảnh TB (15%).

---

### Bước 6: Biên soạn & Kiểm định Jupyter Notebook EDA Tương Tác Sống
1. Khởi tạo notebook chuẩn `notebooks/01_exploratory_data_analysis.ipynb`.
2. **Quy tắc bắt buộc (Inviolable Constraint 7)**:
   - 100% tế bào phân tích phải là code Python tương tác: `pd.read_csv`, `sns.heatmap`, `plt.barh`, `zipfile.ZipFile`, `plt.imshow`.
   - Cấm tuyệt đối `display(Image("...png"))` hay nhúng ảnh tĩnh giả lập.
   - Trích xuất và trực quan hóa ảnh X-quang thật từ các file ZIP của người dùng.
3. Thực thi toàn bộ notebook để đảm bảo mọi cell đều có kết quả đầu ra thực tế (`outputs` chứa hình ảnh và bảng dữ liệu) trước khi bàn giao Gate 2.

---

## 3. TIÊU CHÍ NGHIỆM THU GATE 2 (GATE 2 DEFINITION OF DONE)
- [x] Zero Data Leakage trên NIH (112,120 ảnh chia theo `Patient_ID`, test leakage pass 100%).
- [x] Source-Stratified Split trên COVID-19 (độ lệch nguồn giữa Train/Test $< 0.1\%$).
- [x] Stratified Split trên TB (bảo đảm tỷ lệ 5:1).
- [x] `WeightedMultiTaskBatchSampler` đã mô phỏng thực nghiệm bám sát 60:25:15.
- [x] Notebook `01_exploratory_data_analysis.ipynb` tuân thủ chuẩn nghiên cứu sống, 100% code thư viện thật, đầy đủ outputs biểu đồ và ảnh X-quang.

