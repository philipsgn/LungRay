"use client";

import { useLungRayLanguage, translations } from "../lib/i18n";

export default function PacsHeader() {
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

      {/* Control Actions: Language Switcher */}
      <div className="flex items-center gap-3 text-xs mt-2 sm:mt-0">
        {/* Language Switcher Pill */}
        <div className="bg-slate-900 border border-slate-800 rounded-md p-0.5 flex items-center shadow-inner">
          <button
            type="button"
            onClick={() => setLang("vi")}
            className={`px-2.5 py-0.5 rounded text-[11px] font-bold transition-colors ${
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
            className={`px-2.5 py-0.5 rounded text-[11px] font-bold transition-colors ${
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
