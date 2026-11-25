"use client";

import React, { useMemo, useState } from "react";
import { Search, X, Clock, AlertCircle, CheckCircle2, FileImage, ArrowRight } from "lucide-react";

export type StudyPriority = "STAT" | "URGENT" | "ROUTINE" | "QA";
export type StudyStatus = "Pending" | "AI Screened" | "Signed Off";

export interface StudyRecord {
  studyId: string;
  patientId: string;
  ageSex: string;
  modality: string;
  indication: string;
  acquiredAt: string;
  priority: StudyPriority;
  status: StudyStatus;
  sampleUrl: string;
  filename: string;
}

export const INITIAL_WORKLIST: StudyRecord[] = [
  {
    studyId: "STD-2026-8842",
    patientId: "PT-31084",
    ageSex: "38Y • M",
    modality: "DX Chest PA",
    indication: "Persistent cough, hemoptysis — rule out active TB",
    acquiredAt: "10 mins ago",
    priority: "STAT",
    status: "Pending",
    sampleUrl: "/demo_samples/03_active_tuberculosis.png",
    filename: "03_active_tuberculosis.png",
  },
  {
    studyId: "STD-2026-8841",
    patientId: "PT-49201",
    ageSex: "64Y • M",
    modality: "CR Chest AP",
    indication: "Dyspnea, orthopnea — evaluate pleural effusion & cardiomegaly",
    acquiredAt: "24 mins ago",
    priority: "URGENT",
    status: "Pending",
    sampleUrl: "/demo_samples/02_effusion_cardiomegaly.png",
    filename: "02_effusion_cardiomegaly.png",
  },
  {
    studyId: "STD-2026-8843",
    patientId: "PT-77512",
    ageSex: "29Y • F",
    modality: "DX Chest PA",
    indication: "Pre-operative screening — asymptomatic",
    acquiredAt: "42 mins ago",
    priority: "ROUTINE",
    status: "Pending",
    sampleUrl: "/demo_samples/01_normal_cxr.png",
    filename: "01_normal_cxr.png",
  },
  {
    studyId: "STD-2026-8844",
    patientId: "QA-00000",
    ageSex: "QA Gate",
    modality: "Unverified",
    indication: "Synthetic / Out-of-Distribution safety gate verification",
    acquiredAt: "1 hr ago",
    priority: "QA",
    status: "Pending",
    sampleUrl: "/demo_samples/04_ood_anomaly_synthetic.png",
    filename: "04_ood_anomaly_synthetic.png",
  },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  studies: StudyRecord[];
  activeStudyId: string | null;
  onSelectStudy: (study: StudyRecord) => void;
}

export default function StudyWorklistDrawer({
  isOpen,
  onClose,
  studies,
  activeStudyId,
  onSelectStudy,
}: Props) {
  const [query, setQuery] = useState("");
  const [filterPriority, setFilterPriority] = useState<string>("ALL");

  const filtered = useMemo(() => {
    return studies.filter((s) => {
      const matchesPriority = filterPriority === "ALL" || s.priority === filterPriority;
      const q = query.trim().toLowerCase();
      const matchesQuery =
        !q ||
        s.studyId.toLowerCase().includes(q) ||
        s.patientId.toLowerCase().includes(q) ||
        s.indication.toLowerCase().includes(q);
      return matchesPriority && matchesQuery;
    });
  }, [studies, query, filterPriority]);

  if (!isOpen) return null;

  const priorityBadge = (priority: StudyPriority) => {
    switch (priority) {
      case "STAT":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "URGENT":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "QA":
        return "bg-purple-500/20 text-purple-300 border-purple-500/40";
      default:
        return "bg-sky-500/20 text-sky-300 border-sky-500/40";
    }
  };

  const statusBadge = (status: StudyStatus) => {
    if (status === "Signed Off") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400">
          <CheckCircle2 className="h-3 w-3" /> Signed Off
        </span>
      );
    }
    if (status === "AI Screened") {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#3FD0C4]">
          <AlertCircle className="h-3 w-3" /> AI Screened
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-[#8C9DB0]">
        <Clock className="h-3 w-3" /> Pending
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-start bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#0D1520] border-r border-[#1C2937] h-full flex flex-col shadow-2xl">
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-[#1C2937] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-[#E6EDF4] uppercase tracking-wider flex items-center gap-2">
              <FileImage className="h-4 w-4 text-[#3FD0C4]" />
              Radiology Study Worklist
            </h2>
            <p className="text-[11px] text-[#8C9DB0] mt-0.5">
              DICOM Acquisition Queue • {studies.length} Active Studies
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8C9DB0] hover:text-white hover:bg-[#162233] transition-colors"
            title="Close Worklist"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Search & Filter */}
        <div className="p-4 border-b border-[#1C2937] space-y-3 bg-[#090F17]">
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-[#8C9DB0] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search Study ID, Patient ID, or indication..."
              className="w-full rounded-lg border border-[#1C2937] bg-[#111C2B] pl-9 pr-3 py-2 text-xs text-[#E6EDF4] placeholder-[#566475] focus:border-[#3FD0C4] focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-1.5">
            {["ALL", "STAT", "URGENT", "ROUTINE", "QA"].map((p) => (
              <button
                key={p}
                onClick={() => setFilterPriority(p)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider transition-colors ${
                  filterPriority === p
                    ? "bg-[#3FD0C4] text-[#05080E]"
                    : "bg-[#111C2B] text-[#8C9DB0] hover:text-[#E6EDF4]"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Study List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filtered.map((study) => {
            const isActive = activeStudyId === study.studyId;
            return (
              <button
                key={study.studyId}
                onClick={() => {
                  onSelectStudy(study);
                  onClose();
                }}
                className={`w-full text-left p-3.5 rounded-xl border transition-all group ${
                  isActive
                    ? "bg-[#112432] border-[#3FD0C4]"
                    : "bg-[#111C2B] border-[#1C2937] hover:border-[#3FD0C4]/50 hover:bg-[#132031]"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${priorityBadge(study.priority)}`}>
                      {study.priority}
                    </span>
                    <span className="text-xs font-mono font-bold text-[#E6EDF4]">
                      {study.studyId}
                    </span>
                  </div>
                  {statusBadge(study.status)}
                </div>

                <div className="flex items-center justify-between text-[11px] text-[#8C9DB0] mb-1.5">
                  <span className="font-medium text-[#CBD5E1]">
                    {study.patientId} ({study.ageSex})
                  </span>
                  <span>{study.modality} • {study.acquiredAt}</span>
                </div>

                <p className="text-xs text-[#94A3B8] line-clamp-2 leading-relaxed">
                  {study.indication}
                </p>

                <div className="mt-2 pt-2 border-t border-[#1C2937]/70 flex items-center justify-between text-[11px] text-[#3FD0C4] opacity-80 group-hover:opacity-100">
                  <span>Load into PACS Viewport</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </button>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center py-10 text-xs text-[#8C9DB0]">
              No matching studies found in queue.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
