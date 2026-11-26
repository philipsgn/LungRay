"use client";

import React, { useMemo, useState } from "react";
import { History, Search, X, Clock, CheckCircle2, ShieldAlert, ArrowRight, Trash2 } from "lucide-react";
import { PredictionResponse } from "../types";

export interface ScanHistoryItem {
  id: string;
  filename: string;
  previewUrl: string;
  analyzedAt: string;
  summaryLabel: string;
  tone: "clear" | "alert" | "critical" | "rejected";
  file: File;
  prediction: PredictionResponse;
  heatmapUrl: string | null;
  heatmapHasAlpha: boolean;
  contourUrl: string | null;
  contourHasAlpha: boolean;
  inLungRatio: number | null;
  selectedHead: string;
  selectedClass: number;
  selectedDiseaseName: string;
  signedOffAt: string | null;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  items: ScanHistoryItem[];
  activeId: string | null;
  onSelect: (item: ScanHistoryItem) => void;
  onClear: () => void;
}

export default function ScanHistoryDrawer({
  isOpen,
  onClose,
  items,
  activeId,
  onSelect,
  onClear,
}: Props) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (item) =>
        item.filename.toLowerCase().includes(q) ||
        item.summaryLabel.toLowerCase().includes(q)
    );
  }, [items, query]);

  if (!isOpen) return null;

  const badgeClass = (tone: ScanHistoryItem["tone"]) => {
    switch (tone) {
      case "critical":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "alert":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "rejected":
        return "bg-purple-500/20 text-purple-300 border-purple-500/40";
      default:
        return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-md bg-[#0D1520] border-l border-[#1C2937] h-full flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#1C2937] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-[#E6EDF4] flex items-center gap-2">
              <History className="h-4 w-4 text-[#3FD0C4]" />
              Scan History
            </h2>
            <p className="text-[11px] text-[#8C9DB0] mt-0.5">
              {items.length === 0
                ? "Analyzed scans from this session appear here"
                : `${items.length} analyzed ${items.length === 1 ? "scan" : "scans"} in this session`}
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {items.length > 0 && (
              <button
                type="button"
                onClick={onClear}
                className="p-1.5 rounded-lg text-[#8C9DB0] hover:text-rose-300 hover:bg-rose-950/40 transition-colors"
                title="Clear session history"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#8C9DB0] hover:text-white hover:bg-[#162233] transition-colors"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Search */}
        {items.length > 0 && (
          <div className="p-3.5 border-b border-[#1C2937] bg-[#090F17]">
            <div className="relative">
              <Search className="h-3.5 w-3.5 text-[#8C9DB0] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter by filename or finding..."
                className="w-full rounded-lg border border-[#1C2937] bg-[#111C2B] pl-9 pr-3 py-2 text-xs text-[#E6EDF4] placeholder-[#566475] focus:border-[#3FD0C4] focus:outline-none"
              />
            </div>
          </div>
        )}

        {/* List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filtered.map((item) => {
            const isActive = activeId === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  onSelect(item);
                  onClose();
                }}
                className={`w-full text-left p-3 rounded-xl border transition-all group flex items-center gap-3 ${
                  isActive
                    ? "bg-[#112432] border-[#3FD0C4]"
                    : "bg-[#111C2B] border-[#1C2937] hover:border-[#3FD0C4]/50 hover:bg-[#132031]"
                }`}
              >
                {/* Real Thumbnail */}
                <div className="h-14 w-14 rounded-lg overflow-hidden bg-black border border-[#1C2937] shrink-0">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.previewUrl}
                    alt={item.filename}
                    className="h-full w-full object-cover"
                  />
                </div>

                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-[#E6EDF4] truncate">
                      {item.filename}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] text-[#8C9DB0] shrink-0">
                      <Clock className="h-3 w-3" />
                      {item.analyzedAt}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${badgeClass(item.tone)}`}>
                      {item.tone === "rejected" && <ShieldAlert className="inline h-2.5 w-2.5 mr-1" />}
                      {item.summaryLabel}
                    </span>
                    {item.signedOffAt && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-400">
                        <CheckCircle2 className="h-3 w-3" /> Signed
                      </span>
                    )}
                  </div>
                </div>

                <ArrowRight className="h-3.5 w-3.5 text-[#3FD0C4] opacity-50 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all shrink-0" />
              </button>
            );
          })}

          {items.length === 0 && (
            <div className="text-center py-14 px-6 space-y-2">
              <History className="h-8 w-8 text-[#566475] mx-auto opacity-50" />
              <p className="text-xs font-medium text-[#94A3B8]">No scans analyzed yet</p>
              <p className="text-[11px] text-[#566475] leading-relaxed">
                Upload a chest X-ray or pick a sample case and run analysis. Every scan is cached here so you can switch back instantaneously.
              </p>
            </div>
          )}

          {items.length > 0 && filtered.length === 0 && (
            <div className="text-center py-10 text-xs text-[#8C9DB0]">
              No matching scans found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
