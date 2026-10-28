"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ParticleNetwork } from "./ParticleNetwork";
import { I18nContent } from "../data/i18n";
import { HERO_COUNTERS } from "../data/metrics";
import { Language } from "../types";
import confetti from "canvas-confetti";
import { Activity, ShieldCheck, Database, Zap, Sparkles } from "lucide-react";

interface HeroSectionProps {
  dict: I18nContent;
  lang: Language;
  onExploreClick: () => void;
}

export function HeroSection({ dict, lang, onExploreClick }: HeroSectionProps) {
  const [animatedValues, setAnimatedValues] = useState<number[]>([0, 0, 0, 0]);

  useEffect(() => {
    const targets = HERO_COUNTERS.map((c) => c.value);
    const duration = 1400; // ms
    const startTime = performance.now();

    const updateCounters = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo
      const factor = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);

      setAnimatedValues(targets.map((target) => target * factor));

      if (progress < 1) {
        requestAnimationFrame(updateCounters);
      }
    };

    const frameId = requestAnimationFrame(updateCounters);
    return () => cancelAnimationFrame(frameId);
  }, []);

  const triggerConfetti = () => {
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 },
      colors: ["#0284C7", "#059669", "#D97706", "#38BDF8"],
    });
    onExploreClick();
  };

  const getMetricIcon = (id: string) => {
    switch (id) {
      case "accuracy":
        return <Activity className="w-5 h-5 text-sky-600" />;
      case "loss":
        return <ShieldCheck className="w-5 h-5 text-emerald-600" />;
      case "dataset":
        return <Database className="w-5 h-5 text-amber-600" />;
      case "latency":
        return <Zap className="w-5 h-5 text-indigo-600" />;
      default:
        return <Sparkles className="w-5 h-5 text-sky-600" />;
    }
  };

  return (
    <section
      id="section-0"
      className="relative min-h-screen w-full snap-start bg-gradient-to-br from-[#F0FDF4] to-[#E0F2FE] flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden selection:bg-sky-200"
    >
      {/* Particle Canvas */}
      <ParticleNetwork />

      {/* Top HUD Header */}
      <div className="relative z-10 w-full max-w-7xl mx-auto pt-6 flex flex-wrap items-center justify-between gap-4">
        {/* Status Beacon Badge */}
        <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-white/80 backdrop-blur-md border border-slate-200/90 shadow-sm text-xs font-semibold text-slate-800">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
          <span className="tracking-wide uppercase">{dict.section0_hero.hudBadge}</span>
          <span className="text-slate-300">|</span>
          <span className="text-slate-600 hidden sm:inline">{dict.section0_hero.hudStatus}</span>
        </div>

        {/* Model Spec Badge */}
        <div className="hidden sm:inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/70 backdrop-blur-md border border-slate-200/80 text-xs font-mono text-slate-700 shadow-sm">
          <span className="w-2 h-2 rounded-full bg-sky-500" />
          <span>DenseNet-121 3-Head v3.2</span>
          <span className="text-slate-400 font-sans">•</span>
          <span className="text-slate-500">6.97M Params</span>
        </div>
      </div>

      {/* Main Hero Story Block */}
      <div className="relative z-10 w-full max-w-5xl mx-auto my-auto text-center py-8">
        <div className="inline-block px-4 py-1.5 rounded-full bg-sky-100/80 border border-sky-300 text-sky-900 text-xs font-bold uppercase tracking-wider mb-4 shadow-sm">
          {lang === "vi"
            ? "BÁO CÁO KHOA HỌC & NGHIỆM THU HỆ THỐNG"
            : "CLINICAL MONOGRAPH & SYSTEM ACCEPTANCE REPORT"}
        </div>

        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-[#0B1E36] tracking-tight leading-tight max-w-4xl mx-auto">
          {dict.section0_hero.mainTitle}
        </h1>

        <p className="mt-5 text-base sm:text-lg lg:text-xl text-slate-700 max-w-3xl mx-auto leading-relaxed font-normal">
          {dict.section0_hero.subtitle}
        </p>

        {/* CTAs */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <button
            type="button"
            onClick={triggerConfetti}
            className="px-6 py-3.5 rounded-xl bg-[#0B1E36] text-white font-semibold text-sm sm:text-base shadow-xl hover:bg-slate-900 hover:shadow-2xl hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-sky-400" />
            <span dangerouslySetInnerHTML={{ __html: dict.section0_hero.ctaExplore }} />
          </button>
          <Link
            href="/"
            className="px-6 py-3.5 rounded-xl bg-white/80 backdrop-blur-md border border-slate-300 text-slate-800 font-semibold text-sm sm:text-base shadow-md hover:bg-white hover:border-slate-400 hover:shadow-lg transition-all duration-200 flex items-center gap-2"
          >
            <span dangerouslySetInnerHTML={{ __html: dict.section0_hero.ctaMethodology }} />
          </Link>
        </div>
      </div>

      {/* 4 Live Animated Metric Counters */}
      <div className="relative z-10 w-full max-w-7xl mx-auto pb-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {HERO_COUNTERS.map((counter, idx) => {
            const rawVal = animatedValues[idx];
            const formatted =
              counter.decimals > 0
                ? rawVal.toFixed(counter.decimals)
                : Math.floor(rawVal).toLocaleString();

            return (
              <div
                key={counter.id}
                className="backdrop-blur-md bg-white/75 border border-slate-200/80 shadow-xl rounded-2xl p-5 hover:bg-white/90 hover:shadow-2xl hover:border-slate-300 transition-all duration-300 group flex flex-col justify-between"
              >
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="p-2 rounded-xl bg-slate-100/90 group-hover:scale-110 transition-transform">
                    {getMetricIcon(counter.id)}
                  </div>
                  {counter.badge && (
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {counter.badge[lang]}
                    </span>
                  )}
                </div>

                <div>
                  <div className="text-3xl sm:text-4xl font-extrabold text-[#0B1E36] font-mono tracking-tight flex items-baseline gap-1">
                    <span>{formatted}</span>
                    {counter.suffix && (
                      <span className="text-xl text-slate-600 font-semibold">
                        {counter.suffix}
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-bold text-slate-800 mt-1">
                    {counter.label[lang]}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 leading-snug">
                    {counter.subtext[lang]}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
