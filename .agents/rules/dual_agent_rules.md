# ⚖️ DUAL-AGENT GOVERNANCE RULES (ANTIGRAVITY & COMMANDCODE GO)
<!-- VERIFY: Cập nhật quy tắc Antigravity theo tài liệu Antigravity Customization Root -->
## Quy Chuẩn Phân Quyền & Ràng Buộc Trách Nhiệm Giữa Antigravity (IDE) & CommandCode CLI (Terminal)

---

| Vai trò | Phụ trách chính | Quyền hạn & Trách nhiệm tối cao | Giới hạn bắt buộc |
|:---|:---|:---|:---|
| **Antigravity (IDE)** | **Chief AI Architect & Quality Gatekeeper** | Cùng Kỹ sư Trưởng (User) lên kế hoạch triển khai, thiết kế kiến trúc, soạn Handoff spec, yêu cầu CommandCode làm chặt chẽ logic, kiểm toán Git Diff, phê duyệt nghiệm thu và Git Commit/Push chính thức. | Không tự ý can thiệp viết mã vi mô khi đã giao cho CommandCode; không nghiệm thu khi chưa có bằng chứng verify pass. |
| **CommandCode CLI (Terminal)** | **Tactical Coding & Execution Engine** | **Chịu trách nhiệm cao nhất về tính chính xác của mã nguồn, logic kỹ thuật, thuật toán và toàn bộ Unit Tests cho Team.** Viết code logic, sửa bug, chỉnh hyperparameter, xử lý triệt để ngoại lệ và tự động kiểm thử. | Không tự ý sửa đổi Data Flow, Taxonomy, hoặc 9 Ràng Buộc Sống Còn; không sửa file ngoài Scope. |

---

## 0. QUY TẮC ĐỒNG BỘ BẮT BUỘC TRƯỚC KHI BÀN GIAO & NGHIỆM THU (THE SINGLE VERIFY GATE)
> [!CAUTION]
> **ĐIỀU KHOẢN RÀNG BUỘC CƯỠNG CHẾ**:
> Trước khi nghiệm thu bất kỳ task nào, cả hai Agent **BẮT BUỘC** phải xác nhận MỘT lệnh duy nhất chạy thành công:
> ```powershell
> powershell -File scripts/verify.ps1
> ```
> *(hoặc `python scripts/verify.py`)*
> 
> - **Đối với CommandCode (Terminal)**: Chịu trách nhiệm 100% sửa mọi lỗi logic/cú pháp/unit test cho đến khi lệnh trên đạt **100% PASS (Exit code 0)** trước khi điền mục `## Result`.
> - **Đối với Antigravity (IDE)**: Tuyệt đối không bấm APPROVE hay merge khi chưa chạy lại lệnh này để kiểm toán độc lập trên working tree.

---

## 1. 9 NGUYÊN TẮC BẤT DI BẤT DỊCH (NON-NEGOTIABLE CORE CONSTRAINTS)
Mọi thay đổi code do **CommandCode** thực hiện và được **Antigravity** kiểm duyệt BẮT BUỘC phải tuân thủ:
1. **Kiến trúc 3-Head Độc Lập**: 1 shared backbone cho 3 heads (Head A: 14 NIH, Head B: TB, Head C: COVIDx 3-class).
2. **Zero Data Leakage**: NIH ChestX-ray14 bắt buộc chia theo `Patient_ID` (70/10/20). Cấm chia ngẫu nhiên theo ảnh.
3. **Anti-Shortcut Learning**: COVIDx bắt buộc phân tầng theo `data_source` và kiểm soát theo `patient_id`.
4. **Bounding Box Phân Minh**: Chỉ dùng Bounding Box ở tập test (VinDr-CXR, RSNA Pneumonia) để đo IoU. Tập train không dùng Bounding Box.
5. **Weighted Multi-Task Sampling**: Cố định tỷ lệ 60% NIH : 25% COVID : 15% TB trong `WeightedMultiTaskBatchSampler`.
6. **Shortcut Learning Audit**: Grad-CAM Head C trên ca dương tính COVID-19 phải có tỷ lệ năng lượng kích hoạt trong phế trường $\ge 80\%$.
7. **Nghiên Cứu Sống (Live Code)**: Notebooks phải tính toán và vẽ đồ thị tương tác sống; TUYỆT ĐỐI CẤM dùng `display(Image(...))` giả lập.
8. **Lean Workspace**: Xóa bỏ 100% tệp tạm/scratch scripts ngay sau khi thực thi.
9. **Chuẩn Báo Cáo Khoa Học & Luận Án Đơn Sắc**: Báo cáo nghiệm thu và PDF tuyệt đối cấm icon/emoji, phông Times New Roman, bảng Booktabs 3 đường kẻ đen, tone đơn sắc đen trắng.

---

## 2. QUY CHUẨN ĐỐI VỚI COMMANDCODE (TERMINAL AGENT)
- **Quy chuẩn 1: Trách nhiệm Logic & Độ chính xác mã nguồn**:
  - Chịu trách nhiệm tối cao về tính đúng đắn của logic, bắt lỗi ngoại lệ, xử lý biên (edge cases).
  - Chỉ chỉnh sửa đúng các files được chỉ định trong file `docs/HANDOFF/<ID>.md`.
- **Quy chuẩn 2: Tiêu chuẩn mã nguồn (Code Quality Standard)**:
  - Tuân thủ PEP 8, Type Hinting (`typing.Dict`, `typing.List`, `torch.Tensor`).
  - Không hardcode đường dẫn cục bộ; luôn dùng hàm phân giải đường dẫn linh hoạt hoặc config paths.
- **Quy chuẩn 3: Kiểm thử tự động bắt buộc (Self-Testing Gate)**:
  - Trước khi bàn giao lại cho Antigravity, CommandCode BẮT BUỘC phải chạy `powershell -File scripts/verify.ps1`.
  - Nếu có lỗi biên dịch hoặc rớt test, CommandCode phải tự động sửa cho đến khi **100% passed**.

---

## 3. QUY CHUẨN ĐỐI VỚI ANTIGRAVITY (IDE ARCHITECT & GATEKEEPER)
- **Quy chuẩn 1: Kế hoạch & Yêu cầu Logic chặt chẽ**:
  - Antigravity cùng Kỹ sư Trưởng (User) lên kế hoạch triển khai, phân rã task nhỏ, soạn Handoff spec với tiêu chí nghiệm thu rõ ràng, yêu cầu CommandCode hiện thực hóa chặt chẽ logic.
- **Quy chuẩn 2: Audit Diff & Verify Độc Lập**:
  - Sau khi CommandCode báo hoàn thành, Antigravity chạy `git diff` rà soát từng dòng code và chạy lại `powershell -File scripts/verify.ps1` để xác thực bằng chứng sống.
- **Quy chuẩn 3: Quyền Độc Quyền Git Commit & Push**:
  - Chỉ Antigravity (dưới sự phê duyệt của User) mới được tạo commit chính thức và thực hiện `git push` lên GitHub repository.
