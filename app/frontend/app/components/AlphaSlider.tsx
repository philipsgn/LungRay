"use client";

import React from "react";

interface AlphaSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export default function AlphaSlider({ value, onChange }: AlphaSliderProps) {
  return (
    <div className="bg-[#0D1520] rounded-xl p-3 border border-[#1C2937] font-sans select-none shadow-md">
      <div className="flex items-center justify-between mb-1.5">
        <label
          htmlFor="alpha"
          className="text-xs font-semibold text-[#8C9DB0] uppercase tracking-wider"
        >
          Grad-CAM Heatmap Opacity (Alpha Blend)
        </label>
        <span className="text-xs font-mono font-bold text-[#3FD0C4] tabular-nums">
          {value}%
        </span>
      </div>
      <input
        id="alpha"
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-[#111C2B] rounded appearance-none cursor-pointer accent-[#3FD0C4]"
      />
      <div className="flex justify-between text-[10px] text-[#8C9DB0] font-mono mt-1">
        <span>0% (Raw Film)</span>
        <span>25%</span>
        <span className="text-[#3FD0C4] font-semibold">45% (Optimal)</span>
        <span>75%</span>
        <span>100% (Dense Map)</span>
      </div>
    </div>
  );
}
