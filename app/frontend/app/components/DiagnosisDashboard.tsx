"use client";

import { PredictionResponse } from "../types";

interface DiagnosisDashboardProps {
  prediction: PredictionResponse | null;
  auditRatio: number | null;
  auditPass: boolean | null;
}

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
}: DiagnosisDashboardProps) {
  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-3">
          Head A — NIH 14 Pathologies
        </h3>
        {prediction ? (
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {Object.entries(prediction.head_a_prediction).map(([disease, probability]) => {
              const threshold = NIH_THRESHOLDS[disease] ?? 0.5;
              return (
                <div key={disease} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300">{disease}</span>
                    <span className="text-slate-400">
                      {(probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getBarColor(probability, threshold)}`}
                      style={{ width: `${probability * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Upload an image to see predictions.</p>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-3">
          Head B — Tuberculosis Screening
        </h3>
        {prediction ? (
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${
                prediction.head_b_tb_screening.is_positive
                  ? "bg-rose-500/20 text-rose-400"
                  : "bg-emerald-500/20 text-emerald-400"
              }`}
            >
              {prediction.head_b_tb_screening.is_positive ? "Positive" : "Negative"}
            </span>
            <span className="text-sm text-slate-400">
              {(prediction.head_b_tb_screening.tb_probability * 100).toFixed(1)}%
            </span>
          </div>
        ) : (
          <p className="text-sm text-slate-500">No screening result yet.</p>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-3">
          Head C — COVID-19 & Shortcut Audit
        </h3>
        {prediction ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${
                  prediction.head_c_covidx.is_positive
                    ? "bg-rose-500/20 text-rose-400"
                    : "bg-emerald-500/20 text-emerald-400"
                }`}
              >
                {prediction.head_c_covidx.is_positive ? "COVID-19 Positive" : "COVID-19 Negative"}
              </span>
              <span className="text-sm text-slate-400">
                {(prediction.head_c_covidx.covid_probability * 100).toFixed(1)}%
              </span>
            </div>
            {auditRatio !== null && (
              <div className="text-sm">
                <span className="text-slate-400">In-lung activation:</span>{" "}
                <span
                  className={`font-semibold ${
                    auditPass ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {(auditRatio * 100).toFixed(1)}%
                </span>
                <span className="text-slate-500 ml-1">
                  {auditPass ? "(Passes ≥80% audit)" : "(Fails <80% audit)"}
                </span>
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
