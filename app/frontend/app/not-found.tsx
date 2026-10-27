import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 text-center">
      <h2 className="text-2xl font-bold text-slate-200 mb-2">404 - Page Not Found</h2>
      <p className="text-sm text-slate-400 mb-6">The requested radiological view does not exist.</p>
      <Link
        href="/"
        className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-semibold transition-all"
      >
        Return to PACS Viewer
      </Link>
    </div>
  );
}
