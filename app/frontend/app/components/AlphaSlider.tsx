"use client";

import { useLungRayLanguage, translations } from "../lib/i18n";

interface AlphaSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export default function AlphaSlider({ value, onChange }: AlphaSliderProps) {
  const [lang] = useLungRayLanguage();
  const t = translations[lang];

  return (
    <div className="bg-[#070B12] rounded-xl p-3 border border-slate-800 font-mono">
      <div className="flex items-center justify-between mb-1.5">
        <label htmlFor="alpha" className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
          {t.alphaLabel}
        </label>
        <span className="text-xs font-bold text-cyan-400 tabular-nums">
          {value}{t.alphaUnit}
        </span>
      </div>
      <input
        id="alpha"
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-slate-800 rounded appearance-none cursor-pointer accent-cyan-400"
      />
      <div className="flex justify-between text-[9px] text-slate-500 mt-1">
        <span>0% (Film)</span>
        <span>25%</span>
        <span className="text-slate-400 font-semibold">45% (Default)</span>
        <span>75%</span>
        <span>100% (Dense)</span>
      </div>
    </div>
  );
}
