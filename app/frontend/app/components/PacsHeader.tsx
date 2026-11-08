"use client";

import { useLungRayLanguage, translations } from "../lib/i18n";

interface PacsHeaderProps {
  selectedModel?: string;
  onSelectModel?: (model: string) => void;
}

export default function PacsHeader({
  selectedModel = "standard",
  onSelectModel,
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
