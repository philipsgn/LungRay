"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ShieldAlert, ShieldCheck, AlertTriangle, Crosshair } from "lucide-react";
import { useLungRayLanguage, translations } from "../lib/i18n";
import { LesionMetadata } from "../types";

interface HeatmapViewerProps {
  original: string | null;
  heatmap: string | null;
  contour?: string | null;
  lesions?: LesionMetadata[];
  lesionAreaRatio?: number;
  camResolution?: string;
  alpha: number;
  diseaseName?: string;
  isGrounded?: boolean;
  inLungRatio?: number | null;
  isExplaining?: boolean;
  isRejected?: boolean;
  isTargetPositive?: boolean;
}

export default function HeatmapViewer({
  original,
  heatmap,
  contour,
  lesions,
  lesionAreaRatio,
  camResolution,
  alpha,
  diseaseName,
  isGrounded = true,
  inLungRatio,
  isExplaining = false,
  isRejected = false,
  isTargetPositive = true,
}: HeatmapViewerProps) {
  const [lang] = useLungRayLanguage();
  const t = translations[lang];

  // Visualizer display mode: "both" | "heatmap" | "contour" | "raw"
  const [viewMode, setViewMode] = useState<"both" | "heatmap" | "contour" | "raw">("both");

  return (
    <div
      className={`relative w-full aspect-square bg-[#05080E] rounded-xl overflow-hidden border shadow-2xl transition-all duration-200 select-none ${
        isRejected ? "border-rose-600 ring-2 ring-rose-600/40" : "border-slate-800"
      }`}
    >
      {/* Background X-ray */}
      {original ? (
        <Image
          src={original}
          alt="Chest Radiograph"
          fill
          className="object-contain"
          priority
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600 gap-2 font-mono">
          <svg className="w-12 h-12 stroke-current opacity-30" viewBox="0 0 24 24" fill="none" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
          </svg>
          <span className="text-xs tracking-wider uppercase font-semibold text-slate-400">
            {t.noImageTitle}
          </span>
          <span className="text-[10px] text-slate-600">
            {t.noImageSubtitle}
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
          style={{ opacity: alpha / 100, mixBlendMode: "screen" }}
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
          style={{ mixBlendMode: "lighten" }}
          priority
        />
      )}

      {/* Medical Scanning Reticle / Crosshair (Subtle Clinical Markers) */}
      {original && (
        <div className="absolute inset-0 pointer-events-none opacity-20 z-10">
          {/* Center Crosshair */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8">
            <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-cyan-400" />
            <div className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-cyan-400" />
          </div>
          {/* Corner Brackets */}
          <div className="absolute top-4 left-4 w-4 h-4 border-t border-l border-slate-500" />
          <div className="absolute top-4 right-4 w-4 h-4 border-t border-r border-slate-500" />
          <div className="absolute bottom-4 left-4 w-4 h-4 border-b border-l border-slate-500" />
          <div className="absolute bottom-4 right-4 w-4 h-4 border-b border-r border-slate-500" />
        </div>
      )}

      {/* Medical Laser Scanning Sweep Beam (When Analyzing / Explaining) */}
      {isExplaining && (
        <div className="absolute inset-0 pointer-events-none z-25 overflow-hidden">
          <div className="w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-pulse"
               style={{
                 animation: "scanLine 1.4s ease-in-out infinite",
               }}
          />
          <style jsx>{`
            @keyframes scanLine {
              0% { transform: translateY(0%); opacity: 0.1; }
              15% { opacity: 0.9; }
              85% { opacity: 0.9; }
              100% { transform: translateY(500px); opacity: 0.1; }
            }
          `}</style>
        </div>
      )}

      {/* DICOM PACS Viewport HUD Overlays */}
      {original && (
        <>
          {/* Top-Left: Patient & Acquisition Telemetry */}
          <div className="absolute top-2.5 left-3 text-[10px] font-mono text-slate-400 select-none pointer-events-none drop-shadow space-y-0.5 z-10">
            <div className="font-bold text-slate-200">{t.patientAnon}</div>
            <div>{t.seriesPA}</div>
            <div>{t.matrix512}</div>
          </div>

          {/* Top-Right: Anatomical Right Marker (Patient Right is Viewer Left in Radiography) & Dual View Controls */}
          <div className="absolute top-2.5 right-3 flex items-center gap-2 z-20">
            {original && !isRejected && (heatmap || contour) && (
              <div className="inline-flex rounded-lg border border-slate-800 bg-slate-950/90 p-0.5 text-[10px] font-mono shadow-md backdrop-blur-md">
                <button
                  type="button"
                  onClick={() => setViewMode("both")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    viewMode === "both"
                      ? "bg-slate-800 text-cyan-300 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t.dualViewBoth}
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("heatmap")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    viewMode === "heatmap"
                      ? "bg-slate-800 text-cyan-300 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t.dualViewHeatmap}
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("contour")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    viewMode === "contour"
                      ? "bg-slate-800 text-cyan-300 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t.dualViewContour}
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("raw")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    viewMode === "raw"
                      ? "bg-slate-800 text-cyan-300 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t.dualViewRaw}
                </button>
              </div>
            )}
            <div className="text-sm font-bold text-slate-300 px-2 py-0.5 rounded bg-slate-900/80 border border-slate-700 pointer-events-none select-none">
              L
            </div>
          </div>

          {/* Left-Center: Patient Right Marker */}
          <div className="absolute top-1/2 left-3 -translate-y-1/2 text-sm font-bold text-slate-300 px-2 py-0.5 rounded bg-slate-900/80 border border-slate-700 select-none pointer-events-none z-10">
            R
          </div>

          {/* Lesion Telemetry HUD */}
          {original && !isRejected && lesions && lesions.length > 0 && (viewMode === "both" || viewMode === "contour") && (
            <div className="absolute bottom-11 left-3 bg-slate-950/90 backdrop-blur-md border border-cyan-800/80 rounded-md px-2.5 py-1 text-[10px] font-mono text-slate-300 flex items-center gap-2 shadow z-10 pointer-events-none">
              <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
              <span>
                <strong className="text-cyan-300">{lesions.length}</strong> {t.lesionFoci}
              </span>
              <span className="text-slate-600">|</span>
              <span>
                {((lesionAreaRatio ?? 0) * 100).toFixed(1)}% {lang === "vi" ? "phế trường" : "lung area"}
              </span>
              {camResolution && (
                <>
                  <span className="text-slate-600">|</span>
                  <span className="text-cyan-400/80 text-[9px] font-bold">{camResolution}</span>
                </>
              )}
            </div>
          )}

          {/* Bottom-Left: Window Level / Window Width HUD */}
          <div className="absolute bottom-2.5 left-3 text-[10px] font-mono text-slate-400 select-none pointer-events-none drop-shadow space-y-0.5 z-10">
            <div className="text-slate-300">{t.windowLung}</div>
            <div>{t.gsdfCalibrated}</div>
          </div>

          {/* Bottom-Right: 5cm Physical Scale Bar */}
          <div className="absolute bottom-2.5 right-3 text-[10px] font-mono text-slate-400 select-none pointer-events-none drop-shadow flex flex-col items-end z-10">
            <div className="w-16 h-1 border-b-2 border-l-2 border-r-2 border-slate-300 mb-0.5" />
            <span className="text-[9px] text-slate-300">{t.scale5cm}</span>
          </div>

          {/* Top Floating Target & Grounding Badges */}
          <div className="absolute top-11 inset-x-3 flex flex-col gap-1.5 pointer-events-none z-10">
            <div className="flex items-center justify-between">
              {diseaseName && !isRejected && (
                <div className="bg-slate-950/80 backdrop-blur-md border border-slate-700 px-2.5 py-1 rounded text-[11px] font-mono font-semibold text-slate-200 flex items-center gap-1.5 shadow">
                  <span className={`w-1.5 h-1.5 rounded-full ${isTargetPositive ? "bg-cyan-400" : "bg-amber-400"}`} />
                  {t.targetPrefix} <span className={isTargetPositive ? "text-cyan-300 font-bold" : "text-amber-300 font-bold"}>{diseaseName}</span>
                  {!isTargetPositive && (
                    <span className="text-[9px] px-1 py-0.2 rounded bg-amber-900/60 text-amber-200 border border-amber-700/60 font-sans ml-1">
                      {lang === "vi" ? "ÂM TÍNH" : "NEGATIVE"}
                    </span>
                  )}
                </div>
              )}

              {inLungRatio !== undefined && inLungRatio !== null && !isRejected && (
                <div
                  className={`px-2.5 py-1 rounded text-[11px] font-mono font-semibold flex items-center gap-1.5 shadow backdrop-blur-md border ${
                    inLungRatio < 0.80
                      ? "bg-rose-950/80 border-rose-600/80 text-rose-200"
                      : isGrounded
                      ? "bg-slate-950/80 border-slate-700 text-slate-200"
                      : "bg-slate-950/80 border-slate-700 text-slate-400"
                  }`}
                >
                  {inLungRatio < 0.80 ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  ) : isGrounded ? (
                    <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                  ) : (
                    <ShieldAlert className="w-3.5 h-3.5 text-slate-500" />
                  )}
                  <span>{inLungRatio < 0.80 ? t.auditFailBadge : isGrounded ? t.auditPassBadge : t.unmaskedBadge}</span>
                  <span className="opacity-80">({(inLungRatio * 100).toFixed(1)}% {t.inLungEnergy})</span>
                </div>
              )}
            </div>

            {/* If target is clinically negative, alert user that heatmap is model baseline audit */}
            {!isTargetPositive && !isRejected && (
              <div className="bg-amber-950/90 border border-amber-700/80 text-amber-200 text-[10px] px-2.5 py-1 rounded shadow backdrop-blur-md font-sans">
                ⚠️ {t.negativeTargetNotice}
              </div>
            )}
          </div>
        </>
      )}

      {/* Fail-Safe OOD Lockout Center Watermark */}
      {isRejected && (
        <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-sm flex flex-col items-center justify-center text-center p-6 z-20 pointer-events-none">
          <div className="px-4 py-2 rounded bg-rose-950/90 border-2 border-rose-600 text-rose-300 font-mono text-xs md:text-sm font-bold tracking-widest shadow-2xl mb-2 uppercase">
            {t.oodLockoutTitle}
          </div>
          <p className="text-xs text-rose-200/90 max-w-sm font-mono leading-relaxed">
            {t.oodLockoutDesc}
          </p>
        </div>
      )}

      {/* Subtle Bottom Processing Pill */}
      {isExplaining && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-slate-900/90 border border-slate-700 px-3 py-1 rounded-full text-[10px] font-mono text-cyan-300 flex items-center gap-2 shadow-lg z-20">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          {t.extractingCam}
        </div>
      )}
    </div>
  );
}
