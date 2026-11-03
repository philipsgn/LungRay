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
} from "lucide-react";

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

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files?.[0];
      if (droppedFile) {
        onFileSelect(droppedFile);
        setShowDrawer(false); // Auto-collapse drawer once an image is ingested
      }
    },
    [onFileSelect]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        onFileSelect(selectedFile);
        setShowDrawer(false); // Auto-collapse drawer once an image is ingested
      }
      e.target.value = ""; // Reset input so same file can be reloaded
    },
    [onFileSelect]
  );

  const handleLoadPreset = async (fileName: string) => {
    if (disabled || loadingPreset) return;
    try {
      setLoadingPreset(fileName);
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
        </div>
      )}
    </div>
  );
}
