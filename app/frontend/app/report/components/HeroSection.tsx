"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { I18nContent } from "../data/i18n";
import { Language } from "../types";
import {
  ChevronDown,
  Stethoscope,
  ShieldCheck,
  Layers,
  Crosshair,
  Activity,
  Eye,
} from "lucide-react";

interface HeroSectionProps {
  dict: I18nContent;
  lang: Language;
  onExploreClick: () => void;
}

export function HeroSection({ dict, lang, onExploreClick }: HeroSectionProps) {
  // Visualizer mode: "raw" | "mask" | "cam"
  const [viewMode, setViewMode] = useState<"raw" | "mask" | "cam">("cam");

  const isVi = lang === "vi";

  return (
    <section
      id="section-0"
      className="relative min-h-screen w-full snap-start bg-[#F8FAFC] border-b border-slate-300 flex flex-col justify-between p-6 sm:p-10 lg:p-12 overflow-hidden text-[#0F172A]"
    >
      {/* Main 2-Column Split Hero Layout */}
      <div className="w-full max-w-7xl mx-auto my-auto py-4 sm:py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* ================================================================= */}
          {/* LEFT COLUMN (7 Cols): Title, Abstract & Spec Table               */}
          {/* ================================================================= */}
          <div className="lg:col-span-7 space-y-5">
            {/* Short Unified Title */}
            <h1 className="font-serif text-3xl sm:text-5xl font-extrabold text-[#0F172A] leading-tight tracking-tight">
              {dict.section0_hero.mainTitle}
            </h1>

            {/* Concise Technical Description with native font */}
            <p className="text-sm sm:text-base text-slate-700 leading-relaxed max-w-2xl font-sans">
              {dict.section0_hero.subtitle}
            </p>

            {/* Academic Specification Table (Booktabs 3-Line Standard) */}
            <div className="pt-2">
              <div className="text-[11px] font-sans font-semibold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-slate-700" />
                <span>
                  {isVi
                    ? "Bảng 1: Thông số thực nghiệm lâm sàng hợp nhất (N = 160.953)"
                    : "Table 1: Unified Multi-Center Clinical Metrics (N = 160,953)"}
                </span>
              </div>

              {/* Booktabs Table: Top rule (2px), Mid rule (1px), Bottom rule (2px) */}
              <div className="border-t-2 border-slate-900 border-b-2 border-slate-900 font-sans text-xs">
                <div className="grid grid-cols-4 bg-slate-100/70 p-2.5 font-bold text-slate-800 border-b border-slate-300">
                  <div>{isVi ? "Chỉ Số Đo Đạc" : "Metric"}</div>
                  <div>{isVi ? "Quy Mô Mẫu" : "Cohort"}</div>
                  <div className="text-right">{isVi ? "Kết Quả" : "Score"}</div>
                  <div className="text-right">{isVi ? "Kiểm Định" : "Status"}</div>
                </div>

                <div className="divide-y divide-slate-200">
                  {/* Row 1: Macro AUROC */}
                  <div className="grid grid-cols-4 p-2.5 items-center hover:bg-slate-50 transition-colors">
                    <div className="font-semibold text-slate-900">
                      {isVi ? "Điểm AUROC Hợp Nhất" : "Composite AUROC"}
                    </div>
                    <div className="text-slate-600 text-[11px]">
                      {isVi ? "160.953 Phim CXR" : "160,953 CXRs"}
                    </div>
                    <div className="text-right font-mono font-bold text-slate-900 tabular-nums">
                      0.8538
                    </div>
                    <div className="text-right text-[10px] font-bold text-slate-800">
                      {isVi ? "[ĐẠT CHUẨN]" : "[PASS]"}
                    </div>
                  </div>

                  {/* Row 2: Active TB Screening */}
                  <div className="grid grid-cols-4 p-2.5 items-center hover:bg-slate-50 transition-colors">
                    <div className="font-semibold text-slate-900">
                      {isVi ? "Sàng Lọc Lao (Head B)" : "Active TB (Head B)"}
                    </div>
                    <div className="text-slate-600 text-[11px]">
                      {isVi ? "Mẫu Shenzhen" : "Shenzhen Cohort"}
                    </div>
                    <div className="text-right font-mono font-bold text-slate-900 tabular-nums">
                      1.0000
                    </div>
                    <div className="text-right text-[10px] font-bold text-slate-800">
                      {isVi ? "[ĐẠT CHUẨN]" : "[PASS]"}
                    </div>
                  </div>

                  {/* Row 3: Pulmonary Attention Energy */}
                  <div className="grid grid-cols-4 p-2.5 items-center hover:bg-slate-50 transition-colors">
                    <div className="font-semibold text-slate-900">
                      {isVi ? "Năng Lượng Phế Trường" : "In-Lung Attention"}
                    </div>
                    <div className="text-slate-600 text-[11px]">
                      {isVi ? "Mẫu COVIDx CXR-4" : "COVIDx CXR-4"}
                    </div>
                    <div className="text-right font-mono font-bold text-slate-900 tabular-nums">
                      84.6%
                    </div>
                    <div className="text-right text-[10px] font-bold text-slate-800">
                      [≥ 80.0%]
                    </div>
                  </div>

                  {/* Row 4: Inference Latency */}
                  <div className="grid grid-cols-4 p-2.5 items-center hover:bg-slate-50 transition-colors">
                    <div className="font-semibold text-slate-900">
                      {isVi ? "Độ Trễ Suy Luận" : "Inference Latency"}
                    </div>
                    <div className="text-slate-600 text-[11px]">
                      {isVi ? "CPU Cục Bộ" : "Local CPU"}
                    </div>
                    <div className="text-right font-mono font-bold text-slate-900 tabular-nums">
                      674 ms
                    </div>
                    <div className="text-right text-[10px] font-bold text-slate-800">
                      [&lt; 2.0s]
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons with Be Vietnam Pro font-sans */}
            <div className="pt-2 flex flex-wrap items-center gap-3.5 text-xs font-sans">
              <button
                type="button"
                onClick={onExploreClick}
                className="px-5 py-2.5 rounded-lg bg-[#0F172A] text-white font-semibold shadow hover:bg-slate-800 active:translate-y-0.5 transition-all flex items-center gap-2"
              >
                <ChevronDown className="w-4 h-4 text-slate-300" />
                <span dangerouslySetInnerHTML={{ __html: dict.section0_hero.ctaExplore }} />
              </button>

              <Link
                href="/"
                className="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-900 font-semibold shadow-sm hover:bg-slate-100 hover:border-slate-400 transition-all flex items-center gap-2"
              >
                <Stethoscope className="w-4 h-4 text-slate-800" />
                <span dangerouslySetInnerHTML={{ __html: dict.section0_hero.ctaMethodology }} />
              </Link>
            </div>
          </div>

          {/* ================================================================= */}
          {/* RIGHT COLUMN (5 Cols): Authentic Multi-Task CXR Visualizer        */}
          {/* ================================================================= */}
          <div className="lg:col-span-5">
            <div className="bg-[#05080E] border border-slate-800 rounded-2xl p-4 text-slate-100 font-sans shadow-2xl relative">
              {/* Header Strip & View Mode Switcher */}
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  <span className="font-bold uppercase tracking-wider text-slate-200 text-[11px] font-mono">
                    {isVi ? "Trạm Đọc Phim Lâm Sàng" : "Clinical CXR Visualizer"}
                  </span>
                </div>

                {/* Mode Selector */}
                <div className="inline-flex rounded-lg border border-slate-800 bg-slate-950 p-0.5 text-[10px] font-mono">
                  <button
                    type="button"
                    onClick={() => setViewMode("raw")}
                    className={`px-2 py-1 rounded transition-colors ${
                      viewMode === "raw"
                        ? "bg-slate-800 text-cyan-300 font-bold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {isVi ? "Ảnh Gốc CXR" : "Raw CXR"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode("mask")}
                    className={`px-2 py-1 rounded transition-colors ${
                      viewMode === "mask"
                        ? "bg-slate-800 text-cyan-300 font-bold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {isVi ? "Mặt Nạ Phổi" : "Lung Mask"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode("cam")}
                    className={`px-2 py-1 rounded transition-colors ${
                      viewMode === "cam"
                        ? "bg-slate-800 text-cyan-300 font-bold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Grad-CAM
                  </button>
                </div>
              </div>

              {/* Authentic Radiograph Viewport */}
              <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-black border border-slate-850">
                {/* Real Clinical Chest Radiograph */}
                <Image
                  src="/demo_samples/02_effusion_cardiomegaly.png"
                  alt="Clinical Radiograph"
                  fill
                  className="object-contain"
                  priority
                />

                {/* Overlay Mode 1: Anatomical Lung Mask Contour */}
                {viewMode === "mask" && (
                  <div className="absolute inset-0 pointer-events-none bg-cyan-500/10 mix-blend-screen transition-opacity flex items-center justify-center">
                    <div className="w-[74%] h-[80%] border-2 border-dashed border-cyan-400/80 rounded-[30%] opacity-80" />
                  </div>
                )}

                {/* Overlay Mode 2: Natural Grad-CAM Heatmap Activation */}
                {viewMode === "cam" && (
                  <div
                    className="absolute inset-0 pointer-events-none mix-blend-screen transition-opacity"
                    style={{
                      background:
                        "radial-gradient(circle at 72% 76%, rgba(244, 63, 94, 0.6) 0%, rgba(245, 158, 11, 0.45) 28%, rgba(6, 182, 212, 0.2) 55%, transparent 72%)",
                    }}
                  />
                )}

                {/* Center Crosshair Reticle & Telemetry */}
                <div className="absolute top-2 left-2 text-[9px] font-mono text-slate-300 pointer-events-none drop-shadow">
                  <div>{isVi ? "PA NGỰC THẲNG • 512x512" : "PA CHEST CXR • 512x512"}</div>
                  <div className="text-cyan-400 font-bold">
                    {isVi ? "TỔN THƯƠNG: TRÀN DỊCH" : "TARGET: PLEURAL EFFUSION"}
                  </div>
                </div>

                <div className="absolute top-2 right-2 text-[10px] font-bold font-mono text-slate-300 bg-slate-900/80 px-1.5 py-0.5 rounded border border-slate-700 pointer-events-none">
                  L
                </div>

                <div className="absolute bottom-2 right-2 text-[9px] font-mono text-slate-400 pointer-events-none flex flex-col items-end">
                  <div className="w-12 h-1 border-b border-l border-r border-slate-300 mb-0.5" />
                  <span>5 cm</span>
                </div>
              </div>

              {/* 3-Head Multi-Task Inference Readout */}
              <div className="mt-3.5 space-y-1.5 text-xs">
                {/* Head A */}
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-850 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="font-semibold text-slate-200">
                      {isVi ? "Head A: Tràn Dịch Màng Phổi" : "Head A: Pleural Effusion"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-100 font-bold tabular-nums">
                      78.4%
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-bold uppercase bg-slate-200 text-slate-950">
                      {isVi ? "DƯƠNG TÍNH" : "POSITIVE"}
                    </span>
                  </div>
                </div>

                {/* Head B */}
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-850 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    <span className="font-semibold text-slate-300">
                      {isVi ? "Head B: Sàng Lọc Lao Phổi" : "Head B: Tuberculosis Triage"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-400 tabular-nums">1.2%</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-bold uppercase bg-slate-900 text-slate-400 border border-slate-800">
                      {isVi ? "ÂM TÍNH" : "NEGATIVE"}
                    </span>
                  </div>
                </div>

                {/* Head C */}
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-850 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                    <span className="font-semibold text-slate-300">
                      {isVi ? "Head C: Cấp Cứu COVID-19" : "Head C: Acute COVID-19"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-400 tabular-nums">0.4%</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-bold uppercase bg-slate-900 text-slate-400 border border-slate-800">
                      {isVi ? "ÂM TÍNH" : "NEGATIVE"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Bottom Safety & Audit Telemetry */}
              <div className="mt-3 pt-2.5 border-t border-slate-850 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span className="flex items-center gap-1">
                  <Eye className="w-3 h-3 text-cyan-400" />
                  <span>{isVi ? "Năng lượng phế trường: " : "In-Lung Attention: "}</span>
                  <strong className="text-slate-200">84.6%</strong> [≥80%]
                </span>
                <span className="text-cyan-300 font-bold">
                  {isVi ? "Fail-Safe: HỢP LỆ (S_E = 12.84)" : "Fail-Safe: ACCEPT (S_E = 12.84)"}
                </span>
              </div>
            </div>

            {/* Scientific Figure Caption */}
            <p className="mt-2 text-[10px] text-slate-500 leading-tight text-center font-sans">
              {isVi
                ? "Hình 1: Trình diễn suy luận đa nhiệm 3-Head đồng thời và định vị tổn thương phế trường WSOL trên phim ngực thẳng PA."
                : "Figure 1: Unified 3-Head multi-task inference and WSOL anatomical localization on a posteroanterior chest radiograph."}
            </p>
          </div>
        </div>
      </div>

      {/* Subtle Bottom Page Footer Strip */}
      <div className="w-full max-w-7xl mx-auto pt-3 border-t border-slate-300 flex items-center justify-between text-[11px] text-slate-500 font-sans">
        <div>{dict.footer.copyright}</div>
        <div>{dict.footer.confidentiality}</div>
      </div>
    </section>
  );
}
