"use client";

import React, { useState } from "react";
import { I18nContent } from "../data/i18n";
import { ARCHITECTURE_NODES } from "../data/metrics";
import { ArchitectureNode, Language } from "../types";
import { Network, Cpu, GitFork, X, Info, Layers } from "lucide-react";

interface ArchitectureSectionProps {
  dict: I18nContent;
  lang: Language;
}

export function ArchitectureSection({ dict, lang }: ArchitectureSectionProps) {
  const [selectedNode, setSelectedNode] = useState<ArchitectureNode | null>(ARCHITECTURE_NODES[1]); // DenseNet default
  const [activeTaskSim, setActiveTaskSim] = useState<"A" | "B" | "C">("A");

  const getNodeColor = (color: string) => {
    switch (color) {
      case "sky":
        return "border-slate-300 bg-white text-slate-900 hover:border-slate-500";
      case "emerald":
        return "border-emerald-300 bg-emerald-50 text-emerald-950 hover:border-emerald-500";
      case "amber":
        return "border-amber-300 bg-amber-50 text-amber-950 hover:border-amber-500";
      default:
        return "border-slate-300 bg-white text-slate-900 hover:border-slate-500";
    }
  };

  return (
    <section
      id="section-4"
      className="relative min-h-screen w-full snap-start bg-[#F8FAFC] border-b border-slate-200 flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden text-[#0F172A]"
    >
      <div className="w-full max-w-7xl mx-auto my-auto py-6">
        {/* Section Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div className="max-w-2xl">
            <div className="inline-block px-3 py-1 rounded bg-slate-100 border border-slate-300 text-slate-800 text-[11px] font-mono uppercase tracking-widest mb-3">
              {dict.section4_architecture.tag}
            </div>
            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-[#0F172A]">
              {dict.section4_architecture.title}
            </h2>
            <p className="mt-2 text-slate-600 text-sm sm:text-base leading-relaxed">
              {dict.section4_architecture.description}
            </p>
          </div>

          {/* Masked Gradient Backprop Task Simulator */}
          <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-300 shadow-sm text-xs font-mono">
            <span className="text-slate-500 text-[11px] px-2 font-mono hidden sm:inline">
              Simulate Active Task:
            </span>
            <button
              type="button"
              onClick={() => setActiveTaskSim("A")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeTaskSim === "A"
                  ? "bg-[#0F172A] text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Task A (NIH 14)
            </button>
            <button
              type="button"
              onClick={() => setActiveTaskSim("B")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeTaskSim === "B"
                  ? "bg-[#0F172A] text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Task B (TB)
            </button>
            <button
              type="button"
              onClick={() => setActiveTaskSim("C")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeTaskSim === "C"
                  ? "bg-[#0F172A] text-white shadow-sm font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Task C (COVIDx)
            </button>
          </div>
        </div>

        {/* 2-Column Main Layout: DAG Diagram + Slide-out Layer Drawer */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left Column: Interactive Network Flow Diagram */}
          <div className="lg:col-span-7 bg-white border border-slate-300 shadow-sm rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#0F172A] uppercase tracking-wide font-mono flex items-center gap-2">
                  <Network className="w-4 h-4 text-slate-800" />
                  <span>
                    {lang === "vi"
                      ? "Sơ Đồ Dòng Tín Hiệu & Cách Ly Gradient Đa Nhiệm"
                      : "Multi-Task Signal & Masked Gradient Flow Diagram"}
                  </span>
                </h3>
                <span className="text-xs text-slate-500 font-mono">
                  {lang === "vi" ? "Click để xem tham số tầng" : "Click node to inspect"}
                </span>
              </div>

              {/* Shared Backbone Pipeline (Linear Chain) */}
              <div className="space-y-3 mb-6">
                <div className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">
                  {lang === "vi" ? "1. Khối Mã Hóa Dùng Chung (Shared Encoder)" : "1. Shared Encoder Chain"}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
                  {ARCHITECTURE_NODES.slice(0, 4).map((node) => {
                    const isSelected = selectedNode?.id === node.id;
                    return (
                      <button
                        key={node.id}
                        type="button"
                        onClick={() => setSelectedNode(node)}
                        className={`p-3 rounded-xl text-left border transition-all ${getNodeColor(
                          node.color
                        )} ${
                          isSelected
                            ? "ring-2 ring-[#0F172A] shadow-md"
                            : "shadow-sm hover:border-slate-400"
                        }`}
                      >
                        <div className="text-[10px] font-mono font-bold text-slate-500 uppercase">
                          {node.tensorDim}
                        </div>
                        <div className="text-xs font-extrabold text-[#0F172A] mt-0.5">
                          {node.label[lang]}
                        </div>
                        <div className="text-[10px] font-mono text-slate-600 truncate mt-1">
                          {node.params}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Latent Branching Vector */}
              <div className="flex items-center justify-center my-3 gap-2 text-slate-400">
                <div className="h-0.5 w-16 bg-slate-300" />
                <div className="px-3 py-1 rounded bg-slate-100 border border-slate-300 text-[11px] font-mono font-bold text-slate-800 flex items-center gap-1.5">
                  <GitFork className="w-3.5 h-3.5 text-slate-700" />
                  <span>1024-dim Latent Bottleneck</span>
                </div>
                <div className="h-0.5 w-16 bg-slate-300" />
              </div>

              {/* 3 Dedicated Classification Heads (Branching) */}
              <div className="space-y-2">
                <div className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">
                  {lang === "vi"
                    ? "2. Ba Nhánh Phân Loại Chuyên Biệt (Decoupled Heads)"
                    : "2. Decoupled Clinical Task Heads"}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {ARCHITECTURE_NODES.slice(5).map((node, hIdx) => {
                    const taskLetter = ["A", "B", "C"][hIdx];
                    const isTaskActive = activeTaskSim === taskLetter;
                    const isSelected = selectedNode?.id === node.id;

                    return (
                      <button
                        key={node.id}
                        type="button"
                        onClick={() => setSelectedNode(node)}
                        className={`p-4 rounded-xl text-left border transition-all relative overflow-hidden ${getNodeColor(
                          node.color
                        )} ${
                          isSelected ? "ring-2 ring-[#0F172A] shadow-md" : "shadow-sm hover:border-slate-400"
                        } ${!isTaskActive ? "opacity-50 saturate-50" : "opacity-100 ring-1 ring-slate-800"}`}
                      >
                        {/* Task Active Indicator Beacon */}
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white border border-slate-200">
                            {node.tensorDim}
                          </span>
                          {isTaskActive ? (
                            <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-300 flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                              Active Grad
                            </span>
                          ) : (
                            <span className="text-[10px] font-mono font-semibold text-slate-400">
                              Masked = 0
                            </span>
                          )}
                        </div>

                        <div className="text-xs font-bold text-[#0F172A] mt-1">
                          {node.label[lang]}
                        </div>
                        <div className="text-[11px] font-mono text-slate-600 mt-0.5 line-clamp-1">
                          {node.activation}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Gradient Masking Architecture Rationale Callout */}
            <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-center gap-2">
              <Info className="w-4 h-4 text-slate-700 shrink-0" />
              <span className="font-mono text-[11px]">
                {lang === "vi"
                  ? "Cơ chế Masked Backpropagation: Chỉ có Task được kích hoạt mới truyền ngược gradient về Shared Encoder, đảm bảo không xung đột tối ưu giữa 3 tập dữ liệu."
                  : "Masked Backpropagation: Gradients route exclusively to the active head and shared backbone, eliminating multi-task gradient interference."}
              </span>
            </div>
          </div>

          {/* Right Column: Slide-out / Sticky Layer Parameter Drawer */}
          <div className="lg:col-span-5 bg-white border border-slate-300 shadow-sm rounded-2xl p-6 flex flex-col justify-between">
            {selectedNode ? (
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-md bg-slate-100">
                      <Cpu className="w-4 h-4 text-slate-800" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#0F172A]">
                        {selectedNode.label[lang]}
                      </h3>
                      <p className="text-[11px] font-mono text-slate-500">
                        {selectedNode.modulePath}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedNode(null)}
                    className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Layer Parameter Spec Grid */}
                <div className="grid grid-cols-2 gap-2.5 mb-4 font-mono">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                      {dict.section4_architecture.tensorDimensions}
                    </span>
                    <span className="text-xs font-bold text-slate-900 mt-0.5 block">
                      {selectedNode.tensorDim}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                      {dict.section4_architecture.parameterCount}
                    </span>
                    <span className="text-xs font-bold text-slate-900 mt-0.5 block">
                      {selectedNode.params}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 col-span-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                      {dict.section4_architecture.activationFunction}
                    </span>
                    <span className="text-xs font-bold text-slate-900 mt-0.5 block">
                      {selectedNode.activation}
                    </span>
                  </div>

                  {selectedNode.lossFn && (
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 col-span-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-900 block">
                        Loss Function Formulation
                      </span>
                      <span className="text-xs font-bold text-emerald-950 mt-0.5 block">
                        {selectedNode.lossFn}
                      </span>
                    </div>
                  )}
                </div>

                {/* Description & Clinical Rationale */}
                <div className="space-y-3">
                  <div>
                    <h5 className="text-xs font-mono font-bold text-slate-800 uppercase tracking-wide mb-1">
                      {lang === "vi" ? "Chức Năng Kỹ Thuật" : "Technical Role"}
                    </h5>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {selectedNode.description[lang]}
                    </p>
                  </div>

                  <div>
                    <h5 className="text-xs font-mono font-bold text-slate-800 uppercase tracking-wide mb-1">
                      {lang === "vi" ? "Cơ Sở Thiết Kế Lâm Sàng" : "Clinical Rationale"}
                    </h5>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {selectedNode.rationale[lang]}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="my-auto text-center py-12 text-slate-400">
                <Layers className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-xs font-mono">
                  {lang === "vi"
                    ? "Chọn bất kỳ tầng mạng nào trên sơ đồ để xem thông số chi tiết"
                    : "Select any neural layer on the diagram to inspect parameters"}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
