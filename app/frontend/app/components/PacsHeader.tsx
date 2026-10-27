"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { checkHealth } from "../lib/api";

export default function PacsHeader() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  return (
    <header className="bg-slate-900 border-b border-slate-700 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-sky-500 flex items-center justify-center font-bold text-white">
          LR
        </div>
        <h1 className="text-xl font-semibold text-white tracking-wide">
          LungRay PACS Viewer
        </h1>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <Link
          href="/report"
          className="px-3 py-1.5 rounded-md text-xs font-semibold text-sky-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
        >
          Báo Cáo Nghiệm Thu
        </Link>
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Backend API:</span>
          {connected === null && (
            <span className="text-slate-300">Checking...</span>
          )}
          {connected === true && (
            <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected
            </span>
          )}
          {connected === false && (
            <span className="inline-flex items-center gap-1 text-rose-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              Offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
