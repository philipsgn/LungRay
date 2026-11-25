"use client";

import React, { useRef, useState } from "react";
import Image from "next/image";
import { cardiothoracicRatio } from "../lib/pacsUtils";
import { ShieldAlert, ShieldCheck, AlertTriangle, Ruler, Columns, SunMedium, RotateCcw } from "lucide-react";

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
  isUnavailable?: boolean;
  onCtrMeasured?: (ctr: number) => void;
}

type WindowPreset = "default" | "lung" | "mediastinal" | "bone";

const WL_PRESETS: Record<WindowPreset, { label: string; brightness: number; contrast: number }> = {
  default: { label: "Default", brightness: 100, contrast: 100 },
  lung: { label: "Lung", brightness: 108, contrast: 138 },
  mediastinal: { label: "Mediastinal", brightness: 92, contrast: 165 },
  bone: { label: "Bone", brightness: 96, contrast: 122 },
};

interface LineSegment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
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
  isUnavailable = false,
  onCtrMeasured,
}: HeatmapViewerProps) {
  const [viewMode, setViewMode] = useState<"both" | "heatmap" | "contour" | "raw">("both");
  const [splitView, setSplitView] = useState(false);
  const [inverted, setInverted] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [wlPreset, setWlPreset] = useState<WindowPreset>("default");
  const [showWlBar, setShowWlBar] = useState(false);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);

  // CTR Caliper State (two horizontal lines: Cardiac A, Thoracic B)
  const [ctrActive, setCtrActive] = useState(false);
  const [cardiacLine, setCardiacLine] = useState<LineSegment | null>(null);
  const [thoracicLine, setThoracicLine] = useState<LineSegment | null>(null);
  const [drawingLine, setDrawingLine] = useState<LineSegment | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const applyWlPreset = (preset: WindowPreset) => {
    setWlPreset(preset);
    setBrightness(WL_PRESETS[preset].brightness);
    setContrast(WL_PRESETS[preset].contrast);
  };

  const resetViewport = () => {
    setInverted(false);
    setZoom(1);
    applyWlPreset("default");
    setSplitView(false);
    setCardiacLine(null);
    setThoracicLine(null);
    setDrawingLine(null);
  };

  const getRelCoords = (e: React.MouseEvent) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const rect = containerRef.current.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100)),
      y: Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100)),
    };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!ctrActive || !original) return;
    const pt = getRelCoords(e);
    setDrawingLine({ x1: pt.x, y1: pt.y, x2: pt.x, y2: pt.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ctrActive || !drawingLine) return;
    const pt = getRelCoords(e);
    setDrawingLine({ ...drawingLine, x2: pt.x, y2: drawingLine.y1 });
  };

  const handleMouseUp = () => {
    if (!ctrActive || !drawingLine) return;
    const len = Math.abs(drawingLine.x2 - drawingLine.x1);
    if (len < 2) {
      setDrawingLine(null);
      return;
    }
    if (!cardiacLine) {
      setCardiacLine(drawingLine);
    } else if (!thoracicLine) {
      setThoracicLine(drawingLine);
      const cLen = Math.abs(cardiacLine.x2 - cardiacLine.x1);
      const tLen = len;
      if (tLen > 0 && onCtrMeasured) {
        onCtrMeasured(Number(cardiothoracicRatio(cLen, tLen).toFixed(3)));
      }
    } else {
      setCardiacLine(drawingLine);
      setThoracicLine(null);
    }
    setDrawingLine(null);
  };

  const ctrValue =
    cardiacLine && thoracicLine
      ? cardiothoracicRatio(cardiacLine.x2 - cardiacLine.x1, thoracicLine.x2 - thoracicLine.x1)
      : null;

  const imgFilter = `${inverted ? "invert(1) " : ""}brightness(${brightness}%) contrast(${contrast}%)`;

  return (
    <div className="space-y-2">
      {/* Main Viewport Canvas */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => setDrawingLine(null)}
        className={`relative w-full aspect-square bg-[#05080E] rounded-xl overflow-hidden border shadow-2xl transition-all duration-200 select-none ${
          ctrActive ? "cursor-crosshair" : "cursor-default"
        } ${isRejected ? "border-rose-600 ring-2 ring-rose-600/40" : "border-[#1C2937]"}`}
      >
        {original ? (
          splitView ? (
            /* Side-by-Side Comparison View */
            <div className="absolute inset-0 grid grid-cols-2 divide-x divide-[#3FD0C4]/50">
              <div className="relative w-full h-full overflow-hidden">
                <Image
                  src={original}
                  alt="Original Radiograph"
                  fill
                  className="object-contain"
                  style={{ filter: imgFilter, transform: `scale(${zoom})` }}
                  priority
                />
                <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded bg-[#070B12]/80 border border-[#1C2937] text-[10px] font-mono text-[#CBD5E1] z-20">
                  ORIGINAL
                </span>
              </div>
              <div className="relative w-full h-full overflow-hidden">
                <Image
                  src={original}
                  alt="Localized Radiograph"
                  fill
                  className="object-contain"
                  style={{ filter: imgFilter, transform: `scale(${zoom})` }}
                  priority
                />
                {heatmap && !isRejected && (
                  <Image
                    src={heatmap}
                    alt="Grad-CAM++ Overlay"
                    fill
                    className="object-contain transition-opacity duration-150"
                    style={{ opacity: alpha / 100, mixBlendMode: heatmapHasAlpha ? "normal" : "screen", transform: `scale(${zoom})` }}
                    priority
                  />
                )}
                {contour && !isRejected && (
                  <Image
                    src={contour}
                    alt="Lesion Iso-Contour"
                    fill
                    className="object-contain pointer-events-none"
                    style={{ mixBlendMode: contourHasAlpha ? "normal" : "screen", transform: `scale(${zoom})` }}
                    priority
                  />
                )}
                <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded bg-[#0A7A74]/80 border border-[#3FD0C4]/40 text-[10px] font-mono text-white z-20">
                  GRAD-CAM++
                </span>
              </div>
            </div>
          ) : (
            /* Single Composite Viewport */
            <>
              <Image
                src={original}
                alt="Chest Radiograph"
                fill
                className="object-contain"
                style={{ filter: imgFilter, transform: `scale(${zoom})` }}
                priority
              />
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
              {contour && !isRejected && (viewMode === "both" || viewMode === "contour") && (
                <Image
                  src={contour}
                  alt="Lesion boundary contours"
                  fill
                  className="object-contain transition-opacity duration-150 pointer-events-none"
                  style={{ mixBlendMode: contourHasAlpha ? "normal" : "screen", transform: `scale(${zoom})` }}
                  priority
                />
              )}
            </>
          )
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-[#8C9DB0] gap-2 font-sans">
            <svg className="w-12 h-12 stroke-current opacity-25" viewBox="0 0 24 24" fill="none" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
            </svg>
            <span className="text-xs tracking-wider uppercase font-semibold text-[#8C9DB0]">
              No Radiograph Ingested
            </span>
            <span className="text-[11px] text-[#566475]">
              Open Worklist, browse a file, or select a clinical preset to begin
            </span>
          </div>
        )}

        {/* CTR Interactive Measurement SVG Overlay */}
        {(cardiacLine || thoracicLine || drawingLine) && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-25" viewBox="0 0 100 100" preserveAspectRatio="none">
            {cardiacLine && (
              <g>
                <line x1={cardiacLine.x1} y1={cardiacLine.y1} x2={cardiacLine.x2} y2={cardiacLine.y2} stroke="#F59E0B" strokeWidth="0.6" />
                <circle cx={cardiacLine.x1} cy={cardiacLine.y1} r="0.9" fill="#F59E0B" />
                <circle cx={cardiacLine.x2} cy={cardiacLine.y2} r="0.9" fill="#F59E0B" />
              </g>
            )}
            {thoracicLine && (
              <g>
                <line x1={thoracicLine.x1} y1={thoracicLine.y1} x2={thoracicLine.x2} y2={thoracicLine.y2} stroke="#3FD0C4" strokeWidth="0.6" />
                <circle cx={thoracicLine.x1} cy={thoracicLine.y1} r="0.9" fill="#3FD0C4" />
                <circle cx={thoracicLine.x2} cy={thoracicLine.y2} r="0.9" fill="#3FD0C4" />
              </g>
            )}
            {drawingLine && (
              <line x1={drawingLine.x1} y1={drawingLine.y1} x2={drawingLine.x2} y2={drawingLine.y2} stroke="#FFFFFF" strokeWidth="0.5" strokeDasharray="1,1" />
            )}
          </svg>
        )}

        {/* Top-Left Target Label & CTR Telemetry Badge */}
        {original && (
          <div className="absolute top-3 left-3 flex flex-col gap-1.5 z-20 pointer-events-none">
            {diseaseName && !splitView && (
              <div className="inline-flex items-center gap-2 rounded-lg border border-[#1C2937] bg-[#070B12]/80 px-2.5 py-1 text-xs font-medium text-[#E6EDF4] backdrop-blur-md">
                <span className={`h-2 w-2 rounded-full ${isExplaining ? "bg-amber-400 animate-pulse" : "bg-[#3FD0C4]"}`} />
                <span>Target: {diseaseName}</span>
              </div>
            )}
            {ctrActive && !ctrValue && (
              <div className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-950/80 px-2.5 py-1 text-[11px] font-medium text-amber-200 backdrop-blur-md">
                <Ruler className="w-3.5 h-3.5" />
                <span>{!cardiacLine ? "Step 1: Drag across widest cardiac silhouette" : "Step 2: Drag across inner thoracic width"}</span>
              </div>
            )}
            {ctrValue !== null && (
              <div className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] font-mono font-bold backdrop-blur-md ${
                ctrValue > 0.5
                  ? "border-rose-500/50 bg-rose-950/85 text-rose-200"
                  : "border-emerald-500/50 bg-emerald-950/85 text-emerald-200"
              }`}>
                <Ruler className="w-3.5 h-3.5" />
                <span>CTR: {ctrValue.toFixed(2)} ({ctrValue > 0.5 ? "Cardiomegaly > 0.50" : "Normal ≤ 0.50"})</span>
              </div>
            )}
          </div>
        )}

        {/* Top-Right In-Lung Grounding Badge */}
        {original && !isRejected && !splitView && (
          <div className="absolute top-3 right-3 flex flex-col items-end gap-1.5 z-20 pointer-events-none">
            {inLungRatio !== undefined && inLungRatio !== null && (
              <div
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] font-mono font-semibold backdrop-blur-md ${
                  isGrounded && inLungRatio >= 0.8
                    ? "border-emerald-500/40 bg-emerald-950/75 text-emerald-300"
                    : "border-amber-500/40 bg-amber-950/75 text-amber-300"
                }`}
              >
                {isGrounded && inLungRatio >= 0.8 ? (
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
          <div
            onMouseDown={(e) => e.stopPropagation()}
            onMouseMove={(e) => e.stopPropagation()}
            onMouseUp={(e) => e.stopPropagation()}
            className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 z-30 pointer-events-auto"
          >
            {/* Layer View Mode Switcher */}
            <div className="inline-flex rounded-lg border border-[#1C2937] bg-[#070B12]/90 p-0.5 backdrop-blur-md shadow-lg">
              {(["both", "heatmap", "contour", "raw"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => { setViewMode(m); setSplitView(false); }}
                  className={`px-2 py-1 rounded text-[11px] font-medium transition-all ${
                    !splitView && viewMode === m
                      ? "bg-[#0A7A74] text-white shadow-sm"
                      : "text-[#8C9DB0] hover:text-[#E6EDF4]"
                  }`}
                >
                  {m === "both" ? "Dual" : m === "heatmap" ? "Grad-CAM++" : m === "contour" ? "Contours" : "Raw"}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setSplitView((v) => !v)}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium transition-all ${
                  splitView
                    ? "bg-[#0A7A74] text-white shadow-sm"
                    : "text-[#8C9DB0] hover:text-[#E6EDF4]"
                }`}
                title="Side-by-Side Comparison View"
              >
                <Columns className="w-3 h-3" />
                Split
              </button>
            </div>

            {/* Radiologist Tools: W/L, CTR Ruler, Negative, Zoom, Reset */}
            <div className="inline-flex items-center gap-1">
              <button
                type="button"
                onClick={() => setShowWlBar((v) => !v)}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg border text-[11px] font-medium backdrop-blur-md transition-all ${
                  showWlBar || wlPreset !== "default"
                    ? "bg-[#0A7A74] text-white border-[#3FD0C4]"
                    : "bg-[#070B12]/90 border-[#1C2937] text-[#8C9DB0] hover:text-[#E6EDF4]"
                }`}
                title="Window / Level Presets"
              >
                <SunMedium className="w-3 h-3" />
                W/L
              </button>
              <button
                type="button"
                onClick={() => setCtrActive((v) => !v)}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg border text-[11px] font-medium backdrop-blur-md transition-all ${
                  ctrActive
                    ? "bg-amber-600 text-white border-amber-400"
                    : "bg-[#070B12]/90 border-[#1C2937] text-[#8C9DB0] hover:text-[#E6EDF4]"
                }`}
                title="Measure Cardiothoracic Ratio (CTR)"
              >
                <Ruler className="w-3 h-3" />
                CTR
              </button>
              <button
                type="button"
                onClick={() => setInverted((v) => !v)}
                className={`px-2 py-1 rounded-lg border text-[11px] font-medium backdrop-blur-md transition-all ${
                  inverted
                    ? "bg-slate-700 text-white border-slate-500"
                    : "bg-[#070B12]/90 border-[#1C2937] text-[#8C9DB0] hover:text-[#E6EDF4]"
                }`}
                title="Toggle Negative Film Inversion"
              >
                Inv
              </button>
              <button
                type="button"
                onClick={() => setZoom((z) => (z === 1 ? 1.5 : z === 1.5 ? 2.0 : 1))}
                className={`px-2 py-1 rounded-lg border text-[11px] font-medium backdrop-blur-md transition-all ${
                  zoom > 1
                    ? "bg-[#0A7A74] text-white border-[#3FD0C4]"
                    : "bg-[#070B12]/90 border-[#1C2937] text-[#8C9DB0] hover:text-[#E6EDF4]"
                }`}
                title="Cycle Zoom (1.0x / 1.5x / 2.0x)"
              >
                {zoom.toFixed(1)}×
              </button>
              <button
                type="button"
                onClick={resetViewport}
                className="p-1.5 rounded-lg border bg-[#070B12]/90 border-[#1C2937] text-[#8C9DB0] hover:text-white transition-all"
                title="Reset Viewport & Calipers"
              >
                <RotateCcw className="w-3 h-3" />
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
              {isUnavailable ? "Analysis unavailable" : "Fail-Safe OOD Lockout Triggered"}
            </h3>
            <p className="text-xs text-rose-300/80 max-w-md mt-1.5 leading-relaxed">
              {isUnavailable ? "The inference server could not be reached. No diagnostic analysis was performed. Reconnect and retry." : "Input rejected by the safety policy. Automated interpretation is blocked; verify the original image and review the reported rejection reasons."}
            </p>
          </div>
        )}
      </div>

      {/* Collapsible Window / Level Adjustment Bar */}
      {original && showWlBar && (
        <div className="rounded-xl border border-[#1C2937] bg-[#0D1520] p-3 space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8C9DB0]">
              Window / Level Presets
            </span>
            <div className="flex items-center gap-1.5">
              {(Object.keys(WL_PRESETS) as WindowPreset[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => applyWlPreset(key)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors ${
                    wlPreset === key
                      ? "bg-[#3FD0C4] text-[#05080E]"
                      : "bg-[#111C2B] text-[#8C9DB0] hover:text-[#E6EDF4]"
                  }`}
                >
                  {WL_PRESETS[key].label}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <label className="flex items-center gap-2 text-[11px] text-[#8C9DB0]">
              <span className="w-16">Brightness</span>
              <input
                type="range"
                min={50}
                max={170}
                value={brightness}
                onChange={(e) => setBrightness(Number(e.target.value))}
                className="flex-1 accent-[#3FD0C4]"
              />
              <span className="w-9 text-right font-mono text-[#E6EDF4]">{brightness}%</span>
            </label>
            <label className="flex items-center gap-2 text-[11px] text-[#8C9DB0]">
              <span className="w-16">Contrast</span>
              <input
                type="range"
                min={60}
                max={220}
                value={contrast}
                onChange={(e) => setContrast(Number(e.target.value))}
                className="flex-1 accent-[#3FD0C4]"
              />
              <span className="w-9 text-right font-mono text-[#E6EDF4]">{contrast}%</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}
