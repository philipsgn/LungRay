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
      className="fixed top-2.5 right-6 z-50 bg-white/95 border border-slate-300 shadow-sm rounded-lg p-0.5 flex items-center gap-1 font-mono text-xs"
    >
      <button
        type="button"
        onClick={() => onLanguageChange("en")}
        aria-pressed={currentLang === "en"}
        className={`px-2.5 py-1 rounded text-xs font-bold tracking-wider transition-all duration-150 ${
          currentLang === "en"
            ? "bg-[#0F172A] text-white shadow-sm"
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange("vi")}
        aria-pressed={currentLang === "vi"}
        className={`px-2.5 py-1 rounded text-xs font-bold tracking-wider transition-all duration-150 ${
          currentLang === "vi"
            ? "bg-[#0F172A] text-white shadow-sm"
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
        }`}
      >
        VI
      </button>
    </div>
  );
}
