"use client";

import { PredictionResponse } from "../types";

interface DiagnosisDashboardProps {
  prediction: PredictionResponse | null;
  auditRatio: number | null;
  auditPass: boolean | null;
  selectedHead: string;
  selectedClass: number;
  clinicalGrounding: boolean;
  onSelectPathology: (head: string, classIdx: number, diseaseName: string) => void;
  onToggleGrounding: (grounded: boolean) => void;
  isExplaining?: boolean;
}

const NIH_14_DISEASES = [
  "Atelectasis",
  "Cardiomegaly",
  "Effusion",
  "Infiltration",
  "Mass",
  "Nodule",
  "Pneumonia",
  "Pneumothorax",
  "Consolidation",
  "Edema",
  "Emphysema",
  "Fibrosis",
  "Pleural_Thickening",
  "Hernia",
];

const NIH_THRESHOLDS: Record<string, number> = {
  Atelectasis: 0.35,
  Cardiomegaly: 0.42,
  Effusion: 0.38,
  Infiltration: 0.32,
  Mass: 0.28,
  Nodule: 0.26,
  Pneumonia: 0.22,
  Pneumothorax: 0.3,
  Consolidation: 0.31,
  Edema: 0.36,
  Emphysema: 0.45,
  Fibrosis: 0.24,
  Pleural_Thickening: 0.28,
  Hernia: 0.15,
};

function getBarColor(probability: number, threshold: number): string {
  if (probability >= threshold) {
    return probability >= 0.7 ? "bg-rose-500" : "bg-amber-500";
  }
  return "bg-emerald-500";
}

export default function DiagnosisDashboard({
  prediction,
  auditRatio,
  auditPass,
  selectedHead,
  selectedClass,
  clinicalGrounding,
  onSelectPathology,
  onToggleGrounding,
  isExplaining = false,
}: DiagnosisDashboardProps) {
  return (
    <div className="space-y-4">
      {/* Grounding Mode Controller */}
      <div className="bg-slate-800/90 rounded-xl p-4 border border-slate-700 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            XAI Heatmap Filtering Mode
          </span>
          <span className="text-[11px] text-cyan-400 font-mono">
            {clinicalGrounding ? "CLINICAL ROI" : "RAW GRAD-CAM"}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2 p-1 bg-slate-900/80 rounded-lg border border-slate-700/60">
          <button
            type="button"
            onClick={() => onToggleGrounding(true)}
            disabled={isExplaining}
            className={`py-2 px-2.5 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
              clinicalGrounding
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-900/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
            title="Focus heatmap 100% inside lungs & cardiac margins, eliminating border & marker artifacts"
          >
            <span>🛡️</span>
            <span>Clinical Grounded</span>
          </button>
          <button
            type="button"
            onClick={() => onToggleGrounding(false)}
            disabled={isExplaining}
            className={`py-2 px-2.5 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
              !clinicalGrounding
                ? "bg-amber-600 text-white shadow-md shadow-amber-900/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
            title="Unfiltered attention view to audit shortcut learning artifacts (shoulders, letters, edges)"
          >
            <span>🔍</span>
            <span>Raw Attention</span>
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
          {clinicalGrounding
            ? "✓ Anatomical lung segmentation active. Suppresses non-anatomical noise (letter R, clavicles, borders)."
            : "⚠️ Raw Grad-CAM activation showing model shortcuts and boundary energy distribution."}
        </p>
      </div>

      {/* Head A — 14 Pathologies */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-md">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Head A — NIH 14 Pathologies
          </h3>
          <span className="text-[11px] text-slate-400">Click item to explain</span>
        </div>
        {prediction ? (
          <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
            {NIH_14_DISEASES.map((disease, idx) => {
              const probability = prediction.head_a_prediction[disease] ?? 0.0;
              const threshold = NIH_THRESHOLDS[disease] ?? 0.5;
              const isSelected = selectedHead === "head_a" && selectedClass === idx;

              return (
                <button
                  type="button"
                  key={disease}
                  onClick={() => onSelectPathology("head_a", idx, disease)}
                  disabled={isExplaining}
                  className={`w-full text-left p-2 rounded-lg transition-all border ${
                    isSelected
                      ? "bg-slate-700/90 border-cyan-500 ring-1 ring-cyan-500/50 shadow-md"
                      : "bg-slate-900/40 border-slate-700/50 hover:bg-slate-700/50 hover:border-slate-600"
                  }`}
                >
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className={`font-medium ${isSelected ? "text-cyan-300 font-semibold" : "text-slate-300"}`}>
                      {disease}
                      {isSelected && <span className="ml-1.5 text-[10px] text-cyan-400 uppercase tracking-wider">[Target]</span>}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[10px] font-mono ${probability >= threshold ? "text-rose-400 font-bold" : "text-slate-400"}`}>
                        {(probability * 100).toFixed(1)}%
                      </span>
                      {probability >= threshold && (
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                      )}
                    </div>
                  </div>
                  <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${getBarColor(probability, threshold)}`}
                      style={{ width: `${Math.min(probability * 100, 100)}%` }}
                    />
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Upload an image to see predictions.</p>
        )}
      </div>

      {/* Head B — Tuberculosis */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-md">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Head B — Tuberculosis Screening
          </h3>
          <span className="text-[11px] text-slate-400">Click to explain</span>
        </div>
        {prediction ? (
          <button
            type="button"
            onClick={() => onSelectPathology("head_b", 0, "Tuberculosis")}
            disabled={isExplaining}
            className={`w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between ${
              selectedHead === "head_b" && selectedClass === 0
                ? "bg-slate-700/90 border-cyan-500 ring-1 ring-cyan-500/50 shadow-md"
                : "bg-slate-900/40 border-slate-700/50 hover:bg-slate-700/50 hover:border-slate-600"
            }`}
          >
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${
                  prediction.head_b_tb_screening.is_positive
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                    : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                }`}
              >
                {prediction.head_b_tb_screening.is_positive ? "TB Positive" : "TB Negative"}
              </span>
              <span className="text-sm font-mono text-slate-300">
                {(prediction.head_b_tb_screening.tb_probability * 100).toFixed(1)}%
              </span>
            </div>
            {selectedHead === "head_b" && selectedClass === 0 && (
              <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">[Target]</span>
            )}
          </button>
        ) : (
          <p className="text-sm text-slate-500">No screening result yet.</p>
        )}
      </div>

      {/* Head C — COVID-19 & Audit */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-md">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Head C — COVID-19 & Shortcut Audit
          </h3>
          <span className="text-[11px] text-slate-400">Click to explain</span>
        </div>
        {prediction ? (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => onSelectPathology("head_c", 0, "COVID-19")}
              disabled={isExplaining}
              className={`w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between ${
                selectedHead === "head_c" && selectedClass === 0
                  ? "bg-slate-700/90 border-cyan-500 ring-1 ring-cyan-500/50 shadow-md"
                  : "bg-slate-900/40 border-slate-700/50 hover:bg-slate-700/50 hover:border-slate-600"
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${
                    prediction.head_c_covidx.is_positive
                      ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                      : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  }`}
                >
                  {prediction.head_c_covidx.is_positive ? "COVID-19 Positive" : "COVID-19 Negative"}
                </span>
                <span className="text-sm font-mono text-slate-300">
                  {(prediction.head_c_covidx.covid_probability * 100).toFixed(1)}%
                </span>
              </div>
              {selectedHead === "head_c" && selectedClass === 0 && (
                <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">[Target]</span>
              )}
            </button>

            {auditRatio !== null && (
              <div className="text-xs bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/60 flex items-center justify-between">
                <span className="text-slate-400">Thoracic In-Lung Ratio:</span>
                <div className="flex items-center gap-2">
                  <span
                    className={`font-mono font-bold ${
                      auditPass ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {(auditRatio * 100).toFixed(1)}%
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                    auditPass ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                  }`}>
                    {auditPass ? "Pass (≥80%)" : "Audit Fail (<80%)"}
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No COVID-19 result yet.</p>
        )}
      </div>
    </div>
  );
}
