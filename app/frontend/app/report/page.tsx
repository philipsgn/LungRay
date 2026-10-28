"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Language } from "./types";
import { getDictionary } from "./data/i18n";
import { LanguageSwitcher } from "./components/LanguageSwitcher";
import { NavigationDots } from "./components/NavigationDots";
import { HeroSection } from "./components/HeroSection";
import { ProblemSection } from "./components/ProblemSection";
import { DatasetSection } from "./components/DatasetSection";
import { BalancingSection } from "./components/BalancingSection";
import { ArchitectureSection } from "./components/ArchitectureSection";
import { TrainingSection } from "./components/TrainingSection";
import { BenchmarkSection } from "./components/BenchmarkSection";

export default function ReportPage() {
  const [lang, setLang] = useState<Language>("en");
  const [currentSection, setCurrentSection] = useState<number>(0);
  const totalSections = 7;

  const dict = getDictionary(lang);

  const scrollTo = useCallback((index: number) => {
    if (index < 0 || index >= totalSections) return;
    setCurrentSection(index);
    const el = document.getElementById(`section-${index}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  }, [totalSections]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't scroll if inside an input or textarea
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        setCurrentSection((prev) => {
          const next = Math.min(prev + 1, totalSections - 1);
          const el = document.getElementById(`section-${next}`);
          if (el) el.scrollIntoView({ behavior: "smooth" });
          return next;
        });
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        setCurrentSection((prev) => {
          const next = Math.max(prev - 1, 0);
          const el = document.getElementById(`section-${next}`);
          if (el) el.scrollIntoView({ behavior: "smooth" });
          return next;
        });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [totalSections]);

  // IntersectionObserver to sync activeSection with scroll
  useEffect(() => {
    const observerCallback: IntersectionObserverCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          const match = id.match(/section-(\d+)/);
          if (match) {
            const sectionIdx = parseInt(match[1], 10);
            setCurrentSection(sectionIdx);
          }
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, {
      threshold: 0.45,
    });

    for (let i = 0; i < totalSections; i++) {
      const el = document.getElementById(`section-${i}`);
      if (el) observer.observe(el);
    }

    return () => observer.disconnect();
  }, [totalSections]);

  return (
    <div className="w-full min-h-screen lg:h-screen lg:overflow-y-scroll lg:snap-y lg:snap-mandatory text-[#0B1E36] font-sans antialiased selection:bg-sky-200">
      {/* Top Clinical Bar */}
      <header className="fixed top-0 left-0 right-0 h-12 bg-white/85 backdrop-blur-md border-b border-slate-200/70 z-40 flex items-center justify-between px-6 sm:px-8 text-xs shadow-xs">
        <div className="flex items-center gap-3 sm:gap-4 overflow-hidden">
          <Link
            href="/"
            className="font-bold text-slate-700 hover:text-slate-950 transition flex items-center gap-1.5 shrink-0"
          >
            <span>&larr;</span>
            <span>{dict.nav.backToPacs}</span>
          </Link>
          <span className="text-slate-300 hidden sm:inline">|</span>
          <span className="font-extrabold text-[#0B1E36] tracking-wider uppercase text-[11px] truncate hidden md:inline">
            {dict.nav.instituteName} &bull; {dict.nav.reportTitle}
          </span>
        </div>

        {/* Space reservation for fixed LanguageSwitcher at top-right */}
        <div className="w-24 shrink-0" />
      </header>

      {/* Fixed Capsule Language Switcher at Top-Right */}
      <LanguageSwitcher currentLang={lang} onLanguageChange={setLang} />

      {/* Side Dot Navigation Rail */}
      <NavigationDots
        activeSection={currentSection}
        sectionNames={dict.nav.sectionNames}
        onSelectSection={scrollTo}
      />

      {/* 7 Modular Interactive Storytelling Sections */}
      <main className="w-full pt-12 lg:pt-0">
        <HeroSection dict={dict} lang={lang} onExploreClick={() => scrollTo(1)} />
        <ProblemSection dict={dict} lang={lang} />
        <DatasetSection dict={dict} lang={lang} />
        <BalancingSection dict={dict} lang={lang} />
        <ArchitectureSection dict={dict} lang={lang} />
        <TrainingSection dict={dict} lang={lang} />
        <BenchmarkSection dict={dict} lang={lang} />
      </main>

      {/* Minimal Academic Footer */}
      <footer className="w-full py-4 px-6 sm:px-10 bg-[#0B1E36] text-white text-xs flex flex-wrap items-center justify-between gap-2 border-t border-slate-800">
        <div className="text-slate-400">{dict.footer.copyright}</div>
        <div className="text-slate-400 font-mono text-[11px]">
          {dict.footer.confidentiality}
        </div>
      </footer>
    </div>
  );
}
