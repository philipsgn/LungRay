# 🎯 EXECUTIVE SUMMARY
## Nền tảng LungRay: Hệ thống hỗ trợ chẩn đoán & định vị tổn thương X-quang ngực bằng Deep Learning + Explainable AI (WSOL)

**Ngày cập nhật**: 27/09/2026 (v3 — mở rộng phổ bệnh theo Logic A, tái bổ sung COVID-19 với kiểm soát rủi ro)  
**Tên nền tảng**: **LungRay** (CXR Multi-Task CADx + WSOL Platform)  
**Trạng thái**: ✅ **APPROVED FOR EXECUTION (SPECIFIED & SCOPED — MULTI-TASK 3-HEAD)**  
**Khả năng thành công**: 78-83% (điều chỉnh do mở rộng thêm 2 nhiệm vụ phụ + 1 thí nghiệm audit bắt buộc)

> **📌 Thay đổi so với v1**: Bổ sung nhiệm vụ phân loại Lao phổi (Tuberculosis) và COVID-19 như 2 task phụ trong kiến trúc multi-task, giữ nguyên trọng tâm X-quang ngực (không mở rộng sang cơ quan khác). Bổ sung CheXpert-small và RSNA Pneumonia làm nguồn kiểm định ngoại vi (external validation). COVID-19 Radiography Database được đưa trở lại scope **với điều kiện bắt buộc**: Stratified Split theo nguồn ảnh gốc + Shortcut Learning Audit bằng Grad-CAM (không còn là tùy chọn).

---

## 1️⃣ TỔNG HỢP ĐỀ TÀI & PHÁT BIỂU BÀI TOÁN

### Bài toán kỹ thuật cốt lõi (Multi-Task Objective)
Xây dựng hệ thống học sâu hoàn chỉnh giải quyết đồng thời các bài toán sau từ ảnh X-quang ngực thẳng (PA/AP view), dùng chung 1 backbone (shared encoder) với các classification head riêng biệt theo từng nhóm nhiệm vụ:
1. ✅ **Head A — Multi-label Thoracic Disease Classification ($C = 14$):** Dự đoán đồng thời xác suất của 14 bất thường/bệnh lý lồng ngực (Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Consolidation, Edema, Emphysema, Fibrosis, Pleural Thickening, Hernia) — huấn luyện trên **NIH ChestX-ray14**.
2. ✅ **Head B — Tuberculosis Screening (nhị phân):** Phân loại TB/Normal — huấn luyện trên **Tuberculosis (TB) Chest X-ray Database**. Mỗi batch chỉ backprop qua head tương ứng nguồn dữ liệu của nó (Masked Multi-Task Learning), tránh xung đột taxonomy nhãn giữa 2 nguồn.
3. ✅ **Head C — COVID-19 Screening (3 lớp):** Phân loại COVID-19 / Normal / Pneumonia — chuẩn hóa theo benchmark quốc tế **COVIDx CXR-4** (Kaggle: `andyczhao/covidx-cxr2`, *Nature Scientific Reports*). Đảm bảo Zero Patient Data Leakage (`patient_id`) và Source Stratification (`data_source`) để chống Shortcut Learning.
4. ✅ **Weakly-Supervised Object Localization (WSOL) qua XAI:** Trích xuất bản đồ kích hoạt trực quan (Grad-CAM/Grad-CAM++) chỉ từ nhãn mức ảnh (image-level labels), áp dụng cho Head A.
5. ✅ **Quantitative Grounding Validation (IoU):** Nhị phân hóa heatmap thích nghi và kiểm chứng định lượng độ chính xác vị trí tổn thương (IoU) với Bounding Box thực tế trên **VinDr-CXR** (chính) và **RSNA Pneumonia Detection** (bổ sung, riêng nhãn Pneumonia). *Lưu ý: Head B (TB) và Head C (COVID) không có bounding box ground-truth công khai phù hợp nên chỉ đánh giá Grad-CAM định tính, không có chỉ số IoU định lượng.*
6. ✅ **Shortcut Learning Audit (bắt buộc cho Head C):** Chạy Grad-CAM trên các ca dương tính COVID, kiểm tra vùng kích hoạt có tập trung đúng vùng phổi hay lệch sang viền ảnh/watermark — minh chứng độ tin cậy trước khi công bố kết quả Head C.
7. ✅ **External Validation / Generalization Test:** Đánh giá khả năng tổng quát hóa của Head A trên **CheXpert-small-v1** (bệnh viện/quốc gia khác NIH) — chỉ dùng để TEST, không dùng để TRAIN do khác biệt taxonomy nhãn.
8. ✅ **Web Demo Prototype:** Xây dựng ứng dụng tải ảnh X-quang $\to$ suy luận đa nhãn (cả 3 head) $\to$ trực quan hóa heatmap phục vụ bác sĩ tham khảo trong $\le 2$ giây.

### Ứng dụng thực tiễn
- 🏥 **Hỗ trợ sàng lọc sơ bộ (Clinical Decision Support):** Giảm tải cho bác sĩ tại các cơ sở y tế tuyến cơ sở hoặc ca trực đêm.
- 🔍 **Minh bạch hóa AI (Trustworthy AI):** Cung cấp bằng chứng thị giác có thể kiểm chứng, xóa bỏ định kiến "hộp đen" trong y tế.
- 🇻🇳 **Kiểm thử trên dữ liệu người Việt:** Đánh giá tính tổng quát hóa (out-of-distribution) trên bộ dữ liệu VinDr-CXR.

---

## 2️⃣ ĐÁNH GIÁ TÍNH KHẢ THI (ĐÃ ĐƯỢC THU HẸP PHẠM VI)

### ✅ ĐIỂM MẠNH (Why it's Feasible)

| Khía cạnh | Chi tiết | Mức độ |
|:---|:---|:---:|
| **Chiến lược dữ liệu rõ ràng** | • **Primary Dataset**: NIH ChestX-ray14 (112K ảnh, 14 nhãn chuẩn)<br>• **Validation & WSOL**: VinDr-CXR (~3K ảnh test có Bounding Box)<br>• Không ôm đồm tải Terabytes MIMIC-CXR, phù hợp dung lượng ổ cứng | ✅ TỐI ƯU |
| **Công nghệ trưởng thành** | Transfer learning (DenseNet-121, ResNet-50, ViT) + Grad-CAM/Grad-CAM++ là tiêu chuẩn đã được kiểm chứng | ✅ CÓ |
| **Phần cứng phù hợp** | Google Colab / Kaggle GPU (T4/P100/L4) đủ để train DenseNet và fine-tune ViT | ✅ CÓ |
| **Đóng góp khoa học cụ thể** | Định lượng hóa XAI bằng chỉ số IoU so với BBox thực tế thay vì chỉ nhìn định tính bằng mắt | ✅ CAO |

### ⚠️ THÁCH THỨC & BIỆN PHÁP KIỂM SOÁT

| Thách thức | Tác động | Giải pháp cụ thể |
|:---|:---|:---|
| **Mất cân bằng nhãn nghiêm trọng** | Bệnh hiếm (Hernia: ~0.2%, Pneumothorax: ~2%) $\to$ Model dự đoán toàn âm tính | Sử dụng **Focal Loss** + Pos-weight kết hợp tối ưu ngưỡng $\tau_c$ riêng biệt cho từng lớp qua Youden's Index |
| **Rò rỉ dữ liệu (Data leakage)** | Nếu chia train/test ngẫu nhiên theo ảnh, ảnh của cùng bệnh nhân sẽ lọt vào cả 2 tập $\to$ kết quả giả | **Bắt buộc chia tách nghiêm ngặt theo `Patient_ID` (70% train / 10% val / 20% test)** |
| **Định lượng Heatmap sang IoU** | Heatmap là dải màu liên tục $[0, 1]$, Bounding Box là hình chữ nhật | Áp dụng ngưỡng thích nghi $\tau_{mask} = \alpha \cdot \max(M)$ để binarize mask trước khi tính IoU |
| **Tiến độ tuần 7–9 dốc** | Vừa thử nghiệm Focal Loss, vừa thử ViT | Chuẩn bị sẵn code template chuẩn hóa tuần 5-6, dùng pretrained weights từ timm/torchvision |
| **Multi-task mất cân bằng (Task Starvation)** | NIH (112K) áp đảo TB (7K) gấp 16 lần trong cùng backbone chung, khiến model học lệch, "quên" task TB | Áp dụng **Weighted/Balanced Batch Sampling** giữa 2 task — mỗi batch giữ tỷ lệ cố định ảnh NIH:TB, theo dõi validation loss riêng cho từng head |
| **Phương sai cao ở lớp hiếm (Hernia: chỉ 227 ảnh/112K)** | AUC của các lớp hiếm (Hernia, Fibrosis) có thể dao động mạnh giữa các lần chạy | Báo cáo khoảng tin cậy (Bootstrap CI) riêng cho các lớp hiếm thay vì chỉ 1 con số AUC duy nhất |

---

## 3️⃣ LỘ TRÌNH THỰC HIỆN (16 TUẦN)

```
Tuần 1–2  : Setup, Nghiên cứu Papers & Đề cương chi tiết      🟢 Risk: THẤP
Tuần 3–4  : Tiền xử lý dữ liệu, Split Patient-ID & EDA       🟡 Risk: TRUNG BÌNH  
Tuần 5–6  : Huấn luyện Baseline Model (DenseNet/ResNet)      🟡 Risk: TRUNG BÌNH
Tuần 7–9  : Cải tiến Mô hình (Focal Loss, ViT, Tuning)        🔴 Risk: CAO (Quan trọng nhất!)
Tuần 10–11: XAI Grad-CAM & Đo đạc định lượng IoU (VinDr-CXR)  🟡 Risk: TRUNG BÌNH
Tuần 12–13: Phát triển ứng dụng Web Demo trực quan            🟡 Risk: TRUNG BÌNH
Tuần 14–15: Viết báo cáo đồ án, thiết kế slide & poster      🟢 Risk: THẤP
Tuần 16   : Bảo vệ đồ án tốt nghiệp trước Hội đồng            🟡 Risk: TRUNG BÌNH
```

---

## 4️⃣ CHỈ TIÊU KỸ THUẬT & NGHIỆM THU (TARGET METRICS)

| Chỉ số | Ngưỡng mục tiêu | Phương pháp đo lường |
|:---|:---:|:---|
| **Macro AUC-ROC** | $\ge 0.82$ | Trung bình diện tích dưới đường cong ROC của toàn bộ 14 nhãn bệnh trên test set |
| **Macro F1-Score** | $\ge 0.45$ | F1 trung bình tại các ngưỡng quyết định $\tau_c$ tối ưu hóa theo từng lớp |
| **WSOL Mean IoU** | $\ge 0.35$ | Độ trùng khớp giữa Binarized Grad-CAM và Bounding Box chuyên gia trên VinDr-CXR |
| **Thời gian phản hồi Demo** | $\le 2$ giây/ảnh | Tải ảnh $\to$ inference mô hình $\to$ render bản đồ nhiệt Grad-CAM |

---

## 5️⃣ TÀI NGUYÊN & PHẠM VI DỮ LIỆU ĐÃ ĐỒNG BỘ

### Dữ liệu thực nghiệm

| Dataset | Vai trò | Số lượng | Ghi chú |
|:---|:---|:---:|:---|
| **NIH ChestX-ray14** | TRAIN — Head A (14 nhãn) | 112,120 ảnh | Patient-level split 70/10/20 |
| **Tuberculosis (TB) Chest X-ray Database** | TRAIN — Head B (nhị phân TB/Normal) | 3,500 TB + 3,500 Normal | Kaggle: `tawsifurrahman/tuberculosis-tb-chest-xray-dataset` |
| **COVIDx CXR-4 Benchmark** | TRAIN — Head C (3 lớp COVID-19 / Normal / Pneumonia) | ~16,400+ ảnh ($\ge 1024$px) | Kaggle: `andyczhao/covidx-cxr2` (0s mount, chuẩn quốc tế COVID-Net, có `patient_id` & `data_source`) |
| **VinDr-CXR** | TEST — External Validation + WSOL/IoU chính | ~3,000 ảnh (có bbox) | Vai trò gốc, giữ nguyên |
| **RSNA Pneumonia Detection** | TEST — WSOL/IoU bổ sung (chỉ Pneumonia) | Tập test (có bbox) | Mới bổ sung |
| **CheXpert-small-v1** | TEST — External Validation/Generalization (Head A) | Đã tải sẵn | Chỉ dùng để test, không train, do taxonomy nhãn khác NIH |

* *Loại bỏ:* MIMIC-CXR (quá nặng ~570GB, thủ tục PhysioNet phức tạp).
* *Chuyển đổi chuẩn hóa SOTA:* Thay thế COVID-19 Radiography Database (ảnh gốc thấp 256px) bằng **COVIDx CXR-4** (`andyczhao/covidx-cxr2`): độ phân giải gốc cao $\ge 1024$px, mount tức thì trên Kaggle, chuẩn hóa 3 lớp quốc tế và bảo toàn đầy đủ metadata ID bệnh nhân + nguồn gốc đa trung tâm.

### Thư viện & Công nghệ
* **Framework học sâu:** PyTorch, torchvision, timm (Transformer models).
* **XAI & Xử lý ảnh:** pytorch-grad-cam, OpenCV, PIL, albumentations.
* **Đánh giá & Khoa học dữ liệu:** scikit-learn, numpy, pandas, matplotlib, seaborn.
* **Giao diện Web Demo:** Streamlit (hoặc Flask + Vanilla CSS UI).

---

## 6️⃣ HÀNH ĐỘNG CẦN THỰC HIỆN NGAY

1. [x] **Chuẩn hóa phát biểu bài toán** trong [PROPOSAL.md](file:///c:/Users/TanPhat/Documents/AI_E/Chest%20X-rays/docs/PROPOSAL.md).
2. [ ] **Thiết lập kho mã nguồn (Repository):** Tạo cấu trúc thư mục `src/data`, `src/models`, `src/explainability`, `src/app`.
3. [ ] **Tải và phân tích dữ liệu giai đoạn 1:** Tải metadata và tập ảnh ChestX-ray14 (kiểm tra file resize $512 \times 512$ có giữ `Data_Entry_2017.csv` không), kiểm tra phân bố của 14 nhãn bệnh.
4. [ ] **Hiện thực hàm chia `patient_level_split`:** Đảm bảo triệt để $Train \cap Test = \emptyset$ về ID bệnh nhân (áp dụng cho NIH; TB dataset dùng random stratified split do không có Patient_ID).
5. [x] **Tải/Mount 3 nguồn dữ liệu:** NIH ChestX-ray14 (Head A), TB Chest X-ray Database (Head B), COVIDx CXR-4 Benchmark (Head C).
6. [x] **Thiết kế kiến trúc Multi-Task:** Shared backbone + Head A (14-label) + Head B (TB nhị phân) + Head C (COVIDx 3-lớp) + cơ chế Weighted Batch Sampling giữa 3 task.
7. [x] **Trích xuất metadata nguồn ảnh gốc và Patient ID của COVIDx CXR-4** (từ `train.txt`, `test.txt`) đảm bảo Zero Patient Leakage và Source Stratification.
