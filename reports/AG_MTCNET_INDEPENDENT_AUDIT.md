# Báo cáo thẩm định độc lập AG-MTCNet

**Ngày thẩm định:** 14-11-2026  
**Phạm vi:** Đối chiếu chỉ thị AG-MTCNet với checkpoint và artifact hiện có trong workspace.  
**Mục đích:** Xác định điều gì có thể khẳng định từ bằng chứng lưu trữ; không thay thế đánh giá lại trên tập kiểm định được khóa.

## 1. Kết luận điều hành

**Chưa đủ căn cứ phê duyệt `ag_mtcnet_best.pth` làm mô hình mặc định chính thức.** Checkpoint tồn tại và là mô hình DenseNet-121 ba head với Head C ba lớp. Tuy nhiên, nhiều chỉ số nổi bật trong chỉ thị không khớp metadata checkpoint hoặc các bảng đánh giá độc lập đang có. Một số kết quả có dấu hiệu mâu thuẫn trực tiếp: AUROC Head C trong metadata checkpoint là `NaN`, tập VinDr live hiện có chỉ gồm 20 ca với mean box IoU 0.117685, và 60 ca COVID trong artifact live đều không đạt ngưỡng năng lượng trong phổi 80%.

Kết luận này không chứng minh mô hình không thể đạt các con số được nêu. Nó xác định rằng những con số ấy **chưa được xác nhận bởi artifact có thể kiểm tra trong workspace**. Mô hình chỉ nên được giữ ở trạng thái ứng viên nghiên cứu cho đến khi đánh giá tái lập được trên tập test độc lập, có manifest, mã lệnh, cấu hình và log đầy đủ.

## 2. Kiểm tra checkpoint và kiến trúc

Checkpoint `checkpoints/ag_mtcnet_best.pth` tồn tại, dung lượng 28,475,184 byte (28.48 MB thập phân; khoảng 27.16 MiB). Metadata ghi kiến trúc `DenseNet121-AG-MTCNet-3Head`, `num_classes_c=3`, ảnh đầu vào 256 px, và 7,056,075 phần tử tensor trong state dict. Tên checkpoint và metadata không xác nhận 24.03 triệu tham số hoặc file 95.96 MB như chỉ thị.

State dict chứa backbone DenseNet-121 cùng ba head; không thấy trọng số decoder Dense-UNet trong checkpoint này. Metadata có trường `gate_source` trỏ đến checkpoint Dense-UNet riêng. Vì vậy, nếu hệ thống suy luận dùng cổng giải phẫu, đó là pipeline gồm ít nhất hai artifact, không phải một checkpoint AG-MTCNet tự chứa. Tổng dung lượng triển khai cần được đo với cả hai file và cấu hình phục vụ thực tế.

Checkpoint ghi lịch sử huấn luyện với giai đoạn S2 dừng sau 11 epoch, lựa chọn epoch 5 theo `val_combined_auc`. Metadata test ghi Head A AUROC 0.7578296 và Head B AUROC 0.9975239. Head C AUROC là `NaN`, dù accuracy được ghi là 1.0. `NaN` nghĩa là AUROC chưa được tính hợp lệ hoặc không xác định trong lần đánh giá được lưu; accuracy đơn lẻ không thay thế được AUROC, độ nhạy, độ đặc hiệu, ma trận nhầm lẫn và phân bố lớp.

### 2.1. Lỗi xử lý nhãn Head C được xác định trong notebook huấn luyện

Đầu ra đã lưu của `notebooks/09_finetune_ag_mtcnet_backbones.ipynb` cho thấy COVIDx có 76,345 dòng nhưng phân bố `label` chỉ có **một giá trị duy nhất: 0**. Cùng log ghi số lượng lớp Head C là `[12000, 0, 0]`; AUROC Head C là `NaN` ở validation và test, còn accuracy là 1.0000. Ảnh Data Explorer Kaggle do người dùng cung cấp cho thấy manifest có nhãn chữ `positive` và `negative`. Hàm `covid_label()` trong notebook chỉ nhận diện các chuỗi có `covid`, `pneumonia`, `opacity`, `viral`, `bacterial` hoặc `non` kết hợp với `covid`; chuỗi `positive` không khớp và rơi về lớp 0. Chuỗi `negative` cũng rơi về lớp 0. Do đó cả hai nhãn bị gộp về lớp 0. Đây là lỗi ánh xạ nhãn có bằng chứng trực tiếp từ mã, ảnh manifest Kaggle và log notebook; không phải bằng chứng rằng dữ liệu ảnh không được dùng.

Ngoài ra, COVIDx CXR-4 được mô tả trong tài liệu benchmark NeurIPS là tác vụ **phân loại nhị phân, 2 lớp**, trong khi notebook và checkpoint cấu hình Head C thành 3 lớp (Normal, Non-COVID Pneumonia, COVID-19). Ba lớp này phù hợp với một số biến thể COVIDx trước đó, nhưng không được tự động gán cho CXR-4. Do đó, phải xác định chính xác phiên bản manifest/dataset và taxonomy được phê duyệt trước khi sửa nhãn hoặc huấn luyện lại; không thể chữa bằng cách đổi tên lớp sau huấn luyện.

Kết quả là các metric Head C của checkpoint hiện tại không hợp lệ để diễn giải hiệu năng phân biệt ba lớp. Accuracy 1.0 không có ý nghĩa khi nhãn kiểm tra hoặc nhãn huấn luyện chỉ có một lớp.

### 2.2. Tình trạng dữ liệu hiện có để tái lập

Split NIH có 112,120 dòng, 21,884 dòng test, không có filename trùng và phép giao `Patient ID` giữa train/validation/test bằng 0. Tuy nhiên, dữ liệu ảnh tại máy chỉ là gói mẫu: trong `sample-nih.zip` có 5,606 PNG khớp với metadata, gồm 1,134 ảnh thuộc split test. Đây không phải toàn bộ 21,884 ảnh test; vì vậy không báo cáo lại AUROC NIH như kết quả full-test.

Người dùng đã xác nhận huấn luyện được thực hiện trên Kaggle, và ảnh Data Explorer cho thấy các dataset NIH, COVIDx (`train.txt`/`test.txt`) và TB được mount tại đó. Log notebook cũng ghi `NIH=REAL | COVID=REAL | TB=REAL`. Vì vậy thiếu ảnh đầy đủ trên máy local chỉ ngăn tái chạy độc lập ở workspace này; **không** phủ định việc huấn luyện trên Kaggle hoặc việc đã dùng ảnh thật.

`dataset/splits/covid_splits.csv` local là tập 21,165 ảnh với bốn mã nhãn và sáu nguồn, không có cột patient ID; nó không phải bằng chứng split của COVIDx trong lần chạy Kaggle. Tuy nhiên, log Kaggle cho thấy label collapse ở pipeline huấn luyện, và metric Head C được lưu là `NaN`; đây là lỗi vẫn có thể thẩm định mà không cần tải toàn bộ ảnh về local. Muốn xác minh lại Head C sau khi sửa pipeline, cần chạy lại trên Kaggle với assertion phân bố lớp và xuất logits/nhãn của held-out test.

## 3. Đối chiếu các tuyên bố định lượng

| Chỉ số trong chỉ thị | Artifact tại workspace | Nhận định thẩm định |
|:---|:---|:---|
| Head A macro AUROC 0.8247; test 0.7578 | Checkpoint ghi test AUROC 0.7578296. JSON tổng hợp ghi 0.8247, nhưng không chỉ rõ split và phép tính; lịch sử checkpoint ghi validation AUC khoảng 0.787 ở epoch được chọn. | 0.7578 có trong metadata checkpoint; 0.8247 không được xác nhận là kết quả test của checkpoint này. Không gộp hai số thành một kết quả duy nhất. |
| Head B AUROC 0.9975 | Checkpoint test metadata ghi 0.9975239; JSON ghi 0.9975, sensitivity 0.985 và specificity 0.992. | AUROC có sự nhất quán trong metadata; sensitivity/specificity cần bảng dự đoán và nhãn của đúng split để xác minh độc lập. Kết quả cao trên một cohort không chứng minh khả năng tổng quát hóa lâm sàng. |
| Head C AUROC, accuracy, F1 đều 1.0000 | Checkpoint ghi `auc_c: NaN`. Log notebook cho biết COVIDx có 76,345 dòng nhưng chỉ còn nhãn 0 và trọng số lớp đếm `[12000,0,0]`; manifest Kaggle hiển thị `positive`/`negative`, cả hai không được hàm ánh xạ hiện tại nhận diện. JSON tổng hợp ghi confusion matrix hoàn hảo trên 8,482 mẫu, nhưng không có logits/nhãn từng mẫu đi kèm để tái lập. | Không hợp lệ/chưa xác nhận. Pipeline đã dùng dữ liệu ảnh thật theo log, nhưng gộp nhãn dương/âm về lớp 0; notebook và checkpoint đồng thời cấu hình 3 lớp trong khi benchmark CXR-4 là nhị phân. Không dùng các metric Head C trong chỉ thị cho kết luận hiệu năng. |
| RSNA mean box IoU 0.7631, success@0.30 90% | Chưa xác định được artifact kết quả RSNA AG-MTCNet kèm danh sách mẫu, dự đoán, ground truth và quy tắc ghép box trong hồ sơ đang đối chiếu. | Chưa kiểm chứng. Cần đánh giá lại và nêu rõ metric là IoU ghép box nào, cách xử lý nhiều box và số ca. |
| VinDr mean box IoU 0.6049 | `results/live_vindr_iou_benchmark.csv` có 20 dòng; trung bình cột `mean_box_iou` là 0.117685, trung bình `best_box_iou` là 0.1525, và 4/20 ca có `best_box_iou >= 0.30`. | Artifact live hiện có không ủng hộ 0.6049. Đây chưa chắc là cùng checkpoint hoặc cùng protocol, nên không thể dùng nó để phủ định một lần chạy khác; nhưng kết quả được nêu cần gắn đúng artifact và phiên bản đánh giá. |
| In-lung energy 94.92% ± 1.60%, 100% ca đạt 80% | `results/live_covid_shortcut_audit.csv` ghi 60 mẫu; cột `pass_80_percent` có 0 mẫu đạt. `results/ag_mtcnet_comprehensive_evaluation.json` lại ghi 94.92% ± 1.60% mà không kèm dữ liệu gốc tương ứng. | Chưa xác nhận cho AG-MTCNet. Cần phân biệt heatmap thô của mô hình với heatmap sau khi áp mặt nạ. Nếu mask đặt năng lượng ngoài phổi về 0 rồi mới tính tỷ lệ, tỷ lệ cao là hệ quả của phép biến đổi và không chứng minh mô hình tự chú ý đúng giải phẫu. |
| CheXpert retention 95.43% | JSON ghi trung bình 95.43%; `results/live_chexpert_generalization.csv` có 5 hàng với retention từng bệnh 70.50–95.11% (chỉ một hàng vượt 95%). | Không khớp với các giá trị từng bệnh trong artifact live; chưa xác định cách chọn nhãn, mẫu và mẫu số của phép tính retention. Không nên báo cáo 95.43% như kết quả ngoại kiểm đã xác nhận. |
| OOD AUROC 1.0000, ngưỡng `S_E < 9.0421` | JSON AG ghi energy threshold 5.5 và AUROC 1.0. `configs/ood_thresholds.json` dùng ngưỡng 5.5; `results/ood_results.csv` có các AUROC theo nhóm phần lớn không bằng 1.0 (một số bằng 0.0). | Tuyên bố ngưỡng 9.0421 và AUROC 1.0 không thống nhất với artifact OOD hiện có. Cần khóa định nghĩa chiều score, nhãn OOD/ID, ngưỡng và tập đánh giá; AUROC 0.0 cũng có thể do đảo chiều score nên cần kiểm tra mã tính toán. |
| Latency 0.48 s GPU T4 / 1.15 s CPU i7 | JSON AG ghi 3.5983 giây nhưng không nêu thiết bị hoặc protocol. CSV VinDr có latency từng mẫu ở mức vài giây, nhưng không phải benchmark có kiểm soát cho inference triển khai. | 0.48/1.15 giây chưa được hỗ trợ. Cần đo warm-up, batch size 1, số lần lặp, đồng bộ CUDA, tiền xử lý, phân đoạn và sinh heatmap; báo cáo median và p95 trên phần cứng cụ thể. |

Các CSV là bằng chứng có sẵn, không tự động là nguồn chân lý. Chúng thiếu trong một số trường hợp manifest, phiên bản checkpoint, hash dữ liệu, lệnh chạy, định nghĩa split và dự đoán từng ca. Vì vậy, những con số có mặt trong CSV cũng chỉ được xem là artifact cần truy nguyên, không mặc nhiên là kiểm định độc lập.

## 4. Diễn giải kỹ thuật và giới hạn

### 4.1. Hiệu năng phân loại

Từ checkpoint, Head A test AUROC khoảng 0.758 cho thấy hiệu năng tổng thể thấp hơn con số 0.8247 được gán trong bảng chỉ thị. Head B có AUROC cao trong metadata, nhưng kết quả này cần được đọc cùng cỡ mẫu, phổ bệnh, cơ sở thu thập, patient-level split và khoảng tin cậy. Không thể suy ra nguyên nhân cải thiện do ASL, class weighting hay Dense-UNet nếu không có đối chứng ablation với cùng split và cùng quy trình.

Head C không thể được xem là kết quả hợp lệ trên COVIDx CXR-4: notebook gộp `positive` và `negative` về lớp 0; benchmark CXR-4 là nhị phân, còn kiến trúc xuất checkpoint là 3 lớp. Cần xác định taxonomy được dự án phê duyệt, sửa ingestion theo đúng manifest, xác nhận số mẫu từng lớp ở train/validation/test, rồi huấn luyện lại và đánh giá trên test độc lập. Không thể tính lại kết quả Head C đáng tin cậy từ checkpoint hiện tại.

### 4.2. Định vị tổn thương và kiểm toán shortcut

IoU là chỉ số nhạy với cách tạo vùng dự đoán, ngưỡng hóa heatmap và quy tắc ghép box. Không thể so sánh các con số giữa các lần chạy nếu không khóa chung protocol. Bằng chứng live VinDr hiện có cho thấy chất lượng định vị thấp trên 20 mẫu được lưu, không phải 0.6049. Với shortcut audit, đánh giá phải công bố trước và sau grounding riêng biệt. Chỉ số sau khi che nền đo tác động của tiền xử lý; heatmap thô cần được kiểm tra riêng để biết mô hình có học tín hiệu nội phổi hay không.

### 4.3. Khả năng tổng quát hóa, OOD và triển khai

Artifact CheXpert và OOD hiện không xác nhận các tỉ lệ/điểm tổng hợp trong chỉ thị. Far-OOD nhân tạo (nhiễu, đảo ảnh, nhòe) cũng không thay thế đánh giá domain shift trên ảnh X-quang từ cơ sở khác. Chưa có cơ sở từ các số hiện tại để tuyên bố an toàn lâm sàng.

Đánh đổi tài nguyên chưa thể kết luận từ kích thước một file đơn. AG checkpoint nhỏ hơn 95.96 MB đã nêu, còn Dense-UNet nằm ở artifact riêng. Latency cần đo toàn pipeline gồm nạp ảnh, phân đoạn, masking, backbone, Grad-CAM và mã hóa phản hồi. Đáp ứng ngưỡng thời gian không đồng nghĩa đạt yêu cầu an toàn hoặc hiệu quả chẩn đoán.

## 5. Phán quyết và điều kiện để xem xét lại

**Phán quyết hiện tại: Không phê duyệt làm mô hình mặc định chính thức; không báo cáo Head C như một kết quả có giá trị; chưa đủ bằng chứng để gọi là mô hình SOTA hoặc sẵn sàng triển khai tại PACS.** Có thể giữ checkpoint như một ứng viên nghiên cứu cho các head còn lại và tiếp tục đánh giá, nhưng không nên trình bày các con số chưa được tái lập như kết quả đã xác thực.

Ba lý do chính:

1. **Head C có lỗi xử lý nhãn/taxonomy:** pipeline Kaggle dùng ảnh thật nhưng gộp `positive`/`negative` về một lớp; checkpoint cấu hình ba lớp trong khi COVIDx CXR-4 là benchmark nhị phân; AUROC lưu là `NaN`.
2. **Kết quả định vị và shortcut không được artifact live xác nhận:** VinDr live đạt mean box IoU 0.117685 trên 20 hàng; COVID live audit có 0/60 ca đạt ngưỡng in-lung 80%.
3. **Thông số triển khai không khớp:** checkpoint là 28.48 MB, có 7.056 triệu tensor entries và latency JSON 3.5983 giây; các con số 95.96 MB, 24.03 triệu tham số và 0.48/1.15 giây chưa được tái lập.

Trước khi xem xét lại quyết định, cần sửa và xác nhận ánh xạ lớp Head C theo phiên bản dataset được phê duyệt; assert số lượng từng lớp không bằng 0 cho mỗi split; xác nhận patient ID và source trực tiếp từ manifest Kaggle; lưu hash checkpoint/dữ liệu; xuất nhãn, logits và dự đoán từng mẫu; tính AUROC/F1/CI từ đầu; chạy RSNA/VinDr với protocol cố định; tách shortcut audit trước/sau masking; xác định đúng checkpoint Dense-UNet đi kèm; và benchmark toàn pipeline trên phần cứng nêu rõ. Ngưỡng Youden phải được ước lượng trên validation rồi cố định trước khi mở test. Không dùng lại checkpoint hiện tại để tuyên bố kết quả Head C sau khi sửa ingestion.

Cho FastAPI/PACS, chỉ nên đăng ký AG-MTCNet dưới trạng thái **ứng viên thử nghiệm**, có nhãn phiên bản, model card và đường quay lui về mô hình hiện tại. Không nên chọn mặc định cho sử dụng lâm sàng chỉ dựa vào bảng số liệu trong chỉ thị.

## Nguồn nội bộ đã đối chiếu

- `checkpoints/ag_mtcnet_best.pth` — checkpoint và metadata huấn luyện/đánh giá.
- `results/ag_mtcnet_comprehensive_evaluation.json` — bảng kết quả tổng hợp được đối chiếu.
- `results/ag_mtcnet_performance_matrix.csv` — metric theo bệnh được đối chiếu.
- `results/live_vindr_iou_benchmark.csv` — 20 hàng đánh giá live VinDr.
- `results/live_covid_shortcut_audit.csv` — 60 hàng shortcut audit live.
- `results/live_chexpert_generalization.csv` — kết quả tổng quát hóa live.
- `results/ood_results.csv`, `configs/ood_thresholds.json` — artifact OOD hiện có.
- `src/models/multi_task_net.py`, `src/models/dense_unet.py` — định nghĩa kiến trúc và mask.
- `dataset/splits/patient_splits.csv`, `dataset/splits/covid_splits.csv`, `dataset/nih-chestXray-14/sample-nih.zip` — split metadata và ảnh cục bộ được kiểm kê.
- [COVIDx CXR-4 benchmark paper (NeurIPS Datasets and Benchmarks 2024)](https://papers.neurips.cc/paper_files/paper/2024/file/0cb35e10bf7bb73d10c12414edbd63fd-Paper-Datasets_and_Benchmarks_Track.pdf) — mô tả COVIDx CXR-4 gồm hai lớp và là tác vụ phân loại nhị phân.

