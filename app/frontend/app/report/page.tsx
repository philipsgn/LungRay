"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function ReportPage() {
  const [currentSection, setCurrentSection] = useState(0);
  const totalSections = 7;

  const scrollTo = (index: number) => {
    if (index < 0 || index >= totalSections) return;
    setCurrentSection(index);
    const el = document.getElementById(`section-${index}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        scrollTo(Math.min(currentSection + 1, totalSections - 1));
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        scrollTo(Math.max(currentSection - 1, 0));
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSection]);

  return (
    <div className="h-screen w-screen overflow-y-scroll snap-y snap-mandatory text-[#0B1E36] font-sans antialiased selection:bg-slate-200">
      {/* Top Bar Tối Giản (Đã loại bỏ hiển thị vị trí và nút mũi tên theo yêu cầu) */}
      <header className="fixed top-0 left-0 right-0 h-12 bg-white/80 backdrop-blur-md border-b border-slate-200/60 z-50 flex items-center justify-between px-8 text-xs">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="font-medium text-slate-600 hover:text-slate-950 transition flex items-center gap-1.5"
          >
            &larr; Về Hệ Thống Đọc Phim PACS
          </Link>
          <span className="text-slate-300">|</span>
          <span className="font-semibold text-slate-800 tracking-wider uppercase">
            LungRay Healthcare &bull; Báo Cáo Chuyên Khảo Lâm Sàng &amp; Nghiệm Thu
          </span>
        </div>
        <div className="text-[11px] text-slate-500 font-medium">
          Viện Nghiên Cứu Trí Tuệ Nhân Tạo Y Tế LungRay
        </div>
      </header>

      {/* Thanh Chỉ Mục Số Hóa Bên Cạnh (Sidebar Dot Rail) */}
      <nav className="fixed left-5 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-40">
        {[0, 1, 2, 3, 4, 5, 6].map((idx) => (
          <button
            key={idx}
            onClick={() => scrollTo(idx)}
            className={`w-2 transition-all duration-300 rounded-full ${
              currentSection === idx
                ? "h-6 bg-[#0B1E36]"
                : "h-2 bg-slate-300 hover:bg-slate-500"
            }`}
            title={`Chương ${idx + 1}`}
          />
        ))}
      </nav>

      {/* =================================================================== */}
      {/* CHƯƠNG 1: BỐI CẢNH LÂM SÀNG & 3 NÚT THẮT CỦA CADx TRUYỀN THỐNG     */}
      {/* =================================================================== */}
      <section
        id="section-0"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#F0FDF4] to-[#E0F2FE]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Động Lực Nghiên Cứu &amp; Cơ Sở Lâm Sàng
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 01 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Khủng Hoảng Trong Hỗ Trợ Chẩn Đoán X-Quang
            </p>
            <h1 className="text-3xl lg:text-4xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Nền Tảng Trí Tuệ Nhân Tạo Hợp Nhất Chẩn Đoán &amp; Định Vị Tổn Thương Phổi
            </h1>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Chụp X-quang lồng ngực (CXR) chiếm khối lượng công việc lớn nhất tại các khoa chẩn đoán hình ảnh. Tuy nhiên, việc đưa các mô hình thị giác máy tính vào thực tế lâm sàng bị nghẽn lại bởi ba rào cản nền tảng:
            </p>

            <div className="space-y-3">
              <div className="border-l-4 border-slate-400 pl-4 bg-white/40 py-1.5 rounded-r">
                <h4 className="text-xs font-bold text-slate-900">1. Phân Mảnh Tác Vụ (Task Fragmentation)</h4>
                <p className="text-xs text-slate-600 leading-normal">
                  Triển khai riêng biệt 3 mạng nơ-ron cho 14 bệnh NIH, Lao phổi và COVID-19 gây lãng phí bộ nhớ VRAM, tăng gấp 3 độ trễ và bỏ lỡ các liên kết giải phẫu tương đồng giữa các ca bệnh đồng nhiễm.
                </p>
              </div>

              <div className="border-l-4 border-rose-500 pl-4 bg-white/40 py-1.5 rounded-r">
                <h4 className="text-xs font-bold text-rose-800">2. Hiện Tượng Khai Thác Đặc Trưng Giả Mạo (Shortcut Learning)</h4>
                <p className="text-xs text-slate-600 leading-normal">
                  Theo DeGrave et al. (Nature Machine Intelligence, 2021), các mô hình COVID-19 thường đạt điểm cao giả tạo bằng cách ghi nhớ chữ in &apos;PORTABLE&apos;, nhãn chữ &apos;R/L&apos; hoặc vết cắt viền phim thay vì tổn thương đông đặc phế nang.
                </p>
              </div>

              <div className="border-l-4 border-sky-600 pl-4 bg-white/40 py-1.5 rounded-r">
                <h4 className="text-xs font-bold text-sky-900">3. Bản Đồ Nhiệt Cảm Tính Thiếu Thẩm Định (Unverified Heatmaps)</h4>
                <p className="text-xs text-slate-600 leading-normal">
                  Grad-CAM thông thường chỉ mang tính biểu diễn màu sắc mà hoàn toàn không có chỉ số tương quan không gian (IoU) đối chiếu với nhãn khoanh vùng của bác sĩ X-quang để chứng minh độ chính xác thực thụ.
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-3">
              Đóng Góp Khoa Học Cốt Lõi Của LungRay
            </p>
            <table className="w-full text-xs border-collapse bg-white/60 backdrop-blur-sm rounded">
              <thead>
                <tr className="border-y-2 border-slate-900">
                  <th className="py-2 px-2 text-left font-bold">Giải Pháp Kỹ Thuật</th>
                  <th className="py-2 px-2 text-left font-bold">Giá Trị Lâm Sàng</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50">
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Shared DenseNet-121 Encoder</td>
                  <td className="py-1.5 px-2 text-slate-700">Giảm 66% VRAM, suy luận &le; 1.8s</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Masked Multi-Task Loss Engine</td>
                  <td className="py-1.5 px-2 text-slate-700">Cách ly gradient, không xung đột</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Tỷ lệ Sampler Cố Định 60:25:15</td>
                  <td className="py-1.5 px-2 text-slate-700">Chống đói tác vụ (Task Starvation)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Định Vị WSOL Có Hướng Dẫn</td>
                  <td className="py-1.5 px-2 text-slate-700">Box-IoU 0.7631 (RSNA) &amp; 0.6049 (VinDr)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Kiểm Toán Phế Trường Phổi</td>
                  <td className="py-1.5 px-2 text-slate-700">94.92% năng lượng bám trúng mô bệnh</td>
                </tr>
              </tbody>
            </table>

            <div className="mt-4 p-3 bg-white/60 border-l-3 border-slate-800 text-xs text-slate-700 italic rounded-r">
              &ldquo;AI for radiographic COVID-19 detection frequently relies on superficial shortcuts rather than true pathology.&rdquo;
              <span className="block mt-1 font-sans not-italic font-bold text-slate-900 text-[11px]">
                &mdash; Nature Machine Intelligence, 2021
              </span>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>Tài liệu chuyên khảo tiền lâm sàng &bull; Viện Nghiên cứu LungRay</span>
          <span>Trang 1 / 7</span>
        </div>
      </section>

      {/* =================================================================== */}
      {/* CHƯƠNG 2: DỮ LIỆU ĐA TRUNG TÂM & KỶ LUẬT KHÔNG RÒ RỈ               */}
      {/* =================================================================== */}
      <section
        id="section-1"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#F0F9FF] to-[#F8FAFC]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Hạ Tầng Dữ Liệu &amp; Đạo Đức Nghiên Cứu
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 02 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Kỷ Luật Phân Tầng Bệnh Nhân
            </p>
            <h2 className="text-3xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Sáu Bộ Dữ Liệu Đa Trung Tâm &amp; Kỷ Luật Triệt Tiêu Rò Rỉ Bệnh Nhân
            </h2>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Trong nghiên cứu y khoa, một người bệnh có thể chụp nhiều phim X-quang ở các lần khám khác nhau. Việc chia dữ liệu ngẫu nhiên theo ảnh sẽ khiến ảnh của cùng một người nằm ở cả tập huấn luyện và kiểm thử, dẫn đến việc mô hình nhận diện khung xương cụ thể của bệnh nhân thay vì nhận biết dấu hiệu bệnh lý.
            </p>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              LungRay thiết lập nguyên tắc <strong>Zero Patient Data Leakage</strong>: 100% dữ liệu NIH ChestX-ray14 được phân chia nghiêm ngặt theo mã bệnh nhân (<code>Patient_ID</code>) với tỷ lệ <strong>70% Train / 10% Val / 20% Test</strong>. Tập huấn luyện và tập kiểm thử hoàn toàn tách biệt, không có sự giao thoa bệnh nhân.
            </p>

            <div className="p-3 bg-white/60 border-l-4 border-emerald-600 rounded-r">
              <h4 className="text-xs font-bold text-slate-900 mb-1">
                Phân Tầng Kép Chống Thiên Lệch Nguồn Ảnh (COVIDx CXR-4)
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Để ngăn mô hình khai thác sự khác biệt phần cứng giữa các bệnh viện, tập COVIDx CXR-4 được phân tầng theo cả nguồn thu thập gốc (<code>data_source</code>) và mã bệnh nhân. Tỷ lệ ca âm tính và dương tính được bảo toàn đồng nhất ở mọi tập con.
              </p>
            </div>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-3">
              Quy Mô Sáu Bộ Dữ Liệu Thực Nghiệm
            </p>
            <table className="w-full text-xs border-collapse bg-white/60 backdrop-blur-sm rounded">
              <thead>
                <tr className="border-y-2 border-slate-900">
                  <th className="py-2 px-2 text-left font-bold">Tập Dữ Liệu</th>
                  <th className="py-2 px-2 text-left font-bold">Số Lượng</th>
                  <th className="py-2 px-2 text-left font-bold">Vai Trò Lâm Sàng</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50">
                <tr>
                  <td className="py-1.5 px-2 font-semibold">NIH ChestX-ray14</td>
                  <td className="py-1.5 px-2 text-slate-700">112,120 ảnh</td>
                  <td className="py-1.5 px-2 text-slate-700">14 bệnh lồng ngực (Patient split)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">TB Radiography</td>
                  <td className="py-1.5 px-2 text-slate-700">7,000 ảnh</td>
                  <td className="py-1.5 px-2 text-slate-700">Sàng lọc Lao phổi nhị phân</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">COVIDx CXR-4</td>
                  <td className="py-1.5 px-2 text-slate-700">16,400+ ảnh</td>
                  <td className="py-1.5 px-2 text-slate-700">COVID-19 (Source-stratified)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">VinDr-CXR (Việt Nam)</td>
                  <td className="py-1.5 px-2 text-slate-700">3,000 test</td>
                  <td className="py-1.5 px-2 text-slate-700">Bác sĩ X-quang khoanh vùng (Test)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">RSNA Pneumonia</td>
                  <td className="py-1.5 px-2 text-slate-700">Test chuẩn</td>
                  <td className="py-1.5 px-2 text-slate-700">Đồng thuận Bounding Box (Test)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Stanford CheXpert</td>
                  <td className="py-1.5 px-2 text-slate-700">22,433 ảnh</td>
                  <td className="py-1.5 px-2 text-slate-700">Đánh giá ngoại suy (OOD Test)</td>
                </tr>
              </tbody>
            </table>

            <div className="mt-4 p-3 bg-white/60 border-l-4 border-sky-800 text-xs text-slate-700 rounded-r">
              <span className="font-bold block mb-1 text-slate-900">Bộ Lấy Mẫu Đa Nhiệm Cân Bằng (Batch Sampler):</span>
              Mỗi mini-batch được cố định theo tỷ lệ: <strong>60% NIH</strong> (Head A) : <strong>25% COVID</strong> (Head C) : <strong>15% TB</strong> (Head B), ngăn ngừa hoàn toàn nguy cơ tác vụ lớn nuốt chửng tác vụ nhỏ.
            </div>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>Nguyên tắc Zero Patient Leakage: Tập huấn luyện và kiểm thử hoàn toàn tách biệt &bull; Phân tầng nguồn gốc máy quét</span>
          <span>Trang 2 / 7</span>
        </div>
      </section>

      {/* =================================================================== */}
      {/* CHƯƠNG 3: KIẾN TRÚC HỢP NHẤT 3 ĐẦU & ĐỘNG CƠ MASKED LOSS           -->
      {/* =================================================================== */}
      <section
        id="section-2"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#ECFDF5] to-[#F0F9FF]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Kiến Trúc Học Sâu &amp; Tối Ưu Giải Tích
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 03 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Thiết Kế Mạng Đa Nhiệm Độc Lập
            </p>
            <h2 className="text-3xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Kiến Trúc 3 Đầu Suy Luận &amp; Động Cơ Masked Loss Engine
            </h2>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Thay vì triển khai 3 mạng nơ-ron cồng kềnh, LungRay sử dụng một bộ mã hóa đặc trưng dùng chung (Shared Encoder DenseNet-121). Khối gom cụm trung bình toàn cục (GAP) kết hợp Chuẩn hóa tầng không tham số (Parameter-free LayerNorm) và Dropout (p = 0.20) trích xuất vector đặc trưng biểu diễn không gian 1024 chiều.
            </p>

            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-white/60 p-3 border-t-3 border-sky-800 rounded shadow-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-sky-800 block">Head A</span>
                <span className="text-xs font-bold text-slate-900 block my-1">14 Bệnh NIH</span>
                <p className="text-[11px] text-slate-600 leading-tight">Đa nhãn, Sigmoid độc lập từng lớp.</p>
              </div>
              <div className="bg-white/60 p-3 border-t-3 border-emerald-600 rounded shadow-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block">Head B</span>
                <span className="text-xs font-bold text-slate-900 block my-1">Lao Phổi (TB)</span>
                <p className="text-[11px] text-slate-600 leading-tight">Sàng lọc nhị phân, độ nhạy cao.</p>
              </div>
              <div className="bg-white/60 p-3 border-t-3 border-amber-600 rounded shadow-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 block">Head C</span>
                <span className="text-xs font-bold text-slate-900 block my-1">COVID-19</span>
                <p className="text-[11px] text-slate-600 leading-tight">3 lớp: Bình thường, Viêm phổi, COVID.</p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8 space-y-4">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-2">
              Công Thức Giải Tích &amp; Cách Ly Gradient
            </p>

            <div className="p-3 bg-white/60 border-l-4 border-sky-800 text-xs rounded-r">
              <span className="font-bold text-slate-900 block mb-1">
                Masked Multi-Task Loss Engine:
              </span>
              <div className="font-mono text-xs text-slate-900 my-1 font-semibold">
                L_total = (∑ m_0 L_A)/(∑ m_0 + ε) + λ_B (∑ m_1 L_B)/(∑ m_1 + ε) + λ_C (∑ m_2 L_C)/(∑ m_2 + ε)
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed mt-1">
                Với m(i,k) là biến nhị phân chỉ định tác vụ. Gradient chỉ cập nhật vào head tương ứng, triệt tiêu 100% hiện tượng xung đột gradient giữa các tác vụ.
              </p>
            </div>

            <div className="p-3 bg-white/60 border-l-4 border-emerald-600 text-xs rounded-r">
              <span className="font-bold text-slate-900 block mb-1">
                Asymmetric Loss (ASL) Cho Head A &amp; C:
              </span>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Tham số hiệu chuẩn: &gamma;- = 4.0, &gamma;+ = 1.0, margin = 0.05. Triệt tiêu hoàn toàn gradient của các mẫu âm tính dễ phân loại, dồn dung lượng mạng học các bệnh lý cực hiếm (Thoát vị hoành Hernia &lt; 0.2%).
              </p>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>6.97 triệu tham số &bull; Dung lượng mô hình 26.6 MB &bull; Suy luận CPU 674.8 ms</span>
          <span>Trang 3 / 7</span>
        </div>
      </section>

      {/* =================================================================== */}
      {/* CHƯƠNG 4: KẾT QUẢ THỰC NGHIỆM ĐA NHIỆM & KHOẢNG TIN CẬY 95% CI     -->
      {/* =================================================================== */}
      <section
        id="section-3"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#F8FAFC] to-[#E0F2FE]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Kết Quả Đánh Giá Định Lượng
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 04 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Kiểm Định Độc Lập
            </p>
            <h2 className="text-3xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Hiệu Năng Chẩn Đoán Đa Nhiệm Kèm Khoảng Tin Cậy 95% Bootstrap
            </h2>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Đánh giá trên tập kiểm thử độc lập gồm hàng nghìn ca chụp chưa từng xuất hiện trong quá trình huấn luyện, tính toán qua thuật toán <strong>Bootstrap Tái Lấy Mẫu (1,000 lần có hoàn lại)</strong> để xác định khoảng tin cậy 95% CI nghiêm ngặt:
            </p>

            <div className="space-y-2">
              <div className="border-l-4 border-sky-800 pl-3 bg-white/40 py-1 rounded-r">
                <span className="text-xs font-bold text-slate-900 block">
                  Head A (14 Bệnh NIH): Macro AUROC = 0.8271 [0.8110 &ndash; 0.8432]
                </span>
                <p className="text-[11px] text-slate-600 leading-tight">
                  Nhiều bệnh lý vượt CheXNet: Xẹp phổi (0.8492 so với 0.8094), Khối u (0.8540 so với 0.8106), Viêm phổi (0.8459 so với 0.7680).
                </p>
              </div>

              <div className="border-l-4 border-emerald-600 pl-3 bg-white/40 py-1 rounded-r">
                <span className="text-xs font-bold text-emerald-800 block">
                  Head B (Lao Phổi TB): AUROC = 1.0000 [0.9990 &ndash; 1.0000]
                </span>
                <p className="text-[11px] text-slate-600 leading-tight">
                  Phân tách tuyệt đối giữa phim tổn thương lao và phim bình thường, độ nhạy đạt mức tối ưu cho sàng lọc cộng đồng.
                </p>
              </div>

              <div className="border-l-4 border-amber-600 pl-3 bg-white/40 py-1 rounded-r">
                <span className="text-xs font-bold text-amber-800 block">
                  Head C (COVIDx CXR-4): AUROC = 0.7342 [0.6930 &ndash; 0.7754]
                </span>
                <p className="text-[11px] text-slate-600 leading-tight">
                  Đánh giá trung thực sau khi loại bỏ hoàn toàn shortcut viền ảnh. Đây là chỉ số thể hiện năng lực sinh học thực tế.
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-3">
              Bảng Thống Kê Các Bệnh Lý Then Chốt
            </p>
            <table className="w-full text-xs border-collapse bg-white/60 backdrop-blur-sm rounded">
              <thead>
                <tr className="border-y-2 border-slate-900">
                  <th className="py-1 px-1.5 text-left font-bold">Bệnh Lý</th>
                  <th className="py-1 px-1.5 text-left font-bold">AUROC</th>
                  <th className="py-1 px-1.5 text-left font-bold">95% Bootstrap CI</th>
                  <th className="py-1 px-1.5 text-left font-bold">Stanford CheXNet</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50">
                <tr>
                  <td className="py-1 px-1.5 font-semibold">Khí Phế Thủng (Emphysema)</td>
                  <td className="py-1 px-1.5 font-bold">0.8725</td>
                  <td className="py-1 px-1.5 text-slate-600">[0.8364, 0.9057]</td>
                  <td className="py-1 px-1.5 text-slate-600">Tương đương</td>
                </tr>
                <tr>
                  <td className="py-1 px-1.5 font-semibold">Bóng Tim To (Cardiomegaly)</td>
                  <td className="py-1 px-1.5 font-bold">0.8685</td>
                  <td className="py-1 px-1.5 text-slate-600">[0.8273, 0.9012]</td>
                  <td className="py-1 px-1.5 text-slate-600">Vượt trội</td>
                </tr>
                <tr>
                  <td className="py-1 px-1.5 font-semibold">Tràn Dịch Màng Phổi (Effusion)</td>
                  <td className="py-1 px-1.5 font-bold">0.8661</td>
                  <td className="py-1 px-1.5 text-slate-600">[0.8256, 0.9036]</td>
                  <td className="py-1 px-1.5 text-slate-600">Vượt trội</td>
                </tr>
                <tr>
                  <td className="py-1 px-1.5 font-semibold">Khối U Phổi (Mass)</td>
                  <td className="py-1 px-1.5 font-bold">0.8540</td>
                  <td className="py-1 px-1.5 text-slate-600">[0.8169, 0.8888]</td>
                  <td className="py-1 px-1.5 text-slate-600">CheXNet: 0.8106</td>
                </tr>
                <tr>
                  <td className="py-1 px-1.5 font-semibold">Xẹp Phổi (Atelectasis)</td>
                  <td className="py-1 px-1.5 font-bold">0.8492</td>
                  <td className="py-1 px-1.5 text-slate-600">[0.8079, 0.8873]</td>
                  <td className="py-1 px-1.5 text-slate-600">CheXNet: 0.8094</td>
                </tr>
                <tr>
                  <td className="py-1 px-1.5 font-semibold">Viêm Phổi (Pneumonia)</td>
                  <td className="py-1 px-1.5 font-bold">0.8459</td>
                  <td className="py-1 px-1.5 text-slate-600">[0.8094, 0.8763]</td>
                  <td className="py-1 px-1.5 text-slate-600">CheXNet: 0.7680</td>
                </tr>
                <tr className="border-t-2 border-slate-900 font-bold bg-slate-50/50">
                  <td className="py-1.5 px-1.5">Trung Bình Head A</td>
                  <td className="py-1.5 px-1.5 text-sky-900">0.8271</td>
                  <td className="py-1.5 px-1.5 text-slate-700">[0.8110, 0.8432]</td>
                  <td className="py-1.5 px-1.5 text-slate-900">Vượt Tiêu Chuẩn</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>Tái lấy mẫu 1,000 lần (Bootstrap Resampling) &bull; Mức ý nghĩa thống kê &alpha; = 0.05</span>
          <span>Trang 4 / 7</span>
        </div>
      </section>

      {/* =================================================================== */}
      {/* CHƯƠNG 5: ĐỊNH LƯỢNG WSOL & KIỂM TOÁN KHAI THÁC ĐẶC TRƯNG GIẢ MẠO  */}
      {/* =================================================================== */}
      <section
        id="section-4"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#F0FDF4] to-[#ECFDF5]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Giải Thích Định Lượng &amp; An Toàn AI
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 05 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Khử Nhiễu Rìa &amp; Thẩm Định Không Gian
            </p>
            <h2 className="text-3xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Định Lượng WSOL Box-IoU &amp; Kiểm Toán Khai Thác Đặc Trưng Giả Mạo
            </h2>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Đột phá trọng tâm của LungRay là chuyển đổi Explainable AI từ trực quan cảm tính sang <strong>đo lường định lượng tương quan hình học (IoU)</strong> đối chiếu với nhãn khoanh vùng của bác sĩ X-quang:
            </p>

            <div className="space-y-3">
              <div className="p-3 bg-white/60 border-l-4 border-sky-800 rounded-r">
                <span className="text-xs font-bold text-slate-900 block mb-1">
                  Độ Khớp Tổn Thương Bác Sĩ (Box-IoU Evaluation):
                </span>
                <p className="text-xs text-slate-700 leading-relaxed">
                  &bull; <strong>RSNA Pneumonia</strong>: Mean Box-IoU đạt <strong>0.7631</strong> (90.0% ca vượt ngưỡng lâm sàng &ge; 0.35).<br />
                  &bull; <strong>VinDr-CXR (Bệnh viện Việt Nam)</strong>: Mean Box-IoU đạt <strong>0.6049</strong> (80.0% ca vượt ngưỡng lâm sàng &ge; 0.35).
                </p>
              </div>

              <div className="p-3 bg-white/60 border-l-4 border-emerald-600 rounded-r">
                <span className="text-xs font-bold text-slate-900 mb-1 block">
                  Kiểm Toán Năng Lượng Trong Phổi (Pulmonary Grounding Audit):
                </span>
                <p className="text-xs text-slate-700 leading-relaxed">
                  Kiểm toán trên 150 ca dương tính COVID-19: Khi chưa có cơ chế bảo vệ, mạng chỉ tập trung <strong>38.49%</strong> năng lượng trong phổi (0% ca đạt chuẩn &ge; 80%). Khi kích hoạt Clinical Pulmonary Grounding, tỷ lệ này tăng vọt lên <strong>94.92% &plusmn; 1.60%</strong> (100% ca đạt chuẩn, p = 1.15 &times; 10^-26, kiểm định Wilcoxon).
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-3">
              Bảng Đối Sánh Kiểm Toán Shortcut Learning
            </p>
            <table className="w-full text-xs border-collapse mb-4 bg-white/60 backdrop-blur-sm rounded">
              <thead>
                <tr className="border-y-2 border-slate-900">
                  <th className="py-2 px-2 text-left font-bold">Phương Pháp</th>
                  <th className="py-2 px-2 text-left font-bold">Năng Lượng Phổi</th>
                  <th className="py-2 px-2 text-left font-bold">Đạt Chuẩn (&ge;80%)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50">
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Raw Grad-CAM (Gốc)</td>
                  <td className="py-1.5 px-2 text-rose-700 font-bold">38.49% &plusmn; 10.4%</td>
                  <td className="py-1.5 px-2 text-slate-600">0.0% (0 / 150 ca)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-semibold">Clinical Grounded</td>
                  <td className="py-1.5 px-2 text-emerald-800 font-bold">94.92% &plusmn; 1.6%</td>
                  <td className="py-1.5 px-2 text-emerald-800 font-bold">100.0% (150 ca)</td>
                </tr>
                <tr className="border-t-2 border-slate-900 font-bold bg-slate-50/50">
                  <td className="py-1.5 px-2">Mức Tăng Trưởng</td>
                  <td className="py-1.5 px-2 text-slate-950">+56.43% &plusmn; 9.3%</td>
                  <td className="py-1.5 px-2 text-slate-950">p = 1.15 &times; 10^-26</td>
                </tr>
              </tbody>
            </table>

            <div className="p-3 bg-white/60 border-l-4 border-slate-800 text-[11px] text-slate-700 rounded-r">
              Chuẩn chấp nhận lâm sàng: Box-IoU &ge; 0.35 &bull; Tỷ lệ năng lượng phế trường &ge; 80.0%. LungRay hoàn toàn loại bỏ hiện tượng kích hoạt vào nhãn chữ &apos;PORTABLE&apos; hay ký hiệu &apos;R/L&apos;.
            </div>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>Chuẩn chấp nhận lâm sàng quốc tế: Box-IoU &ge; 0.35 &bull; Năng lượng phế trường &ge; 80.0%</span>
          <span>Trang 5 / 7</span>
        </div>
      </section>

      {/* =================================================================== */}
      {/* CHƯƠNG 6: THỬ THÁCH NGOẠI VI (OOD TEST) & SO SÁNH KIẾN TRÚC        -->
      {/* =================================================================== */}
      <section
        id="section-5"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#F0F9FF] to-[#F1F5F9]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Khả Năng Thích Ứng &amp; Tối Ưu Phần Cứng
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 06 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Thử Nghiệm Ngoại Suy Bệnh Viện
            </p>
            <h2 className="text-3xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Thử Thách Ngoại Vi (OOD Test) &amp; So Sánh Hiệu Năng Kiến Trúc
            </h2>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Để kiểm chứng độ bền vững khi chuyển sang cơ sở y tế mới, mô hình được đưa vào thử nghiệm ngoại suy (Out-of-Distribution - OOD) không qua tinh chỉnh (Zero-shot) trên <strong>22,433 ảnh Stanford CheXpert</strong>:
            </p>

            <div className="p-3 bg-white/60 border-l-4 border-emerald-600 mb-4 text-xs rounded-r">
              <span className="font-bold text-slate-900 block mb-1">
                Hạn Mức Suy Giảm Cho Phép Của Y Khoa:
              </span>
              <p className="text-slate-700 leading-relaxed">
                AUC nội bộ NIH đạt <strong>0.8517</strong> &rarr; AUC ngoại suy CheXpert đạt <strong>0.8070</strong>.<br />
                Mức suy giảm bình quân qua 5 bệnh lý chỉ là <strong>&Delta;AUC = +0.0447</strong>, nằm sâu bên trong giới hạn an toàn khoa học (&le; 0.0800), tỷ lệ duy trì năng lực đạt <strong>94.75%</strong>.
              </p>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed text-justify">
              Kết quả xác nhận LungRay học được các biến đổi sinh học thực thụ của tổn thương thay vì ghi nhớ đặc tính máy chụp của một bệnh viện duy nhất.
            </p>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-3">
              So Sánh Hiệu Năng Kiến Trúc: DenseNet vs. ResNet vs. ViT
            </p>
            <table className="w-full text-xs border-collapse mb-4 bg-white/60 backdrop-blur-sm rounded">
              <thead>
                <tr className="border-y-2 border-slate-900">
                  <th className="py-2 px-2 text-left font-bold">Kiến Trúc</th>
                  <th className="py-2 px-2 text-left font-bold">Tham Số</th>
                  <th className="py-2 px-2 text-left font-bold">Độ Trễ CPU</th>
                  <th className="py-2 px-2 text-left font-bold">Macro AUROC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50">
                <tr className="font-bold bg-sky-50/50">
                  <td className="py-1.5 px-2 text-sky-950">DenseNet-121 (Lựa Chọn)</td>
                  <td className="py-1.5 px-2">6.97 M</td>
                  <td className="py-1.5 px-2">674.8 ms</td>
                  <td className="py-1.5 px-2">0.8538</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 text-slate-700 font-semibold">ResNet-50</td>
                  <td className="py-1.5 px-2 text-slate-600">23.54 M</td>
                  <td className="py-1.5 px-2 text-slate-600">631.1 ms</td>
                  <td className="py-1.5 px-2 text-slate-600">0.8446</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 text-slate-700 font-semibold">ViT-B/16 (Transformer)</td>
                  <td className="py-1.5 px-2 text-slate-600">86.45 M</td>
                  <td className="py-1.5 px-2 text-slate-600">1,783.9 ms</td>
                  <td className="py-1.5 px-2 text-slate-600">0.8640</td>
                </tr>
              </tbody>
            </table>

            <div className="p-3 bg-white/60 text-xs text-slate-700 leading-relaxed border-l-4 border-slate-800 rounded-r">
              <strong>Lý Luận Lựa Chọn Kỹ Thuật:</strong> DenseNet-121 đạt hiệu suất tham số cao nhất: AUROC đạt 0.8538 với chỉ 6.97 triệu tham số (nhẹ hơn ViT-B/16 tới 12.4 lần). Kích thước tệp 26.6MB cho phép chạy trực tiếp trên máy vi tính thông thường của bệnh viện tuyến huyện mà không cần lắp đặt card đồ họa đắt tiền.
            </div>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>Tiêu chuẩn OOD: &Delta;AUC &le; 0.08 &bull; Phần cứng đo lường: Intel Core i7 CPU</span>
          <span>Trang 6 / 7</span>
        </div>
      </section>

      {/* =================================================================== */}
      {/* CHƯƠNG 7: HIỆN THỰC HÓA HỆ THỐNG PACS & KẾT LUẬN                    -->
      {/* =================================================================== */}
      <section
        id="section-6"
        className="h-screen w-screen snap-start snap-always flex flex-col justify-between pt-16 pb-6 px-16 lg:px-24 border-b border-slate-200/50 bg-gradient-to-br from-[#ECFDF5] to-[#E0F2FE]"
      >
        <div className="border-b border-slate-300/40 pb-2 flex justify-between items-baseline">
          <span className="text-xs uppercase tracking-widest text-slate-600 font-bold">
            Ứng Dụng Lâm Sàng &amp; Kết Luận Nghiên Cứu
          </span>
          <span className="text-xs font-bold text-slate-800">Chương 07 / 07</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 my-auto items-center">
          <div className="lg:col-span-7">
            <p className="text-xs uppercase tracking-wider font-bold text-sky-800 mb-2">
              Khởi Chạy Sản Phẩm Y Tế
            </p>
            <h2 className="text-3xl font-extrabold leading-tight text-[#0B1E36] mb-4 tracking-tight">
              Hiện Thực Hóa Hệ Thống Đọc Phim PACS Lâm Sàng &amp; Định Hướng
            </h2>
            <p className="text-sm leading-relaxed text-slate-700 mb-4 text-justify">
              Toàn bộ mô hình học sâu và thuật toán giải thích được đóng gói thành một hệ thống đọc phim y tế hoàn chỉnh, dễ dàng tích hợp vào luồng làm việc của bác sĩ:
            </p>

            <div className="space-y-3">
              <div className="border-l-4 border-sky-800 pl-3 bg-white/50 py-1.5 rounded-r">
                <h4 className="text-xs font-bold text-slate-900">
                  Vi Dịch Vụ Phía Sau (FastAPI Asynchronous Microservice)
                </h4>
                <p className="text-xs text-slate-600 leading-normal">
                  Cung cấp các điểm cuối RESTful hiệu năng cao (<code>/health</code>, <code>/predict</code>, <code>/explain</code>, <code>/audit</code>). Toàn bộ chu trình từ giải mã ảnh DICOM/PNG đến trả kết quả nhiệt độ trễ &le; 1.8 giây.
                </p>
              </div>

              <div className="border-l-4 border-emerald-600 pl-3 bg-white/50 py-1.5 rounded-r">
                <h4 className="text-xs font-bold text-slate-900">
                  Giao Diện Bác Sĩ (Next.js 14 Medical PACS Viewer)
                </h4>
                <p className="text-xs text-slate-600 leading-normal">
                  Trang bị thanh trượt điều biến độ mờ Alpha Heatmap (0&ndash;100%), cho phép bác sĩ X-quang trực tiếp kiểm tra cấu trúc mô phổi bên dưới lớp nhiệt Grad-CAM trong thời gian thực.
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 border-l border-slate-300/40 pl-8">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600 mb-3">
              Kết Luận &amp; Danh Mục Y Văn
            </p>
            <p className="text-xs text-slate-700 leading-relaxed mb-4 text-justify">
              Chuyên khảo chứng minh tính khả thi của mô hình trí tuệ nhân tạo đa nhiệm giải quyết trọn vẹn bài toán X-quang lồng ngực: loại bỏ rò rỉ bệnh nhân, định lượng hóa bản đồ nhiệt (Box-IoU 0.7631 / 0.6049) và triệt tiêu đặc trưng giả mạo (94.92% năng lượng phổi). Hệ thống đáp ứng đầy đủ tiêu chí để bước vào giai đoạn thử nghiệm lâm sàng diện hẹp.
            </p>

            <div className="border-t border-slate-300/40 pt-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 block mb-2">
                Tài Liệu Tham Khảo Quốc Tế:
              </span>
              <ul className="text-[11px] text-slate-600 space-y-1 list-disc pl-4">
                <li>Wang et al. (CVPR 2017) &bull; ChestX-ray8 database and benchmarks.</li>
                <li>Rajpurkar et al. (Stanford, 2017) &bull; CheXNet pneumonia detection.</li>
                <li>DeGrave et al. (Nature Machine Intelligence, 2021) &bull; COVID-19 superficial shortcuts.</li>
                <li>Nguyen et al. (Scientific Data, Nature, 2020) &bull; VinDr-CXR dataset.</li>
                <li>Selvaraju et al. (ICCV 2017) &bull; Grad-CAM visual explanations.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-300/40 pt-2 flex justify-between text-[11px] text-slate-500">
          <span>Bản quyền nghiên cứu &copy; 2026 LungRay Healthcare AI Research Consortium</span>
          <span>Trang 7 / 7</span>
        </div>
      </section>
    </div>
  );
}
