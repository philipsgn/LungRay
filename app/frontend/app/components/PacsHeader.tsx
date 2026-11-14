"use client";

import { useLungRayLanguage, translations } from "../lib/i18n";

interface PacsHeaderProps {
  selectedModel?: string;
  onSelectModel?: (model: string) => void;
  failsafeEnabled?: boolean;
  onToggleFailsafe?: (enabled: boolean) => void;
}

export default function PacsHeader({
  selectedModel = "standard",
  onSelectModel,
  failsafeEnabled = true,
  onToggleFailsafe,
}: PacsHeaderProps) {
  const [lang, setLang] = useLungRayLanguage();
  const t = translations[lang];

  return (
    <header className="bg-[#05080E] border-b border-slate-800/80 px-4 md:px-6 py-2.5 flex flex-wrap items-center justify-between sticky top-0 z-30 shadow-md">
      {/* Brand: Logo, Title & Subtitle */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700/80 flex items-center justify-center font-bold text-white text-xs tracking-wider shadow-inner">
          LR
        </div>
        <div>
          <h1 className="text-xs md:text-sm font-bold text-slate-100 tracking-wider uppercase">
            {t.headerTitle}
          </h1>
          <p className="text-[10px] text-slate-400 tracking-tight">
            {t.subTitle}
          </p>
        </div>
      </div>

      {/* Control Actions: Model Selector & Language Switcher */}
      <div className="flex items-center gap-3 text-xs mt-2 sm:mt-0">
        {/* Dual-Model Engine Selector */}
        {onSelectModel && (
          <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-md p-0.5 shadow-inner">
            <span className="text-[10px] uppercase font-bold text-slate-400 px-2 tracking-wider">
              {lang === "vi" ? "Mô hình" : "Engine"}:
            </span>
            <button
              type="button"
              onClick={() => onSelectModel("standard")}
              title="Primary Clinical CADx (SOTA AUC 0.9095, Balanced Multi-Task)"
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                selectedModel === "standard"
                  ? "bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Standard CADx
            </button>
            <button
              type="button"
              onClick={() => onSelectModel("wsol")}
              title="WSOL Specialist (Attention-Regularized Grounding, RSNA IoU 0.2454, TB AUC 0.9684)"
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                selectedModel === "wsol"
                  ? "bg-amber-950/80 text-amber-300 border border-amber-700/60 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              WSOL Specialist
            </button>
            <button
              type="button"
              onClick={() => onSelectModel("resnet50")}
              title="ResNet-50 Specialist (Deep Residual Representation, Val Score 0.9121, TB AUC 1.000, COVID AUC 0.9891)"
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                selectedModel === "resnet50"
                  ? "bg-rose-950/80 text-rose-300 border border-rose-700/60 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              ResNet-50 Specialist
            </button>
            <button
              type="button"
              onClick={() => onSelectModel("ensemble")}
              title="Consensus Ensemble (DenseNet-121 + ResNet-50 + WSOL Adaptive Soft-Voting & Inter-Model Agreement)"
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                selectedModel === "ensemble"
                  ? "bg-purple-950/80 text-purple-300 border border-purple-700/60 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Consensus Ensemble
            </button>
          </div>
        )}

        {/* Fail-Safe Safety Toggle */}
        {onToggleFailsafe && (
          <button
            type="button"
            onClick={() => onToggleFailsafe(!failsafeEnabled)}
            title={
              failsafeEnabled
                ? "Khóa an toàn OOD: ĐANG BẬT (Tự động từ chối ảnh lỗi/ngoài phân phối)"
                : "Khóa an toàn OOD: ĐÃ BỎ QUA (Chấp nhận phân tích mọi ảnh theo chỉ định bác sĩ)"
            }
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-[10px] font-bold transition-all shadow-sm ${
              failsafeEnabled
                ? "bg-cyan-950/50 text-cyan-300 border-cyan-700/60 hover:bg-cyan-900/60"
                : "bg-amber-950/60 text-amber-300 border-amber-700/70 hover:bg-amber-900/70"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                failsafeEnabled ? "bg-cyan-400 animate-pulse" : "bg-amber-400"
              }`}
            ></span>
            <span>{failsafeEnabled ? "Fail-Safe: ON" : "Fail-Safe: BYPASS"}</span>
          </button>
        )}

        {/* Clinical TTA Robustness Indicator */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 bg-emerald-950/40 border border-emerald-800/60 rounded text-[10px] text-emerald-400 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>TTA 3-Pass Active</span>
        </div>

        {/* Language Switcher Pill */}
        <div className="bg-slate-900 border border-slate-800 rounded-md p-0.5 flex items-center shadow-inner">
          <button
            type="button"
            onClick={() => setLang("vi")}
            className={`px-2.5 py-1 rounded text-[11px] font-bold transition-colors ${
              lang === "vi"
                ? "bg-slate-800 text-cyan-300 shadow-sm border border-slate-700/70"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            VI
          </button>
          <button
            type="button"
            onClick={() => setLang("en")}
            className={`px-2.5 py-1 rounded text-[11px] font-bold transition-colors ${
              lang === "en"
                ? "bg-slate-800 text-cyan-300 shadow-sm border border-slate-700/70"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            EN
          </button>
        </div>
      </div>
    </header>
  );
}
