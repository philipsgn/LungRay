"use client";

import { csvRow } from "../lib/pacsUtils";
import React from "react";
import { X, ShieldCheck, Download, Activity } from "lucide-react";

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: "STUDY_LOADED" | "AI_INFERENCE" | "OOD_LOCKOUT" | "CTR_MEASURED" | "REPORT_SIGNED_OFF";
  studyId: string;
  model: string;
  detail: string;
  latencyMs?: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  logs: AuditLogEntry[];
}

export default function AuditTrailModal({ isOpen, onClose, logs }: Props) {
  if (!isOpen) return null;

  const exportCsv = () => {
    const header = "ID,Timestamp,Action,StudyID,Model,LatencyMs,Detail\n";
    const rows = logs
      .map(log => csvRow([log.id, log.timestamp, log.action, log.studyId, log.model, log.latencyMs ?? "", log.detail]))
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lungray_audit_trail_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const badgeStyle = (action: AuditLogEntry["action"]) => {
    switch (action) {
      case "OOD_LOCKOUT":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "REPORT_SIGNED_OFF":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      case "AI_INFERENCE":
        return "bg-[#3FD0C4]/20 text-[#3FD0C4] border-[#3FD0C4]/40";
      default:
        return "bg-slate-700/40 text-slate-300 border-slate-600";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl bg-[#0D1520] border border-[#1C2937] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#1C2937] flex items-center justify-between bg-[#090F17]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[#0A7A74]/20 border border-[#3FD0C4]/30 text-[#3FD0C4]">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#E6EDF4] uppercase tracking-wider">
                Clinical Compliance & Telemetry Audit Log
              </h2>
              <p className="text-xs text-[#8C9DB0] mt-0.5">
                Immutable session trace for model inference, OOD gate events, and physician sign-offs
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={exportCsv}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] text-xs font-medium text-[#E6EDF4] hover:border-[#3FD0C4] transition-colors"
            >
              <Download className="h-3.5 w-3.5 text-[#3FD0C4]" />
              Export CSV
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#8C9DB0] hover:text-white hover:bg-[#162233] transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto p-4">
          {logs.length === 0 ? (
            <div className="text-center py-12 text-xs text-[#8C9DB0] flex flex-col items-center gap-2">
              <Activity className="h-8 w-8 opacity-30" />
              <span>No clinical events recorded in this session yet.</span>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#1C2937] text-[10px] font-mono uppercase tracking-wider text-[#8C9DB0]">
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Study ID</th>
                  <th className="py-2.5 px-3">Model / Engine</th>
                  <th className="py-2.5 px-3">Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1C2937]/60 text-xs">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-[#111C2B]/60 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-[#8C9DB0] whitespace-nowrap">
                      {log.timestamp}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${badgeStyle(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-[#E6EDF4]">
                      {log.studyId}
                    </td>
                    <td className="py-2.5 px-3 text-[#94A3B8]">
                      {log.model}
                      {log.latencyMs ? ` (${log.latencyMs.toFixed(0)}ms)` : ""}
                    </td>
                    <td className="py-2.5 px-3 text-[#CBD5E1]">{log.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
