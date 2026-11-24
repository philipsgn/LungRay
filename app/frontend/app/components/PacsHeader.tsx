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
  onOpenAtlasTab?: () => void;
}

const MODELS: [string, string, string][] = [
  ["standard", "Standard CADx", "DenseNet-121 primary clinical backbone"],
  ["ag_mtcnet", "AG-MTCNet (Gated)", "Dense-UNet anatomically gated 512×512 network"],
  ["wsol", "WSOL Specialist", "Attention-regularized weak localization model"],
  ["resnet50", "ResNet-50", "Deep residual 50-layer representation"],
  ["ensemble", "Consensus Ensemble", "Multi-backbone soft voting consensus"],
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
  onOpenAtlasTab,
}: Props) {
  return (
    <header className="border-b border-[#1C2937] bg-[#0D1520] px-4 sm:px-6 py-3.5 select-none sticky top-0 z-40 shadow-xl shadow-black/40">
      <div className="mx-auto max-w-7xl space-y-3">
        {/* Top Row: Brand & System Connection */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#0A7A74] border border-[#3FD0C4]/60 font-mono text-sm font-bold text-white shadow-sm shadow-[#3FD0C4]/20">
              LR
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold tracking-tight text-[#E6EDF4]">
                  LungRay
                </h1>
                <span className="rounded-md border border-[#3FD0C4]/40 bg-[#0A7A74]/20 px-2 py-0.5 text-[11px] font-medium text-[#3FD0C4]">
                  Clinical Workstation
                </span>
              </div>
              <p className="text-xs text-[#8C9DB0]">
                Multi-Task Chest Radiography CADx &amp; WSOL Platform
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Quick Link to 3D Pipeline Atlas */}
            {onOpenAtlasTab ? (
              <button
                type="button"
                onClick={onOpenAtlasTab}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#1C2937] bg-[#111C2B] px-2.5 py-1 text-xs font-medium text-[#8C9DB0] transition-colors hover:border-[#3FD0C4] hover:text-[#3FD0C4]"
                title="Switch to interactive 3D Pipeline Atlas tab"
              >
                <span>3D Pipeline Atlas</span>
                <ExternalLink className="h-3 w-3" />
              </button>
            ) : (
              <a
                href="/pipeline-atlas.html"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#1C2937] bg-[#111C2B] px-2.5 py-1 text-xs font-medium text-[#8C9DB0] transition-colors hover:border-[#3FD0C4] hover:text-[#3FD0C4]"
                title="Open full interactive 3D WSOL Pipeline Atlas in a new tab"
              >
                <span>3D Pipeline Atlas</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            )}

            {/* API Health Status Pill */}
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
                  ? "Online (Port 8000)"
                  : connected === false
                  ? "Offline (Port 8000)"
                  : "Checking API..."}
              </span>
            </div>
          </div>
        </div>

        {/* Bottom Row: Model Engine Selector & Safety Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#1C2937]/60">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#8C9DB0] mr-1.5">
              AI Engine:
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
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition-all ${
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

          {/* Clinical Safety & Inference Toggles */}
          <div className="flex items-center gap-4 text-xs font-medium text-[#E6EDF4]">
            <label className="inline-flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={failsafeEnabled}
                disabled={disabled}
                onChange={(e) => onToggleFailsafe(e.target.checked)}
                className="rounded border-[#1C2937] bg-[#111C2B] text-[#3FD0C4] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <span
                className={failsafeEnabled ? "text-[#3FD0C4]" : "text-[#8C9DB0]"}
                title="Helmholtz Free Energy & Shannon Entropy OOD Gatekeeper"
              >
                Fail-Safe Guard
              </span>
            </label>

            <label className="inline-flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={ttaEnabled}
                disabled={disabled}
                onChange={(e) => onToggleTta(e.target.checked)}
                className="rounded border-[#1C2937] bg-[#111C2B] text-[#3FD0C4] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <span
                className={ttaEnabled ? "text-[#3FD0C4]" : "text-[#8C9DB0]"}
                title="3-Pass Test-Time Augmentation (Horizontal Flip + Scaling)"
              >
                3-Pass TTA
              </span>
            </label>
          </div>
        </div>
      </div>
    </header>
  );
}
