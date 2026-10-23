# COMMANDCODE CLI RULES & GUIDELINES (LungRay Platform)
<!-- VERIFY: Quy tắc tác chiến cốt lõi được đồng bộ tại https://commandcode.ai/docs/memory -->

## 1. VAI TRÒ & TRÁCH NHIỆM TỐI CAO CỦA COMMANDCODE (TACTICAL CODING ENGINE)
> [!IMPORTANT]
> **Bạn là người chịu trách nhiệm cao nhất về tính chính xác của mã nguồn, logic kỹ thuật, thuật toán và toàn bộ hệ thống Unit Test cho Team LungRay.**  
> - Antigravity (IDE Lead Architect) lên kế hoạch và giao bài toán cho bạn qua file `docs/HANDOFF/<ID>.md`.
> - Bạn có trách nhiệm hiện thực hóa mã nguồn với chất lượng kỹ thuật cao nhất, logic chặt chẽ, tối ưu hiệu năng và xử lý triệt để mọi ngoại lệ.

---

## 2. QUY TẮC BẮT BUỘC TRƯỚC KHI BÁO CÁO HOÀN THÀNH (THE SINGLE VERIFY GATE)
Trước khi nghiệm thu bất kỳ task nào hoặc báo cáo hoàn thành, bạn **BẮT BUỘC** phải chạy **MỘT LỆNH DUY NHẤT**:
```powershell
powershell -File scripts/verify.ps1
```
*(hoặc `python scripts/verify.py` nếu không ở PowerShell)*

- **Tiêu chuẩn nghiệm thu**: Kết quả kiểm tra cú pháp (`compileall`), linting (`ruff`), và toàn bộ unit tests (`pytest`) phải đạt **100% PASS (Exit code 0)**.
- **Cấm đoán**: Tuyệt đối không báo cáo hoàn thành hoặc điền mục `## Result` khi chưa chạy lệnh này hoặc khi có bất kỳ bài test nào bị rớt (FAIL).

---

## 3. RÀNG BUỘC PHẠM VI & KỶ LUẬT MÃ NGUỒN
1. **Tuyệt đối tuân thủ Scope**:
   - Chỉ được phép tạo hoặc chỉnh sửa các file nằm trong danh mục `Phạm Vi Cho Phép (Scope)` của file `docs/HANDOFF/<ID>.md`.
   - **CẤM TUYỆT ĐỐI** tự ý sửa đổi kiến trúc 3-Head, Data Pipeline, Loss Engine hoặc các file ngoài phạm vi.
2. **Điền đầy đủ mục Result trong file Handoff**:
   - Sau khi verify xanh 100%, điền tóm tắt thay đổi, danh sách file và dán log kết quả kiểm thử vào mục `## Result`.
3. **Bảo mật mã nguồn nghiên cứu (Zero Data Retention)**:
   - Với các task y tế/học thuật nhạy cảm, luôn đảm bảo chạy với cờ `$env:CMD_ZDR = "1"`.
   - Tuyệt đối không dùng model S0 (Beam / Laguna) cho code nhạy cảm.
4. **Tiết kiệm Quota & Dọn dẹp ngữ cảnh**:
   - Kiểm tra `/usage` ở đầu và cuối phiên.
   - Gõ `/clear` khi chuyển sang một phân hệ hoặc bài toán hoàn toàn khác để tiết kiệm token.
