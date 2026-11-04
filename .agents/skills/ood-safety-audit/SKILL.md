---
name: ood-safety-audit
description: Quy trình kiểm toán an toàn lâm sàng, phát hiện mẫu ảnh ngoài phân phối (Out-of-Distribution - OOD) bằng điểm số Free Energy và cơ chế khóa an toàn (Fail-Safe Lockout) tự động cho hệ thống CADx.
---

# 🛡️ SKILL: OUT-OF-DISTRIBUTION (OOD) SAFETY AUDIT & CLINICAL FAIL-SAFE
## Quy Trình Kiểm Toán An Toàn Lâm Sàng, Phát Hiện Ảnh Bất Thường Ngoài Phân Phối & Khóa An Toàn Tự Động

---

### 1. MỤC TIÊU & BỐI CẢNH LÂM SÀNG
Trong thực tế lâm sàng, các mô hình học sâu rất dễ gặp hiện tượng "tự tin thái quá" (Overconfident Misclassification) khi tiếp nhận các ảnh không hợp lệ (ảnh nhiễu trắng, ảnh đảo màu, ảnh chụp bụng/sọ não, hoặc ảnh nhiễu artifact nghiêm trọng). 
Kỹ năng này hướng dẫn việc triển khai **Lớp bảo vệ an toàn 2 chặn (Dual-Bounded Fail-Safe Layer)** dựa trên hàm Free Energy để tự động từ chối chẩn đoán (Reject Policy) và khóa chức năng xuất báo cáo lâm sàng khi phát hiện ảnh ngoài phân phối (OOD).

---

### 2. CƠ SỞ TOÁN HỌC & ĐIỂM SỐ NĂNG LƯỢNG (FREE ENERGY SCORE)
1. **Điểm Năng Lượng Tự Do (Free Energy Score)**:
   Với vector logits $f(x) \in \mathbb{R}^C$ từ Shared Backbone và Classifier Head, điểm số năng lượng tự do âm được định nghĩa:
   $$E(x; T) = -T \cdot \log \sum_{c=1}^C \exp\left( \frac{f_c(x)}{T} \right)$$
   Trong đó $T = 1.0$ là tham số nhiệt độ (Temperature scaling).
2. **Cơ Chế Hai Đầu Chặn (Dual-Bounded Rejection Policy)**:
   - **Chặn Dưới (Hypo-Activation / Noise / Inversion)**: Nếu $E(x) > \tau_E^{\text{lower}} = 9.0421$, năng lượng logits của mô hình quá yếu $\to$ Ảnh bị mờ, nhiễu hoặc sai giải phẫu $\to$ **REJECT (Far-OOD)**.
   - **Chặn Trên (Hyper-Activation Anomaly / Pediatric Domain Shift)**: Nếu $E(x) < \tau_E^{\text{upper}} = -22.0$ (hoặc $|E(x)| > 22.0$), mô hình bị kích hoạt quá mức bất thường do dịch chuyển phân phối giải phẫu nghiêm trọng $\to$ **REJECT (Domain Shift OOD)**.
3. **Entropy Ngưỡng Cắt (Predictive Entropy)**:
   - Nếu entropy phân bố xác suất $H(p(x)) > \tau_H = 0.6275$, mô hình hoàn toàn phân vân giữa các lớp $\to$ **Cảnh báo Không Chắc Chắn (Uncertainty Warning)**.

---

### 3. CÁC BƯỚC THỰC HIỆN KIỂM TOÁN AN TOÀN

#### Bước 1: Tính Toán và Cập Nhật Ngưỡng OOD
- Cấu hình ngưỡng được lưu trữ tập trung tại: `configs/ood_thresholds.json`:
  ```json
  {
    "energy_lower_threshold": 9.0421,
    "energy_upper_threshold": 22.0,
    "entropy_threshold": 0.6275,
    "temperature": 1.0
  }
  ```

#### Bước 2: Tích Hợp Reject Policy Trong API Backend
- Trong `src/safety/reject_policy.py`:
  ```python
  def evaluate_safety_policy(logits: torch.Tensor, thresholds: dict) -> dict:
      energy = compute_free_energy(logits, temperature=thresholds.get("temperature", 1.0))
      entropy = compute_predictive_entropy(logits)
      
      is_ood = False
      rejection_reason = None
      
      if energy > thresholds["energy_lower_threshold"]:
          is_ood = True
          rejection_reason = "Hypo-activation: Low model confidence or non-CXR image (Far-OOD)."
      elif abs(energy) > thresholds["energy_upper_threshold"]:
          is_ood = True
          rejection_reason = "Hyper-activation anomaly: Severe anatomical domain shift (Pediatric/Foreign body)."
      elif entropy > thresholds["entropy_threshold"]:
          rejection_reason = "High predictive entropy: Clinical uncertainty threshold exceeded."
          
      return {
          "is_ood": is_ood,
          "energy": float(energy),
          "entropy": float(entropy),
          "rejection_reason": rejection_reason,
          "allow_clinical_report": not is_ood
      }
  ```

#### Bước 3: Khóa An Toàn Tự Động Trên Giao Diện PACS
- Khi `is_ood == True`:
  - Frontend hiển thị biểu ngữ đỏ (Red Safety Banner): *"CẢNH BÁO AN TOÀN LÂM SÀNG: Ảnh ngoài phân phối giải phẫu. Hệ thống từ chối đưa ra kết luận chẩn đoán."*
  - Nút bấm *"Xuất Báo Cáo Y Khoa (Export Report)"* bị khóa (Disabled) hoàn toàn để ngăn chặn việc đưa thông tin sai lệch vào hồ sơ bệnh án.
