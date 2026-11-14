"use client";

import { useMemo, useState } from "react";
import AlphaSlider from "./components/AlphaSlider";
import DiagnosisDashboard from "./components/DiagnosisDashboard";
import HeatmapViewer from "./components/HeatmapViewer";
import PacsHeader from "./components/PacsHeader";
import UploadDropzone from "./components/UploadDropzone";
import { auditImage, explainImage, predictImage } from "./lib/api";
import { useLungRayLanguage, translations } from "./lib/i18n";
import { AuditResponse, PredictionResponse, LesionMetadata } from "./types";
import {
  Monitor,
  FileSpreadsheet,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";

export default function Home() {
  const [lang] = useLungRayLanguage();
  const t = translations[lang];

  // Two-Section Navigation State: "scan" | "report"
  const [activeSection, setActiveSection] = useState<"scan" | "report">("scan");
  const [selectedModel, setSelectedModel] = useState<string>("standard");
  const [failsafeEnabled, setFailsafeEnabled] = useState<boolean>(true);

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [heatmapUrl, setHeatmapUrl] = useState<string | null>(null);
  const [alpha, setAlpha] = useState<number>(45);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isExplaining, setIsExplaining] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Interactive Pathology & Grounding State
  const [selectedHead, setSelectedHead] = useState<string>("head_c");
  const [selectedClass, setSelectedClass] = useState<number>(0);
  const [selectedDiseaseName, setSelectedDiseaseName] = useState<string>("COVID-19");
  const [clinicalGrounding, setClinicalGrounding] = useState<boolean>(true);
  const [inLungRatio, setInLungRatio] = useState<number | null>(null);
  const [isTargetPositive, setIsTargetPositive] = useState<boolean>(true);
  const [contourUrl, setContourUrl] = useState<string | null>(null);
  const [lesions, setLesions] = useState<LesionMetadata[]>([]);
  const [lesionAreaRatio, setLesionAreaRatio] = useState<number>(0);
  const [camResolution, setCamResolution] = useState<string>("32x32 fused");

  // Calculate positive findings count
  const findingsCount = useMemo(() => {
    if (!prediction || prediction.safety?.decision === "REJECT") return 0;
    let count = 0;
    if (prediction.head_b_tb_screening?.is_positive) count += 1;
    if (prediction.head_c_covidx?.is_positive) count += 1;
    if (prediction.head_a_prediction) {
      const thresholds: Record<string, number> = {
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
      Object.entries(prediction.head_a_prediction).forEach(([dis, prob]) => {
        if (prob >= (thresholds[dis] ?? 0.35)) count += 1;
      });
    }
    return count;
  }, [prediction]);

  const fetchExplanation = async (
    currentFile: File,
    head: string,
    classIdx: number,
    diseaseName: string,
    grounding: boolean,
    modelName: string = selectedModel
  ) => {
    setIsExplaining(true);
    setError(null);
    try {
      const explainResult = await explainImage(
        currentFile,
        head,
        classIdx,
        grounding,
        diseaseName,
        modelName
      );
      setHeatmapUrl(`data:image/png;base64,${explainResult.heatmap_base64}`);
      if (explainResult.contour_base64) {
        setContourUrl(`data:image/png;base64,${explainResult.contour_base64}`);
      } else {
        setContourUrl(null);
      }
      setLesions(explainResult.lesion_bounding_boxes ?? []);
      setLesionAreaRatio(explainResult.lesion_area_ratio ?? 0);
      setCamResolution(explainResult.cam_resolution ?? "32x32 fused");
      setSelectedHead(explainResult.target_head);
      setSelectedClass(explainResult.target_class);
      setSelectedDiseaseName(explainResult.target_disease_name || diseaseName);
      setClinicalGrounding(Boolean(explainResult.is_grounded));
      if (explainResult.in_lung_energy_ratio !== undefined) {
        setInLungRatio(explainResult.in_lung_energy_ratio);
      }
      if (explainResult.is_target_positive !== undefined) {
        setIsTargetPositive(explainResult.is_target_positive);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate pathology heatmap");
    } finally {
      setIsExplaining(false);
    }
  };

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    setHeatmapUrl(null);
    setContourUrl(null);
    setLesions([]);
    setLesionAreaRatio(0);
    setPrediction(null);
    setAudit(null);
    setInLungRatio(null);

    setLoading(true);
    try {
      const [predResult, auditResult] = await Promise.all([
        predictImage(selectedFile, selectedModel, failsafeEnabled),
        auditImage(selectedFile),
      ]);
      setPrediction(predResult);
      setAudit(auditResult);

      // Smart Default Explanation: Prioritize highest confidence pathology on the scan
      const nihList = [
        "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
        "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
        "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
      ];
      let bestHead = "head_c";
      let bestClass = 0;
      let bestName = "COVID-19";
      let maxScore = 0;

      if (predResult.head_a_prediction) {
        nihList.forEach((d, idx) => {
          const prob = predResult.head_a_prediction[d] ?? 0;
          if (prob > maxScore) {
            maxScore = prob;
            bestHead = "head_a";
            bestClass = idx;
            bestName = d;
          }
        });
      }

      const tbProb = predResult.head_b_tb_screening?.tb_probability ?? 0;
      if (predResult.head_b_tb_screening?.is_positive && tbProb > maxScore) {
        maxScore = tbProb;
        bestHead = "head_b";
        bestClass = 0;
        bestName = "Tuberculosis";
      }

      const covProb = predResult.head_c_covidx?.covid_probability ?? 0;
      if (predResult.head_c_covidx?.is_positive && covProb > maxScore) {
        maxScore = covProb;
        bestHead = "head_c";
        bestClass = 0;
        bestName = "COVID-19";
      }

      await fetchExplanation(selectedFile, bestHead, bestClass, bestName, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPathology = async (
    head: string,
    classIdx: number,
    diseaseName: string
  ) => {
    if (!file) return;
    await fetchExplanation(file, head, classIdx, diseaseName, clinicalGrounding);
  };

  const handleToggleGrounding = async (newGrounding: boolean) => {
    if (!file) {
      setClinicalGrounding(newGrounding);
      return;
    }
    await fetchExplanation(
      file,
      selectedHead,
      selectedClass,
      selectedDiseaseName,
      newGrounding,
      selectedModel
    );
  };

  const handleModelChange = async (newModel: string) => {
    setSelectedModel(newModel);
    if (!file) return;
    setLoading(true);
    try {
      const predResult = await predictImage(file, newModel, failsafeEnabled);
      setPrediction(predResult);
      await fetchExplanation(
        file,
        selectedHead,
        selectedClass,
        selectedDiseaseName,
        clinicalGrounding,
        newModel
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch model");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFailsafe = async (enabled: boolean) => {
    setFailsafeEnabled(enabled);
    if (!file) return;
    setLoading(true);
    try {
      const predResult = await predictImage(file, selectedModel, enabled);
      setPrediction(predResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to re-evaluate with fail-safe toggle");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#05080E] text-slate-100 font-sans">
      <PacsHeader
        selectedModel={selectedModel}
        onSelectModel={handleModelChange}
        failsafeEnabled={failsafeEnabled}
        onToggleFailsafe={handleToggleFailsafe}
      />

      <main className="max-w-5xl mx-auto p-3 sm:p-5 space-y-4">
        {/* ========================================================================= */}
        {/* SECTION NAVIGATION TABS (WORKSTATION vs FINDINGS & REPORT)                */}
        {/* ========================================================================= */}
        <div className="bg-[#070B12] border border-slate-800 rounded-xl p-1.5 flex items-center justify-between gap-2 shadow-sm font-sans">
          <div className="flex items-center gap-1.5 w-full sm:w-auto">
            {/* Tab 1: Scan & Viewport Workstation */}
            <button
              type="button"
              onClick={() => setActiveSection("scan")}
              className={`flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                activeSection === "scan"
                  ? "bg-slate-800 text-cyan-300 border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Monitor className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.section1Tab}</span>
            </button>

            {/* Tab 2: Diagnostic Findings & Report */}
            <button
              type="button"
              onClick={() => setActiveSection("report")}
              className={`flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                activeSection === "report"
                  ? "bg-slate-800 text-cyan-300 border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.section2Tab}</span>

              {/* Status Badge */}
              {prediction && (
                <span className="ml-1 px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-slate-950 text-cyan-400 border border-cyan-800 animate-pulse">
                  {findingsCount > 0 ? `${findingsCount}` : "✓"}
                </span>
              )}
            </button>
          </div>

          {/* Quick Context Summary */}
          <div className="hidden sm:flex items-center gap-2 text-[10px] text-slate-400">
            {file ? (
              <span className="truncate max-w-[200px] text-slate-300 font-medium">
                {file.name}
              </span>
            ) : (
              <span className="text-slate-500 italic">
                {lang === "vi" ? "Chưa có phim" : "No CXR"}
              </span>
            )}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* SECTION 1: TRẠM ĐỌC PHIM & SCAN (SCAN & VIEWPORT WORKSTATION)             */}
        {/* ========================================================================= */}
        {activeSection === "scan" && (
          <div className="space-y-3.5 animate-in fade-in duration-200">
            {/* Compact Ingestion Toolbar (Browse CXR + Presets Dropdown + Drawer Toggle) */}
            <UploadDropzone
              onFileSelect={handleFileSelect}
              disabled={loading}
              hasFile={Boolean(file)}
            />

            {/* Prominent High-Precision X-ray & Heatmap Viewport */}
            <HeatmapViewer
              original={previewUrl}
              heatmap={heatmapUrl}
              contour={contourUrl}
              lesions={lesions}
              lesionAreaRatio={lesionAreaRatio}
              camResolution={camResolution}
              alpha={alpha}
              diseaseName={selectedDiseaseName}
              isGrounded={clinicalGrounding}
              inLungRatio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null}
              isExplaining={isExplaining || loading}
              isRejected={prediction?.safety?.decision === "REJECT"}
              isTargetPositive={isTargetPositive}
            />

            {/* Viewport Control Strip: Alpha Slider & Anatomical Grounding Filter */}
            {file && (
              <div className="space-y-2.5 font-sans">
                {/* Alpha Slider */}
                <AlphaSlider value={alpha} onChange={setAlpha} />

                {/* Grounding & Quick Jump Bar */}
                <div className="bg-[#070B12] border border-slate-800 rounded-xl p-2.5 px-3 flex flex-wrap items-center justify-between gap-3 shadow-sm">
                  {/* Left: Anatomical Filter Switch */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">
                      {t.groundingTitle}:
                    </span>
                    <div className="inline-flex rounded-lg border border-slate-800 bg-slate-950 p-0.5">
                      <button
                        type="button"
                        onClick={() => handleToggleGrounding(true)}
                        disabled={isExplaining || loading}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                          clinicalGrounding
                            ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                            : "text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        <ShieldCheck className="w-3 h-3 text-cyan-400" />
                        <span>{t.groundedBtn}</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleGrounding(false)}
                        disabled={isExplaining || loading}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                          !clinicalGrounding
                            ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                            : "text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        <ShieldAlert className="w-3 h-3 text-slate-400" />
                        <span>{t.rawBtn}</span>
                      </button>
                    </div>
                  </div>

                  {/* Right: CTA Button to jump to Section 2 (Report) */}
                  {prediction && (
                    <button
                      type="button"
                      onClick={() => setActiveSection("report")}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/40 text-cyan-200 text-xs font-semibold hover:bg-slate-850 hover:text-white transition-all shadow-sm group"
                    >
                      <span>{t.viewReportBtn}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Multi-Task Processing Indicator */}
            {loading && (
              <div className="text-center text-slate-400 py-3 flex items-center justify-center gap-2 font-mono text-xs bg-slate-900/60 border border-slate-800 rounded-lg">
                <svg
                  className="animate-spin h-4 w-4 text-cyan-400"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
                <span>{t.analyzingCxr}</span>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-rose-950/60 border border-rose-800/80 text-rose-200 rounded-lg p-3 text-xs font-mono">
                {error}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECTION 2: KẾT QUẢ & BÁO CÁO LÂM SÀNG (DIAGNOSTIC FINDINGS & REPORT)      */}
        {/* ========================================================================= */}
        {activeSection === "report" && (
          <div className="animate-in fade-in duration-200">
            <DiagnosisDashboard
              prediction={prediction}
              auditRatio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null}
              auditPass={audit?.pass_80_percent ?? null}
              selectedHead={selectedHead}
              selectedClass={selectedClass}
              clinicalGrounding={clinicalGrounding}
              onSelectPathology={handleSelectPathology}
              onToggleGrounding={handleToggleGrounding}
              onNavigateToScan={() => setActiveSection("scan")}
              onBypassFailsafe={() => handleToggleFailsafe(false)}
              isExplaining={isExplaining || loading}
            />
          </div>
        )}
      </main>
    </div>
  );
}
