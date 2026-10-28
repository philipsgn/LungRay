"use client";

import React, { useState, useEffect, ReactNode } from "react";

interface DynamicChartWrapperProps {
  children: ReactNode;
  fallbackHeight?: number | string;
}

export function DynamicChartWrapper({
  children,
  fallbackHeight = 320,
}: DynamicChartWrapperProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div
        style={{ height: fallbackHeight }}
        className="w-full rounded-2xl bg-slate-100/60 backdrop-blur-sm border border-slate-200/50 animate-pulse flex flex-col items-center justify-center text-xs text-slate-400 font-mono gap-2"
      >
        <div className="w-6 h-6 border-2 border-slate-300 border-t-sky-500 rounded-full animate-spin" />
        <span>Loading Visualizer...</span>
      </div>
    );
  }

  return <>{children}</>;
}
