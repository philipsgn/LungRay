"use client";

import React from "react";
import { ExternalLink } from "lucide-react";

interface Props {
  selectedModel: string;
  onSelectModel: (model: string) => void;
  failsafeEnabled: boolean;
  onToggleFailsafe: (enabled: boolean) => void;
  ttaEnabled: boolean;
  onToggleTta: (enabled: boolean) => void;
  connected: boolean | null;
  disabled: boolean;
}

const MODELS: [string, string, string][] = [
  ["standard", "Standard CADx", "DenseNet-121 primary clinical backbone"],
  ["ag_mtcnet", "AG-MTCNet", "Anatomically gated dual-pathway network"],
  ["wsol", "WSOL Specialist", "Attention-regularized weak localization model"],
  ["resnet50", "ResNet-50", "Residual 50-layer representation"],
  ["ensemble", "Consensus Ensemble", "Multi-backbone consensus voting"],
];

export default function PacsHeader({
  selectedModel,
  onSelectModel,
  failsafeEnabled,
  onToggleFailsafe,
  ttaEnabled,
  onToggleTta,
  connected,
  disabled,
}: Props) {
  return (
    <header className="border-b border-[#1C2937] bg-[#0D1520] px-3 sm:px-6 lg:px-8 py-3 select-none sticky top-0 z-40 shadow-xl shadow-black/40">
      <div className="w-full max-w-[1750px] mx-auto space-y-2.5">
        {/* Top Row: Brand, Architecture Link & System Status */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0A7A74] border border-[#3FD0C4]/60 font-mono text-sm font-bold text-white shadow-sm shadow-[#3FD0C4]/20">
              LR
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold tracking-tight text-[#E6EDF4]">
                  LungRay
                </h1>
                <span className="rounded border border-[#3FD0C4]/40 bg-[#0A7A74]/20 px-1.5 py-0.2 text-[10px] font-semibold uppercase tracking-wider text-[#3FD0C4]">
                  Workstation
                </span>
              </div>
              <p className="text-[11px] text-[#8C9DB0]">
                Intelligent Chest Diagnostics
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Direct Link to Architecture 3D Atlas in a Separate Tab */}
            <a
              href="/pipeline-atlas.html"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#1C2937] bg-[#111C2B] px-2.5 py-1 text-xs font-medium text-[#8C9DB0] transition-colors hover:border-[#3FD0C4] hover:text-[#3FD0C4]"
              title="Open interactive 3D Pipeline Atlas in a new tab"
            >
              <span>Architecture Atlas</span>
              <ExternalLink className="h-3 w-3" />
            </a>

            {/* Clean System Status Pill (No Port or Backend Jargon) */}
            <div
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-mono font-medium ${
                connected === true
                  ? "border-emerald-500/40 bg-emerald-950/40 text-emerald-300"
                  : connected === false
                  ? "border-rose-500/40 bg-rose-950/40 text-rose-300"
                  : "border-slate-700 bg-slate-900 text-slate-400"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  connected === true
                    ? "bg-emerald-400 animate-pulse"
                    : connected === false
                    ? "bg-rose-400"
                    : "bg-slate-400"
                }`}
              />
              <span>
                {connected === true
                  ? "System Online"
                  : connected === false
                  ? "Disconnected"
                  : "Connecting..."}
              </span>
            </div>
          </div>
        </div>

        {/* Bottom Row: AI Engine Selector & Minimalist Controls */}
        <div className="flex flex-wrap items-center justify-between gap-2.5 pt-1 border-t border-[#1C2937]/60">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#8C9DB0] mr-1">
              Engine:
            </span>
            {MODELS.map(([id, label, desc]) => {
              const isSelected = selectedModel === id;
              return (
                <button
                  key={id}
                  type="button"
                  disabled={disabled}
                  onClick={() => onSelectModel(id)}
                  title={desc}
                  className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-all ${
                    isSelected
                      ? "border-[#3FD0C4] bg-[#0A7A74] text-white shadow-sm shadow-[#3FD0C4]/25"
                      : "border-[#1C2937] bg-[#111C2B] text-[#8C9DB0] hover:border-slate-600 hover:text-[#E6EDF4]"
                  } disabled:opacity-50`}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {/* Minimalist Clinical Safety & Precision Toggles */}
          <div className="flex items-center gap-3.5 text-xs font-medium text-[#E6EDF4]">
            <label className="inline-flex items-center gap-1.5 cursor-pointer" title="Automatic safety gate for out-of-distribution or corrupt radiographs">
              <input
                type="checkbox"
                checked={failsafeEnabled}
                disabled={disabled}
                onChange={(e) => onToggleFailsafe(e.target.checked)}
                className="rounded border-[#1C2937] bg-[#111C2B] text-[#3FD0C4] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <span className={failsafeEnabled ? "text-[#3FD0C4]" : "text-[#8C9DB0]"}>
                Safety Gate
              </span>
            </label>

            <label className="inline-flex items-center gap-1.5 cursor-pointer" title="Multi-scale test-time augmentation for higher localization precision">
              <input
                type="checkbox"
                checked={ttaEnabled}
                disabled={disabled}
                onChange={(e) => onToggleTta(e.target.checked)}
                className="rounded border-[#1C2937] bg-[#111C2B] text-[#3FD0C4] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <span className={ttaEnabled ? "text-[#3FD0C4]" : "text-[#8C9DB0]"}>
                Precision Mode
              </span>
            </label>
          </div>
        </div>
      </div>
    </header>
  );
}
