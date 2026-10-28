"use client";

import React from "react";
import { Language } from "../types";

interface LanguageSwitcherProps {
  currentLang: Language;
  onLanguageChange: (lang: Language) => void;
}

export function LanguageSwitcher({
  currentLang,
  onLanguageChange,
}: LanguageSwitcherProps) {
  return (
    <div
      aria-label="Language Switcher"
      className="fixed top-6 right-6 z-50 backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-lg rounded-full p-1.5 flex items-center gap-1 transition-all duration-200 hover:shadow-xl"
    >
      <button
        type="button"
        onClick={() => onLanguageChange("en")}
        aria-pressed={currentLang === "en"}
        className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 flex items-center gap-1.5 ${
          currentLang === "en"
            ? "bg-[#0B1E36] text-white shadow-sm"
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
        }`}
      >
        <span>🇬🇧</span>
        <span>EN</span>
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange("vi")}
        aria-pressed={currentLang === "vi"}
        className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 flex items-center gap-1.5 ${
          currentLang === "vi"
            ? "bg-[#0B1E36] text-white shadow-sm"
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
        }`}
      >
        <span>🇻🇳</span>
        <span>VI</span>
      </button>
    </div>
  );
}
