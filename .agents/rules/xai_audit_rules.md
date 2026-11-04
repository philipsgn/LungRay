# 🔬 AGENT RULE: EXPLAINABILITY (XAI) & AUDIT PROTOCOL (LUNGRAY PLATFORM)
## Mã Quy Chuẩn: RULE-03-XAI-AUDIT
## Dự án: Nền tảng LungRay
## Áp dụng cho: `XAIEvalAgent`, `ModelArchitectAgent`

---

### 1. QUY CHUẨN TRÍCH XUẤT GRAD-CAM
- **Target Layer**: Bắt buộc gắn hook vào tầng tích chập cuối cùng chứa thông tin không gian ngữ nghĩa cao nhất:
  - DenseNet-121: `model.backbone.features.denseblock4.denselayer16.conv2`
  - ResNet-50: `model.backbone.layer4[2].conv3`
  - Vision Transformer (ViT): Lớp Attention Rollout hoặc Gradient-weighted attention map của tầng Transformer cuối cùng.
- **Chuẩn hóa Heatmap**:
  Bản đồ nhiệt thô sau phép nhân gradient và feature map BẮT BUỘC phải đi qua hàm kích hoạt ReLU (chỉ giữ lại các đặc trưng đóng góp tích cực cho lớp bệnh $c$) và được chuẩn hóa Min-Max độc lập về khoảng $[0, 1]$:
  $$M_c = \frac{M_c - \min(M_c)}{\max(M_c) - \min(M_c) + 10^{-8}}$$

---

### 2. QUY CHUẨN NHỊ PHÂN HÓA THÍCH NGHI & ĐO ĐẠC IOU
- **Cấm cố định ngưỡng cứng (Không dùng $\tau = 0.5$ bất biến)**:
  Cường độ gradient giữa các ca bệnh khác nhau có độ tương phản khác nhau.
- **Công thức nhị phân hóa thích nghi**:
  $$\hat{B}_c(x, y) = \mathbb{I}(M_c(x, y) \ge \alpha \cdot \max(M_c)) \quad \text{với } \alpha \in [0.2, 0.4] \text{ (mặc định: } 0.3)$$
- **Tiêu chuẩn tính IoU**:
  - Chỉ tính IoU trên tập **True Positives (TP)** có tồn tại Bounding Box chuyên gia từ tập VinDr-CXR hoặc RSNA.
  - Mẫu False Negative hoặc True Negative không đưa vào mẫu số tính Mean IoU.
  - Công thức:
    $$\text{IoU}(\hat{B}_c, B^{GT}) = \frac{|\hat{B}_c \cap B^{GT}|}{|\hat{B}_c \cup B^{GT}|}$$
  - **Chỉ tiêu nghiệm thu**: **Mean IoU $\ge 0.35$**.

---

### 3. QUY TRÌNH KIỂM TOÁN SHORTCUT LEARNING AUDIT CHO HEAD C
- **Bối cảnh**: Bộ dữ liệu COVID-19 Radiography Database có nguy cơ học thuộc viền đen, ký hiệu R/L hoặc chữ in góc phim.
- **Tiêu chuẩn kiểm toán**:
  1. Trích xuất mặt nạ phế trường phổi $P_{\text{lung}}$ từ ảnh X-quang.
  2. Đo lường tỷ lệ năng lượng nhiệt Grad-CAM tập trung trong phổi:
     $$\text{In-Lung Activation Ratio} = \frac{\sum_{(x,y) \in P_{\text{lung}}} M_{\text{COVID}}(x,y)}{\sum_{(x,y)} M_{\text{COVID}}(x,y)}$$
  3. **Phân loại kết quả kiểm toán**:
     - ✅ **PASS ($\ge 80\%$)**: Vùng chú ý tập trung đúng tổn thương kính mờ nhu mô phổi. Đạt chuẩn công bố khoa học.
     - ⚠️ **WARNING ($75\% - 79.9\%$)**: Cần kiểm tra trực quan thủ công và ghi chú trong báo cáo.
     - ❌ **FAIL ($< 75\%$)**: Phát hiện dấu hiệu Shortcut Learning. Bắt buộc áp dụng kỹ thuật tiền xử lý Lung Masking cắt bỏ viền ngoài để train lại mô hình.
