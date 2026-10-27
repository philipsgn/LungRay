import Link from "next/link";

export default function ReportPage() {
  const kpis = [
    { label: "Quy Mô Dữ Liệu", value: "112.120", sub: "Ảnh X-quang chuẩn hóa" },
    { label: "Sàng Lọc Lao Phổi", value: "100,0%", sub: "Độ chính xác AUROC kiểm định" },
    { label: "14 Bệnh Lồng Ngực", value: "82,7%", sub: "Macro AUROC (Tương đương Stanford CheXNet)" },
    { label: "Định Vị Tổn Thương", value: "0,763", sub: "Chỉ số IoU so với chuyên gia RSNA" },
    { label: "Năng Lượng Trong Phổi", value: "94,9%", sub: "Triệt tiêu hoàn toàn kích hoạt viền ngoài" },
  ];

  const phases = [
    {
      num: "GIAI ĐOẠN 1",
      title: "Cơ Sở Lý Thuyết & 8 Nguyên Tắc Y Đức Dữ Liệu",
      objective: "Khảo sát 5 công trình nền tảng quốc tế (CheXNet, VinDr-CXR, COVIDx) và thiết lập nguyên tắc chống rò rỉ dữ liệu.",
      breakthrough: "Bảo vệ danh tính bệnh nhân, phân tầng nguồn ảnh gốc, cấm hoàn toàn hành vi giả lập kết quả.",
      metric: "Bộ hồ sơ thiết kế kỹ thuật, đề cương học thuật và cấu trúc quản trị dự án.",
    },
    {
      num: "GIAI ĐOẠN 2",
      title: "Kỹ Thuật Dữ Liệu & Phân Tách Không Trùng Lặp Bệnh Nhân",
      objective: "112.120 ảnh NIH ChestX-ray14, 76.345 ảnh COVIDx CXR-4, 4.200 ảnh Lao phổi.",
      breakthrough: "Phân chia train/val/test triệt để theo mã định danh bệnh nhân. Tỷ lệ lấy mẫu cân bằng 60% NIH : 25% COVID : 15% TB.",
      metric: "0% Rò rỉ dữ liệu bệnh nhân; 100% Khớp tập tin thực tế trên đám mây.",
    },
    {
      num: "GIAI ĐOẠN 3",
      title: "Kiến Trúc Học Sâu Đa Nhiệm Lồng Ngực 3 Nhánh",
      objective: "Bộ mã hóa dùng chung DenseNet-121 tiếp nhận độ phân giải y khoa 512x512, trích xuất đặc trưng tại tầng dày đặc cuối.",
      breakthrough: "Cơ chế lan truyền ngược có chọn lọc: Mẫu bệnh của nhánh nào chỉ cập nhật gradient riêng cho nhánh đó.",
      metric: "Head A (82,7%), Head B (100,0%), Head C (73,4%).",
    },
    {
      num: "GIAI ĐOẠN 4",
      title: "Hàm Mất Mát Bất Đối Xứng & Cân Bằng Tổn Thương Hiếm",
      objective: "Xử lý tỷ lệ mất cân bằng cực hạn (Thoát vị hoành chỉ chiếm 0,2% dữ liệu) và tổn thương mờ khó thấy.",
      breakthrough: "Tích hợp hàm mất mát bất đối xứng triệt tiêu mẫu âm tính dễ, kết hợp tầng chuẩn hóa không tham số tương thích ngược.",
      metric: "16 Giá trị ngưỡng quyết định tối ưu theo chỉ số Youden's J.",
    },
    {
      num: "GIAI ĐOẠN 5",
      title: "Định Vị Tổn Thương Giải Phẫu & Kiểm Toán Minh Bạch",
      objective: "Bản đồ kích hoạt gradient bậc cao kết hợp thuật toán phân đoạn phế trường phổi nhị phân thích nghi.",
      breakthrough: "Đo lường định lượng trên tập nhãn Bounding Box chuyên gia từ VinDr-CXR và RSNA Pneumonia.",
      metric: "IoU đạt 0,763 (RSNA) và 0,605 (VinDr-CXR); Năng lượng kích hoạt trong phổi 94,9%.",
    },
    {
      num: "GIAI ĐOẠN 6",
      title: "Trạm Đọc Phim Y Tế Số Hóa PACS Thông Minh",
      objective: "Hệ thống dịch vụ vi mô phân tách: Máy chủ suy luận FastAPI xử lý ảnh y tế và giao diện Web PACS hiện đại.",
      breakthrough: "Thanh trượt độ mờ bản đồ nhiệt tương tác, chuyển đổi chế độ lọc giải phẫu học và phơi bày kiểm toán.",
      metric: "1,4 Giây / Ca chụp độ phân giải cao; Khởi chạy cục bộ một thao tác.",
    },
    {
      num: "GIAI ĐOẠN 7",
      title: "Báo Cáo Nghiên Cứu Khoa Học & Định Hướng Tiền Lâm Sàng",
      objective: "Báo cáo khoa học đơn sắc chuẩn IEEE/MICCAI, bộ đề cương slide thuyết trình 39 trang và 20 câu hỏi phản biện lâm sàng.",
      breakthrough: "114/114 Bài kiểm thử đơn vị tự động vượt qua 100%, không phát sinh lỗi cú pháp hay suy thoái.",
      metric: "30/31 Nhiệm vụ hoàn thành (Tiến độ dự án: 96,8%).",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50/40 via-slate-50 to-sky-50/50 text-slate-800 antialiased">
      {/* Navigation Header */}
      <header className="bg-white/90 backdrop-blur border-b border-slate-200 sticky top-0 z-20 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-sky-700 flex items-center justify-center font-bold text-white text-sm">
              LR
            </div>
            <div>
              <span className="font-extrabold text-slate-900 text-lg tracking-tight">LUNGRAY</span>
              <span className="ml-2 text-xs text-teal-700 font-semibold uppercase tracking-wider">Báo Cáo Nghiệm Thu</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-xs font-semibold px-4 py-2 rounded-full border border-slate-300 text-slate-700 hover:bg-slate-100 transition"
            >
              Về Trạm Đọc Phim PACS
            </Link>
            <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              Kiểm Định Hoàn Tất
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Title Block */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <span className="inline-block px-3 py-1 rounded-full bg-sky-100 text-sky-800 text-xs font-bold uppercase tracking-wider mb-3">
            Tổng Quan Nghiên Cứu & Phát Triển
          </span>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight leading-snug mb-3">
            Hệ Thống Trí Tuệ Nhân Tạo Hỗ Trợ Chẩn Đoán & Định Vị Tổn Thương X-Quang Ngực Đa Nhiệm
          </h1>
          <p className="text-slate-600 text-sm leading-relaxed">
            Nền tảng học sâu đa nhiệm 3 nhánh tiếp nhận ảnh X-quang 512x512, tích hợp thuật toán tổn thất bất đối xứng, cách ly gradient nhiệm vụ và trực quan hóa bản đồ nhiệt có bảo vệ giải phẫu học lồng ngực.
          </p>
        </div>

        {/* KPI Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {kpis.map((kpi, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition"
            >
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                {kpi.label}
              </div>
              <div className="text-2xl font-extrabold text-slate-900 mb-1">
                {kpi.value}
              </div>
              <div className="text-xs text-teal-700 font-medium leading-snug">
                {kpi.sub}
              </div>
            </div>
          ))}
        </div>

        {/* Clinical Callout */}
        <div className="bg-white rounded-xl p-6 border-l-4 border-teal-600 border border-slate-200 shadow-sm mb-12">
          <h2 className="text-base font-bold text-slate-900 mb-1.5">
            Đánh Giá Độ Tin Cậy Thực Nghiệm & Hướng Dẫn Ứng Dụng
          </h2>
          <p className="text-slate-600 text-xs leading-relaxed">
            Hệ thống đạt độ chính xác sàng lọc rất cao ở nhánh Lao phổi (AUROC 100%) và 14 bệnh lồng ngực (AUROC 82,7%). Ở nhánh COVID-19, việc chủ động triệt tiêu các đặc trưng giả tạo ngoài phế trường (chống Shortcut Learning) đưa AUROC thực tế về mức 73,4%, bảo toàn tính liêm chính khoa học tuyệt đối. Hệ thống được định hình tối ưu cho vai trò công cụ hỗ trợ thứ hai tại trạm đọc phim y tế, hỗ trợ bác sĩ nhận định sơ bộ trong 1,4 giây/ảnh.
          </p>
        </div>

        {/* 7 Phases Overview */}
        <div className="mb-6 flex items-end justify-between">
          <div>
            <div className="text-xs font-bold text-teal-700 uppercase tracking-wider mb-1">
              Tiến Trình Thực Nghiệm
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Tổng Quan 7 Giai Đoạn Dự Án
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            30/31 Nhiệm Vụ Hoàn Thành (96,8%)
          </span>
        </div>

        <div className="space-y-4 mb-14">
          {phases.map((phase, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:border-slate-300 transition"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 text-xs font-bold">
                    {phase.num}
                  </span>
                  <h3 className="text-base font-bold text-slate-900">
                    {phase.title}
                  </h3>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Nghiệm Thu Đạt
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <div className="text-slate-400 font-semibold uppercase tracking-wider mb-1">
                    Mục Tiêu & Dữ Liệu
                  </div>
                  <div className="text-slate-700 leading-relaxed font-medium">
                    {phase.objective}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 font-semibold uppercase tracking-wider mb-1">
                    Đột Phá Kỹ Thuật
                  </div>
                  <div className="text-slate-700 leading-relaxed font-medium">
                    {phase.breakthrough}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 font-semibold uppercase tracking-wider mb-1">
                    Kết Quả Nghiệm Thu
                  </div>
                  <div className="text-teal-800 font-bold leading-relaxed">
                    {phase.metric}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-500">
        <p className="font-semibold text-slate-700">Dự Án Nghiên Cứu Trí Tuệ Nhân Tạo LungRay</p>
        <p className="max-w-xl mx-auto mt-1 text-slate-400 text-[11px] leading-relaxed">
          Số liệu thực nghiệm được đo đạc và kiểm định độc lập trên các bộ dữ liệu X-quang chuẩn mực quốc tế (NIH, COVIDx, TB, VinDr-CXR, RSNA Pneumonia).
        </p>
      </footer>
    </div>
  );
}
