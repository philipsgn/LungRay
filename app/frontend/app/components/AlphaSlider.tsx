"use client";

interface AlphaSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export default function AlphaSlider({ value, onChange }: AlphaSliderProps) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <label htmlFor="alpha" className="text-sm font-medium text-slate-200">
          Heatmap Opacity
        </label>
        <span className="text-sm font-semibold text-sky-400">{value}%</span>
      </div>
      <input
        id="alpha"
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer accent-sky-500"
      />
      <div className="flex justify-between text-xs text-slate-500 mt-1">
        <span>Original</span>
        <span>Heatmap</span>
      </div>
    </div>
  );
}
