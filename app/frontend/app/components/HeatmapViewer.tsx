"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react";

interface HeatmapViewerProps {
  original: string | null;
  heatmap: string | null;
  heatmapHasAlpha?: boolean;
  contour?: string | null;
  contourHasAlpha?: boolean;
  alpha: number;
  diseaseName?: string;
  isGrounded?: boolean;
  inLungRatio?: number | null;
  isExplaining?: boolean;
  isRejected?: boolean;
}

export default function HeatmapViewer({
  original,
  heatmap,
  heatmapHasAlpha = false,
  contour,
  contourHasAlpha = false,
  alpha,
  diseaseName,
  isGrounded = true,
  inLungRatio,
  isExplaining = false,
  isRejected = false,
}: HeatmapViewerProps) {
  // Visualizer display mode: "both" | "heatmap" | "contour" | "raw"
  const [viewMode, setViewMode] = useState<"both" | "heatmap" | "contour" | "raw">("both");
  const [inverted, setInverted] = useState(false);
  const [zoom, setZoom] = useState(1);

  return (
    <div
      className={`relative w-full aspect-square bg-[#05080E] rounded-xl overflow-hidden border shadow-2xl transition-all duration-200 select-none ${
        isRejected ? "border-rose-600 ring-2 ring-rose-600/40" : "border-[#1C2937]"
      }`}
    >
      {/* Background X-ray */}
      {original ? (
        <Image
          src={original}
          alt="Chest Radiograph"
          fill
          className="object-contain"
          style={{ filter: inverted ? "invert(1)" : undefined, transform: `scale(${zoom})` }}
          priority
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-[#8C9DB0] gap-2 font-sans">
          <svg className="w-12 h-12 stroke-current opacity-25" viewBox="0 0 24 24" fill="none" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
          </svg>
          <span className="text-xs tracking-wider uppercase font-semibold text-[#8C9DB0]">
            No Radiograph Ingested
          </span>
          <span className="text-[11px] text-[#566475]">
            Browse a file or select a clinical preset above to begin
          </span>
        </div>
      )}

      {/* 1. Grad-CAM Heatmap Layer with Screen Blending */}
      {heatmap && !isRejected && (viewMode === "both" || viewMode === "heatmap") && (
        <Image
          src={heatmap}
          alt="Grad-CAM activation overlay"
          fill
          className="object-contain transition-opacity duration-150"
          style={{ opacity: alpha / 100, mixBlendMode: heatmapHasAlpha ? "normal" : "screen", transform: `scale(${zoom})` }}
          priority
        />
      )}

      {/* 2. Clinical Lesion Iso-Contour Layer */}
      {contour && !isRejected && (viewMode === "both" || viewMode === "contour") && (
        <Image
          src={contour}
          alt="Clinical lesion iso-contour overlay"
          fill
          className="object-contain transition-opacity duration-150 pointer-events-none"
          style={{ mixBlendMode: contourHasAlpha ? "normal" : "lighten", transform: `scale(${zoom})` }}
          priority
        />
      )}

      {/* Medical Scanning Reticle / Crosshair */}
      {original && (
        <div className="absolute inset-0 pointer-events-none opacity-20 z-10">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8">
            <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-[#3FD0C4]" />
            <div className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-[#3FD0C4]" />
          </div>
          <div className="absolute top-4 left-4 w-4 h-4 border-t border-l border-slate-600" />
          <div className="absolute top-4 right-4 w-4 h-4 border-t border-r border-slate-600" />
          <div className="absolute bottom-4 left-4 w-4 h-4 border-b border-l border-slate-600" />
          <div className="absolute bottom-4 right-4 w-4 h-4 border-b border-r border-slate-600" />
        </div>
      )}

      {/* Laser Scanning Sweep Beam (When Explaining) */}
      {isExplaining && (
        <div className="absolute inset-0 pointer-events-none z-25 overflow-hidden">
          <div className="w-full h-1 bg-gradient-to-r from-transparent via-[#3FD0C4] to-transparent shadow-[0_0_15px_#3FD0C4] animate-pulse"
               style={{ animation: "scanLine 1.4s ease-in-out infinite" }}
          />
          <style jsx>{`
            @keyframes scanLine {
              0% { transform: translateY(0); }
              50% { transform: translateY(500px); }
              100% { transform: translateY(0); }
            }
          `}</style>
        </div>
      )}

      {/* Viewport Top HUD Strip: Target Condition & Grounding Status */}
      {original && (
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 z-30 pointer-events-none">
          <div className="flex items-center gap-2 pointer-events-auto flex-wrap">
            {diseaseName && (
              <span className="px-2.5 py-1 rounded-md bg-[#070B12]/80 border border-[#1C2937] text-xs font-mono font-medium text-[#E6EDF4] backdrop-blur-md shadow-sm">
                Target: <strong className="text-[#3FD0C4]">{diseaseName}</strong>
              </span>
            )}

            {isGrounded !== undefined && (
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase border backdrop-blur-md ${
                  isGrounded
                    ? "bg-[#0A7A74]/20 border-[#3FD0C4]/40 text-[#3FD0C4]"
                    : "bg-slate-900/80 border-slate-700 text-slate-400"
                }`}
              >
                {isGrounded ? "Anatomical Masked" : "Unmasked Frame"}
              </span>
            )}
          </div>

          {/* In-Lung Activation Energy Audit Badge */}
          {inLungRatio !== null && inLungRatio !== undefined && !isRejected && (
            <div
              className={`pointer-events-auto px-2.5 py-1 rounded-md text-[11px] font-mono border backdrop-blur-md flex items-center gap-1.5 shadow-sm ${
                inLungRatio >= 0.8
                  ? "bg-emerald-950/70 border-emerald-700/60 text-emerald-300"
                  : "bg-amber-950/80 border-amber-600/70 text-amber-300"
              }`}
              title="Shortcut Audit: Lung field activation ratio (Threshold ≥ 80%)"
            >
              {inLungRatio >= 0.8 ? (
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              )}
              <span>In-Lung Energy: {(inLungRatio * 100).toFixed(1)}%</span>
            </div>
          )}
        </div>
      )}

      {/* Viewport Bottom Floating Controls Toolbar */}
      {original && (
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between gap-2 z-30 pointer-events-auto">
          {/* Layer View Mode Switcher */}
          <div className="inline-flex rounded-lg border border-[#1C2937] bg-[#070B12]/85 p-0.5 backdrop-blur-md shadow-lg">
            <button
              type="button"
              onClick={() => setViewMode("both")}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                viewMode === "both"
                  ? "bg-[#0A7A74] text-white shadow-sm"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4]"
              }`}
            >
              Dual View
            </button>
            <button
              type="button"
              onClick={() => setViewMode("heatmap")}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                viewMode === "heatmap"
                  ? "bg-[#0A7A74] text-white shadow-sm"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4]"
              }`}
            >
              Grad-CAM
            </button>
            <button
              type="button"
              onClick={() => setViewMode("contour")}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                viewMode === "contour"
                  ? "bg-[#0A7A74] text-white shadow-sm"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4]"
              }`}
            >
              Contours
            </button>
            <button
              type="button"
              onClick={() => setViewMode("raw")}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                viewMode === "raw"
                  ? "bg-[#0A7A74] text-white shadow-sm"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4]"
              }`}
            >
              Raw CXR
            </button>
          </div>

          {/* Negative Invert & Zoom Reset */}
          <div className="inline-flex items-center gap-1">
            <button
              type="button"
              onClick={() => setInverted((v) => !v)}
              className={`px-2.5 py-1 rounded-lg border text-[11px] font-medium backdrop-blur-md transition-all ${
                inverted
                  ? "bg-slate-700 text-white border-slate-500"
                  : "bg-[#070B12]/85 border-[#1C2937] text-[#8C9DB0] hover:text-[#E6EDF4]"
              }`}
              title="Toggle Negative Film Inversion"
            >
              Negative
            </button>
            <button
              type="button"
              onClick={() => setZoom((z) => (z === 1 ? 1.5 : 1))}
              className={`px-2.5 py-1 rounded-lg border text-[11px] font-medium backdrop-blur-md transition-all ${
                zoom > 1
                  ? "bg-[#0A7A74] text-white border-[#3FD0C4]"
                  : "bg-[#070B12]/85 border-[#1C2937] text-[#8C9DB0] hover:text-[#E6EDF4]"
              }`}
              title="Toggle Zoom 1.5x"
            >
              {zoom > 1 ? "1.5×" : "1.0×"}
            </button>
          </div>
        </div>
      )}

      {/* OOD Fail-Safe Lockout Overlay */}
      {isRejected && (
        <div className="absolute inset-0 bg-[#070B12]/92 backdrop-blur-md z-35 flex flex-col items-center justify-center p-6 text-center text-rose-300">
          <div className="w-12 h-12 rounded-full bg-rose-950/80 border border-rose-600/80 flex items-center justify-center mb-3 text-rose-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold uppercase tracking-wider text-rose-200">
            Fail-Safe OOD Lockout Triggered
          </h3>
          <p className="text-xs text-rose-300/80 max-w-md mt-1.5 leading-relaxed">
            Extreme image degradation, inverted contrast, or non-thoracic radiograph detected.
            Automated diagnostic prediction withheld to prevent clinical misinterpretation.
          </p>
        </div>
      )}
    </div>
  );
}
