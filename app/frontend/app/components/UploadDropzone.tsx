"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  UploadCloud,
  AlertTriangle,
  FolderOpen,
  ChevronDown,
  Layers,
  Sparkles,
  FileCheck,
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
  activeFileName?: string;
}

const PRESETS = [
  {
    id: "01_normal_cxr.png",
    name: "Normal Control",
    desc: "Clear parenchyma, sharp costophrenic angles, normal cardiac silhouette.",
    badge: "Normal",
    badgeColor: "text-emerald-400 bg-emerald-950/60 border-emerald-800",
  },
  {
    id: "02_effusion_cardiomegaly.png",
    name: "Effusion & Cardiomegaly",
    desc: "Bilateral fluid layering with enlarged cardiac silhouette.",
    badge: "Effusion",
    badgeColor: "text-sky-300 bg-sky-950/60 border-sky-800",
  },
  {
    id: "03_active_tuberculosis.png",
    name: "Active Tuberculosis",
    desc: "Bilateral upper-zone infiltrates and apical cavitation.",
    badge: "Active TB",
    badgeColor: "text-amber-300 bg-amber-950/60 border-amber-800",
  },
  {
    id: "04_ood_anomaly_synthetic.png",
    name: "Out-of-Distribution Noise",
    desc: "Extreme Gaussian noise / corrupt projection for safety testing.",
    badge: "OOD Noise",
    badgeColor: "text-rose-300 bg-rose-950/60 border-rose-800",
  },
];

export default function UploadDropzone({
  onFileSelect,
  disabled = false,
  hasFile = false,
  activeFileName,
}: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
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

  const inspectAndSelectFile = useCallback(
    (file: File) => {
      setDimWarning(null);

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
    },
    [onFileSelect]
  );

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
      e.target.value = "";
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
    } catch (err) {
      console.error("Failed to load preset sample:", err);
    } finally {
      setLoadingPreset(null);
    }
  };

  return (
    <div className="space-y-2 font-sans select-none">
      {/* Pre-Validation Dimension Warning */}
      {dimWarning && (
        <div className="bg-amber-950/40 border border-amber-800/80 rounded-xl p-2.5 px-3.5 text-xs text-amber-200 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Non-standard image dimensions ({dimWarning.width}×{dimWarning.height} px, aspect {dimWarning.ratio}). LungRay normalizes automatically to 512×512.
          </span>
        </div>
      )}

      {/* STATE A: A SCAN IS LOADED -> Minimalist 1-Line Status Bar */}
      {hasFile ? (
        <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-2 px-4 flex flex-wrap items-center justify-between gap-2.5 shadow-md">
          {/* Active File Info */}
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[#0A7A74]/20 border border-[#3FD0C4]/40 text-[#3FD0C4] font-medium font-mono">
              <FileCheck className="w-3.5 h-3.5" />
              <span>Loaded Scan</span>
            </span>
            <span className="text-[#E6EDF4] font-mono truncate max-w-[280px] sm:max-w-[400px]">
              {activeFileName ?? "Radiograph active"}
            </span>
          </div>

          {/* Quick Actions: Change File or Switch Preset */}
          <div className="flex items-center gap-2">
            {loadingPreset && (
              <span className="text-[11px] text-[#3FD0C4] flex items-center gap-1 animate-pulse mr-1 font-mono">
                <Sparkles className="w-3 h-3 text-[#3FD0C4]" />
                Switching case...
              </span>
            )}

            {/* Change Scan Button */}
            <label
              className={`inline-flex items-center gap-1.5 cursor-pointer rounded-lg bg-[#111C2B] border border-[#1C2937] px-2.5 py-1 text-xs font-medium text-[#8C9DB0] hover:text-[#E6EDF4] hover:border-slate-600 transition shadow-sm ${
                disabled ? "opacity-50 pointer-events-none" : ""
              }`}
            >
              <FolderOpen className="w-3.5 h-3.5" />
              <span>Change Scan</span>
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.dcm,image/png,image/jpeg,image/jpg"
                className="hidden"
                onChange={handleChange}
                disabled={disabled}
              />
            </label>

            {/* Presets Dropdown */}
            <div className="relative" ref={presetsMenuRef}>
              <button
                type="button"
                onClick={() => setShowPresetsMenu((prev) => !prev)}
                disabled={disabled || Boolean(loadingPreset)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] px-2.5 py-1 text-xs font-medium text-[#8C9DB0] hover:text-[#E6EDF4] hover:border-slate-600 transition disabled:opacity-50"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Sample Cases</span>
                <ChevronDown
                  className={`w-3 h-3 transition-transform ${
                    showPresetsMenu ? "rotate-180" : ""
                  }`}
                />
              </button>

              {/* Presets Dropdown Menu */}
              {showPresetsMenu && (
                <div className="absolute right-0 top-full mt-2 w-80 bg-[#0D1520] border border-[#1C2937] rounded-xl p-2.5 shadow-2xl z-50 animate-in fade-in slide-in-from-top-1">
                  <div className="text-[10px] text-[#8C9DB0] font-semibold uppercase tracking-wider pb-2 mb-2 border-b border-[#1C2937]">
                    Select Clinical Sample Case
                  </div>
                  <div className="space-y-1.5">
                    {PRESETS.map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => handleLoadPreset(p.id)}
                        disabled={disabled || Boolean(loadingPreset)}
                        className="w-full text-left p-2 rounded-lg bg-[#111C2B] hover:bg-[#162233] border border-[#1C2937] hover:border-[#3FD0C4]/60 transition flex items-center justify-between group"
                      >
                        <div>
                          <div className="text-xs font-semibold text-[#E6EDF4] group-hover:text-[#3FD0C4]">
                            {p.name}
                          </div>
                          <div className="text-[10px] text-[#8C9DB0] line-clamp-1 mt-0.5">
                            {p.desc}
                          </div>
                        </div>
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0 ml-2 ${p.badgeColor}`}
                        >
                          {p.badge}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* STATE B: NO SCAN LOADED -> Single Elegant Ingestion Card (Zero Duplication) */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-7 text-center transition-all duration-200 ${
            isDragging
              ? "border-[#3FD0C4] bg-[#0A7A74]/10 shadow-lg shadow-[#3FD0C4]/10"
              : "border-[#1C2937] bg-[#0D1520] hover:border-slate-600"
          }`}
        >
          {/* Main Drop Content */}
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="p-3 rounded-full bg-[#111C2B] border border-[#1C2937] text-[#3FD0C4]">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div>
              <p className="text-sm font-semibold text-[#E6EDF4]">
                Drop chest radiograph here, or choose from computer
              </p>
              <p className="text-xs text-[#8C9DB0] mt-0.5">
                Supports DICOM (.dcm), PNG, JPEG
              </p>
            </div>

            {/* Single Unified Browse Button */}
            <label
              className={`inline-flex items-center gap-1.5 cursor-pointer rounded-lg bg-[#0A7A74] hover:bg-[#0A7A74]/80 border border-[#3FD0C4]/50 px-4 py-2 text-xs font-semibold text-white transition-all shadow-md shadow-[#3FD0C4]/20 ${
                disabled ? "opacity-50 pointer-events-none" : ""
              }`}
            >
              <FolderOpen className="w-3.5 h-3.5" />
              <span>Select CXR File</span>
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.dcm,image/png,image/jpeg,image/jpg"
                className="hidden"
                onChange={handleChange}
                disabled={disabled}
              />
            </label>

            {/* Integrated Quick Sample Cases (Clickable Pills) */}
            <div className="pt-3 mt-1 border-t border-[#1C2937]/80 w-full max-w-xl">
              <p className="text-[11px] text-[#8C9DB0] uppercase tracking-wider font-semibold mb-2">
                Or test with a clinical sample case:
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2">
                {PRESETS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleLoadPreset(p.id)}
                    disabled={disabled || Boolean(loadingPreset)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] hover:border-[#3FD0C4] text-xs text-[#E6EDF4] transition disabled:opacity-50 group"
                  >
                    <span className="font-medium group-hover:text-[#3FD0C4]">{p.name}</span>
                    <span className={`text-[9px] font-mono px-1 py-0.2 rounded border ${p.badgeColor}`}>
                      {p.badge}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}