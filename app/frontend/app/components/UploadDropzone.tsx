"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  UploadCloud,
  AlertTriangle,
  FolderOpen,
  ChevronDown,
  Layers,
  Sparkles,
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

const PRESETS = [
  {
    id: "01_normal_cxr.png",
    name: "Normal Control CXR",
    desc: "Clear parenchyma, sharp costophrenic angles, normal cardiac ratio.",
    badge: "Control",
    badgeColor: "text-emerald-400 bg-emerald-950/60 border-emerald-800",
  },
  {
    id: "02_effusion_cardiomegaly.png",
    name: "Effusion & Cardiomegaly",
    desc: "Bilateral fluid layering with enlarged cardiac silhouette.",
    badge: "Thoracic Panel",
    badgeColor: "text-sky-300 bg-sky-950/60 border-sky-800",
  },
  {
    id: "03_active_tuberculosis.png",
    name: "Active Apical Tuberculosis",
    desc: "Bilateral upper-zone infiltrates and apical cavitation.",
    badge: "TB Screening",
    badgeColor: "text-amber-300 bg-amber-950/60 border-amber-800",
  },
  {
    id: "04_ood_anomaly_synthetic.png",
    name: "Out-of-Distribution Anomaly",
    desc: "Corrupt projection / extreme noise to test Fail-Safe Gatekeeper.",
    badge: "OOD Stress",
    badgeColor: "text-rose-300 bg-rose-950/60 border-rose-800",
  },
];

export default function UploadDropzone({
  onFileSelect,
  disabled = false,
  hasFile = false,
}: UploadDropzoneProps) {
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
      setShowDrawer(false);
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
      setShowDrawer(false);
    } catch (err) {
      console.error("Failed to load preset sample:", err);
    } finally {
      setLoadingPreset(null);
    }
  };

  return (
    <div className="space-y-2.5 font-sans select-none">
      {/* PACS Workstation Ingestion Toolbar */}
      <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-2.5 px-3 flex flex-wrap items-center justify-between gap-2.5 shadow-md">
        {/* Left: Quick Ingestion Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Primary Action: Browse CXR File */}
          <label
            className={`inline-flex items-center gap-1.5 cursor-pointer rounded-lg bg-[#111C2B] border border-[#3FD0C4]/40 px-3 py-1.5 text-xs font-semibold text-[#3FD0C4] hover:bg-[#0A7A74]/20 hover:border-[#3FD0C4] transition-all shadow-sm ${
              disabled ? "opacity-50 pointer-events-none" : ""
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Browse CXR File</span>
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
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] px-3 py-1.5 text-xs font-medium text-[#E6EDF4] hover:border-slate-600 transition-all disabled:opacity-50"
            >
              <Layers className="w-3.5 h-3.5 text-[#8C9DB0]" />
              <span>Load Clinical Presets (4 Cases)</span>
              <ChevronDown
                className={`w-3.5 h-3.5 text-[#8C9DB0] transition-transform ${
                  showPresetsMenu ? "rotate-180" : ""
                }`}
              />
            </button>

            {/* Presets Popover Dropdown */}
            {showPresetsMenu && (
              <div className="absolute top-full left-0 mt-2 w-84 bg-[#0D1520] border border-[#1C2937] rounded-xl p-2.5 shadow-2xl z-50 animate-in fade-in slide-in-from-top-1">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#1C2937] text-[10px] text-[#8C9DB0] font-semibold uppercase tracking-wider">
                  <span>Standard Clinical Case Library</span>
                  <button
                    type="button"
                    onClick={() => setShowPresetsMenu(false)}
                    className="text-[#8C9DB0] hover:text-[#E6EDF4]"
                  >
                    Close
                  </button>
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

        {/* Right: Drawer On/Off Toggle & Ingestion Status */}
        <div className="flex items-center gap-2">
          {loadingPreset && (
            <span className="text-[10px] text-[#3FD0C4] flex items-center gap-1 animate-pulse">
              <Sparkles className="w-3 h-3 text-[#3FD0C4]" />
              Loading preset radiograph...
            </span>
          )}

          <button
            type="button"
            onClick={() => setShowDrawer((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs transition-colors ${
              showDrawer
                ? "bg-[#0A7A74]/30 text-[#3FD0C4] border-[#3FD0C4]/50"
                : "bg-[#111C2B] text-[#8C9DB0] border-[#1C2937] hover:text-[#E6EDF4]"
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Dropzone</span>
            <span
              className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase ${
                showDrawer
                  ? "bg-[#0A7A74] text-white"
                  : "bg-[#1C2937] text-[#8C9DB0]"
              }`}
            >
              {showDrawer ? "ON" : "OFF"}
            </span>
          </button>
        </div>
      </div>

      {/* Pre-Validation Dimension Warning Banner */}
      {dimWarning && (
        <div className="bg-amber-950/40 border border-amber-800/80 rounded-xl p-2.5 px-3.5 text-xs text-amber-200 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Non-standard image dimensions ({dimWarning.width}×{dimWarning.height} px, aspect {dimWarning.ratio}). LungRay will letterbox and normalize automatically to 512×512.
          </span>
        </div>
      )}

      {/* Collapsible Drag-and-Drop Area */}
      {showDrawer && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer ${
            isDragging
              ? "border-[#3FD0C4] bg-[#0A7A74]/10 shadow-lg shadow-[#3FD0C4]/10"
              : "border-[#1C2937] bg-[#0D1520]/60 hover:border-slate-600 hover:bg-[#0D1520]"
          }`}
        >
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.dcm,image/png,image/jpeg,image/jpg"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleChange}
            disabled={disabled}
          />
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="p-2.5 rounded-full bg-[#111C2B] border border-[#1C2937] text-[#3FD0C4]">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-[#E6EDF4]">
                Drag and drop chest radiograph (CXR) here, or click to browse
              </p>
              <p className="text-xs text-[#8C9DB0] mt-1">
                Standard DICOM (.dcm), 16-bit Grayscale, PNG, JPEG · Standardized to 512×512 input
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
