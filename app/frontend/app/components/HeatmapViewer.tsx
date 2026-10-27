"use client";

import Image from "next/image";

interface HeatmapViewerProps {
  original: string | null;
  heatmap: string | null;
  alpha: number;
  diseaseName?: string;
  isGrounded?: boolean;
  inLungRatio?: number | null;
  isExplaining?: boolean;
}

export default function HeatmapViewer({
  original,
  heatmap,
  alpha,
  diseaseName,
  isGrounded = true,
  inLungRatio,
  isExplaining = false,
}: HeatmapViewerProps) {
  return (
    <div className="relative w-full aspect-square bg-slate-900 rounded-xl overflow-hidden border border-slate-700 shadow-2xl">
      {/* Background X-ray */}
      {original ? (
        <Image
          src={original}
          alt="Chest X-ray"
          fill
          className="object-contain"
          priority
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 gap-2">
          <svg className="w-12 h-12 stroke-current opacity-40" viewBox="0 0 24 24" fill="none" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
          </svg>
          <span className="text-sm font-medium">No chest radiograph loaded</span>
        </div>
      )}

      {/* Grad-CAM Heatmap Layer with Screen Blending */}
      {heatmap && (
        <Image
          src={heatmap}
          alt="Grad-CAM heatmap"
          fill
          className="object-contain transition-opacity duration-150"
          style={{ opacity: alpha / 100, mixBlendMode: "screen" }}
          priority
        />
      )}

      {/* Floating Badges */}
      {original && (
        <div className="absolute top-3 inset-x-3 flex items-center justify-between pointer-events-none z-10">
          {diseaseName && (
            <div className="bg-slate-950/80 backdrop-blur-md border border-slate-700 px-3 py-1 rounded-md text-xs font-semibold text-slate-200 flex items-center gap-1.5 shadow">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              Target: <span className="text-cyan-300">{diseaseName}</span>
            </div>
          )}

          {inLungRatio !== undefined && inLungRatio !== null && (
            <div
              className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 shadow backdrop-blur-md border ${
                isGrounded
                  ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-300"
                  : "bg-amber-950/80 border-amber-500/40 text-amber-300"
              }`}
            >
              <span>{isGrounded ? "🛡️ Clinical Grounded" : "⚠️ Raw AI Attention"}</span>
              <span className="opacity-80">({(inLungRatio * 100).toFixed(1)}% In-Lung)</span>
            </div>
          )}
        </div>
      )}

      {/* Loading overlay for live CAM update */}
      {isExplaining && (
        <div className="absolute inset-0 bg-slate-950/50 backdrop-blur-[2px] flex items-center justify-center z-20">
          <div className="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-xs font-medium text-slate-200 flex items-center gap-2 shadow-xl">
            <svg className="animate-spin h-4 w-4 text-cyan-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Generating Grad-CAM Map...
          </div>
        </div>
      )}
    </div>
  );
}
