"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { DynamicChartWrapper } from "./DynamicChartWrapper";
import { I18nContent } from "../data/i18n";
import { TRAINING_HISTORY_24_EPOCHS } from "../data/metrics";
import { Language } from "../types";
import {
  LineChart as ChartIcon,
  Play,
  Pause,
  RotateCcw,
  Zap,
  Sliders,
  CheckCircle2,
} from "lucide-react";

interface TrainingSectionProps {
  dict: I18nContent;
  lang: Language;
}

export function TrainingSection({ dict, lang }: TrainingSectionProps) {
  const [activeEpoch, setActiveEpoch] = useState<number>(19); // Default to best checkpoint epoch 19
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [activeMetricMode, setActiveMetricMode] = useState<"both" | "loss" | "auc">("both");

  // Playback timer
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setActiveEpoch((prev) => (prev >= 24 ? 1 : prev + 1));
      }, 700);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying]);

  const currentRecord =
    TRAINING_HISTORY_24_EPOCHS.find((r) => r.epoch === activeEpoch) ||
    TRAINING_HISTORY_24_EPOCHS[18];

  const chartData = TRAINING_HISTORY_24_EPOCHS.map((rec) => ({
    epoch: rec.epoch,
    trainLoss: rec.trainLoss,
    lossA: rec.lossA,
    valAucA: rec.valAucA,
    valAucB: rec.valAucB,
    valAucC: rec.valAucC,
    valScore: rec.valScore,
    lr: rec.lr * 10000, // scaled for display
  }));

  return (
    <section
      id="section-5"
      className="relative min-h-screen w-full snap-start bg-[#F8FAFC] border-b border-slate-200 flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0F172A]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Section Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div className="max-w-2xl">
            <div className="inline-block px-3 py-1 rounded bg-slate-100 border border-slate-300 text-slate-800 text-[11px] font-mono uppercase tracking-widest mb-3">
              {dict.section5_training.tag}
            </div>
            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0F172A]">
              {dict.section5_training.title}
            </h2>
            <p className="mt-2 text-slate-600 text-sm sm:text-base leading-relaxed">
              {dict.section5_training.description}
            </p>
          </div>

          {/* Metric Filter Tabs */}
          <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-300 shadow-sm text-xs font-mono">
            <button
              type="button"
              onClick={() => setActiveMetricMode("both")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeMetricMode === "both"
                  ? "bg-[#0F172A] text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "Tất Cả Đường Cong" : "All Curves"}
            </button>
            <button
              type="button"
              onClick={() => setActiveMetricMode("loss")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeMetricMode === "loss"
                  ? "bg-[#0F172A] text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "Chỉ Hàm Mất Mát" : "Loss Only"}
            </button>
            <button
              type="button"
              onClick={() => setActiveMetricMode("auc")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeMetricMode === "auc"
                  ? "bg-[#0F172A] text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang === "vi" ? "Chỉ AUROC" : "AUROC Only"}
            </button>
          </div>
        </div>

        {/* 2-Column Main Layout: Chart + Epoch Scrubber Controller */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left Column: Recharts Interactive LineChart */}
          <div className="lg:col-span-8 bg-white border border-slate-300 shadow-sm rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-[#0F172A] uppercase tracking-wide font-mono flex items-center gap-2">
                  <ChartIcon className="w-4 h-4 text-slate-800" />
                  <span>
                    {dict.section5_training.chartTitleLoss} &amp; {dict.section5_training.chartTitleAuc}
                  </span>
                </h3>
                <span className="text-xs font-mono font-bold text-slate-800 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-300">
                  24 Epochs History
                </span>
              </div>

              <div className="w-full h-[320px]">
                <DynamicChartWrapper fallbackHeight={320}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                      <XAxis
                        dataKey="epoch"
                        tick={{ fontSize: 11, fill: "#64748B" }}
                        label={{ value: "Epoch", position: "insideBottom", offset: -2, fontSize: 11 }}
                      />
                      <YAxis
                        yAxisId="left"
                        domain={[0.0, 1.6]}
                        tick={{ fontSize: 11, fill: "#64748B" }}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        domain={[0.65, 1.02]}
                        tick={{ fontSize: 11, fill: "#059669" }}
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
                      />
                      <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "6px" }} />

                      {/* Scrubber Active Vertical Reference Line */}
                      <ReferenceLine
                        x={activeEpoch}
                        stroke="#0F172A"
                        strokeDasharray="3 3"
                        strokeWidth={2}
                        label={{
                          value: `Active: Ep ${activeEpoch}`,
                          position: "top",
                          fill: "#0F172A",
                          fontSize: 10,
                          fontWeight: "bold",
                        }}
                      />

                      {(activeMetricMode === "both" || activeMetricMode === "loss") && (
                        <>
                          <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="trainLoss"
                            name="Train Loss"
                            stroke="#DC2626"
                            strokeWidth={2}
                            dot={false}
                          />
                          <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="lossA"
                            name="Loss Head A (NIH)"
                            stroke="#F87171"
                            strokeWidth={1.5}
                            strokeDasharray="2 2"
                            dot={false}
                          />
                        </>
                      )}

                      {(activeMetricMode === "both" || activeMetricMode === "auc") && (
                        <>
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="valScore"
                            name="Composite Score (0.4A+0.3B+0.3C)"
                            stroke="#0F172A"
                            strokeWidth={2.5}
                            dot={false}
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="valAucA"
                            name="Val AUROC Head A"
                            stroke="#0284C7"
                            strokeWidth={1.8}
                            dot={false}
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="valAucB"
                            name="Val AUROC Head B (TB)"
                            stroke="#059669"
                            strokeWidth={1.8}
                            dot={false}
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="valAucC"
                            name="Val AUROC Head C (COVID)"
                            stroke="#D97706"
                            strokeWidth={1.8}
                            dot={false}
                          />
                        </>
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                </DynamicChartWrapper>
              </div>
            </div>

            {/* PyTorch Mixed Precision AMP Callout */}
            <div className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Zap className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1 font-mono">
                  {dict.section5_training.ampTitle}:
                </span>
                <span className="text-slate-600">{dict.section5_training.ampDesc}</span>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Epoch Scrubber Simulator HUD */}
          <div className="lg:col-span-4 bg-white border border-slate-300 shadow-sm rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-slate-800" />
                  <h3 className="text-sm font-bold text-[#0F172A] font-mono">
                    {dict.section5_training.scrubberLabel}
                  </h3>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="p-1.5 rounded bg-slate-100 text-slate-800 hover:bg-slate-200 transition-colors"
                    title={isPlaying ? "Pause" : "Play"}
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsPlaying(false);
                      setActiveEpoch(1);
                    }}
                    className="p-1.5 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                    title="Reset"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Range Slider */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-xs font-mono font-bold mb-1.5">
                  <span className="text-slate-900 font-extrabold">Epoch {activeEpoch} / 24</span>
                  {currentRecord.isBestCheckpoint && (
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 text-[10px] font-bold border border-emerald-300 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                      Best Checkpoint
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="1"
                  max="24"
                  value={activeEpoch}
                  onChange={(e) => {
                    setIsPlaying(false);
                    setActiveEpoch(parseInt(e.target.value, 10));
                  }}
                  className="w-full h-2 bg-slate-200 rounded appearance-none cursor-pointer accent-[#0F172A]"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
                  <span>Ep 1 (Warmup)</span>
                  <span>Ep 6 (Unfreeze)</span>
                  <span>Ep 19 (Best)</span>
                  <span>Ep 24 (Final)</span>
                </div>
              </div>

              {/* Dynamic Live Metric HUD Cards */}
              <div className="space-y-2 font-mono">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span className="text-xs text-slate-600">
                    {dict.section5_training.trainLossLabel}
                  </span>
                  <span className="text-sm font-bold text-rose-700">
                    {currentRecord.trainLoss.toFixed(4)}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span className="text-xs text-slate-600">
                    {dict.section5_training.valScoreLabel}
                  </span>
                  <span className="text-sm font-bold text-slate-900">
                    {currentRecord.valScore.toFixed(4)}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded bg-slate-50 border border-slate-200 text-center">
                    <span className="text-[10px] text-slate-500 font-bold block">Head A</span>
                    <span className="text-xs font-bold text-slate-900 block mt-0.5">
                      {currentRecord.valAucA.toFixed(4)}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-200 text-center">
                    <span className="text-[10px] text-slate-500 font-bold block">Head B (TB)</span>
                    <span className="text-xs font-bold text-emerald-800 block mt-0.5">
                      {currentRecord.valAucB.toFixed(4)}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-200 text-center">
                    <span className="text-[10px] text-slate-500 font-bold block">Head C</span>
                    <span className="text-xs font-bold text-amber-800 block mt-0.5">
                      {currentRecord.valAucC.toFixed(4)}
                    </span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <span className="text-slate-600">
                    {dict.section5_training.lrLabel}
                  </span>
                  <span className="font-bold text-slate-900">
                    {currentRecord.lr.toExponential(2)}
                  </span>
                </div>

                <div className="p-2 rounded bg-slate-100 text-[11px] text-slate-700 text-center font-semibold">
                  {currentRecord.stageName[lang]}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
