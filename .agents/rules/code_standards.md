# 📏 AGENT RULE: CODE & REPRODUCIBILITY STANDARDS (LUNGRAY PLATFORM)
## Mã Quy Chuẩn: RULE-01-CODE-STANDARDS
## Dự án: Nền tảng LungRay
## Áp dụng cho: Toàn bộ Agent & Nhà phát triển

---

### 1. TÍNH TÁI TẠO (REPRODUCIBILITY & DETERMINISM)
- Mọi script và notebook huấn luyện BẮT BUỘC phải gọi hàm cố định seed ngẫu nhiên trước khi khởi tạo bất kỳ module nào:
```python
import os
import random
import numpy as np
import torch

def seed_everything(seed: int = 42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```
- Nghiêm cấm sử dụng các giá trị magic numbers hoặc hardcode đường dẫn cục bộ trong mã nguồn. Mọi siêu tham số (Hyperparameters) và đường dẫn (Paths) phải được cấu hình qua file YAML trong `configs/`.

---

### 2. QUY CHUẨN MÃ NGUỒN PYTHON (PEP 8 & TYPE HINTS)
- **Type Hints**: 100% các hàm và phương thức trong `src/` bắt buộc phải có type annotation rõ ràng cho cả tham số đầu vào và kiểu dữ liệu trả về:
```python
# ✅ CHUẨN XÁC
def compute_adaptive_threshold(heatmap: np.ndarray, alpha: float = 0.3) -> float:
    """Tính ngưỡng nhị phân thích nghi từ activation heatmap.
    
    Args:
        heatmap: Mảng numpy 2D chứa giá trị activation trong khoảng [0, 1].
        alpha: Hệ số nhân điều chỉnh ngưỡng.
        
    Returns:
        Ngưỡng nhị phân thích nghi tau_mask.
    """
    return float(alpha * np.max(heatmap))
```
- **Docstrings**: Sử dụng chuẩn Google Python Style Docstrings cho toàn bộ module, class và function.
- **Code Formatting**: Tuân thủ công cụ `black` (line-length = 100) và kiểm tra tĩnh với `flake8`.

---

### 3. QUẢN LÝ THIẾT BỊ & BỘ NHỚ GPU (PYTORCH BEST PRACTICES)
- **Device Agnostic**: Mã nguồn phải tự động nhận diện thiết bị khả dụng:
  `device = torch.device("cuda" if torch.cuda.is_available() else "cpu")`
- **Bộ nhớ VRAM**:
  - Luôn sử dụng `with torch.no_grad():` trong các vòng lặp validation, testing và evaluation để tránh tích lũy computation graph.
  - Sử dụng Mixed Precision `torch.cuda.amp.autocast()` khi huấn luyện trên GPU để tiết kiệm bộ nhớ và tăng tốc.
  - Gọi `torch.cuda.empty_cache()` sau các tác vụ nặng (như chạy batch sinh heatmap Grad-CAM quy mô lớn).

---

### 4. LOGGING THAY VÌ PRINT STATEMENT
- Tuyệt đối không dùng lệnh `print()` tùy tiện trong mã nguồn production hoặc package `src/`.
- Sử dụng module `logging` chuẩn của Python với định dạng thống nhất:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Hoàn thành epoch %d | Val Loss: %.4f | Val AUC: %.4f", epoch, val_loss, val_auc)
```

---

### 5. QUY CHUẨN JUPYTER NOTEBOOK & NGHIÊN CỨU TƯƠNG TÁC SỐNG (INTERACTIVE RESEARCH & REPRODUCIBILITY)
> [!CAUTION]
> **ĐIỀU KHOẢN CƯỠNG CHẾ VỚI TẤT CẢ FILE NOTEBOOK (`notebooks/*.ipynb`)**:
> Jupyter Notebook trong dự án LungRay là **tài liệu nghiên cứu khoa học sống (Living Research Document)**, bắt buộc tuân thủ 4 nguyên tắc sau:
> 1. **100% Cú pháp Phân tích Dữ liệu Thực thụ**: Mọi cell xử lý dữ liệu, vẽ đồ thị phân tích (EDA), huấn luyện mô hình, trực quan hóa heatmap hay tính chỉ số IoU phải được viết bằng code Python tương tác (`pandas`, `seaborn`, `matplotlib`, `torch`, `cv2`, `PIL`).
> 2. **Tuyệt đối cấm "Lối đi tắt lười biếng" (No Lazy Shortcuts)**: Nghiêm cấm dùng lệnh `display(Image("...png"))` hoặc nạp ảnh render sẵn vào cell để giả lập kết quả đồ thị. Đồ thị phải được vẽ động bằng `plt.show()` hoặc `sns.*` ngay trong cell.
> 3. **Trực quan hóa Dữ liệu Thật**: Mọi ảnh X-quang minh họa phải được trích xuất trực tiếp từ các tệp dữ liệu thật (kể cả tệp `.zip` thông qua thư viện `zipfile`).
> 4. **Trạng thái lưu trữ (Committed Notebook State)**: Khi bàn giao notebook cho người dùng hoặc nghiệm thu, notebook BẮT BUỘC phải được chạy qua kernel để mọi cell đều có kết quả đầu ra thực tế (`outputs` chứa hình ảnh và bảng dữ liệu), không để notebook ở trạng thái rỗng (`outputs: []`).

---

### 6. QUẢN LÝ VÀ DỌN DẸP TỆP TẠM THỜI (TEMPORARY ARTIFACT CLEANUP POLICY)
- **Ưu tiên Inline Execution**: Khi cần kiểm tra nhanh, trích xuất mẫu hoặc debug, ưu tiên sử dụng câu lệnh inline `python -c "..."` thay vì tạo file tạm trong project.
- **Xóa sạch ngay lập tức (Immediate Cleanup)**: Mọi tệp sinh ra phục vụ mục đích tạm thời (helper scripts, runner scripts, debug logs, test outputs trung gian) trong `scripts/`, `src/` hoặc thư mục gốc **BẮT BUỘC PHẢI ĐƯỢC XÓA BỎ NGAY LẬP TỨC** sau khi tác vụ hoàn thành.
- **Không để lại mã nguồn rác (Zero Lingering Code)**: Không được phép để lại bất kỳ tệp mồ côi nào sau mỗi lượt tương tác với người dùng. Thư mục `scripts/` chỉ lưu các công cụ vận hành chính thức được đăng ký trong kiến trúc dự án. Workspace phải luôn ở trạng thái tinh gọn, sạch sẽ chuẩn Enterprise.
