"use client";

import React from "react";

interface NavigationDotsProps {
  activeSection: number;
  sectionNames: string[];
  onSelectSection: (index: number) => void;
}

const ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII"];

export function NavigationDots({
  activeSection,
  sectionNames,
  onSelectSection,
}: NavigationDotsProps) {
  return (
    <nav
      aria-label="Horizontal Academic Chapter Navigation"
      className="sticky top-11 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 py-2 px-4 shadow-xs"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-1.5 sm:gap-3 flex-wrap">
        {sectionNames.map((name, index) => {
          const isActive = activeSection === index;
          const roman = ROMAN_NUMERALS[index] || `${index + 1}`;

          return (
            <button
              key={index}
              type="button"
              onClick={() => onSelectSection(index)}
              aria-label={`Jump to Chapter ${roman}: ${name}`}
              className={`inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs transition-all duration-150 ${
                isActive
                  ? "bg-[#0F172A] text-white font-bold shadow-sm ring-1 ring-slate-400"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900 border border-slate-200 font-medium"
              }`}
            >
              <span className="font-serif font-bold text-[11px]">{roman}</span>
              <span className="hidden sm:inline text-[11px] font-sans truncate max-w-[120px]">
                {name}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
