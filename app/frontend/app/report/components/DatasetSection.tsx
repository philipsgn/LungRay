"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { DynamicChartWrapper } from "./DynamicChartWrapper";
import { I18nContent } from "../data/i18n";
import { DATASET_CATALOG } from "../data/metrics";
import { Language } from "../types";
import { ShieldCheck, BarChart3, PieChart as PieIcon, Eye, Radio } from "lucide-react";

interface DatasetSectionProps {
  dict: I18nContent;
  lang: Language;
}

const RADAR_DATA = [
  { subject: "Volume (Số Lượng)", nih: 100, tb: 25, covid: 40, vindr: 15, chexpert: 50 },
  { subject: "Classes (Đa Dạng)", nih: 95, tb: 20, covid: 35, vindr: 95, chexpert: 45 },
  { subject: "Radiologist Box", nih: 10, tb: 5, covid: 15, vindr: 100, chexpert: 10 },
  { subject: "OOD Diversity", nih: 30, tb: 40, covid: 85, vindr: 90, chexpert: 100 },
  { subject: "Zero Leakage", nih: 100, tb: 90, covid: 95, vindr: 100, chexpert: 95 },
];

const COLORS = ["#0284C7", "#059669", "#D97706", "#8B5CF6", "#EC4899", "#64748B"];

export function DatasetSection({ dict, lang }: DatasetSectionProps) {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [chartType, setChartType] = useState<"bar" | "pie" | "radar">("bar");

  const filteredDatasets =
    activeCategory === "all"
      ? DATASET_CATALOG
      : DATASET_CATALOG.filter((d) => d.category === activeCategory);

  const chartData = DATASET_CATALOG.map((d, i) => ({
    name: d.name.replace(" Database", "").replace(" Benchmark", "").replace("-small-v1", ""),
    fullName: d.name,
    images: d.images,
    fill: COLORS[i % COLORS.length],
  }));

  return (
    <section
      id="section-2"
      className="relative min-h-screen w-full snap-start bg-gradient-to-br from-[#ECFDF5] to-[#F0F9FF] flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0B1E36]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Section Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div className="max-w-2xl">
            <div className="inline-block px-3.5 py-1 rounded-full bg-emerald-100/80 border border-emerald-300 text-emerald-900 text-xs font-bold uppercase tracking-wider mb-2">
              {dict.section2_datasets.tag}
            </div>
            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0B1E36]">
              {dict.section2_datasets.title}
            </h2>
            <p className="mt-2 text-slate-600 text-sm sm:text-base leading-relaxed">
              {dict.section2_datasets.description}
            </p>
          </div>

          {/* Chart View Mode Controls */}
          <div className="flex items-center gap-1.5 bg-white/80 backdrop-blur-md p-1 rounded-xl border border-slate-200/90 shadow-sm text-xs font-semibold">
            <button
              type="button"
              onClick={() => setChartType("bar")}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                chartType === "bar"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Cột" : "Bar"}</span>
            </button>
            <button
              type="button"
              onClick={() => setChartType("pie")}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                chartType === "pie"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <PieIcon className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Tròn" : "Pie"}</span>
            </button>
            <button
              type="button"
              onClick={() => setChartType("radar")}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                chartType === "radar"
                  ? "bg-[#0B1E36] text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Radio className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Radar Đa Chiều" : "Radar"}</span>
            </button>
          </div>
        </div>

        {/* 2-Column Visual Explorer */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left Column: Recharts Distribution Visualizer */}
          <div className="lg:col-span-5 backdrop-blur-md bg-white/75 border border-slate-200/80 shadow-xl rounded-3xl p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-[#0B1E36]">
                {chartType === "radar"
                  ? lang === "vi"
                    ? "Đa Dạng Hóa Thuộc Tính Dữ Liệu"
                    : "Multi-Cohort Diversity Radar"
                  : lang === "vi"
                  ? "Phân Bố Số Lượng Ảnh Đa Trung Tâm"
                  : "Multi-Center Cohort Distribution"}
              </h3>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-sky-100 text-sky-800 border border-sky-200">
                160,953 CXRs
              </span>
            </div>

            <div className="w-full h-[280px]">
              <DynamicChartWrapper fallbackHeight={280}>
                {chartType === "bar" && (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      layout="vertical"
                      margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
                    >
                      <XAxis type="number" tick={{ fontSize: 11, fill: "#64748B" }} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fontSize: 11, fill: "#0B1E36", fontWeight: 600 }}
                        width={90}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0B1E36",
                          borderColor: "#1E293B",
                          borderRadius: "12px",
                          color: "#fff",
                          fontSize: "12px",
                        }}
                        formatter={(value) => [typeof value === "number" ? `${value.toLocaleString()} images` : String(value ?? ""), "Volume"]}
                      />
                      <Bar dataKey="images" radius={[0, 8, 8, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}

                {chartType === "pie" && (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={chartData}
                        dataKey="images"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={95}
                        paddingAngle={3}
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0B1E36",
                          borderColor: "#1E293B",
                          borderRadius: "12px",
                          color: "#fff",
                          fontSize: "12px",
                        }}
                        formatter={(value) => [typeof value === "number" ? `${value.toLocaleString()} images` : String(value ?? ""), "Volume"]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}

                {chartType === "radar" && (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={RADAR_DATA}>
                      <PolarGrid stroke="#CBD5E1" />
                      <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: "#475569" }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
                      <Radar
                        name="NIH"
                        dataKey="nih"
                        stroke="#0284C7"
                        fill="#0284C7"
                        fillOpacity={0.3}
                      />
                      <Radar
                        name="VinDr"
                        dataKey="vindr"
                        stroke="#8B5CF6"
                        fill="#8B5CF6"
                        fillOpacity={0.3}
                      />
                      <Radar
                        name="COVIDx"
                        dataKey="covid"
                        stroke="#D97706"
                        fill="#D97706"
                        fillOpacity={0.3}
                      />
                      <Tooltip />
                    </RadarChart>
                  </ResponsiveContainer>
                )}
              </DynamicChartWrapper>
            </div>

            {/* Zero Leakage Callout Card */}
            <div className="mt-4 p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-200/90 text-xs">
              <div className="flex items-center gap-1.5 font-bold text-emerald-950 mb-1">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{dict.section2_datasets.leakageDisciplineTitle}</span>
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">
                {dict.section2_datasets.leakageDisciplineDesc}
              </p>
            </div>
          </div>

          {/* Right Column: Filterable Dataset Catalog Grid */}
          <div className="lg:col-span-7 flex flex-col justify-between">
            {/* Filter Chips */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              {[
                { id: "all", label: dict.section2_datasets.filterAll },
                { id: "primary", label: dict.section2_datasets.filterPrimary },
                { id: "groundtruth", label: dict.section2_datasets.filterGroundTruth },
                { id: "ood", label: dict.section2_datasets.filterOod },
              ].map((chip) => (
                <button
                  key={chip.id}
                  type="button"
                  onClick={() => setActiveCategory(chip.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    activeCategory === chip.id
                      ? "bg-[#0B1E36] text-white shadow-md"
                      : "bg-white/80 text-slate-700 border border-slate-200 hover:bg-white"
                  }`}
                >
                  {chip.label}
                </button>
              ))}
            </div>

            {/* Dataset Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[460px] overflow-y-auto pr-1">
              {filteredDatasets.map((ds) => (
                <div
                  key={ds.id}
                  className="backdrop-blur-md bg-white/80 border border-slate-200/80 shadow-md rounded-2xl p-4 hover:shadow-lg hover:border-slate-300 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-sky-100 text-sky-800 border border-sky-200">
                        {ds.badge}
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-900">
                        {ds.images.toLocaleString()} CXRs
                      </span>
                    </div>

                    <h4 className="text-sm font-extrabold text-[#0B1E36]">{ds.name}</h4>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{ds.role[lang]}</p>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                    <span>
                      {typeof ds.patients === "number"
                        ? `${ds.patients.toLocaleString()} pts`
                        : ds.patients}
                    </span>
                    <span className="text-emerald-700 font-semibold flex items-center gap-1">
                      <Eye className="w-3 h-3 text-emerald-600" />
                      {ds.leakageRate}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
