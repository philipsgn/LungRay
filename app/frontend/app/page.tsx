"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import AlphaSlider from "./components/AlphaSlider";
import DiagnosisDashboard, { NIH_14_DISEASES, NIH_THRESHOLDS } from "./components/DiagnosisDashboard";
import HeatmapViewer from "./components/HeatmapViewer";
import PacsHeader from "./components/PacsHeader";
import UploadDropzone from "./components/UploadDropzone";
import ClinicalRagAssistant from "./components/ClinicalRagAssistant";
import { checkBackendHealth, explainImage, predictImage } from "./lib/api";
import { AuditResponse, PredictionResponse } from "./types";
import {
  Monitor,
  BarChart3,
  FileText,
  BookOpen,
  Layers,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Printer,
  Sparkles,
  ExternalLink,
} from "lucide-react";

type TabScreen = "viewport" | "findings" | "report" | "rag" | "atlas";

export default function Home() {
  // 5-Tab Modular Navigation State
  const [activeTab, setActiveTab] = useState<TabScreen>("viewport");
  const [selectedModel, setSelectedModel] = useState<string>("standard");
  const [ttaEnabled, setTtaEnabled] = useState(true);
  const [failsafeEnabled, setFailsafeEnabled] = useState<boolean>(true);

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const [heatmapUrl, setHeatmapUrl] = useState<string | null>(null);
  const [heatmapHasAlpha, setHeatmapHasAlpha] = useState(false);
  const [alpha, setAlpha] = useState<number>(45);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isExplaining, setIsExplaining] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const lastExplanation = useRef<{ file: File; head: string; classIdx: number; diseaseName: string; grounding: boolean; modelName: string } | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);

  // Interactive Pathology & Grounding State
  const [selectedHead, setSelectedHead] = useState<string>("head_a");
  const [selectedClass, setSelectedClass] = useState<number>(0);
  const [selectedDiseaseName, setSelectedDiseaseName] = useState<string>("Atelectasis");
  const [clinicalGrounding, setClinicalGrounding] = useState<boolean>(true);
  const [inLungRatio, setInLungRatio] = useState<number | null>(null);
  const [explanationAuditPass, setExplanationAuditPass] = useState<boolean | null>(null);
  const [contourUrl, setContourUrl] = useState<string | null>(null);
  const [contourHasAlpha, setContourHasAlpha] = useState(false);
  const [noActivation, setNoActivation] = useState(false);
  const [maskWarning, setMaskWarning] = useState("");

  // Initial Backend Health Probe
  useEffect(() => {
    checkBackendHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  // Positive findings count across all panels
  const findingsCount = useMemo(() => {
    if (!prediction || prediction.safety?.decision === "REJECT") return 0;
    let count = 0;
    if (prediction.head_b_tb_screening?.is_positive) count += 1;
    if (prediction.head_c_covidx?.is_positive) count += 1;
    if (prediction.head_a_prediction) {
      Object.entries(prediction.head_a_prediction).forEach(([dis, prob]) => {
        if (prob >= (NIH_THRESHOLDS[dis] ?? 0.35)) count += 1;
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
    lastExplanation.current = { file: currentFile, head, classIdx, diseaseName, grounding, modelName };
    setIsExplaining(true);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);
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
      setHeatmapHasAlpha(Boolean(explainResult.heatmap_rgba_base64));
      setHeatmapUrl(`data:image/png;base64,${explainResult.heatmap_rgba_base64 || explainResult.heatmap_base64}`);
      setNoActivation(explainResult.heatmap_has_activation === false);
      setMaskWarning(explainResult.mask_warning ?? "");
      if (explainResult.contour_base64) {
        setContourHasAlpha(Boolean(explainResult.contour_rgba_base64));
        setContourUrl(`data:image/png;base64,${explainResult.contour_rgba_base64 || explainResult.contour_base64}`);
      } else {
        setContourUrl(null);
      }
      setInLungRatio(explainResult.in_lung_energy_ratio ?? null);
      setExplanationAuditPass(explainResult.audit_pass ?? null);

      setSelectedHead(head);
      setSelectedClass(classIdx);
      setSelectedDiseaseName(diseaseName);
      setClinicalGrounding(grounding);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setError("Explanation computation timed out. Please retry.");
      } else if (err instanceof TypeError) {
        setConnected(false);
        setError("Could not reach LungRay API backend (Port 8000). Please ensure server is running.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to generate heatmap.");
      }
    } finally {
      setIsExplaining(false);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    lastExplanation.current = null;
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setPrediction(null);
    setAudit(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    const selectedFile = file;
    setError(null);
    setPrediction(null);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);
    setLoading(true);

    try {
      await checkBackendHealth();
      setConnected(true);
    } catch {
      setConnected(false);
      setError("Cannot connect to AI Backend (FastAPI, Port 8000). Please check the service.");
      setLoading(false);
      return;
    }

    try {
      const predResult = await predictImage(selectedFile, selectedModel, failsafeEnabled, ttaEnabled);
      setPrediction(predResult);
      setAudit(null);

      // Prioritize highest confidence pathology on the radiograph
      const nihList = [
        "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
        "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
        "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
      ];
      let bestHead = "head_a";
      let bestClass = 0;
      let bestName = "Atelectasis";
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

      if (predResult.safety?.decision !== "REJECT") {
        await fetchExplanation(selectedFile, bestHead, bestClass, bestName, clinicalGrounding);
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setError("Inference request timed out. Please retry.");
      } else if (err instanceof TypeError) {
        setConnected(false);
        setError("Cannot connect to AI Backend (Port 8000). Please check the service.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to analyze radiograph.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPathology = async (
    head: string,
    classIdx: number,
    diseaseName: string
  ) => {
    if (!file || !prediction) return;
    await fetchExplanation(file, head, classIdx, diseaseName, clinicalGrounding);
  };

  const handleToggleGrounding = async (newGrounding: boolean) => {
    if (!file || !prediction) {
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

  const handleModelChange = (newModel: string) => {
    setSelectedModel(newModel);
    setError(null);
    lastExplanation.current = null;
    setPrediction(null);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);
    setAudit(null);
  };

  const handleToggleFailsafe = (enabled: boolean) => {
    setError(null);
    lastExplanation.current = null;
    setFailsafeEnabled(enabled);
    setPrediction(null);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);
  };

  return (
    <div className="min-h-screen bg-[#070B12] text-[#E6EDF4] font-sans">
      {/* Primary PACS Header */}
      <PacsHeader
        selectedModel={selectedModel}
        onSelectModel={handleModelChange}
        failsafeEnabled={failsafeEnabled}
        onToggleFailsafe={handleToggleFailsafe}
        ttaEnabled={ttaEnabled}
        onToggleTta={(value) => {
          setTtaEnabled(value);
          setError(null);
          lastExplanation.current = null;
          setPrediction(null);
          setHeatmapUrl(null);
          setNoActivation(false);
          setMaskWarning("");
          setContourUrl(null);
          setInLungRatio(null);
          setExplanationAuditPass(null);
        }}
        connected={connected}
        disabled={loading || isExplaining}
        onOpenAtlasTab={() => setActiveTab("atlas")}
      />

      <main className="max-w-7xl mx-auto p-3 sm:p-5 space-y-4">
        {/* ========================================================================= */}
        {/* 5-TAB SCREEN SWITCHER                                                     */}
        {/* ========================================================================= */}
        <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-1.5 flex items-center justify-between gap-2 shadow-lg">
          <nav className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto" aria-label="Workstation Tabs">
            {/* Tab 1: Viewport & Inspection */}
            <button
              type="button"
              onClick={() => setActiveTab("viewport")}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                activeTab === "viewport"
                  ? "bg-[#0A7A74] text-white border border-[#3FD0C4]/60 shadow-sm shadow-[#3FD0C4]/20"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4] hover:bg-[#111C2B]"
              }`}
            >
              <Monitor className="w-3.5 h-3.5 text-[#3FD0C4]" />
              <span>1 · Viewport &amp; Inspection</span>
            </button>

            {/* Tab 2: Diagnostic Findings */}
            <button
              type="button"
              onClick={() => setActiveTab("findings")}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                activeTab === "findings"
                  ? "bg-[#0A7A74] text-white border border-[#3FD0C4]/60 shadow-sm shadow-[#3FD0C4]/20"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4] hover:bg-[#111C2B]"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5 text-[#3FD0C4]" />
              <span>2 · Findings Panel</span>
              {prediction && (
                <span className="ml-1 px-1.5 py-0.2 rounded text-[9px] font-mono font-bold uppercase bg-[#070B12] text-[#3FD0C4] border border-[#3FD0C4]/40">
                  {findingsCount > 0 ? `${findingsCount}` : "Clear"}
                </span>
              )}
            </button>

            {/* Tab 3: Clinical Report */}
            <button
              type="button"
              onClick={() => setActiveTab("report")}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                activeTab === "report"
                  ? "bg-[#0A7A74] text-white border border-[#3FD0C4]/60 shadow-sm shadow-[#3FD0C4]/20"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4] hover:bg-[#111C2B]"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-[#3FD0C4]" />
              <span>3 · Clinical Report</span>
            </button>

            {/* Tab 4: Knowledge Assistant (RAG) */}
            <button
              type="button"
              onClick={() => setActiveTab("rag")}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                activeTab === "rag"
                  ? "bg-[#0A7A74] text-white border border-[#3FD0C4]/60 shadow-sm shadow-[#3FD0C4]/20"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4] hover:bg-[#111C2B]"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-[#3FD0C4]" />
              <span>4 · Knowledge Assistant (RAG)</span>
            </button>

            {/* Tab 5: Architecture & 3D Atlas */}
            <button
              type="button"
              onClick={() => setActiveTab("atlas")}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                activeTab === "atlas"
                  ? "bg-[#0A7A74] text-white border border-[#3FD0C4]/60 shadow-sm shadow-[#3FD0C4]/20"
                  : "text-[#8C9DB0] hover:text-[#E6EDF4] hover:bg-[#111C2B]"
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-[#3FD0C4]" />
              <span>5 · Architecture &amp; 3D Atlas</span>
            </button>
          </nav>

          {/* Quick Context Summary */}
          <div className="hidden lg:flex items-center gap-2 text-xs text-[#8C9DB0]">
            {file ? (
              <span className="truncate max-w-[200px] text-[#E6EDF4] font-mono">
                {file.name}
              </span>
            ) : (
              <span className="text-[#566475] italic">No scan loaded</span>
            )}
          </div>
        </div>

        {/* Global Error Notice */}
        {error && (
          <div className="bg-rose-950/40 border border-rose-800 text-rose-200 p-3 rounded-xl text-xs flex items-center justify-between gap-3 shadow-md">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-white font-mono uppercase text-[10px]"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 1: VIEWPORT & INSPECTION                                              */}
        {/* ========================================================================= */}
        {activeTab === "viewport" && (
          <div className="space-y-4 animate-in fade-in duration-200">
            {/* Ingestion & Sample Bar */}
            <UploadDropzone
              onFileSelect={handleFileSelect}
              disabled={loading || isExplaining}
              hasFile={Boolean(file)}
            />

            {/* Run Analysis Action Button Strip */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0D1520] border border-[#1C2937] rounded-xl p-3 px-4 shadow-md">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={!file || loading || isExplaining}
                  className="rounded-xl bg-[#0A7A74] hover:bg-[#0A7A74]/80 border border-[#3FD0C4]/60 px-6 py-2.5 text-white font-semibold text-xs tracking-wider uppercase transition-all shadow-md shadow-[#3FD0C4]/20 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Sparkles className="w-4 h-4 animate-spin text-[#3FD0C4]" />
                      <span>Analyzing Radiograph...</span>
                    </>
                  ) : (
                    <>
                      <Monitor className="w-4 h-4 text-[#3FD0C4]" />
                      <span>Run Multi-Task AI Analysis</span>
                    </>
                  )}
                </button>

                {file && !prediction && !loading && (
                  <span className="text-xs text-[#8C9DB0]">
                    Ready to evaluate across 16 clinical conditions.
                  </span>
                )}
              </div>

              {prediction && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab("findings")}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] hover:border-[#3FD0C4] text-xs font-medium text-[#3FD0C4] transition"
                  >
                    <span>View All Findings ({findingsCount})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>

            {/* Viewport Grid Layout: Main Canvas on Left, Target Selectors on Right */}
            <div className="grid gap-5 lg:grid-cols-[3fr_2fr]">
              <div className="space-y-3">
                {/* High-Resolution Viewport Canvas */}
                <HeatmapViewer
                  original={previewUrl}
                  heatmap={heatmapUrl}
                  heatmapHasAlpha={heatmapHasAlpha}
                  contour={contourUrl}
                  contourHasAlpha={contourHasAlpha}
                  alpha={alpha}
                  diseaseName={selectedDiseaseName}
                  isGrounded={clinicalGrounding}
                  inLungRatio={maskWarning ? null : (inLungRatio ?? audit?.in_lung_energy_ratio ?? null)}
                  isExplaining={isExplaining || loading}
                  isRejected={prediction?.safety?.decision === "REJECT"}
                />

                {/* Heatmap Guidance Banners */}
                {noActivation && (
                  <div role="status" className="rounded-lg border border-amber-800/80 bg-amber-950/40 p-3 text-xs text-amber-200">
                    No focal activation detected for {selectedDiseaseName}. You may switch to Unmasked frame mode to check wider regions.
                  </div>
                )}
                {maskWarning && (
                  <div role="status" className="rounded-lg border border-amber-800/80 bg-amber-950/40 p-3 text-xs text-amber-200">
                    {maskWarning}{inLungRatio !== null && ` Estimated ratio: ${(inLungRatio * 100).toFixed(1)}%.`}
                  </div>
                )}

                {/* Opacity Slider & Anatomical Filter Toggle */}
                {file && (
                  <div className="space-y-2.5">
                    <AlphaSlider value={alpha} onChange={setAlpha} />

                    <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-2.5 px-3.5 flex flex-wrap items-center justify-between gap-3 shadow-md">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-[#8C9DB0] uppercase font-semibold">
                          Anatomical Grounding:
                        </span>
                        <div className="inline-flex rounded-lg border border-[#1C2937] bg-[#111C2B] p-0.5">
                          <button
                            type="button"
                            onClick={() => handleToggleGrounding(true)}
                            disabled={isExplaining || loading}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold transition-all ${
                              clinicalGrounding
                                ? "bg-[#0A7A74] text-white shadow-sm"
                                : "text-[#8C9DB0] hover:text-[#E6EDF4]"
                            }`}
                          >
                            <ShieldCheck className="w-3.5 h-3.5 text-[#3FD0C4]" />
                            <span>Masked Lung Field</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleToggleGrounding(false)}
                            disabled={isExplaining || loading}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold transition-all ${
                              !clinicalGrounding
                                ? "bg-[#0A7A74] text-white shadow-sm"
                                : "text-[#8C9DB0] hover:text-[#E6EDF4]"
                            }`}
                          >
                            <ShieldAlert className="w-3.5 h-3.5 text-[#8C9DB0]" />
                            <span>Unmasked Full Frame</span>
                          </button>
                        </div>
                      </div>

                      <span className="text-[10px] text-[#566475] hidden sm:inline">
                        Filters hospital text markers &amp; machine borders
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Quick Target Pathology Chips & Scan Insights */}
              <div className="space-y-4">
                {/* Quick Target Pathology Selector */}
                <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-4 shadow-md space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#1C2937]">
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-[#E6EDF4]">
                        Quick Pathology Selector
                      </h3>
                      <p className="text-[10px] text-[#8C9DB0]">
                        Click any condition to immediately inspect its Grad-CAM localization
                      </p>
                    </div>
                    <span className="text-[10px] font-mono text-[#3FD0C4]">
                      16 Conditions
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 max-h-[380px] overflow-y-auto pr-1">
                    {/* Specialized Screenings */}
                    <button
                      type="button"
                      onClick={() => handleSelectPathology("head_b", 0, "Tuberculosis")}
                      disabled={!prediction || isExplaining}
                      className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                        selectedHead === "head_b"
                          ? "bg-[#0A7A74] text-white border-[#3FD0C4] shadow-sm shadow-[#3FD0C4]/20"
                          : prediction?.head_b_tb_screening?.is_positive
                          ? "bg-amber-950/60 text-amber-300 border-amber-700"
                          : "bg-[#111C2B] text-[#8C9DB0] border-[#1C2937] hover:text-[#E6EDF4]"
                      } disabled:opacity-40`}
                    >
                      Tuberculosis (TB)
                    </button>

                    <button
                      type="button"
                      onClick={() => handleSelectPathology("head_c", 0, "COVID-19")}
                      disabled={!prediction || isExplaining}
                      className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                        selectedHead === "head_c"
                          ? "bg-[#0A7A74] text-white border-[#3FD0C4] shadow-sm shadow-[#3FD0C4]/20"
                          : prediction?.head_c_covidx?.is_positive
                          ? "bg-rose-950/60 text-rose-300 border-rose-700"
                          : "bg-[#111C2B] text-[#8C9DB0] border-[#1C2937] hover:text-[#E6EDF4]"
                      } disabled:opacity-40`}
                    >
                      COVID-19 Triage
                    </button>

                    {/* 14 Thoracic Conditions */}
                    {NIH_14_DISEASES.map((d, idx) => {
                      const isSelected = selectedHead === "head_a" && selectedClass === idx;
                      const prob = prediction?.head_a_prediction?.[d.id] ?? 0;
                      const isPos = Boolean(prediction && prob >= (NIH_THRESHOLDS[d.id] ?? 0.35));

                      return (
                        <button
                          key={d.id}
                          type="button"
                          onClick={() => handleSelectPathology("head_a", idx, d.id)}
                          disabled={!prediction || isExplaining}
                          className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all flex items-center gap-1.5 ${
                            isSelected
                              ? "bg-[#0A7A74] text-white border-[#3FD0C4] shadow-sm shadow-[#3FD0C4]/20"
                              : isPos
                              ? "bg-[#111C2B] text-[#3FD0C4] border-[#3FD0C4]/60"
                              : "bg-[#111C2B] text-[#8C9DB0] border-[#1C2937] hover:text-[#E6EDF4]"
                          } disabled:opacity-40`}
                        >
                          <span>{d.name}</span>
                          {prediction && (
                            <span className="font-mono text-[10px] opacity-75">
                              {(prob * 100).toFixed(0)}%
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Scan Status Summary Card */}
                {prediction && (
                  <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-4 shadow-md space-y-2.5 text-xs">
                    <h4 className="font-bold uppercase tracking-wider text-[#E6EDF4] text-xs">
                      Scan Evaluation Overview
                    </h4>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                      <div className="p-2.5 rounded-lg bg-[#111C2B] border border-[#1C2937]">
                        <span className="text-[#8C9DB0] block text-[10px]">INFERENCE LATENCY</span>
                        <span className="text-[#E6EDF4] font-bold">
                          {prediction.inference_time_ms.toFixed(0)} ms
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#111C2B] border border-[#1C2937]">
                        <span className="text-[#8C9DB0] block text-[10px]">TOTAL DETECTIONS</span>
                        <span className="text-[#3FD0C4] font-bold">
                          {findingsCount} Conditions
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: DIAGNOSTIC FINDINGS PANEL                                         */}
        {/* ========================================================================= */}
        {activeTab === "findings" && (
          <div className="animate-in fade-in duration-200">
            <DiagnosisDashboard
              prediction={prediction}
              auditRatio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null}
              auditPass={audit?.pass_80_percent ?? null}
              selectedHead={selectedHead}
              selectedClass={selectedClass}
              onSelectPathology={handleSelectPathology}
              onNavigateToScan={() => setActiveTab("viewport")}
              onBypassFailsafe={() => handleToggleFailsafe(false)}
              isExplaining={isExplaining || loading}
            />
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: CLINICAL CDS REPORT                                               */}
        {/* ========================================================================= */}
        {activeTab === "report" && (
          <div className="space-y-4 animate-in fade-in duration-200">
            {/* Formal Report Card */}
            <div className="rounded-xl border border-[#1C2937] bg-[#0D1520] p-6 space-y-5 shadow-xl text-[#E6EDF4]">
              {/* Report Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[#1C2937]">
                <div>
                  <h2 className="text-lg font-bold tracking-tight text-[#E6EDF4]">
                    LungRay Clinical Decision Support (CDS) Report
                  </h2>
                  <p className="text-xs text-[#8C9DB0] mt-0.5">
                    Automated Second-Reader Radiologic Evaluation
                  </p>
                </div>
                <div className="text-right text-xs font-mono text-[#8C9DB0]">
                  <p>Scan ID: <span className="text-[#E6EDF4]">{file?.name ?? "N/A"}</span></p>
                  <p>AI Engine: <span className="text-[#3FD0C4]">{prediction?.model_display_name ?? selectedModel}</span></p>
                  <p>Processing: <span className="text-[#E6EDF4]">{prediction ? `${prediction.inference_time_ms.toFixed(0)} ms` : "—"}</span></p>
                </div>
              </div>

              {/* Clinical Impression Box */}
              <div className="p-4 rounded-xl bg-[#111C2B] border border-[#1C2937] space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#3FD0C4]">
                  Clinical Impression
                </h3>
                <p className="text-sm text-[#E6EDF4] leading-relaxed">
                  {isExplaining
                    ? "Generating anatomical activation heatmap..."
                    : (inLungRatio !== null && inLungRatio < 0.8) || explanationAuditPass === false
                    ? "Heatmap activation within lung parenchyma is below 80%. Automated impression withheld; radiologist review advised."
                    : prediction?.report?.impression?.replace(/<[^>]*>/g, "") ?? "No radiograph analyzed yet."}
                </p>
                {maskWarning && (
                  <p className="text-xs text-amber-400 pt-1 border-t border-[#1C2937]">
                    Anatomical note: {maskWarning}
                  </p>
                )}
              </div>

              {/* Side-by-Side Visual Documentation (Radiograph + Heatmap) */}
              {previewUrl && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-[#111C2B] border border-[#1C2937]">
                  <figure className="space-y-1.5">
                    <figcaption className="text-xs font-semibold text-[#8C9DB0] uppercase tracking-wider">
                      Original Radiograph (512×512 Standardized)
                    </figcaption>
                    <div className="relative aspect-square rounded-lg overflow-hidden bg-black border border-[#1C2937]">
                      <Image src={previewUrl} alt="Original CXR" fill className="object-contain" />
                    </div>
                  </figure>

                  <figure className="space-y-1.5">
                    <figcaption className="text-xs font-semibold text-[#8C9DB0] uppercase tracking-wider">
                      Grad-CAM Localization ({selectedDiseaseName})
                    </figcaption>
                    <div className="relative aspect-square rounded-lg overflow-hidden bg-black border border-[#1C2937]">
                      {heatmapUrl ? (
                        <>
                          <Image src={previewUrl} alt="Original CXR" fill className="object-contain" />
                          <Image
                            src={heatmapUrl}
                            alt="Grad-CAM overlay"
                            fill
                            className="object-contain"
                            style={{ opacity: alpha / 100, mixBlendMode: heatmapHasAlpha ? "normal" : "screen" }}
                          />
                        </>
                      ) : (
                        <div className="flex h-full items-center justify-center text-xs text-[#566475]">
                          Heatmap not generated
                        </div>
                      )}
                    </div>
                  </figure>
                </div>
              )}

              {/* Diagnostic Findings Table with ICD-10 */}
              {prediction && prediction.safety?.decision !== "REJECT" && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#8C9DB0]">
                    Pathology Evaluation Summary Table
                  </h3>
                  <div className="overflow-x-auto rounded-xl border border-[#1C2937]">
                    <table className="w-full text-left text-xs text-[#E6EDF4]">
                      <thead className="bg-[#111C2B] text-[#8C9DB0] uppercase font-mono text-[10px] border-b border-[#1C2937]">
                        <tr>
                          <th className="p-3">Pathology</th>
                          <th className="p-3">ICD-10</th>
                          <th className="p-3">Score / Cutoff</th>
                          <th className="p-3">Detection Status</th>
                          <th className="p-3">Clinical Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1C2937]">
                        {NIH_14_DISEASES.map((disease) => {
                          const score = prediction.head_a_prediction?.[disease.id];
                          const threshold = NIH_THRESHOLDS[disease.id] ?? 0.35;
                          const isDetected = score !== undefined && score >= threshold;

                          return (
                            <tr key={disease.id} className="hover:bg-[#111C2B]/50 transition-colors">
                              <td className="p-3 font-medium text-[#E6EDF4]">{disease.name}</td>
                              <td className="p-3 font-mono text-[#8C9DB0]">{disease.icd10}</td>
                              <td className="p-3 font-mono">
                                {score === undefined ? "—" : `${(score * 100).toFixed(1)}%`} / {(threshold * 100).toFixed(1)}%
                              </td>
                              <td className="p-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                                    isDetected
                                      ? "bg-[#0A7A74]/30 text-[#3FD0C4] border-[#3FD0C4]/50"
                                      : "bg-[#070B12] text-[#8C9DB0] border-[#1C2937]"
                                  }`}
                                >
                                  {isDetected ? "Detected" : "Clear"}
                                </span>
                              </td>
                              <td className="p-3 text-[#8C9DB0]">
                                {isDetected ? "Radiologist verification recommended" : "Routine clinical monitoring"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Follow-up Recommendations */}
              {prediction?.report?.recommendations && prediction.report.recommendations.length > 0 && (
                <div className="p-4 rounded-xl bg-[#111C2B] border border-[#1C2937] space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#3FD0C4]">
                    Follow-Up Clinical Recommendations
                  </h3>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-[#E6EDF4] leading-relaxed">
                    {prediction.report.recommendations.map((rec, index) => (
                      <li key={index}>{rec.replace(/<[^>]*>/g, "")}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons: Print & PDF Export */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-[#1C2937]">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0A7A74] hover:bg-[#0A7A74]/80 text-white text-xs font-semibold transition"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    <span>Print Report</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#111C2B] hover:bg-[#162233] border border-[#1C2937] text-[#E6EDF4] text-xs font-semibold transition"
                  >
                    <span>Save as PDF</span>
                  </button>
                </div>
                <p className="text-[10px] text-[#566475] italic">
                  Select &quot;Save as PDF&quot; in the print dialog to export a digital copy.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: CLINICAL KNOWLEDGE ASSISTANT (RAG)                                */}
        {/* ========================================================================= */}
        {activeTab === "rag" && (
          <div className="animate-in fade-in duration-200">
            {prediction ? (
              <ClinicalRagAssistant
                prediction={prediction}
                ratio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null}
              />
            ) : (
              <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-8 text-center text-[#8C9DB0] space-y-2">
                <BookOpen className="w-8 h-8 mx-auto text-[#566475]" />
                <h3 className="text-sm font-semibold text-[#E6EDF4]">
                  No Active Radiograph Case Loaded
                </h3>
                <p className="text-xs text-[#8C9DB0] max-w-md mx-auto">
                  Please ingest a chest radiograph and run AI analysis in Tab 1 to enable case-grounded clinical knowledge lookup.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveTab("viewport")}
                  className="mt-3 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#0A7A74] text-white text-xs font-semibold"
                >
                  <span>Go to Viewport</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 5: ARCHITECTURE & 3D ATLAS                                           */}
        {/* ========================================================================= */}
        {activeTab === "atlas" && (
          <div className="space-y-3 animate-in fade-in duration-200">
            <div className="bg-[#0D1520] border border-[#1C2937] rounded-xl p-3 px-4 flex flex-wrap items-center justify-between gap-3 shadow-md">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#E6EDF4]">
                  LungRay Interactive 3D WSOL Stack &amp; Pipeline Atlas
                </h3>
                <p className="text-[10px] text-[#8C9DB0]">
                  Volumetric spatial feature map decomposition &amp; three-stage multi-task pipeline
                </p>
              </div>

              <a
                href="/pipeline-atlas.html"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111C2B] border border-[#1C2937] hover:border-[#3FD0C4] text-xs font-medium text-[#3FD0C4] transition"
              >
                <span>Open in Full Screen</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* Embedded Interactive 3D WSOL Atlas Iframe */}
            <div className="w-full rounded-xl overflow-hidden border border-[#1C2937] bg-[#070B12] shadow-2xl">
              <iframe
                src="/pipeline-atlas.html"
                title="LungRay 3D WSOL Pipeline Atlas"
                className="w-full h-[82vh] border-0"
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
