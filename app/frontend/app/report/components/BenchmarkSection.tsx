"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { DynamicChartWrapper } from "./DynamicChartWrapper";
import { I18nContent } from "../data/i18n";
import {
  NIH_LEADERBOARD,
  COVID_CONFUSION_MATRIX,
  TB_CONFUSION_MATRIX,
  ROC_POINTS,
  SHORTCUT_AUDIT,
  CHEXPERT_OOD,
  ERROR_ANALYSIS_CASES,
} from "../data/metrics";
import { Language } from "../types";
import {
  Award,
  Grid3X3,
  TrendingUp,
  ShieldAlert,
  Search,
  CheckCircle,
  FileCheck,
  Stethoscope,
} from "lucide-react";

interface BenchmarkSectionProps {
  dict: I18nContent;
  lang: Language;
}

export function BenchmarkSection({ dict, lang }: BenchmarkSectionProps) {
  const [activeTab, setActiveTab] = useState<"leaderboard" | "confusion" | "roc" | "audit" | "gallery">(
    "leaderboard"
  );
  const [selectedConfusionTask, setSelectedConfusionTask] = useState<"covid" | "tb">("covid");
  const [activeHoverCell, setActiveHoverCell] = useState<{ row: number; col: number } | null>(null);

  const activeMatrix =
    selectedConfusionTask === "covid" ? COVID_CONFUSION_MATRIX : TB_CONFUSION_MATRIX;

  return (
    <section
      id="section-6"
      className="relative min-h-screen w-full snap-start bg-gradient-to-br from-[#ECFDF5] to-[#E0F2FE] flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0B1E36]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div className="max-w-2xl">
            <div className="inline-block px-3.5 py-1 rounded-full bg-emerald-100/80 border border-emerald-300 text-emerald-900 text-xs font-bold uppercase tracking-wider mb-2">
              {dict.section6_evaluation.tag}
            </div>
            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0B1E36]">
              {dict.section6_evaluation.title}
            </h2>
            <p className="mt-2 text-slate-600 text-sm sm:text-base leading-relaxed">
              {dict.section6_evaluation.description}
            </p>
          </div>

          {/* Benchmark Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 bg-white/80 backdrop-blur-md p-1 rounded-2xl border border-slate-200/90 shadow-sm text-xs font-semibold">
            <button
              type="button"
              onClick={() => setActiveTab("leaderboard")}
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition-all ${
                activeTab === "leaderboard"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>{dict.section6_evaluation.tabLeaderboard}</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("confusion")}
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition-all ${
                activeTab === "confusion"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Grid3X3 className="w-3.5 h-3.5" />
              <span>{dict.section6_evaluation.tabConfusion}</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("roc")}
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition-all ${
                activeTab === "roc"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Đường Cong ROC" : "ROC Curves"}</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("audit")}
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition-all ${
                activeTab === "audit"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>{dict.section6_evaluation.tabShortcut}</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("gallery")}
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition-all ${
                activeTab === "gallery"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Ca Khó Lâm Sàng" : "Error Cases"}</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Head A 14 Diseases Leaderboard */}
        {activeTab === "leaderboard" && (
          <div className="backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-2xl rounded-3xl p-6 overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
              <h3 className="text-base font-extrabold text-[#0B1E36]">
                {dict.section6_evaluation.leaderboardTitle}
              </h3>
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                1,000 Bootstrap Resamples
              </span>
            </div>

            <div className="overflow-x-auto max-h-[440px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="sticky top-0 bg-[#0B1E36] text-white font-mono uppercase text-[11px] tracking-wider z-10">
                  <tr>
                    <th className="py-2.5 px-3 rounded-l-lg">{dict.section6_evaluation.tableDisease}</th>
                    <th className="py-2.5 px-3">{dict.section6_evaluation.tableAuroc}</th>
                    <th className="py-2.5 px-3">{dict.section6_evaluation.tableCi95}</th>
                    <th className="py-2.5 px-3">{dict.section6_evaluation.tableThreshold}</th>
                    <th className="py-2.5 px-3">{dict.section6_evaluation.tableBenchmark}</th>
                    <th className="py-2.5 px-3 rounded-r-lg">Prevalence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {NIH_LEADERBOARD.map((item, idx) => (
                    <tr
                      key={item.disease}
                      className={idx % 2 === 0 ? "bg-white/60 hover:bg-sky-50/60" : "bg-slate-50/60 hover:bg-sky-50/60"}
                    >
                      <td className="py-2 px-3 font-sans font-bold text-slate-900">
                        {lang === "vi" ? item.diseaseVi : item.disease}
                      </td>
                      <td className="py-2 px-3 font-extrabold text-sky-800">
                        {item.auroc.toFixed(4)}
                      </td>
                      <td className="py-2 px-3 text-slate-600">
                        [{item.ci95[0].toFixed(4)} – {item.ci95[1].toFixed(4)}]
                      </td>
                      <td className="py-2 px-3 text-emerald-700 font-semibold">
                        τ = {item.threshold.toFixed(2)}
                      </td>
                      <td className="py-2 px-3 text-slate-500">
                        {item.chexnet.toFixed(4)}
                      </td>
                      <td className="py-2 px-3 text-slate-500">{item.prevalence}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Confusion Matrix Heatmap */}
        {activeTab === "confusion" && (
          <div className="backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-2xl rounded-3xl p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div>
                <h3 className="text-base font-extrabold text-[#0B1E36]">
                  {selectedConfusionTask === "covid"
                    ? dict.section6_evaluation.confusionTitle
                    : lang === "vi"
                    ? "Ma Trận Nhầm Lẫn Nhị Phân Sàng Lọc Lao (TB)"
                    : "Binary Tuberculosis Screening Confusion Matrix"}
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  {dict.section6_evaluation.confusionDesc}
                </p>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setSelectedConfusionTask("covid")}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    selectedConfusionTask === "covid"
                      ? "bg-[#0B1E36] text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  COVIDx (3x3)
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedConfusionTask("tb")}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    selectedConfusionTask === "tb"
                      ? "bg-[#0B1E36] text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  TB (2x2)
                </button>
              </div>
            </div>

            {/* Matrix Grid */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              <div className="md:col-span-7 flex flex-col items-center justify-center p-4">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Predicted Class (Hàng: Thực tế / Cột: Dự đoán)
                </div>

                <div
                  className="grid gap-2 text-center font-mono"
                  style={{
                    gridTemplateColumns: `auto repeat(${activeMatrix.labels.length}, minmax(80px, 110px))`,
                  }}
                >
                  {/* Top-left empty corner */}
                  <div className="p-2" />
                  {activeMatrix.labels.map((colLabel, cIdx) => (
                    <div key={cIdx} className="p-2 font-sans font-extrabold text-xs text-slate-800">
                      {colLabel}
                    </div>
                  ))}

                  {activeMatrix.labels.map((rowLabel, rIdx) => (
                    <React.Fragment key={rIdx}>
                      {/* Row Label */}
                      <div className="p-2 font-sans font-extrabold text-xs text-slate-800 flex items-center justify-end pr-3">
                        {rowLabel}
                      </div>

                      {/* Cells */}
                      {activeMatrix.matrix[rIdx].map((val, cIdx) => {
                        const count = activeMatrix.sampleCounts[rIdx][cIdx];
                        const isDiagonal = rIdx === cIdx;
                        const bgIntensity = isDiagonal
                          ? `rgba(2, 132, 199, ${Math.max(0.2, val)})`
                          : `rgba(225, 29, 72, ${Math.max(0.08, val * 2.5)})`;

                        return (
                          <div
                            key={cIdx}
                            onMouseEnter={() => setActiveHoverCell({ row: rIdx, col: cIdx })}
                            onMouseLeave={() => setActiveHoverCell(null)}
                            style={{ backgroundColor: bgIntensity }}
                            className="p-4 rounded-2xl border border-slate-300 shadow-sm cursor-pointer hover:scale-105 transition-transform flex flex-col items-center justify-center"
                          >
                            <span className="text-sm font-extrabold text-[#0B1E36]">
                              {(val * 100).toFixed(1)}%
                            </span>
                            <span className="text-[10px] text-slate-700 mt-0.5">
                              ({count.toLocaleString()})
                            </span>
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Consequence Explanation Card */}
              <div className="md:col-span-5 p-5 rounded-2xl bg-slate-50 border border-slate-200 shadow-sm text-xs">
                <div className="flex items-center gap-2 font-extrabold text-[#0B1E36] mb-2">
                  <Stethoscope className="w-4 h-4 text-sky-600" />
                  <span>
                    {lang === "vi"
                      ? "Phân Tích Hệ Quả Lâm Sàng Theo Ô"
                      : "Cell Clinical Consequence Analysis"}
                  </span>
                </div>

                {activeHoverCell ? (
                  <div>
                    <div className="text-[11px] font-mono text-slate-500 mb-2">
                      True: <strong className="text-slate-800">{activeMatrix.labels[activeHoverCell.row]}</strong> &rarr; Predicted: <strong className="text-slate-800">{activeMatrix.labels[activeHoverCell.col]}</strong>
                    </div>
                    {activeMatrix.clinicalConsequences.find(
                      (c) =>
                        c.cell[0] === activeHoverCell.row && c.cell[1] === activeHoverCell.col
                    ) ? (
                      <p className="text-slate-700 leading-relaxed">
                        {
                          activeMatrix.clinicalConsequences.find(
                            (c) =>
                              c.cell[0] === activeHoverCell.row && c.cell[1] === activeHoverCell.col
                          )?.explanation[lang]
                        }
                      </p>
                    ) : (
                      <p className="text-slate-600">
                        {lang === "vi"
                          ? "Dự đoán trùng khớp với nhãn giải phẫu chuẩn."
                          : "Accurate prediction aligned with ground-truth radiologist diagnosis."}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">
                    {lang === "vi"
                      ? "Rê chuột vào bất kỳ ô nào trên ma trận để xem đánh giá hệ quả lâm sàng đối với bệnh nhân."
                      : "Hover over any cell in the confusion matrix to view its clinical consequences for patient care."}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: ROC Curve Viewer */}
        {activeTab === "roc" && (
          <div className="backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-2xl rounded-3xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-extrabold text-[#0B1E36]">
                  {lang === "vi"
                    ? "Đường Cong Đặc Tuyến Hoạt Động Của Máy Thu (ROC Curves)"
                    : "Receiver Operating Characteristic (ROC Curves)"}
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  True Positive Rate (Sensitivity) vs False Positive Rate (1 - Specificity)
                </p>
              </div>
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200">
                Youden&apos;s J Calibrated
              </span>
            </div>

            <div className="w-full h-[320px]">
              <DynamicChartWrapper fallbackHeight={320}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={ROC_POINTS} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                    <XAxis
                      dataKey="fpr"
                      tick={{ fontSize: 11, fill: "#64748B" }}
                      label={{ value: "False Positive Rate (1 - Specificity)", position: "insideBottom", offset: -2, fontSize: 11 }}
                    />
                    <YAxis
                      domain={[0, 1.0]}
                      tick={{ fontSize: 11, fill: "#64748B" }}
                      label={{ value: "True Positive Rate (Sensitivity)", angle: -90, position: "insideLeft", fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0B1E36",
                        borderColor: "#1E293B",
                        borderRadius: "12px",
                        color: "#fff",
                        fontSize: "12px",
                      }}
                    />
                    {/* Chance diagonal line */}
                    <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#94A3B8" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="headA" name="Head A (Macro 0.8271)" stroke="#0284C7" strokeWidth={2.5} />
                    <Line type="monotone" dataKey="headB" name="Head B TB (1.0000)" stroke="#059669" strokeWidth={2.5} />
                    <Line type="monotone" dataKey="headC" name="Head C COVID (0.7342)" stroke="#D97706" strokeWidth={2.5} />
                  </LineChart>
                </ResponsiveContainer>
              </DynamicChartWrapper>
            </div>
          </div>
        )}

        {/* Tab 4: Shortcut Audit & CheXpert OOD */}
        {activeTab === "audit" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Shortcut Audit Gauge */}
            <div className="lg:col-span-6 backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-2xl rounded-3xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <ShieldAlert className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-base font-extrabold text-[#0B1E36]">
                    {dict.section6_evaluation.shortcutTitle}
                  </h3>
                </div>
                <p className="text-xs text-slate-600 mb-4">
                  {dict.section6_evaluation.shortcutDesc}
                </p>

                {/* Before vs After Metric Comparison Bar */}
                <div className="space-y-4">
                  <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200">
                    <div className="flex items-center justify-between text-xs font-bold text-rose-950 mb-1">
                      <span>{dict.section6_evaluation.rawCamMetric}</span>
                    </div>
                    <div className="w-full h-3 bg-rose-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-rose-500 rounded-full"
                        style={{ width: `${SHORTCUT_AUDIT.unmasked.meanRatio}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-rose-700 font-mono mt-1 block">
                      Fail Rate: 100% (Energy dissipated on R/L tags &amp; hospital labels)
                    </span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200">
                    <div className="flex items-center justify-between text-xs font-bold text-emerald-950 mb-1">
                      <span>{dict.section6_evaluation.groundedMetric}</span>
                    </div>
                    <div className="w-full h-3 bg-emerald-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${SHORTCUT_AUDIT.clinicalGrounding.meanRatio}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-emerald-700 font-mono mt-1 block">
                      Pass Rate: 100% (Wilcoxon p = 1.15e-26, W = 11325.0)
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-700 font-mono">
                {dict.section6_evaluation.auditStatusPass}
              </div>
            </div>

            {/* CheXpert OOD Table */}
            <div className="lg:col-span-6 backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-2xl rounded-3xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileCheck className="w-5 h-5 text-sky-600" />
                  <h3 className="text-base font-extrabold text-[#0B1E36]">
                    {dict.section6_evaluation.oodTitle}
                  </h3>
                </div>
                <p className="text-xs text-slate-600 mb-4">
                  {dict.section6_evaluation.oodDesc}
                </p>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#0B1E36] text-white text-[11px] uppercase">
                      <tr>
                        <th className="py-2 px-2.5 rounded-l-lg">Pathology</th>
                        <th className="py-2 px-2.5">NIH (In-Dist)</th>
                        <th className="py-2 px-2.5">CheXpert (OOD)</th>
                        <th className="py-2 px-2.5">Retention</th>
                        <th className="py-2 px-2.5 rounded-r-lg">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {CHEXPERT_OOD.map((item) => (
                        <tr key={item.pathology} className="hover:bg-slate-50">
                          <td className="py-2 px-2.5 font-sans font-bold text-slate-900">
                            {item.pathology}
                          </td>
                          <td className="py-2 px-2.5 text-slate-600">{item.nihAuc.toFixed(4)}</td>
                          <td className="py-2 px-2.5 font-bold text-sky-800">
                            {item.chexpertAuc.toFixed(4)}
                          </td>
                          <td className="py-2 px-2.5 text-emerald-700 font-bold">
                            {item.retention.toFixed(1)}%
                          </td>
                          <td className="py-2 px-2.5 text-emerald-600 font-bold flex items-center gap-1">
                            <CheckCircle className="w-3.5 h-3.5" />
                            Pass
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-4 text-xs font-semibold text-slate-700">
                {dict.section6_evaluation.retentionLabel}
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Clinical Error Analysis Gallery */}
        {activeTab === "gallery" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {ERROR_ANALYSIS_CASES.map((caseItem) => (
              <div
                key={caseItem.id}
                className="backdrop-blur-md bg-white/80 border border-slate-200/90 shadow-xl rounded-2xl p-4 flex flex-col justify-between hover:shadow-2xl transition-all"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {caseItem.patientId}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        caseItem.caseType === "fn"
                          ? "bg-rose-100 text-rose-800 border border-rose-200"
                          : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                      }`}
                    >
                      {caseItem.caseType === "fn" ? "Edge FN" : "True Positive"}
                    </span>
                  </div>

                  <h4 className="text-xs font-extrabold text-[#0B1E36] line-clamp-1">
                    {caseItem.targetDisease[lang]}
                  </h4>

                  <div className="my-2.5 p-2 rounded-xl bg-slate-50 border border-slate-200/80 font-mono text-[11px] space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Pred Prob:</span>
                      <strong className="text-slate-900">{caseItem.predictedProb.toFixed(2)}</strong>
                    </div>
                    {caseItem.boxIou && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Box-IoU:</span>
                        <strong className="text-emerald-700">{caseItem.boxIou.toFixed(2)}</strong>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-slate-500">In-Lung:</span>
                      <strong className="text-sky-700">{caseItem.inLungEnergyPct}%</strong>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-600 leading-snug">
                    {caseItem.radiologistNotes[lang]}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
