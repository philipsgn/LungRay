"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { ExternalLink, History, Settings, ShieldCheck, Sparkles } from "lucide-react";

interface Props {
  selectedModel: string;
  availableModels?: string[];
  onSelectModel: (model: string) => void;
  failsafeEnabled: boolean;
  onToggleFailsafe: (enabled: boolean) => void;
  ttaEnabled: boolean;
  onToggleTta: (enabled: boolean) => void;
  connected: boolean | null;
  disabled: boolean;
  historyCount?: number;
  onOpenHistory?: () => void;
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
  availableModels = ["standard"],
  onSelectModel,
  failsafeEnabled,
  onToggleFailsafe,
  ttaEnabled,
  onToggleTta,
  connected,
  disabled,
  historyCount = 0,
  onOpenHistory,
}: Props) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!settingsOpen) return;
    const onDocClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setSettingsOpen(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [settingsOpen]);

  const visibleModels = MODELS.filter(([id]) => availableModels.includes(id));

  return (
    <header className="border-b border-[#1C2937] bg-[#0D1520]/95 backdrop-blur-md px-4 sm:px-6 lg:px-8 py-2.5 select-none sticky top-0 z-40 shadow-lg shadow-black/30">
      <div className="w-full max-w-[1750px] mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Left: Flowing Artistic Brand Lockup */}
        <div className="flex items-center gap-3">
          <Image
            src="/brand-icon.png"
            alt="LungRay"
            width={40}
            height={40}
            className="h-9 w-9 object-contain drop-shadow-[0_0_10px_rgba(63,208,196,0.35)] shrink-0"
            priority
          />
          <div className="leading-none">
            <h1 className="font-brand text-2xl font-semibold tracking-tight leading-none flex items-baseline">
              <span className="text-[#F1F5F9]">Lung</span>
              <span className="italic font-bold bg-gradient-to-r from-[#3FD0C4] via-[#5EEAD4] to-[#99F6E4] bg-clip-text text-transparent pr-1">
                Ray
              </span>
            </h1>
            <p className="text-[10.5px] text-[#8C9DB0] mt-1 tracking-wider uppercase font-medium">
              CXR Diagnostics
            </p>
          </div>
        </div>

        {/* Right: Purposeful Single-Row Controls */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          {onOpenHistory && (
            <button
              type="button"
              onClick={onOpenHistory}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#1C2937] bg-[#111C2B] px-3 py-1.5 text-xs font-medium text-[#CBD5E1] transition-colors hover:border-[#3FD0C4]/60 hover:text-[#3FD0C4]"
              title="Switch between scans analyzed in this session"
            >
              <History className="h-3.5 w-3.5 text-[#3FD0C4]" />
              <span>History{historyCount > 0 ? ` (${historyCount})` : ""}</span>
            </button>
          )}

          <a
            href="/pipeline-atlas.html"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[#1C2937] bg-[#111C2B] px-3 py-1.5 text-xs font-medium text-[#8C9DB0] transition-colors hover:border-[#3FD0C4]/60 hover:text-[#3FD0C4]"
            title="Open Architecture & 3D Atlas"
          >
            <span>Atlas</span>
            <ExternalLink className="h-3 w-3" />
          </a>

          {/* Settings Popover (Safety Gate, Precision Mode & Model Selector) */}
          <div className="relative" ref={popoverRef}>
            <button
              type="button"
              onClick={() => setSettingsOpen((v) => !v)}
              className={`inline-flex items-center justify-center rounded-lg border p-1.5 transition-colors ${
                settingsOpen
                  ? "border-[#3FD0C4] bg-[#0A7A74]/25 text-[#3FD0C4]"
                  : "border-[#1C2937] bg-[#111C2B] text-[#8C9DB0] hover:border-[#3FD0C4]/60 hover:text-[#E6EDF4]"
              }`}
              title="Analysis Settings"
              aria-label="Analysis Settings"
            >
              <Settings className="h-4 w-4" />
            </button>

            {settingsOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-xl border border-[#1C2937] bg-[#0D1520] p-4 shadow-2xl shadow-black/70 z-50 space-y-4">
                <div className="text-[11px] font-bold uppercase tracking-wider text-[#8C9DB0]">
                  Analysis Settings
                </div>

                {/* Safety Gate Toggle */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="text-xs font-semibold text-[#E6EDF4] flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-[#3FD0C4]" />
                      Safety Gate
                    </div>
                    <p className="text-[11px] text-[#8C9DB0] leading-snug">
                      Auto-reject non-X-ray or corrupted scans
                    </p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={failsafeEnabled}
                    disabled={disabled}
                    onClick={() => onToggleFailsafe(!failsafeEnabled)}
                    className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border transition-colors ${
                      failsafeEnabled
                        ? "bg-[#0A7A74] border-[#3FD0C4]"
                        : "bg-[#162233] border-[#263547]"
                    } disabled:opacity-50`}
                  >
                    <span
                      className={`inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform mt-[1px] ${
                        failsafeEnabled ? "translate-x-4" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>

                {/* Precision Mode Toggle */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="text-xs font-semibold text-[#E6EDF4] flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-[#3FD0C4]" />
                      Precision Mode
                    </div>
                    <p className="text-[11px] text-[#8C9DB0] leading-snug">
                      3-pass multi-view analysis for higher accuracy
                    </p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={ttaEnabled}
                    disabled={disabled}
                    onClick={() => onToggleTta(!ttaEnabled)}
                    className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border transition-colors ${
                      ttaEnabled
                        ? "bg-[#0A7A74] border-[#3FD0C4]"
                        : "bg-[#162233] border-[#263547]"
                    } disabled:opacity-50`}
                  >
                    <span
                      className={`inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform mt-[1px] ${
                        ttaEnabled ? "translate-x-4" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>

                {/* Model Selector (only when >1 model is exposed) */}
                {visibleModels.length > 1 && (
                  <div className="pt-3 border-t border-[#1C2937] space-y-2">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-[#8C9DB0]">
                      Active Model
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {visibleModels.map(([id, label, desc]) => (
                        <button
                          key={id}
                          type="button"
                          disabled={disabled}
                          onClick={() => onSelectModel(id)}
                          title={desc}
                          className={`rounded-md border px-2.5 py-1 text-[11px] font-medium transition-all ${
                            selectedModel === id
                              ? "border-[#3FD0C4] bg-[#0A7A74] text-white"
                              : "border-[#1C2937] bg-[#111C2B] text-[#8C9DB0] hover:text-[#E6EDF4]"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Concise Status Indicator */}
          <div
            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
              connected === true
                ? "border-emerald-500/40 bg-emerald-950/40 text-emerald-300"
                : connected === false
                ? "border-rose-500/40 bg-rose-950/40 text-rose-300"
                : "border-slate-700 bg-slate-900 text-slate-400"
            }`}
            title={
              connected === true
                ? "Connected to live inference server"
                : connected === false
                ? "Inference server unavailable"
                : "Checking server status"
            }
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
              {connected === true ? "Online" : connected === false ? "Offline" : "Connecting"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
