"use client";

import React from "react";

interface NavigationDotsProps {
  activeSection: number;
  sectionNames: string[];
  onSelectSection: (index: number) => void;
}

export function NavigationDots({
  activeSection,
  sectionNames,
  onSelectSection,
}: NavigationDotsProps) {
  return (
    <nav
      aria-label="Section Navigation"
      className="fixed left-5 top-1/2 -translate-y-1/2 hidden lg:flex flex-col gap-3 z-40 bg-white/60 backdrop-blur-md p-2 rounded-full border border-slate-200/60 shadow-lg"
    >
      {sectionNames.map((name, index) => {
        const isActive = activeSection === index;
        return (
          <div key={index} className="relative group flex items-center">
            <button
              type="button"
              onClick={() => onSelectSection(index)}
              aria-label={`Jump to Section ${index + 1}: ${name}`}
              className={`w-3.5 h-3.5 rounded-full transition-all duration-300 flex items-center justify-center ${
                isActive
                  ? "bg-[#0B1E36] scale-125 ring-4 ring-sky-200"
                  : "bg-slate-300 hover:bg-slate-500 scale-100"
              }`}
            >
              {isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
              )}
            </button>
            {/* Tooltip */}
            <div className="absolute left-7 px-3 py-1 bg-[#0B1E36] text-white text-xs font-medium rounded-lg shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50">
              <span className="text-sky-300 font-mono mr-1.5">{index + 1}.</span>
              {name}
            </div>
          </div>
        );
      })}
    </nav>
  );
}
