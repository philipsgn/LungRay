# KAGGLE GPU PRODUCTION TRAINING OPERATIONAL GUIDE
## Nền tảng LungRay: Quy Trình Vận Hành Huấn Luyện SOTA Trên Hạ Tầng Kaggle GPU (`kaggle/train_multitask_kaggle.py`)

---

| Thuộc tính | Chi tiết |
|:---|:---|
| **Hệ thống** | **LungRay** (CXR Multi-Task CADx + WSOL Grounding Engine) |
| **Kịch bản thực thi** | `kaggle/train_multitask_kaggle.py` (Kaggle Production SOTA Training Script) |
| **Phiên bản tài liệu** | v7.0 (Post-TASK-013, Delivery Gate 6 Approved) |
| **Hạ tầng mục tiêu** | Kaggle Cloud GPU (NVIDIA Tesla P100 16GB / 2x NVIDIA T4 15GB) |
| **Mục đích** | Hướng dẫn vận hành chi tiết, chuẩn hóa các bước mount dữ liệu, cấu hình tham số, huấn luyện hai giai đoạn và hiệu chuẩn ngưỡng Youden's J |

---

## 1. TỔNG QUAN & PHẠM VI VẬN HÀNH

Tài liệu này cung cấp hướng dẫn vận hành chuẩn hóa ở cấp độ sản xuất (Production-Grade Operational Guide) để khởi chạy, giám sát và thu hoạch kết quả huấn luyện mô hình học sâu đa nhiệm 3 nhánh **LungRay** thông qua kịch bản `kaggle/train_multitask_kaggle.py` trên hạ tầng đám mây Kaggle GPU.

### Các Tính Năng Đột Phá Được Tích Hợp (TASK-013 Milestones):
1. **Asymmetric Loss (ASL)**: Triệt tiêu có chọn lọc gradient của các mẫu âm tính dễ (easy negatives), khắc phục hoàn toàn sự mất cân bằng lớp cực đoan trên 14 bệnh lý NIH ChestX-ray14.
2. **Focal Loss với Dynamic `pos_weight`**: Tính toán và kẹp trần tỷ lệ âm/dương cho từng lớp bệnh hiếm (như Thoát vị hoành 0.2%), tự động đăng ký module buffer an toàn thiết bị GPU.
3. **Parameter-Free LayerNorm**: Chuẩn hóa không gian đặc trưng sau pooling mà không thêm tham số học được, bảo đảm tương thích ngược tuyệt đối với các trọng số đã lưu.
4. **Weighted Multi-Task Batch Sampler**: Duy trì cố định tỷ lệ $60\% \text{ NIH} : 25\% \text{ COVIDx} : 15\% \text{ TB}$ trong mỗi mini-batch để triệt tiêu hiện tượng bỏ đói nhiệm vụ (Task Starvation).
5. **Hiệu Chuẩn Ngưỡng Youden's J Tự Động**: Tự động tính toán 16 ngưỡng quyết định tối ưu trên tập validation và xuất file JSON chuẩn hóa.

---

## 2. YÊU CẦU PHẦN CỨNG & HẠ TẦNG KAGGLE CLOUD

### 2.1. Cấu Hình Phần Cứng Khuyến Nghị

| Thành phần hạ tầng | Cấu hình tiêu chuẩn | Cơ sở kỹ thuật & Lưu ý vận hành |
|:---|:---|:---|
| **GPU Accelerator** | NVIDIA Tesla P100 (16GB VRAM) hoặc 2x NVIDIA T4 (15GB VRAM) | Ưu tiên Tesla P100 đơn nhân vì băng thông FP16 cao và bộ nhớ thống nhất, loại bỏ chi phí truyền thông đa GPU DDP trên kernel Kaggle. |
| **Kiến trúc GPU** | Pascal (P100) hoặc Turing (T4) có Tensor Cores | Tensor Cores tăng tốc tính toán ma trận hỗn hợp thông qua `torch.amp.autocast("cuda")`. |
| **Hệ thống vCPU** | 4 vCPUs (Kaggle Standard) | Cần giới hạn số lượng luồng worker của DataLoader để tránh xung đột tài nguyên OpenMP CPU. |
| **Bộ nhớ RAM** | 30 GB System RAM | Đủ để lưu trữ toàn bộ Pandas DataFrame metadata và chỉ mục tệp trong bộ nhớ. |
| **Ổ đĩa tạm thời** | 20 GB Disk tại `/kaggle/working/` | **QUAN TRỌNG**: Không thực hiện resize 112K ảnh trực tiếp trong phiên chạy vì sẽ gây tràn đĩa. **Bắt buộc mount các tập dữ liệu đã resize sẵn 512x512 tại `/kaggle/input/`**. |

---

## 3. CẤU TRÚC MOUNT DỮ LIỆU & PHÁT HIỆN ĐƯỜNG DẪN TỰ ĐỘNG

Module `src/data/ingestion.py` cung cấp hàm tìm kiếm linh hoạt `find_kaggle_dataset()`, tự động quét cây thư mục `/kaggle/input/` lên đến độ sâu 5 tầng, xử lý các biến thể slug và thư mục người dùng lồng nhau.

### 3.1. Danh Sách Kaggle Datasets Bắt Buộc Phải Mount

| Tên Bộ Dữ Liệu | Kaggle Slug Đề Xuất | Quy Tắc Nhận Diện Trong `src/data/ingestion.py` | Vai Trò Trong Huấn Luyện |
|:---|:---|:---|:---|
| **NIH ChestX-ray14 (512px)** | `lungray-nih-512` | Tìm chuỗi `["lungray-nih-512", "nih-512", "nih_512", "chestxray14"]` (yêu cầu thư mục ảnh tồn tại) | Huấn luyện Head A (14 bệnh lồng ngực đa nhãn) |
| **COVIDx CXR-4 (512px)** | `lungray-covidx-512` | Tìm chuỗi `["lungray-covidx-512", "covidx-512", "covidx-cxr4", "covidx-cxr2"]` (yêu cầu `train.txt` và `test.txt`) | Huấn luyện Head C (Sàng lọc COVID-19 3 lớp / nhị phân) |
| **Tuberculosis Database** | `tuberculosis-tb-chest-xray-dataset` | Tìm chuỗi `["tuberculosis-tb-chest-xray-dataset", "tb-chest-xray", "tuberculosis"]` | Huấn luyện Head B (Sàng lọc Lao phổi nhị phân) |
| **Chỉ mục Phân chia (Splits)** | Tích hợp sẵn trong repo | `data/splits/` hoặc `dataset/splits/` (`patient_splits.csv`, `covid_splits.csv`, `tb_splits.csv`) | Khóa chặt Zero Patient Leakage và Source Stratification |

### 3.2. Sơ Đồ Cấu Trúc Thư Mục Thực Thi Trên Kaggle

```
/kaggle/
├── input/
│   ├── lungray-nih-512/
│   │   ├── images/                       # 112,120 ảnh chuẩn 512x512
│   │   └── patient_splits.csv            # Phân chia 70/10/20 theo Patient_ID
│   ├── lungray-covidx-512/
│   │   ├── train/                        # Ảnh COVIDx train letterboxed 512x512
│   │   ├── test/                         # Ảnh COVIDx test letterboxed 512x512
│   │   ├── train.txt                     # Metadata train: id, filename, class, data_source
│   │   └── test.txt                      # Metadata test
│   └── tuberculosis-tb-chest-xray-dataset/
│       └── Tuberculosis-Chest-X-ray-Dataset/
│           ├── Normal/                   # 3,500 ảnh bình thường
│           └── Tuberculosis/             # 3,500 ảnh lao phổi
└── working/
    ├── checkpoint_multitask_optimized.pth # Checkpoint validation tốt nhất (atomic replace)
    ├── last_model.pth                    # Checkpoint atomic lưu cuối mỗi epoch để resume
    ├── configs/
    │   └── optimal_thresholds.json       # 16 ngưỡng quyết định được hiệu chuẩn theo Youden's J
    └── results/
        └── baseline/
            ├── multitask_training_curves.png # Đồ thị trực quan hóa Loss và AUROC
            └── training_history.csv      # Bảng số liệu chi tiết qua từng epoch
```

---

## 4. THIẾT LẬP MÔI TRƯỜNG PYTHON & XỬ LÝ WORKER

### 4.1. Cài Đặt Gói Phụ Thuộc
Môi trường Kaggle Notebook đã tích hợp sẵn PyTorch $\ge 2.0$ và CUDA. Khởi tạo các thư viện bổ sung qua lệnh sau tại đầu notebook:

```bash
pip install -q albumentations timm opencv-python-headless scikit-learn pandas matplotlib
```

### 4.2. Tối Ưu Hóa Tiến Trình Worker & Biến Môi Trường
Để tránh tình trạng quá tải CPU do tranh chấp tài nguyên luồng OpenMP giữa PyTorch và OpenCV, thiết lập các biến môi trường sau trước khi chạy script:

```bash
export CMD_ZDR=1
export NO_ALBUMENTATIONS_UPDATE=1
export LUNGRAY_NUM_WORKERS=4
```

Trong mã nguồn `kaggle/train_multitask_kaggle.py`, hàm khởi tạo worker đã tích hợp sẵn:
```python
def _dataloader_worker_init(worker_id: int) -> None:
    cv2.setNumThreads(0)
    torch.set_num_threads(1)
```

---

## 5. TRA CỨU ĐẦY ĐỦ THAM SỐ DÒNG LỆNH (CLI ARGUMENTS REFERENCE)

Kịch bản `kaggle/train_multitask_kaggle.py` hỗ trợ cấu hình toàn diện qua `argparse`:

| Tham số dòng lệnh | Kiểu dữ liệu | Giá trị mặc định | Giải thích ý nghĩa & Cơ sở kỹ thuật |
|:---|:---:|:---:|:---|
| `--backbone` | `str` | `densenet121` | Kiến trúc trích xuất đặc trưng (`densenet121`, `resnet50`, `vit_base_patch16_224`). |
| `--head-norm` | `str` | `layernorm` | Tầng chuẩn hóa đặc trưng (`layernorm`, `batchnorm`, `none`). Sử dụng LayerNorm parameter-free (`elementwise_affine=False`). |
| `--head-a-criterion`| `str` | `focal` | Hàm mất mát cho Head A (`focal`, `asl`, `bce`). Mặc định trong code là focal; truyền `--head-a-criterion asl` để huấn luyện SOTA Asymmetric Loss. |
| `--head-c-criterion`| `str` | `focal` | Hàm mất mát cho Head C (`focal`, `asl`, `bce`). |
| `--asl-gamma-neg` | `float` | `4.0` | Số mũ tập trung nhãn âm tính của ASL. Triệt tiêu gradient của easy negatives ($p < 0.05$). |
| `--asl-gamma-pos` | `float` | `1.0` | Số mũ tập trung nhãn dương tính của ASL. Giữ gradient cho tổn thương mờ. |
| `--asl-clip` | `float` | `0.05` | Ngưỡng dịch chuyển lề xác suất âm tính $p_m = \max(p - \text{clip}, 0)$. |
| `--focal-alpha` | `float` | `0.25` | Hệ số cân bằng alpha cho Focal Loss. |
| `--focal-gamma` | `float` | `2.0` | Số mũ focusing gamma cho Focal Loss. |
| `--pos-weight-clamp`| `float` | `50.0` | Ngưỡng kẹp trần tối đa cho trọng số positive động $(N_{neg} / N_{pos})$ trên các bệnh cực hiếm. |
| `--epochs` | `int` | `25` | Tổng số chu kỳ huấn luyện. |
| `--batch-size` | `int` | `16` | Kích thước mini-batch cho ảnh 512x512 trên 16GB VRAM. |
| `--lr` | `float` | `1e-4` | Learning rate đỉnh của bộ tối ưu AdamW. |
| `--weight-decay` | `float` | `1e-5` | Hệ số suy giảm trọng số (L2 regularization). |
| `--max-batches` | `int` | `600` | Giới hạn batch mỗi epoch cho chế độ chạy nhanh Kaggle (`0` = chạy toàn bộ ~4,200 batches). |
| `--max-val-batches` | `int` | `120` | Giới hạn batch validation mỗi head (`0` = chạy toàn bộ tập validation). |
| `--save-name` | `str` | `checkpoint_multitask_optimized.pth` | Tên tệp checkpoint validation tốt nhất được xuất ra. |
| `--resume` | `flag` | `False` | Tự động khôi phục mô hình, optimizer, scheduler và epoch từ `last_model.pth`. |
| `--no-calibrate` | `flag` | `False` | Bỏ qua bước hiệu chuẩn ngưỡng Youden's J sau khi huấn luyện xong. |
| `--thresholds-out` | `str` | `None` | Đường dẫn xuất file JSON kết quả hiệu chuẩn ngưỡng (mặc định lưu tại `configs/optimal_thresholds.json`). |
| `--allow-missing` | `flag` | `False` | Cờ cho phép chạy thử nghiệm cục bộ nếu thiếu một phần dữ liệu ảnh. |

---

## 6. SỔ TAY THỰC THI TỪNG BƯỚC (STEP-BY-STEP PLAYBOOK)

### 6.1. Kịch Bản 1: Chạy Thử Nghiệm Nhanh & Kiểm Tra Pipeline (Quick Prototyping)
Khuyến nghị chạy thử 2 epochs với ngân sách 600 batches để xác minh DataLoader, bộ máy Masked Loss và cơ chế tính AUROC:

```bash
python kaggle/train_multitask_kaggle.py \
    --backbone densenet121 \
    --head-norm layernorm \
    --head-a-criterion asl \
    --head-c-criterion focal \
    --epochs 2 \
    --batch-size 16 \
    --lr 1e-4 \
    --max-batches 600 \
    --max-val-batches 120 \
    --save-name checkpoint_multitask_prototype.pth
```

### 6.2. Kịch Bản 2: Huấn Luyện SOTA Hoàn Chỉnh Với Asymmetric Loss (Production SOTA Run)
Chạy toàn diện 25-30 epochs với toàn bộ dữ liệu (uncapped batches: `--max-batches 0 --max-val-batches 0`):

```bash
python kaggle/train_multitask_kaggle.py \
    --backbone densenet121 \
    --head-norm layernorm \
    --head-a-criterion asl \
    --head-c-criterion focal \
    --asl-gamma-neg 4.0 \
    --asl-gamma-pos 1.0 \
    --asl-clip 0.05 \
    --epochs 25 \
    --batch-size 16 \
    --lr 1e-4 \
    --weight-decay 1e-5 \
    --max-batches 0 \
    --max-val-batches 0 \
    --save-name best_model_asl_sota.pth
```

### 6.3. Kịch Bản 3: Huấn Luyện Đối Chuẩn Với Focal Loss & Dynamic Pos-weight
Chạy kịch bản đối chuẩn để so sánh hiệu năng giữa Focal Loss và Asymmetric Loss trên cùng một kiến trúc:

```bash
python kaggle/train_multitask_kaggle.py \
    --backbone densenet121 \
    --head-norm layernorm \
    --head-a-criterion focal \
    --head-c-criterion focal \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --pos-weight-clamp 50.0 \
    --epochs 25 \
    --batch-size 16 \
    --lr 1e-4 \
    --max-batches 0 \
    --max-val-batches 0 \
    --save-name best_model_focal_sota.pth
```

### 6.4. Kịch Bản 4: Khôi Phục Phiên Huấn Luyện Bị Gián Đoạn (Resume Training)
Khi phiên làm việc Kaggle đạt giới hạn 9 hoặc 12 giờ GPU và bị ngắt kết nối, sử dụng cờ `--resume` để tiếp tục ngay tại epoch dở dang từ checkpoint `last_model.pth`:

```bash
python kaggle/train_multitask_kaggle.py \
    --head-a-criterion asl \
    --resume \
    --save-name best_model_asl_sota.pth
```

---

## 7. QUY TRÌNH HIỆU CHUẨN NGƯỠNG TỰ ĐỘNG (POST-TRAINING CALIBRATION)

Sau khi hoàn tất epoch cuối cùng hoặc khi kích hoạt dừng sớm (Early Stopping), kịch bản tự động kích hoạt hàm `calibrate_thresholds()`:
1. Nạp toàn bộ tập validation của cả 3 heads.
2. Quét toàn bộ các điểm cắt trên đường cong ROC để tìm ngưỡng $\tau_c^*$ cực đại hóa chỉ số Youden's J:
   $$J = \text{Sensitivity} + \text{Specificity} - 1 = \text{TPR} - \text{FPR}$$
3. Xuất kết quả ra tệp `configs/optimal_thresholds.json`.

Ví dụ cấu trúc tệp xuất ra:
```json
{
  "head_a": {
    "Atelectasis": 0.35,
    "Cardiomegaly": 0.42,
    "Effusion": 0.38,
    "Infiltration": 0.32,
    "Mass": 0.28,
    "Nodule": 0.26,
    "Pneumonia": 0.22,
    "Pneumothorax": 0.30,
    "Consolidation": 0.31,
    "Edema": 0.36,
    "Emphysema": 0.45,
    "Fibrosis": 0.24,
    "Pleural_Thickening": 0.28,
    "Hernia": 0.15
  },
  "head_b": {
    "Tuberculosis": 0.50
  },
  "head_c": {
    "COVID-19": 0.50
  }
}
```

---

## 8. SẢN PHẨM ĐẦU RA & CHỈ SỐ NGHIỆM THU DỰ KIẾN (EXPECTED OUTPUTS)

### 8.1. Các Tệp Artifacts Được Tạo Ra

1. **`checkpoint_multitask_optimized.pth`**: Checkpoint trọng số tối ưu nhất, được đánh giá trên điểm tổng hợp đa nhiệm:
   $$S_{\text{val}} = 0.40 \cdot \text{AUC}_A + 0.30 \cdot \text{AUC}_B + 0.30 \cdot \text{AUC}_C$$
2. **`last_model.pth`**: Checkpoint atomic lưu trữ trạng thái của model, optimizer và scheduler sau mỗi epoch.
3. **`results/baseline/multitask_training_curves.png`**: Đồ thị biểu diễn tiến trình hội tụ của Loss và Macro AUROC qua từng epoch.
4. **`results/baseline/training_history.csv`**: Bảng dữ liệu định lượng chi tiết loss và AUC của từng head.
5. **`configs/optimal_thresholds.json`**: Tập tin cấu hình chứa 16 ngưỡng quyết định lâm sàng.

### 8.2. Chỉ Tiêu Đạt Chuẩn Nghiệm Thu (Acceptance Targets)

| Chỉ số kiểm định | Ngưỡng tối thiểu chấp nhận | Kết quả kỳ vọng với ASL & LayerNorm |
|:---|:---:|:---:|
| **Macro AUROC Head A (14 bệnh NIH)** | $\ge 0.820$ | **$0.827 – 0.835$** |
| **AUROC Head B (Lao phổi TB)** | $\ge 0.950$ | **$0.995 – 1.000$** |
| **Macro AUROC Head C (COVIDx CXR-4)** | $\ge 0.730$ | **$0.780 – 0.850$** |
| **Tỷ lệ Gradient Rò Rỉ Giữa Các Head** | $0.0\%$ | **$0.0\%$ (Zero Gradient Leakage)** |
| **Tính Toàn Vẹn Của `state_dict`** | Strict Load = True | **0 keys mới sinh ra** |

---

## 9. XỬ LÝ SỰ CỐ & CÂU HỎI VẬN HÀNH THƯỜNG GẶP (TROUBLESHOOTING)

1. **Sự cố tràn bộ nhớ GPU (CUDA Out Of Memory - OOM)**:
   - *Nguyên nhân*: Batch size quá lớn hoặc gradient accumulation không được giải phóng.
   - *Khắc phục*: Giảm `--batch-size` từ `16` xuống `8` hoặc `12`. Do ảnh có kích thước $512 \times 512$, batch size 16 là giới hạn tối ưu cho VRAM 16GB.
2. **Cảnh báo DataLoader Worker Timeout hoặc CPU Thrashing**:
   - *Nguyên nhân*: Số lượng luồng worker vượt quá số vCPU thực tế của Kaggle kernel.
   - *Khắc phục*: Thiết lập biến môi trường `export LUNGRAY_NUM_WORKERS=2` hoặc `4`. Tuyệt đối không đặt quá 4.
3. **Mô hình không tìm thấy tệp ảnh trên Kaggle Input**:
   - *Nguyên nhân*: Người dùng đổi tên dataset hoặc cấu trúc thư mục lồng nhau khác chuẩn.
   - *Khắc phục*: Hàm `find_kaggle_dataset()` trong `src/data/ingestion.py` sẽ tự động quét các thư mục con. Hãy đảm bảo dataset được add chính xác vào thanh panel bên phải của Kaggle Notebook.
