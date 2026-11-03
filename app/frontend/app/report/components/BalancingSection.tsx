"use client";

import React, { useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { DynamicChartWrapper } from "./DynamicChartWrapper";
import { I18nContent } from "../data/i18n";
import { IMBALANCE_DATA, PIPELINE_STEPS } from "../data/metrics";
import { Language } from "../types";
import { Scale, Code2, AlertTriangle, CheckCircle2, ChevronRight, Layers } from "lucide-react";

interface BalancingSectionProps {
  dict: I18nContent;
  lang: Language;
}

export function BalancingSection({ dict, lang }: BalancingSectionProps) {
  const [activeView, setActiveView] = useState<"raw" | "balanced">("balanced");
  const [selectedStepIndex, setSelectedStepIndex] = useState<number>(3); // Step 4 default (sampler)

  const selectedStep = PIPELINE_STEPS[selectedStepIndex];

  const chartData = IMBALANCE_DATA.map((d) => ({
    name: d.task.replace(" ChestX-ray14", "").replace(" CXR-4", "").replace(" Radiography", ""),
    percentage: activeView === "raw" ? d.rawPct : d.balancedPct,
    rawPct: d.rawPct,
    balancedPct: d.balancedPct,
    count: d.rawCount,
    fill: activeView === "raw" ? d.fillRaw : d.fillBalanced,
  }));

  return (
    <section
      id="section-3"
      className="relative min-h-screen w-full snap-start bg-[#F8FAFC] border-b border-slate-200 flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0F172A]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Header */}
        <div className="max-w-3xl mb-6">
          <div className="inline-block px-3 py-1 rounded bg-slate-100 border border-slate-300 text-slate-800 text-[11px] font-mono uppercase tracking-widest mb-3">
            {dict.section3_balancing.tag}
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0F172A]">
            {dict.section3_balancing.title}
          </h2>
          <p className="mt-2 text-slate-600 text-sm sm:text-base leading-relaxed">
            {dict.section3_balancing.description}
          </p>
        </div>

        {/* 2-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left Column: Imbalance Transformation Card */}
          <div className="lg:col-span-5 bg-white border border-slate-300 shadow-sm rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-[#0F172A] uppercase tracking-wide font-mono flex items-center gap-1.5">
                  <Scale className="w-4 h-4 text-slate-800" />
                  <span>{dict.section3_balancing.imbalanceTitle}</span>
                </h3>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed mb-4">
                {dict.section3_balancing.imbalanceDesc}
              </p>

              {/* View Switcher Toggle */}
              <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200 mb-4 text-xs font-mono">
                <button
                  type="button"
                  onClick={() => setActiveView("raw")}
                  className={`py-2 px-3 rounded transition-all text-center flex items-center justify-center gap-1.5 ${
                    activeView === "raw"
                      ? "bg-white text-rose-800 shadow-sm font-bold border border-slate-200"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>{lang === "vi" ? "Tỷ Lệ Thô (16:2.3:1)" : "Raw (82%:12%:5%)"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveView("balanced")}
                  className={`py-2 px-3 rounded transition-all text-center flex items-center justify-center gap-1.5 ${
                    activeView === "balanced"
                      ? "bg-[#0F172A] text-white shadow-sm font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{lang === "vi" ? "Cân Bằng 60:25:15" : "Balanced 60:25:15"}</span>
                </button>
              </div>

              {/* Imbalance Chart */}
              <div className="w-full h-[200px]">
                <DynamicChartWrapper fallbackHeight={200}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                        unit="%"
                        tick={{ fontSize: 11, fill: "#64748B" }}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fontSize: 11, fill: "#0F172A", fontWeight: 600 }}
                        width={80}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0F172A",
                          borderColor: "#334155",
                          borderRadius: "8px",
                          color: "#fff",
                          fontSize: "12px",
                          fontFamily: "monospace",
                        }}
                        formatter={(value) => [typeof value === "number" ? `${value.toFixed(1)}% of Batch` : String(value ?? ""), "Quota"]}
                      />
                      <Bar dataKey="percentage" radius={[0, 4, 4, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </DynamicChartWrapper>
              </div>
            </div>

            {/* Quota Callout */}
            <div className="mt-4 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div className="font-bold text-slate-900 flex items-center gap-1.5 mb-1">
                <Layers className="w-4 h-4 text-slate-700" />
                <span>
                  {activeView === "balanced"
                    ? lang === "vi"
                      ? "Phân Bổ Batch 16: 10 NIH / 4 COVID / 2 TB"
                      : "Batch Size 16 Allocation: 10 NIH / 4 COVID / 2 TB"
                    : lang === "vi"
                    ? "Cảnh Báo Đói Tác Vụ: TB Chỉ Chiếm 0.8 Ảnh / Batch"
                    : "Task Starvation Alert: TB Head Starved at 0.8 Images/Batch"}
                </span>
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed font-mono">
                {dict.section3_balancing.starvationWarning}
              </p>
            </div>
          </div>

          {/* Right Column: 5-Stage Interactive Pipeline Flowchart */}
          <div className="lg:col-span-7 flex flex-col justify-between bg-white border border-slate-300 shadow-sm rounded-2xl p-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-[#0F172A] uppercase tracking-wide font-mono flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-slate-800" />
                  <span>{dict.section3_balancing.pipelineTitle}</span>
                </h3>
                <span className="text-xs text-slate-500 font-mono">
                  Stage {selectedStep.step} / 05
                </span>
              </div>

              {/* 5-Step Horizontal Navigation Bar */}
              <div className="grid grid-cols-5 gap-2 mb-4">
                {PIPELINE_STEPS.map((s, idx) => {
                  const isSelected = selectedStepIndex === idx;
                  return (
                    <button
                      key={s.step}
                      type="button"
                      onClick={() => setSelectedStepIndex(idx)}
                      className={`p-2.5 rounded-lg text-left transition-all border ${
                        isSelected
                          ? "bg-[#0F172A] text-white border-[#0F172A] shadow-sm"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-xs font-mono font-bold ${
                            isSelected ? "text-sky-300" : "text-slate-800"
                          }`}
                        >
                          {s.step}
                        </span>
                        <ChevronRight
                          className={`w-3.5 h-3.5 ${
                            isSelected ? "text-sky-300" : "text-slate-400"
                          }`}
                        />
                      </div>
                      <div className="text-[11px] font-bold truncate mt-1">{s.title[lang]}</div>
                      <div
                        className={`text-[10px] font-mono truncate ${
                          isSelected ? "text-slate-300" : "text-slate-500"
                        }`}
                      >
                        {s.subtitle[lang]}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Selected Step Detail Panel */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <h4 className="text-sm font-bold text-[#0F172A]">
                    {selectedStep.step}. {selectedStep.title[lang]}
                  </h4>
                  <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-white text-slate-800 border border-slate-300">
                    {selectedStep.subtitle[lang]}
                  </span>
                </div>

                <p className="text-xs text-slate-700 leading-relaxed mb-3">
                  {selectedStep.description[lang]}
                </p>

                {/* Key Bullet Highlights */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
                  {selectedStep.details.map((detail, dIdx) => (
                    <div
                      key={dIdx}
                      className="p-2 rounded bg-white border border-slate-200 text-[11px] text-slate-700 flex items-start gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-900 mt-1 shrink-0" />
                      <span>{detail[lang]}</span>
                    </div>
                  ))}
                </div>

                {/* Code Snippet Drawer */}
                <div className="rounded-lg overflow-hidden border border-slate-800 shadow-inner bg-[#0B131E]">
                  <div className="px-3 py-1.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span>PyTorch Pipeline Implementation</span>
                    <span className="text-sky-400 text-[10px]">Python 3.10</span>
                  </div>
                  <pre className="p-3 text-[11px] font-mono text-emerald-400 overflow-x-auto leading-relaxed">
                    <code>{selectedStep.codeSnippet}</code>
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
