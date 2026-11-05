# SKILL DUMP: ood-safety-audit
# Source: c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\skills\ood-safety-audit\SKILL.md

Quy trình kiểm toán an toàn lâm sàng, phát hiện mẫu ảnh ngoài phân phối (Out-of-Distribution - OOD) bằng điểm số Free Energy và cơ chế khóa an toàn (Fail-Safe Lockout) tự động cho hệ thống CADx.
- Dual-bounded energy rejection policy:
  energy > lower (9.0421) -> Far-OOD / Hypo-activation
  abs(energy) > upper (22.0) -> Hyper-activation domain shift
  entropy > 0.6275 -> High uncertainty
- Fail-Safe Lockout:
  is_ood == True -> allow_clinical_report = False, block report export, show red warning banner and watermarked heatmap.
