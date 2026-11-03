"use client";

import React, { useState, useRef, useCallback } from "react";
import { I18nContent } from "../data/i18n";
import { Language } from "../types";
import { AlertCircle, CheckCircle2, Quote, ArrowLeftRight } from "lucide-react";

interface ProblemSectionProps {
  dict: I18nContent;
  lang: Language;
}

export function ProblemSection({ dict, lang }: ProblemSectionProps) {
  const [sliderPos, setSliderPos] = useState(50); // percentage 0-100
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isDragging = useRef(false);

  const handlePointerDown = () => {
    isDragging.current = true;
  };

  const handlePointerUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!isDragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const clientX = e.clientX;
      const relativeX = clientX - rect.left;
      const pct = Math.max(5, Math.min(95, (relativeX / rect.width) * 100));
      setSliderPos(pct);
    },
    []
  );

  return (
    <section
      id="section-1"
      className="relative min-h-screen w-full snap-start bg-[#F8FAFC] border-b border-slate-200 flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0F172A]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Section Header */}
        <div className="max-w-3xl mb-8">
          <div className="inline-block px-3 py-1 rounded bg-slate-100 border border-slate-300 text-slate-800 text-[11px] font-mono uppercase tracking-widest mb-3">
            {dict.section1_problem.tag}
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0F172A]">
            {dict.section1_problem.title}
          </h2>
          <p className="mt-2 text-slate-600 text-sm sm:text-base leading-relaxed">
            {dict.section1_problem.description}
          </p>
        </div>

        {/* Quick Presets Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="text-xs font-mono font-semibold text-slate-600 uppercase tracking-wide flex items-center gap-1.5">
            <ArrowLeftRight className="w-4 h-4 text-slate-800" />
            <span>
              {lang === "vi"
                ? "Thanh Trượt Đối Chiếu Lâm Sàng Trực Tiếp"
                : "Comparative Clinical Assessment Split-Screen"}
            </span>
          </div>

          <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-300 shadow-sm text-xs font-mono">
            <button
              type="button"
              onClick={() => setSliderPos(10)}
              className={`px-3 py-1 rounded font-medium transition-all ${
                sliderPos <= 15
                  ? "bg-[#0F172A] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "100% Khủng Hoảng Cũ" : "100% Conventional"}
            </button>
            <button
              type="button"
              onClick={() => setSliderPos(50)}
              className={`px-3 py-1 rounded font-medium transition-all ${
                sliderPos > 40 && sliderPos < 60
                  ? "bg-[#0F172A] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              50 / 50
            </button>
            <button
              type="button"
              onClick={() => setSliderPos(90)}
              className={`px-3 py-1 rounded font-medium transition-all ${
                sliderPos >= 85
                  ? "bg-[#0F172A] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "100% Giải Pháp LungRay" : "100% LungRay"}
            </button>
          </div>
        </div>

        {/* Split-Screen Slider Card */}
        <div
          ref={containerRef}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="relative w-full h-[520px] sm:h-[480px] rounded-2xl overflow-hidden border border-slate-300 shadow-sm bg-white select-none cursor-ew-resize touch-none"
        >
          {/* Left Side: Conventional Pain Points */}
          <div
            className="absolute inset-y-0 left-0 bg-[#FFF5F5] border-r border-slate-300 p-6 sm:p-8 overflow-y-auto"
            style={{ width: `${sliderPos}%` }}
          >
            <div className="min-w-[280px] sm:min-w-[400px] max-w-xl pr-6">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-rose-100 text-rose-900 text-xs font-mono font-bold uppercase tracking-wider mb-4 border border-rose-300">
                <AlertCircle className="w-3.5 h-3.5 text-rose-700" />
                <span>{dict.section1_problem.painPointLabel}</span>
              </div>

              <div className="space-y-3.5">
                {dict.section1_problem.painPoints.map((item, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-lg bg-white border border-rose-200 shadow-sm"
                  >
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {item.desc}
                    </p>
                    <div className="mt-2 text-[10px] font-mono text-rose-900 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 inline-block font-semibold">
                      Systemic Impact: {item.impact}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Side: LungRay Breakthrough Solution */}
          <div
            className="absolute inset-y-0 right-0 bg-[#F0FDF4] p-6 sm:p-8 overflow-y-auto"
            style={{ width: `${100 - sliderPos}%` }}
          >
            <div className="min-w-[280px] sm:min-w-[400px] max-w-xl pl-6 ml-auto">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-emerald-100 text-emerald-900 text-xs font-mono font-bold uppercase tracking-wider mb-4 border border-emerald-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                <span>{dict.section1_problem.aiSolutionLabel}</span>
              </div>

              <div className="space-y-3.5">
                {dict.section1_problem.solutions.map((item, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-lg bg-white border border-emerald-200 shadow-sm"
                  >
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {item.desc}
                    </p>
                    <div className="mt-2 text-[10px] font-mono text-emerald-900 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 inline-block font-semibold">
                      Clinical Validation: {item.benefit}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Draggable Divider Line & Thumb */}
          <div
            onPointerDown={handlePointerDown}
            className="absolute top-0 bottom-0 w-0.5 bg-slate-900 shadow-xl z-20 cursor-ew-resize flex items-center justify-center -translate-x-1/2"
            style={{ left: `${sliderPos}%` }}
          >
            <div className="w-8 h-8 rounded-full bg-white shadow border border-slate-400 flex items-center justify-center text-slate-900 hover:scale-105 active:scale-95 transition-transform">
              <ArrowLeftRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>

        {/* Nature MI 2021 Scientific Citation Callout */}
        <div className="mt-5 p-4 rounded-xl bg-white border-l-4 border-slate-900 border-r border-t border-b border-slate-200 shadow-sm flex items-start gap-3">
          <Quote className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm text-slate-700 leading-relaxed">
            <span className="italic font-serif">&ldquo;{dict.section1_problem.natureQuote}&rdquo;</span>
            <span className="block mt-1 font-semibold text-slate-900 font-mono text-xs">
              — {dict.section1_problem.natureCitation}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
