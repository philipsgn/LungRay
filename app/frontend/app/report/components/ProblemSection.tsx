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
      className="relative min-h-screen w-full snap-start bg-gradient-to-br from-[#F0F9FF] to-[#F8FAFC] flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0B1E36]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Section Header */}
        <div className="max-w-3xl mb-8">
          <div className="inline-block px-3.5 py-1 rounded-full bg-rose-100/80 border border-rose-300 text-rose-900 text-xs font-bold uppercase tracking-wider mb-2">
            {dict.section1_problem.tag}
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0B1E36]">
            {dict.section1_problem.title}
          </h2>
          <p className="mt-3 text-slate-600 text-sm sm:text-base leading-relaxed">
            {dict.section1_problem.description}
          </p>
        </div>

        {/* Quick Presets Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1.5">
            <ArrowLeftRight className="w-4 h-4 text-sky-600" />
            <span>
              {lang === "vi"
                ? "Thanh Trượt So Sánh Lâm Sàng Trực Tiếp"
                : "Interactive Clinical Comparison Slider"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 bg-white/70 backdrop-blur-md p-1 rounded-xl border border-slate-200/80 shadow-sm text-xs">
            <button
              type="button"
              onClick={() => setSliderPos(10)}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                sliderPos <= 15
                  ? "bg-rose-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "100% Rào Cản" : "100% Conventional"}
            </button>
            <button
              type="button"
              onClick={() => setSliderPos(50)}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                sliderPos > 40 && sliderPos < 60
                  ? "bg-sky-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "Chia Đôi 50/50" : "Split 50/50"}
            </button>
            <button
              type="button"
              onClick={() => setSliderPos(90)}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                sliderPos >= 85
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "100% LungRay AI" : "100% LungRay AI"}
            </button>
          </div>
        </div>

        {/* Interactive Split-Screen Slider Card */}
        <div
          ref={containerRef}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="relative w-full h-[520px] sm:h-[480px] rounded-3xl overflow-hidden border border-slate-200/90 shadow-2xl backdrop-blur-md bg-white/80 select-none cursor-ew-resize touch-none"
        >
          {/* Left Side: Conventional Pain Points */}
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-br from-rose-50/90 to-amber-50/70 p-6 sm:p-8 overflow-y-auto"
            style={{ width: `${sliderPos}%` }}
          >
            <div className="min-w-[280px] sm:min-w-[400px] max-w-xl pr-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-200/70 text-rose-900 text-xs font-bold uppercase tracking-wider mb-4 border border-rose-300">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>{dict.section1_problem.painPointLabel}</span>
              </div>

              <div className="space-y-4">
                {dict.section1_problem.painPoints.map((item, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl bg-white/80 border border-rose-200/80 shadow-sm"
                  >
                    <h4 className="text-sm font-bold text-rose-950 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                      {item.desc}
                    </p>
                    <div className="mt-2 text-[11px] font-mono text-rose-800 bg-rose-100/60 px-2 py-0.5 rounded border border-rose-200/60 inline-block">
                      Impact: {item.impact}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Side: LungRay Breakthrough Solution */}
          <div
            className="absolute inset-y-0 right-0 bg-gradient-to-br from-emerald-50/90 to-sky-50/70 p-6 sm:p-8 overflow-y-auto"
            style={{ width: `${100 - sliderPos}%` }}
          >
            <div className="min-w-[280px] sm:min-w-[400px] max-w-xl pl-6 ml-auto">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-200/70 text-emerald-900 text-xs font-bold uppercase tracking-wider mb-4 border border-emerald-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>{dict.section1_problem.aiSolutionLabel}</span>
              </div>

              <div className="space-y-4">
                {dict.section1_problem.solutions.map((item, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl bg-white/80 border border-emerald-200/80 shadow-sm"
                  >
                    <h4 className="text-sm font-bold text-emerald-950 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      {item.title}
                    </h4>
                    <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                      {item.desc}
                    </p>
                    <div className="mt-2 text-[11px] font-mono text-emerald-800 bg-emerald-100/60 px-2 py-0.5 rounded border border-emerald-200/60 inline-block">
                      Benefit: {item.benefit}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Draggable Divider Line & Thumb */}
          <div
            onPointerDown={handlePointerDown}
            className="absolute top-0 bottom-0 w-1 bg-white shadow-2xl z-20 cursor-ew-resize flex items-center justify-center -translate-x-1/2"
            style={{ left: `${sliderPos}%` }}
          >
            <div className="w-9 h-9 rounded-full bg-white shadow-xl border-2 border-slate-300 flex items-center justify-center text-slate-700 hover:scale-110 active:scale-95 transition-transform">
              <ArrowLeftRight className="w-4 h-4 text-sky-600" />
            </div>
          </div>
        </div>

        {/* Nature MI 2021 Scientific Citation Callout */}
        <div className="mt-6 p-4 rounded-2xl bg-white/70 backdrop-blur-md border border-slate-200/80 shadow-sm flex items-start gap-3">
          <Quote className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm text-slate-700 leading-relaxed">
            <span className="italic font-medium">&ldquo;{dict.section1_problem.natureQuote}&rdquo;</span>
            <span className="block mt-1 font-semibold text-slate-900 font-mono text-xs">
              — {dict.section1_problem.natureCitation}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
