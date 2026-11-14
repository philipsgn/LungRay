"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useLungRayLanguage, translations } from "../lib/i18n";
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  FolderOpen,
  ChevronDown,
  Layers,
  Sparkles,
  Info,
} from "lucide-react";

interface DimensionWarning {
  width: number;
  height: number;
  ratio: number;
  isSmall: boolean;
  isRatioDeviant: boolean;
}

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  hasFile?: boolean;
}

export default function UploadDropzone({
  onFileSelect,
  disabled = false,
  hasFile = false,
}: UploadDropzoneProps) {
  const [lang] = useLungRayLanguage();
  const t = translations[lang];

  const [isDragging, setIsDragging] = useState(false);
  const [showDrawer, setShowDrawer] = useState(!hasFile);
  const [showPresetsMenu, setShowPresetsMenu] = useState(false);
  const [loadingPreset, setLoadingPreset] = useState<string | null>(null);
  const [dimWarning, setDimWarning] = useState<DimensionWarning | null>(null);

  const presetsMenuRef = useRef<HTMLDivElement>(null);

  // Close presets menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        presetsMenuRef.current &&
        !presetsMenuRef.current.contains(event.target as Node)
      ) {
        setShowPresetsMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const inspectAndSelectFile = useCallback(
    (file: File) => {
      setDimWarning(null);

      // Pre-check dimension on image formats
      if (file.type.startsWith("image/") || file.name.match(/\.(png|jpe?g|webp)$/i)) {
        const objectUrl = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => {
          const w = img.naturalWidth;
          const h = img.naturalHeight;
          URL.revokeObjectURL(objectUrl);

          const isSmall = w < 256 || h < 256;
          const ratio = h > 0 ? Number((w / h).toFixed(2)) : 1.0;
          const isRatioDeviant = ratio > 2.0 || ratio < 0.5;

          if (isSmall || isRatioDeviant) {
            setDimWarning({
              width: w,
              height: h,
              ratio,
              isSmall,
              isRatioDeviant,
            });
          }
        };
        img.onerror = () => {
          URL.revokeObjectURL(objectUrl);
        };
        img.src = objectUrl;
      }

      onFileSelect(file);
      setShowDrawer(false); // Auto-collapse drawer once an image is ingested
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files?.[0];
      if (droppedFile) {
        inspectAndSelectFile(droppedFile);
      }
    },
    [inspectAndSelectFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        inspectAndSelectFile(selectedFile);
      }
      e.target.value = ""; // Reset input so same file can be reloaded
    },
    [inspectAndSelectFile]
  );

  const handleLoadPreset = async (fileName: string) => {
    if (disabled || loadingPreset) return;
    try {
      setLoadingPreset(fileName);
      setDimWarning(null);
      const res = await fetch(`/demo_samples/${fileName}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const file = new File([blob], fileName, { type: "image/png" });
      onFileSelect(file);
      setShowPresetsMenu(false);
      setShowDrawer(false); // Collapse drawer when preset is chosen
    } catch (err) {
      console.error("Failed to load preset sample:", err);
    } finally {
      setLoadingPreset(null);
    }
  };

  return (
    <div className="space-y-2 font-sans">
      {/* Slim PACS Workstation Ingestion Toolbar */}
      <div className="bg-[#070B12] border border-slate-800 rounded-xl p-2 px-3 flex flex-wrap items-center justify-between gap-2 shadow-sm">
        {/* Left: Quick Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Primary Action: Browse CXR File */}
          <label
            className={`inline-flex items-center gap-1.5 cursor-pointer rounded-lg bg-slate-900 border border-cyan-500/40 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-slate-850 hover:text-white transition-all shadow-sm ${
              disabled ? "opacity-50 pointer-events-none" : ""
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>{t.browseBtn}</span>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.dcm,image/png,image/jpeg,image/jpg"
              className="hidden"
              onChange={handleChange}
              disabled={disabled}
            />
          </label>

          {/* Clinical Presets Dropdown Menu */}
          <div className="relative" ref={presetsMenuRef}>
            <button
              type="button"
              onClick={() => setShowPresetsMenu((prev) => !prev)}
              disabled={disabled || Boolean(loadingPreset)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 border border-slate-750 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 hover:text-white transition-all disabled:opacity-50"
            >
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>{t.presetsMenuBtn}</span>
              <ChevronDown
                className={`w-3.5 h-3.5 text-slate-400 transition-transform ${
                  showPresetsMenu ? "rotate-180" : ""
                }`}
              />
            </button>

            {/* Presets Popover Dropdown */}
            {showPresetsMenu && (
              <div className="absolute top-full left-0 mt-1.5 w-80 bg-[#0A0F1D] border border-slate-700 rounded-xl p-2.5 shadow-2xl z-50 animate-in fade-in slide-in-from-top-1">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                  <span>{t.presetsMenuTitle}</span>
                  <button
                    type="button"
                    onClick={() => setShowPresetsMenu(false)}
                    className="text-slate-500 hover:text-slate-300"
                  >
                    {t.presetsMenuClose}
                  </button>
                </div>

                <div className="space-y-1.5">
                  {/* Preset 1: Normal CXR */}
                  <button
                    type="button"
                    onClick={() => handleLoadPreset("01_normal_cxr.png")}
                    disabled={disabled || Boolean(loadingPreset)}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between group"
                  >
                    <div>
                      <div className="text-[11px] font-bold text-slate-200 group-hover:text-cyan-300">
                        {t.presets.normal.name}
                      </div>
                      <div className="text-[9px] text-slate-500 line-clamp-1">
                        {t.presets.normal.desc}
                      </div>
                    </div>
                    <CheckCircle2 className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 shrink-0 ml-2" />
                  </button>

                  {/* Preset 2: Effusion & Cardio */}
                  <button
                    type="button"
                    onClick={() => handleLoadPreset("02_effusion_cardiomegaly.png")}
                    disabled={disabled || Boolean(loadingPreset)}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between group"
                  >
                    <div>
                      <div className="text-[11px] font-bold text-slate-200 group-hover:text-cyan-300">
                        {t.presets.effusion.name}
                      </div>
                      <div className="text-[9px] text-slate-500 line-clamp-1">
                        {t.presets.effusion.desc}
                      </div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 shrink-0 ml-2">
                      Head A
                    </span>
                  </button>

                  {/* Preset 3: Active TB */}
                  <button
                    type="button"
                    onClick={() => handleLoadPreset("03_active_tuberculosis.png")}
                    disabled={disabled || Boolean(loadingPreset)}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between group"
                  >
                    <div>
                      <div className="text-[11px] font-bold text-slate-200 group-hover:text-cyan-300">
                        {t.presets.tb.name}
                      </div>
                      <div className="text-[9px] text-slate-500 line-clamp-1">
                        {t.presets.tb.desc}
                      </div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 shrink-0 ml-2">
                      Head B
                    </span>
                  </button>

                  {/* Preset 4: OOD Anomaly */}
                  <button
                    type="button"
                    onClick={() => handleLoadPreset("04_ood_anomaly_synthetic.png")}
                    disabled={disabled || Boolean(loadingPreset)}
                    className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-rose-900/60 transition flex items-center justify-between group"
                  >
                    <div>
                      <div className="text-[11px] font-bold text-slate-200 group-hover:text-rose-400">
                        {t.presets.ood.name}
                      </div>
                      <div className="text-[9px] text-slate-500 line-clamp-1">
                        {t.presets.ood.desc}
                      </div>
                    </div>
                    <AlertTriangle className="w-3.5 h-3.5 text-slate-500 group-hover:text-rose-400 shrink-0 ml-2" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Drawer On/Off Toggle & Ingestion Status */}
        <div className="flex items-center gap-2">
          {loadingPreset && (
            <span className="text-[10px] text-cyan-300 flex items-center gap-1 animate-pulse">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              {t.loadingSample}
            </span>
          )}

          <button
            type="button"
            onClick={() => setShowDrawer((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs transition-colors ${
              showDrawer
                ? "bg-slate-800 text-cyan-300 border-cyan-500/50"
                : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850"
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>{t.toggleDropzoneBtn}</span>
            <span
              className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase ${
                showDrawer
                  ? "bg-cyan-950 text-cyan-400 border border-cyan-800"
                  : "bg-slate-950 text-slate-500"
              }`}
            >
              {showDrawer ? "ON" : "OFF"}
            </span>
          </button>
        </div>
      </div>

      {/* Soft Pre-Validation Dimension Warning Banner */}
      {dimWarning && (
        <div className="bg-amber-950/40 border border-amber-600/60 rounded-xl p-3 px-3.5 flex items-start gap-2.5 text-xs text-amber-200 animate-in fade-in slide-in-from-top-1 shadow-sm">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="font-bold text-amber-300">
                {t.dimWarningTitle} {dimWarning.width} × {dimWarning.height} px (Tỷ lệ {dimWarning.ratio}:1)
              </span>
              <button
                type="button"
                onClick={() => setDimWarning(null)}
                className="text-[10px] text-amber-400/80 hover:text-amber-200 uppercase font-semibold"
              >
                ✕ Đóng
              </button>
            </div>
            <div className="text-[11px] text-amber-200/90 space-y-0.5 leading-relaxed">
              {dimWarning.isSmall && (
                <div>
                  • {t.dimWarningSmall.replace("{width}", String(dimWarning.width)).replace("{height}", String(dimWarning.height))}
                </div>
              )}
              {dimWarning.isRatioDeviant && (
                <div>
                  • {t.dimWarningRatio.replace("{ratio}", String(dimWarning.ratio))}
                </div>
              )}
              <div className="mt-1 font-medium text-amber-100 flex items-center gap-1">
                <Info className="w-3 h-3 text-amber-400 shrink-0" />
                <span>{t.dimWarningAdvice}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Collapsible Drag & Drop Ingestion Drawer */}
      {showDrawer && (
        <div
          className={`border-2 border-dashed rounded-xl p-4 text-center bg-[#070B12]/90 backdrop-blur-sm transition-all duration-150 animate-in fade-in slide-in-from-top-2 ${
            isDragging
              ? "border-cyan-400 bg-cyan-950/20"
              : "border-slate-800 hover:border-slate-700"
          } ${disabled ? "opacity-60 pointer-events-none" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center justify-center gap-1">
            <UploadCloud className="w-6 h-6 text-slate-500 stroke-[1.5]" />
            <p className="text-xs text-slate-200 font-semibold uppercase tracking-wider">
              {t.dragPrompt}
            </p>
            <p className="text-[10px] text-slate-500 max-w-md">
              {t.formatsText}
            </p>
          </div>

          {/* CXR Technical Standards & Dimension Guidelines */}
          <div className="mt-3.5 pt-3 border-t border-slate-800/80 text-left">
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-2">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.guidelinesTitle}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-lg p-2.5 shadow-sm">
                <div className="text-[10px] font-bold text-cyan-300 uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                  <span>1. Độ phân giải</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1 leading-snug font-normal">{t.guideDimensions}</div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-lg p-2.5 shadow-sm">
                <div className="text-[10px] font-bold text-emerald-300 uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  <span>2. Tỷ lệ khung hình</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1 leading-snug font-normal">{t.guideRatio}</div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-lg p-2.5 shadow-sm">
                <div className="text-[10px] font-bold text-amber-300 uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                  <span>3. Tư thế chiếu chụp</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1 leading-snug font-normal">{t.guideProjection}</div>
              </div>
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-lg p-2.5 shadow-sm">
                <div className="text-[10px] font-bold text-purple-300 uppercase flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                  <span>4. Mẹo tránh OOD</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1 leading-snug font-normal">{t.guideOodTip}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
