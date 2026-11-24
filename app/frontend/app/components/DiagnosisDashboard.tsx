"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Search,
  Lock,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { PredictionResponse } from "../types";

export interface DiseaseMeta {
  id: string;
  name: string;
  icd10: string;
  category: string;
}

export const NIH_14_DISEASES: DiseaseMeta[] = [
  { id: "Atelectasis", name: "Atelectasis", icd10: "J98.11", category: "Volume Loss" },
  { id: "Cardiomegaly", name: "Cardiomegaly", icd10: "I51.7", category: "Cardiac" },
  { id: "Effusion", name: "Pleural Effusion", icd10: "J90", category: "Pleural" },
  { id: "Infiltration", name: "Infiltration", icd10: "R91", category: "Parenchyma" },
  { id: "Mass", name: "Lung Mass", icd10: "R91", category: "Focal Lesion" },
  { id: "Nodule", name: "Pulmonary Nodule", icd10: "R91", category: "Focal Lesion" },
  { id: "Pneumonia", name: "Pneumonia", icd10: "J18.9", category: "Infection" },
  { id: "Pneumothorax", name: "Pneumothorax", icd10: "J93.9", category: "Pleural" },
  { id: "Consolidation", name: "Consolidation", icd10: "R91", category: "Parenchyma" },
  { id: "Edema", name: "Pulmonary Edema", icd10: "J81", category: "Vascular/Interstitial" },
  { id: "Emphysema", name: "Emphysema", icd10: "J43.9", category: "Airway" },
  { id: "Fibrosis", name: "Pulmonary Fibrosis", icd10: "J84.1", category: "Interstitial" },
  { id: "Pleural_Thickening", name: "Pleural Thickening", icd10: "J94.9", category: "Pleural" },
  { id: "Hernia", name: "Diaphragmatic Hernia", icd10: "K44.9", category: "Diaphragm" },
];

export const NIH_THRESHOLDS: Record<string, number> = {
  Atelectasis: 0.4658,
  Cardiomegaly: 0.485,
  Effusion: 0.4844,
  Infiltration: 0.5367,
  Mass: 0.3831,
  Nodule: 0.3891,
  Pneumonia: 0.3957,
  Pneumothorax: 0.4578,
  Consolidation: 0.4419,
  Edema: 0.4633,
  Emphysema: 0.4284,
  Fibrosis: 0.4309,
  Pleural_Thickening: 0.4169,
  Hernia: 0.3854,
};

interface DiagnosisDashboardProps {
  prediction: PredictionResponse | null;
  auditRatio?: number | null;
  auditPass?: boolean | null;
  selectedHead: string;
  selectedClass: number;
  onSelectPathology: (head: string, classIdx: number, diseaseName: string) => void;
  onNavigateToScan?: () => void;
  onBypassFailsafe?: () => void;
  isExplaining?: boolean;
}

export default function DiagnosisDashboard({
  prediction,
  selectedHead,
  selectedClass,
  onSelectPathology,
  onNavigateToScan,
  onBypassFailsafe,
  isExplaining = false,
}: DiagnosisDashboardProps) {
  const [openSection1, setOpenSection1] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const isRejected = prediction?.safety?.decision === "REJECT";

  // Total findings count across panels
  const positiveFindingsCount = useMemo(() => {
    if (!prediction || isRejected) return 0;
    let count = 0;
    NIH_14_DISEASES.forEach((d) => {
      const prob = prediction.head_a_prediction[d.id] ?? 0;
      const th = NIH_THRESHOLDS[d.id] ?? 0.35;
      if (prob >= th) count += 1;
    });
    if (prediction.head_b_tb_screening?.is_positive) count += 1;
    if (prediction.head_c_covidx?.is_positive) count += 1;
    return count;
  }, [prediction, isRejected]);

  // Filtered & sorted 14 diseases (positive first, then probability descending)
  const filteredNihDiseases = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let list = NIH_14_DISEASES;
    if (q) {
      list = NIH_14_DISEASES.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          d.icd10.toLowerCase().includes(q) ||
          d.id.toLowerCase().includes(q) ||
          d.category.toLowerCase().includes(q)
      );
    }
    if (!prediction?.head_a_prediction) return list;

    return [...list].sort((a, b) => {
      const probA = prediction.head_a_prediction[a.id] ?? 0;
      const probB = prediction.head_a_prediction[b.id] ?? 0;
      const isPosA = probA >= (NIH_THRESHOLDS[a.id] ?? 0.35);
      const isPosB = probB >= (NIH_THRESHOLDS[b.id] ?? 0.35);
      if (isPosA && !isPosB) return -1;
      if (!isPosA && isPosB) return 1;
      return probB - probA;
    });
  }, [searchQuery, prediction]);

  const handleSelectAndInspect = (
    head: string,
    classIdx: number,
    diseaseName: string
  ) => {
    onSelectPathology(head, classIdx, diseaseName);
    if (onNavigateToScan) {
      onNavigateToScan();
    }
  };

  return (
    <div className="space-y-4 font-sans select-none">
      {/* Top Reading Room Status Summary */}
      <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-3.5 shadow-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#111C2B] border border-[#1C2937] text-[#3FD0C4]">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#E6EDF4]">
              Multi-Task Diagnostic Findings
            </h2>
            <p className="text-[11px] text-[#8C9DB0]">
              Simultaneous evaluation of 16 common thoracic pathologies &amp; infections
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {prediction ? (
            isRejected ? (
              <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold uppercase bg-rose-950/80 text-rose-300 border border-rose-700 flex items-center gap-1.5 shadow-sm">
                <Lock className="w-3.5 h-3.5 text-rose-400" />
                Fail-Safe Locked
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-md text-xs font-mono font-medium uppercase bg-[#111C2B] text-[#3FD0C4] border border-[#1C2937]">
                {positiveFindingsCount > 0
                  ? `${positiveFindingsCount} Pathologies Detected`
                  : "No Significant Findings"}
              </span>
            )
          ) : (
            <span className="text-xs text-[#8C9DB0] italic">
              Awaiting radiograph analysis...
            </span>
          )}
        </div>
      </div>

      {/* Fail-Safe Rejection Alert Banner */}
      {isRejected && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-4 text-rose-200 space-y-2 shadow-lg">
          <div className="flex items-center gap-2 font-bold text-sm text-rose-100">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>OOD GATEKEEPER LOCKOUT ACTIVE</span>
          </div>
          <p className="text-xs text-rose-300/90 leading-relaxed">
            Helmholtz Free Energy score exceeded safety limits ({prediction?.safety?.energy_score?.toFixed(2)} ≥ 9.04). Automated diagnostic predictions are withheld to protect clinical decision integrity.
          </p>
          {onBypassFailsafe && (
            <button
              type="button"
              onClick={onBypassFailsafe}
              className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-900/60 border border-rose-700 text-xs font-semibold text-white hover:bg-rose-800 transition"
            >
              Bypass Fail-Safe (Clinical Override)
            </button>
          )}
        </div>
      )}

      {/* PANEL 1: General Thoracic Conditions (14 Pathologies) */}
      <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl overflow-hidden shadow-md">
        <button
          type="button"
          onClick={() => setOpenSection1((v) => !v)}
          className="w-full p-3.5 px-4 flex items-center justify-between text-left bg-[#111C2B]/60 hover:bg-[#111C2B] transition-colors border-b border-[#1C2937]"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#0A7A74]/30 text-[#3FD0C4] text-xs font-mono font-bold">
              14
            </span>
            <div>
              <h3 className="text-xs font-bold text-[#E6EDF4] uppercase tracking-wider">
                General Thoracic Panel (14 Pathologies)
              </h3>
              <p className="text-[10px] text-[#8C9DB0]">
                Calibrated against NIH ChestX-ray14 with Youden optimal threshold cutoffs
              </p>
            </div>
          </div>
          {openSection1 ? (
            <ChevronUp className="w-4 h-4 text-[#8C9DB0]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[#8C9DB0]" />
          )}
        </button>

        {openSection1 && (
          <div className="p-4 space-y-3">
            {/* Search Input Bar */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8C9DB0]" />
              <input
                type="text"
                placeholder="Search condition name, ICD-10 code, or anatomical region..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] text-xs text-[#E6EDF4] placeholder-[#566475] focus:outline-none focus:border-[#3FD0C4] transition"
              />
            </div>

            {/* Pathologies Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {filteredNihDiseases.map((d, index) => {
                const probability = prediction?.head_a_prediction?.[d.id] ?? 0;
                const threshold = NIH_THRESHOLDS[d.id] ?? 0.35;
                const isPositive = Boolean(prediction && !isRejected && probability >= threshold);
                const isSelected = selectedHead === "head_a" && selectedClass === index;

                return (
                  <div
                    key={d.id}
                    className={`p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "bg-[#111C2B] border-[#3FD0C4] ring-1 ring-[#3FD0C4]/40 shadow-sm shadow-[#3FD0C4]/15"
                        : isPositive
                        ? "bg-[#111C2B]/80 border-[#3FD0C4]/50"
                        : "bg-[#111C2B]/40 border-[#1C2937] hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-semibold text-[#E6EDF4]">
                            {d.name}
                          </span>
                          <span className="text-[10px] font-mono text-[#8C9DB0]">
                            ({d.icd10})
                          </span>
                        </div>
                        <span className="text-[10px] text-[#566475]">
                          {d.category}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase border ${
                            isPositive
                              ? "bg-[#0A7A74]/30 text-[#3FD0C4] border-[#3FD0C4]/50"
                              : "bg-[#070B12] text-[#8C9DB0] border-[#1C2937]"
                          }`}
                        >
                          {prediction ? (isPositive ? "Detected" : "Clear") : "Pending"}
                        </span>
                      </div>
                    </div>

                    {/* Probability Bar with Youden Marker */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] font-mono">
                        <span className="text-[#8C9DB0]">
                          Confidence: <strong className={isPositive ? "text-[#3FD0C4]" : "text-[#E6EDF4]"}>{(probability * 100).toFixed(1)}%</strong>
                        </span>
                        <span className="text-[#566475] text-[10px]">
                          Cutoff: {(threshold * 100).toFixed(1)}%
                        </span>
                      </div>

                      <div className="relative w-full h-1.5 bg-[#070B12] rounded-full overflow-hidden border border-[#1C2937]">
                        <div
                          className={`h-full transition-all duration-300 ${
                            isPositive ? "bg-[#3FD0C4]" : "bg-slate-600"
                          }`}
                          style={{ width: `${Math.min(probability * 100, 100)}%` }}
                        />
                        {/* Threshold Notch Indicator */}
                        <div
                          className="absolute top-0 bottom-0 w-[2px] bg-[#F2A93B] shadow-[0_0_4px_#F2A93B]"
                          style={{ left: `${threshold * 100}%` }}
                          title={`Youden Optimal Cutoff: ${(threshold * 100).toFixed(1)}%`}
                        />
                      </div>
                    </div>

                    {/* Quick Inspect Button */}
                    <div className="mt-2.5 pt-2 border-t border-[#1C2937]/60 flex items-center justify-between">
                      <span className="text-[10px] text-[#566475]">
                        {isSelected ? "Active in Viewport" : "Grad-CAM WSOL"}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleSelectAndInspect("head_a", index, d.id)}
                        disabled={!prediction || isExplaining || isRejected}
                        className={`inline-flex items-center gap-1 text-[11px] font-medium transition-colors ${
                          isSelected
                            ? "text-[#3FD0C4] font-semibold"
                            : "text-[#8C9DB0] hover:text-[#3FD0C4]"
                        } disabled:opacity-40 disabled:pointer-events-none`}
                      >
                        <span>View Heatmap</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* PANEL 2: Specialized Infection Screenings (TB & COVID-19) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tuberculosis Screening Card */}
        <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-4 shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono text-[#F2A93B] uppercase font-semibold">
                Infection Panel
              </span>
              <h3 className="text-sm font-bold text-[#E6EDF4]">
                Tuberculosis Screening (TB)
              </h3>
              <p className="text-[10px] text-[#8C9DB0]">
                Apical infiltration and cavitation triage · ICD-10 A15.0 / A16.2
              </p>
            </div>
            {prediction?.head_b_tb_screening && (
              <span
                className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${
                  prediction.head_b_tb_screening.is_positive
                    ? "bg-amber-950/60 text-amber-300 border-amber-700"
                    : "bg-[#111C2B] text-emerald-400 border-emerald-800/60"
                }`}
              >
                {prediction.head_b_tb_screening.is_positive ? "TB Suspect" : "TB Clear"}
              </span>
            )}
          </div>

          {prediction?.head_b_tb_screening ? (
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-[#8C9DB0]">Screening Probability:</span>
                <span className="font-bold text-[#E6EDF4]">
                  {(prediction.head_b_tb_screening.tb_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-1.5 bg-[#070B12] rounded-full overflow-hidden border border-[#1C2937]">
                <div
                  className={`h-full transition-all duration-300 ${
                    prediction.head_b_tb_screening.is_positive ? "bg-[#F2A93B]" : "bg-emerald-500"
                  }`}
                  style={{
                    width: `${Math.min(prediction.head_b_tb_screening.tb_probability * 100, 100)}%`,
                  }}
                />
              </div>
              <button
                type="button"
                onClick={() => handleSelectAndInspect("head_b", 0, "Tuberculosis")}
                disabled={isExplaining || isRejected}
                className="w-full mt-2 inline-flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] hover:border-[#3FD0C4] text-xs font-medium text-[#E6EDF4] transition disabled:opacity-50"
              >
                <span>View Tuberculosis Heatmap</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <p className="text-xs text-[#8C9DB0] italic py-2">
              Ingest a scan to run tuberculosis screening.
            </p>
          )}
        </div>

        {/* COVID-19 Triage Card */}
        <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-4 shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono text-[#3FD0C4] uppercase font-semibold">
                Emergency Triage
              </span>
              <h3 className="text-sm font-bold text-[#E6EDF4]">
                COVID-19 Triage
              </h3>
              <p className="text-[10px] text-[#8C9DB0]">
                Bilateral ground-glass opacity &amp; consolidation · ICD-10 U07.1
              </p>
            </div>
            {prediction?.head_c_covidx && (
              <span
                className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${
                  (prediction.head_c_covidx.model_is_positive ?? prediction.head_c_covidx.is_positive)
                    ? "bg-rose-950/60 text-rose-300 border-rose-700"
                    : "bg-[#111C2B] text-emerald-400 border-emerald-800/60"
                }`}
              >
                {(prediction.head_c_covidx.model_is_positive ?? prediction.head_c_covidx.is_positive)
                  ? "COVID Suspect"
                  : "COVID Clear"}
              </span>
            )}
          </div>

          {prediction?.head_c_covidx ? (
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-[#8C9DB0]">Triage Probability:</span>
                <span className="font-bold text-[#E6EDF4]">
                  {((prediction.head_c_covidx.covid_probability ?? 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-1.5 bg-[#070B12] rounded-full overflow-hidden border border-[#1C2937]">
                <div
                  className={`h-full transition-all duration-300 ${
                    (prediction.head_c_covidx.model_is_positive ?? prediction.head_c_covidx.is_positive)
                      ? "bg-rose-500"
                      : "bg-emerald-500"
                  }`}
                  style={{
                    width: `${Math.min((prediction.head_c_covidx.covid_probability ?? 0) * 100, 100)}%`,
                  }}
                />
              </div>

              {/* Smart Clinical Report Guardrail Notice */}
              {prediction.head_c_covidx.guardrail_reasons && prediction.head_c_covidx.guardrail_reasons.length > 0 ? (
                <div className="p-2 rounded-lg bg-amber-950/40 border border-amber-800/80 text-[11px] text-amber-200 flex items-start gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <span>
                    Smart Guardrail Downgrade: {prediction.head_c_covidx.guardrail_reasons.join(". ")}. Flag lowered to prevent false-positive alert.
                  </span>
                </div>
              ) : (
                <div className="p-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] text-[10px] text-[#8C9DB0] flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Protected by Clinical Pulmonary Grounding (Nature MI shortcut audit)</span>
                </div>
              )}

              <button
                type="button"
                onClick={() => handleSelectAndInspect("head_c", 0, "COVID-19")}
                disabled={isExplaining || isRejected}
                className="w-full mt-2 inline-flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] hover:border-[#3FD0C4] text-xs font-medium text-[#E6EDF4] transition disabled:opacity-50"
              >
                <span>View COVID-19 Heatmap</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <p className="text-xs text-[#8C9DB0] italic py-2">
              Ingest a scan to run COVID-19 emergency triage.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
