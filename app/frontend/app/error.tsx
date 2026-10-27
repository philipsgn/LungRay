"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("PACS Viewer runtime error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 text-center">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl p-8 max-w-md shadow-2xl">
        <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-4 text-xl">
          ⚠️
        </div>
        <h2 className="text-lg font-bold text-slate-100 mb-2">LungRay PACS Viewer Notice</h2>
        <p className="text-sm text-slate-400 mb-6">
          {error.message || "An unexpected error occurred while rendering the medical interface."}
        </p>
        <button
          type="button"
          onClick={() => reset()}
          className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-semibold transition-all shadow-md"
        >
          Reload Interface
        </button>
      </div>
    </div>
  );
}
