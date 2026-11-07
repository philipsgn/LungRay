"use client";

import { useMemo, useState } from "react";
import { PredictionResponse } from "../types";
import { useLungRayLanguage, translations } from "../lib/i18n";
import {
  ShieldAlert,
  ShieldCheck,
  AlertCircle,
  Lock,
  FileText,
  ChevronDown,
  ChevronUp,
  Search,
  ArrowLeft,
  Activity,
  Layers,
  Crosshair,
} from "lucide-react";

interface DiagnosisDashboardProps {
  prediction: PredictionResponse | null;
  auditRatio: number | null;
  auditPass: boolean | null;
  selectedHead: string;
  selectedClass: number;
  clinicalGrounding: boolean;
  onSelectPathology: (head: string, classIdx: number, diseaseName: string) => void;
  onToggleGrounding: (grounded: boolean) => void;
  onNavigateToScan?: () => void;
  isExplaining?: boolean;
}

interface DiseaseMeta {
  id: string;
  nameEn: string;
  nameVi: string;
  icd10: string;
}

const NIH_14_DISEASES: DiseaseMeta[] = [
  { id: "Atelectasis", nameEn: "Atelectasis", nameVi: "Xẹp phổi", icd10: "J98.11" },
  { id: "Cardiomegaly", nameEn: "Cardiomegaly", nameVi: "Tim to", icd10: "I51.7" },
  { id: "Effusion", nameEn: "Effusion", nameVi: "Tràn dịch màng phổi", icd10: "J90" },
  { id: "Infiltration", nameEn: "Infiltration", nameVi: "Thâm nhiễm phổi", icd10: "J18.9" },
  { id: "Mass", nameEn: "Mass", nameVi: "Khối u lồng ngực", icd10: "R91.8" },
  { id: "Nodule", nameEn: "Nodule", nameVi: "Nốt mờ phổi", icd10: "R91.1" },
  { id: "Pneumonia", nameEn: "Pneumonia", nameVi: "Viêm phổi", icd10: "J18.9" },
  { id: "Pneumothorax", nameEn: "Pneumothorax", nameVi: "Tràn khí màng phổi", icd10: "J93.9" },
  { id: "Consolidation", nameEn: "Consolidation", nameVi: "Đông đặc nhu mô", icd10: "J18.9" },
  { id: "Edema", nameEn: "Edema", nameVi: "Phù phổi cấp", icd10: "J81.0" },
  { id: "Emphysema", nameEn: "Emphysema", nameVi: "Khí phế thũng", icd10: "J43.9" },
  { id: "Fibrosis", nameEn: "Fibrosis", nameVi: "Xơ hóa phổi", icd10: "J84.10" },
  { id: "Pleural_Thickening", nameEn: "Pleural Thickening", nameVi: "Dày màng phổi", icd10: "J92.9" },
  { id: "Hernia", nameEn: "Hernia", nameVi: "Thoát vị hoành", icd10: "K44.9" },
];

const NIH_THRESHOLDS: Record<string, number> = {
  Atelectasis: 0.4658,
  Cardiomegaly: 0.485,
  Effusion: 0.4844,
  Infiltration: 0.5245,
  Mass: 0.48,
  Nodule: 0.46,
  Pneumonia: 0.45,
  Pneumothorax: 0.4228,
  Consolidation: 0.45,
  Edema: 0.42,
  Emphysema: 0.40,
  Fibrosis: 0.38,
  Pleural_Thickening: 0.42,
  Hernia: 0.25,
};

export default function DiagnosisDashboard({
  prediction,
  auditRatio,
  auditPass,
  selectedHead,
  selectedClass,
  clinicalGrounding,
  onSelectPathology,
  onToggleGrounding,
  onNavigateToScan,
  isExplaining = false,
}: DiagnosisDashboardProps) {
  const [lang] = useLungRayLanguage();
  const t = translations[lang];

  // Accordion open/close states (Independent On/Off)
  const [openSection1, setOpenSection1] = useState(true);
  const [openSection2, setOpenSection2] = useState(true);
  const [openSection3, setOpenSection3] = useState(true);

  // Search filter for 14 NIH pathologies
  const [searchQuery, setSearchQuery] = useState("");

  const isRejected = prediction?.safety?.decision === "REJECT";

  // Calculate positive findings count across all 3 heads
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

  // Filtered NIH-14 list based on search query with positive findings sorted to top
  const filteredNihDiseases = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let list = NIH_14_DISEASES;
    if (q) {
      list = NIH_14_DISEASES.filter(
        (d) =>
          d.nameEn.toLowerCase().includes(q) ||
          d.nameVi.toLowerCase().includes(q) ||
          d.icd10.toLowerCase().includes(q) ||
          d.id.toLowerCase().includes(q)
      );
    }
    if (!prediction?.head_a_prediction) return list;

    // Stable sort: Positive findings first (sorted by probability descending), then negative
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
    <div className="space-y-3.5 font-mono">
      {/* Top Reading Room Header & Quick Navigation */}
      <div className="bg-[#070B12] border border-slate-800 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-2">
          {onNavigateToScan && (
            <button
              type="button"
              onClick={onNavigateToScan}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/40 text-cyan-200 text-xs font-semibold hover:bg-slate-850 hover:text-white transition-all shadow-sm"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.backToScanBtn}</span>
            </button>
          )}

          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {t.quickSummaryTitle}
            </span>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2">
          {prediction ? (
            isRejected ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-950 text-rose-300 border border-rose-800 flex items-center gap-1">
                <Lock className="w-3 h-3 text-rose-400" />
                {t.failSafeRejectedBadge}
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-900 text-cyan-300 border border-slate-750">
                {positiveFindingsCount > 0
                  ? `${positiveFindingsCount} ${t.findingsCount}`
                  : t.noFindingsDetected}
              </span>
            )
          ) : (
            <span className="text-[10px] text-slate-500">{t.noPredictionsYet}</span>
          )}
        </div>
      </div>

      {/* Helpful Interactive Note */}
      {prediction && !isRejected && (
        <div className="flex items-center gap-2 p-2 px-3 rounded-lg bg-slate-950 border border-slate-850 text-[11px] text-slate-400">
          <Crosshair className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span>{t.inspectOnXrayNote}</span>
        </div>
      )}

      {/* Consensus Ensemble Agreement Banner */}
      {prediction?.ensemble_agreement !== undefined && (
        <div className="bg-[#0B0F19] border border-purple-800/60 rounded-xl p-3 shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
              <span className="text-xs font-bold text-purple-200 uppercase tracking-wider">
                {lang === "vi" ? "Độ đồng thuận Ensemble" : "Ensemble Consensus Agreement"}
              </span>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-xs font-bold border ${
                prediction.ensemble_agreement >= 0.9
                  ? "bg-emerald-950/80 text-emerald-300 border-emerald-700/60"
                  : prediction.ensemble_agreement >= 0.8
                  ? "bg-amber-950/80 text-amber-300 border-amber-700/60"
                  : "bg-rose-950/80 text-rose-300 border-rose-700/60"
              }`}
            >
              {(prediction.ensemble_agreement * 100).toFixed(1)}%{" "}
              {prediction.ensemble_agreement >= 0.9
                ? lang === "vi"
                  ? "Đồng thuận cao"
                  : "High Agreement"
                : lang === "vi"
                ? "Có phân kỳ"
                : "Moderate Divergence"}
            </span>
          </div>
          {prediction.ensemble_models && (
            <div className="text-[10px] text-slate-400 flex flex-wrap gap-1.5 items-center">
              <span className="text-slate-500 font-semibold">
                {lang === "vi" ? "Mô hình tham gia:" : "Participating Backbones:"}
              </span>
              {prediction.ensemble_models.map((m, idx) => (
                <span
                  key={idx}
                  className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-purple-300/80"
                >
                  {m}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* ACCORDION 1: BÁO CÁO LÂM SÀNG TỔNG HỢP & CẢNH BÁO AN TOÀN OOD            */}
      {/* ========================================================================= */}
      <div className="bg-[#070B12] rounded-xl border border-slate-800 shadow-md overflow-hidden">
        {/* Accordion Header / Toggle */}
        <button
          type="button"
          onClick={() => setOpenSection1((prev) => !prev)}
          className="w-full p-3 flex items-center justify-between text-left hover:bg-slate-900/60 transition-colors border-b border-slate-850"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {t.accordion1Title}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {prediction?.safety && (
              <span
                className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                  isRejected
                    ? "bg-rose-950 text-rose-300 border-rose-800"
                    : "bg-slate-900 text-cyan-300 border-slate-750"
                }`}
              >
                {isRejected ? t.failSafeRejectedBadge : t.failSafeVerifiedBadge}
              </span>
            )}
            {openSection1 ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </button>

        {/* Accordion Body */}
        {openSection1 && (
          <div className="p-3.5 space-y-3 animate-in fade-in slide-in-from-top-1">
            {/* OOD Safety Banner */}
            {prediction?.safety &&
              (isRejected ? (
                <div className="bg-slate-900 border-2 border-rose-600/90 rounded-xl p-3.5 shadow-lg">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <Lock className="w-4 h-4 text-rose-400 shrink-0" />
                      <h4 className="font-bold text-rose-300 text-xs tracking-wider uppercase">
                        {t.failSafeRejectedTitle}
                      </h4>
                    </div>
                    <span className="px-2 py-0.5 bg-rose-950 text-rose-300 border border-rose-700 font-bold text-[10px] rounded uppercase">
                      {t.failSafeRejectedBadge}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-relaxed mb-2">
                    {t.failSafeRejectedDesc}
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-950 p-2 rounded border border-slate-800 my-1.5">
                    <div>
                      <span className="text-slate-500">{t.helmholtzEnergyLabel} </span>
                      <span className="font-bold text-rose-400">
                        {prediction.safety.energy_score.toFixed(4)}
                      </span>
                      <span className="text-[9px] text-slate-500 block">
                        &lt; 9.0421 (Reject)
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">{t.shannonEntropyLabel} </span>
                      <span className="font-bold text-rose-400">
                        {prediction.safety.entropy_score.toFixed(4)}
                      </span>
                      <span className="text-[9px] text-slate-500 block">
                        &gt; 0.6275 (Reject)
                      </span>
                    </div>
                  </div>
                  <div className="flex items-start gap-1.5 text-[10px] text-slate-300 mt-2 p-1.5 bg-slate-950/80 rounded border border-slate-800">
                    <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                    <span>
                      <strong>{t.clinicalRecLabel}</strong> {t.clinicalRecRejectText}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-md flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200 text-xs uppercase tracking-wide">
                          {t.failSafeVerifiedTitle}
                        </span>
                        <span className="px-1.5 py-0.2 bg-slate-800 text-cyan-300 border border-slate-700 rounded text-[9px] font-semibold uppercase">
                          {t.failSafeVerifiedBadge}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {t.failSafeVerifiedDesc}
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-[10px] text-slate-400">
                    <div>
                      S_E:{" "}
                      <span className="text-slate-200 font-semibold">
                        {prediction.safety.energy_score.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      H:{" "}
                      <span className="text-slate-200 font-semibold">
                        {prediction.safety.entropy_score.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}

            {/* Grounded Clinical Narrative Report */}
            {prediction?.report ? (
              prediction.report.is_blocked ? (
                <div className="text-[11px] text-rose-300 bg-rose-950/40 border border-rose-900/60 p-2.5 rounded">
                  <p className="font-bold mb-1">{t.reportBlockedTitle}</p>
                  <p className="text-slate-300">{t.reportBlockedText}</p>
                </div>
              ) : (
                <div className="space-y-3 text-[11px] text-slate-300 bg-slate-950/70 p-3.5 rounded-lg border border-slate-850">
                  {/* Executive Impression (Narrative Synthesis) */}
                  <div className="pb-2 border-b border-slate-900">
                    <span className="font-bold text-slate-400 block text-[10px] uppercase tracking-wider mb-1">
                      {t.impressionHeading}
                    </span>
                    <p
                      className="text-slate-100 text-xs leading-relaxed font-sans font-medium [&_u]:underline [&_u]:font-bold [&_u]:text-cyan-200 [&_u]:decoration-cyan-400/80 [&_u]:decoration-1"
                      dangerouslySetInnerHTML={{
                        __html: prediction.report.impression || t.normalImpression,
                      }}
                    />
                  </div>

                  {/* Findings */}
                  <div>
                    <span className="font-bold text-slate-400 block text-[10px] uppercase tracking-wider mb-1">
                      {t.findingsHeading}
                    </span>
                    {prediction.report.findings?.length > 0 ? (
                      <ul className="space-y-1.5 text-slate-200 mt-1">
                        {prediction.report.findings.map((f, i) => (
                          <li
                            key={i}
                            className="text-[11px] leading-relaxed [&_u]:underline [&_u]:font-semibold [&_u]:text-slate-100 [&_u]:decoration-cyan-400/70"
                            dangerouslySetInnerHTML={{ __html: f }}
                          />
                        ))}
                      </ul>
                    ) : (
                      <p className="text-slate-400 italic">{t.noFindings}</p>
                    )}
                  </div>

                  {/* Recommendations */}
                  {prediction.report.recommendations?.length > 0 && (
                    <div className="pt-2 border-t border-slate-900">
                      <span className="font-bold text-slate-400 block text-[10px] uppercase tracking-wider mb-1">
                        {t.recommendationsHeading}
                      </span>
                      <ul className="space-y-1 text-slate-300 mt-1">
                        {prediction.report.recommendations.map((rec, i) => (
                          <li
                            key={i}
                            className="text-[11px] leading-relaxed [&_u]:underline [&_u]:font-semibold [&_u]:text-slate-200 [&_u]:decoration-slate-400"
                            dangerouslySetInnerHTML={{ __html: rec }}
                          />
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Disclaimer */}
                  <p className="text-[9px] text-slate-500 pt-1.5 border-t border-slate-850 leading-relaxed italic">
                    {t.reportDisclaimer}
                  </p>
                </div>
              )
            ) : (
              <p className="text-[11px] text-slate-500 py-1">{t.noPredictionsYet}</p>
            )}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* ACCORDION 2: SÀNG LỌC LAO PHỔI & COVID-19 (HEAD B & HEAD C)              */}
      {/* ========================================================================= */}
      <div className="bg-[#070B12] rounded-xl border border-slate-800 shadow-md overflow-hidden">
        {/* Accordion Header / Toggle */}
        <button
          type="button"
          onClick={() => setOpenSection2((prev) => !prev)}
          className="w-full p-3 flex items-center justify-between text-left hover:bg-slate-900/60 transition-colors border-b border-slate-850"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {t.accordion2Title}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {openSection2 ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </button>

        {/* Accordion Body */}
        {openSection2 && (
          <div className="p-3.5 space-y-3 animate-in fade-in slide-in-from-top-1">
            {/* Head B: Tuberculosis (A15.0) */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    {t.headBTitle}
                  </h4>
                </div>
                <span className="text-[10px] text-slate-500">{t.clickToExplain}</span>
              </div>

              {prediction ? (
                <button
                  type="button"
                  onClick={() => handleSelectAndInspect("head_b", 0, "Tuberculosis")}
                  disabled={isExplaining || isRejected}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between ${
                    selectedHead === "head_b" && selectedClass === 0
                      ? "bg-slate-800 border-cyan-500 ring-1 ring-cyan-500/40 shadow-sm"
                      : "bg-slate-950/60 border-slate-850 hover:bg-slate-900 hover:border-slate-800"
                  } ${isRejected ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        prediction.head_b_tb_screening.is_positive
                          ? "bg-slate-200 text-slate-950 border border-white"
                          : "bg-slate-900 text-slate-400 border border-slate-800"
                      }`}
                    >
                      {prediction.head_b_tb_screening.is_positive
                        ? t.tbPositive
                        : t.tbNegative}
                    </span>
                    <span className="text-xs text-slate-300 tabular-nums">
                      {(
                        prediction.head_b_tb_screening.tb_probability * 100
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                  {selectedHead === "head_b" && selectedClass === 0 && (
                    <span className="text-[9px] text-cyan-400 font-bold uppercase">
                      {t.targetIndicator}
                    </span>
                  )}
                </button>
              ) : (
                <p className="text-[11px] text-slate-500 py-1">{t.noTbYet}</p>
              )}
            </div>

            {/* Head C: COVID-19 (U07.1) & Shortcut Audit */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    {t.headCTitle}
                  </h4>
                </div>
                <span className="text-[10px] text-slate-500">{t.clickToExplain}</span>
              </div>

              {prediction ? (
                <div className="space-y-2">
                  <button
                    type="button"
                    onClick={() => handleSelectAndInspect("head_c", 0, "COVID-19")}
                    disabled={isExplaining || isRejected}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between ${
                      selectedHead === "head_c" && selectedClass === 0
                        ? "bg-slate-800 border-cyan-500 ring-1 ring-cyan-500/40 shadow-sm"
                        : "bg-slate-950/60 border-slate-850 hover:bg-slate-900 hover:border-slate-800"
                    } ${isRejected ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                          prediction.head_c_covidx.is_positive
                            ? "bg-slate-200 text-slate-950 border border-white"
                            : "bg-slate-900 text-slate-400 border border-slate-800"
                        }`}
                      >
                        {prediction.head_c_covidx.is_positive
                          ? t.covidPositive
                          : t.covidNegative}
                      </span>
                      <span className="text-xs text-slate-300 tabular-nums">
                        {(
                          prediction.head_c_covidx.covid_probability * 100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                    {selectedHead === "head_c" && selectedClass === 0 && (
                      <span className="text-[9px] text-cyan-400 font-bold uppercase">
                        {t.targetIndicator}
                      </span>
                    )}
                  </button>

                  {/* Shortcut Learning Audit Result */}
                  {auditRatio !== null && (
                    <div className="text-[11px] bg-slate-950 p-2.5 rounded-lg border border-slate-850 flex items-center justify-between">
                      <span className="text-slate-400">{t.inLungRatioLabel}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200 tabular-nums">
                          {(auditRatio * 100).toFixed(1)}%
                        </span>
                        <span
                          className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase ${
                            auditPass
                              ? "bg-slate-800 text-slate-200 border border-slate-700"
                              : "bg-rose-950 text-rose-300 border border-rose-800"
                          }`}
                        >
                          {auditPass ? t.auditPass : t.auditFail}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-[11px] text-slate-500 py-1">{t.noCovidYet}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* ACCORDION 3: 14 BỆNH LÝ LỒNG NGỰC - HEAD A (WHO ICD-10)                   */}
      {/* ========================================================================= */}
      <div className="bg-[#070B12] rounded-xl border border-slate-800 shadow-md overflow-hidden">
        {/* Accordion Header / Toggle */}
        <button
          type="button"
          onClick={() => setOpenSection3((prev) => !prev)}
          className="w-full p-3 flex items-center justify-between text-left hover:bg-slate-900/60 transition-colors border-b border-slate-850"
        >
          <div className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {t.accordion3Title}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-500">{t.clickToExplain}</span>
            {openSection3 ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </button>

        {/* Accordion Body */}
        {openSection3 && (
          <div className="p-3.5 space-y-2.5 animate-in fade-in slide-in-from-top-1">
            {/* Search / Filter Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.searchPathologyPlaceholder}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>

            {/* List of 14 Pathologies */}
            {prediction ? (
              filteredNihDiseases.length > 0 ? (
                <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
                  {filteredNihDiseases.map((dMeta) => {
                    const originalIdx = NIH_14_DISEASES.findIndex(
                      (item) => item.id === dMeta.id
                    );
                    const probability =
                      prediction.head_a_prediction[dMeta.id] ?? 0.0;
                    const threshold = NIH_THRESHOLDS[dMeta.id] ?? 0.35;
                    const isPositive = probability >= threshold;
                    const isSelected =
                      selectedHead === "head_a" && selectedClass === originalIdx;

                    return (
                      <button
                        type="button"
                        key={dMeta.id}
                        onClick={() =>
                          handleSelectAndInspect("head_a", originalIdx, dMeta.id)
                        }
                        disabled={isExplaining || isRejected}
                        className={`w-full text-left p-2 rounded-lg border transition-all ${
                          isSelected
                            ? "bg-slate-800 border-cyan-500 ring-1 ring-cyan-500/40 shadow-sm"
                            : "bg-slate-950/60 border-slate-850 hover:bg-slate-900 hover:border-slate-800"
                        } ${isRejected ? "opacity-50 cursor-not-allowed" : ""}`}
                      >
                        <div className="flex justify-between items-center text-xs mb-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span
                              className={`font-semibold ${
                                isSelected
                                  ? "text-cyan-300"
                                  : isPositive
                                  ? "text-slate-100"
                                  : "text-slate-400"
                              }`}
                            >
                              {lang === "vi" ? dMeta.nameVi : dMeta.nameEn}
                            </span>
                            <span className="text-[9px] text-slate-400 font-normal">
                              {lang === "vi" ? `(${dMeta.nameEn})` : `(${dMeta.icd10})`}
                            </span>
                            {isSelected && (
                              <span className="text-[9px] text-cyan-400 font-bold uppercase">
                                {t.targetIndicator}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] px-1.5 py-0.2 rounded font-bold uppercase ${
                                isPositive
                                  ? "bg-slate-200 text-slate-950 border border-white"
                                  : "bg-slate-900 text-slate-500 border border-slate-800"
                              }`}
                            >
                              {isPositive ? t.positiveBadge : t.negativeBadge}
                            </span>
                            <span
                              className={`text-[11px] tabular-nums ${
                                isPositive
                                  ? "text-slate-100 font-bold"
                                  : "text-slate-400"
                              }`}
                            >
                              {(probability * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        {/* High contrast monochrome bar */}
                        <div className="w-full h-1 bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                          <div
                            className={`h-full transition-all duration-300 ${
                              isPositive ? "bg-slate-200" : "bg-slate-700"
                            }`}
                            style={{
                              width: `${Math.min(probability * 100, 100)}%`,
                            }}
                          />
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <p className="text-[11px] text-slate-500 py-2">
                  {t.noPathologyMatch}
                </p>
              )
            ) : (
              <p className="text-[11px] text-slate-500 py-2">
                {t.noPredictionsYet}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Grounding Mode Controller in Report Section as well */}
      <div className="bg-[#070B12] rounded-xl p-3 border border-slate-800 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-300">
            {t.groundingTitle}
          </span>
          <span className="text-[10px] text-cyan-400">
            {clinicalGrounding ? t.groundedBadge : t.unmaskedBadge}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-950 rounded-lg border border-slate-850">
          <button
            type="button"
            onClick={() => onToggleGrounding(true)}
            disabled={isExplaining || isRejected}
            className={`py-1.5 px-2 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
              clinicalGrounding
                ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>{t.groundedBtn}</span>
          </button>
          <button
            type="button"
            onClick={() => onToggleGrounding(false)}
            disabled={isExplaining || isRejected}
            className={`py-1.5 px-2 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
              !clinicalGrounding
                ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-slate-400" />
            <span>{t.rawBtn}</span>
          </button>
        </div>
        <p className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">
          {clinicalGrounding ? t.groundedHelp : t.rawHelp}
        </p>
      </div>
    </div>
  );
}
