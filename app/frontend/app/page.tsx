"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import AlphaSlider from "./components/AlphaSlider";
import DiagnosisDashboard, { NIH_14_DISEASES, NIH_THRESHOLDS } from "./components/DiagnosisDashboard";
import HeatmapViewer from "./components/HeatmapViewer";
import PacsHeader from "./components/PacsHeader";
import UploadDropzone from "./components/UploadDropzone";
import { checkBackendHealth, explainImage, predictImage } from "./lib/api";
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
  const [failedStep, setFailedStep] = useState<"predict" | "explain" | null>(null);
  const lastExplanation = useRef<{ file: File; head: string; classIdx: number; diseaseName: string; grounding: boolean; modelName: string } | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);

  // Interactive Pathology & Grounding State
  const [selectedHead, setSelectedHead] = useState<string>("head_a");
  const [selectedClass, setSelectedClass] = useState<number>(0);
  const [selectedDiseaseName, setSelectedDiseaseName] = useState<string>("Atelectasis");
  const [clinicalGrounding, setClinicalGrounding] = useState<boolean>(true);
  const [inLungRatio, setInLungRatio] = useState<number | null>(null);
  const [explanationAuditPass, setExplanationAuditPass] = useState<boolean | null>(null);
  const [isTargetPositive, setIsTargetPositive] = useState<boolean>(true);
  const [contourUrl, setContourUrl] = useState<string | null>(null);
  const [contourHasAlpha, setContourHasAlpha] = useState(false);
  const [noActivation, setNoActivation] = useState(false);
  const [maskWarning, setMaskWarning] = useState("");
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
      setFailedStep(null);
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
      setExplanationAuditPass(explainResult.audit_pass ?? null);
      if (explainResult.is_target_positive !== undefined) {
        setIsTargetPositive(explainResult.is_target_positive);
      }
    } catch (err) {
      setFailedStep("explain");
      if (err instanceof Error && err.name === "AbortError") {
        setError("Tạo heatmap quá thời gian cho phép. Backend có thể đang bận; vui lòng thử lại.");
      } else if (err instanceof TypeError) {
        setConnected(false);
        setError("Không thể kết nối Máy chủ AI Backend (FastAPI, localhost:8000). Vui lòng kiểm tra dịch vụ.");
      } else {
        setError(err instanceof Error ? err.message : "Không thể tạo heatmap.");
      }
    } finally {
      setIsExplaining(false);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setFailedStep(null);
    lastExplanation.current = null;
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setLesions([]);
    setLesionAreaRatio(0);
    setPrediction(null);
    setAudit(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);

  };

  const handleAnalyze = async () => {
    if (!file) return;
    const selectedFile = file;
    setError(null);
    setFailedStep(null);
    setPrediction(null);
    setHeatmapUrl(null);
    setNoActivation(false);
    setMaskWarning("");
    setContourUrl(null);
    setInLungRatio(null);
    setExplanationAuditPass(null);
    setLoading(true);
    try { await checkBackendHealth(); setConnected(true); } catch { setConnected(false); setFailedStep("predict"); setError("Không thể kết nối Máy chủ AI Backend (FastAPI, localhost:8000). Vui lòng kiểm tra dịch vụ."); setLoading(false); return; }
    try {
      const predResult = await predictImage(selectedFile, selectedModel, failsafeEnabled, ttaEnabled);
      setPrediction(predResult);
      setAudit(null);

      // Smart Default Explanation: Prioritize highest confidence pathology on the scan
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

      if (predResult.safety?.decision !== "REJECT") await fetchExplanation(selectedFile, bestHead, bestClass, bestName, clinicalGrounding);
    } catch (err) {
      setFailedStep("predict");
      if (err instanceof Error && err.name === "AbortError") {
        setError("Phân tích quá thời gian cho phép. Backend có thể đang bận; vui lòng thử lại.");
      } else if (err instanceof TypeError) {
        setConnected(false);
        setError("Không thể kết nối Máy chủ AI Backend (FastAPI, localhost:8000). Vui lòng kiểm tra dịch vụ.");
      } else {
        setError(err instanceof Error ? err.message : "Không thể phân tích ảnh.");
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
    setFailedStep(null); setError(null); lastExplanation.current = null;
    setPrediction(null); setHeatmapUrl(null); setNoActivation(false); setMaskWarning(""); setContourUrl(null); setInLungRatio(null); setExplanationAuditPass(null); setAudit(null);
  };
  const handleToggleFailsafe = (enabled: boolean) => {
    setFailedStep(null); setError(null); lastExplanation.current = null;
    setFailsafeEnabled(enabled); setPrediction(null); setHeatmapUrl(null); setNoActivation(false); setMaskWarning(""); setContourUrl(null); setInLungRatio(null); setExplanationAuditPass(null);
  };
  const retryConnection = async () => {
    if (failedStep === "explain" && lastExplanation.current) {
      const retry = lastExplanation.current;
      await fetchExplanation(retry.file, retry.head, retry.classIdx, retry.diseaseName, retry.grounding, retry.modelName);
    } else if (failedStep === "predict") {
      await handleAnalyze();
    }
  };

  return (
    <div className="min-h-screen bg-[#FBFBF9] text-slate-900 font-sans">
      <PacsHeader
        selectedModel={selectedModel}
        onSelectModel={handleModelChange}
        failsafeEnabled={failsafeEnabled}
        onToggleFailsafe={handleToggleFailsafe}
        ttaEnabled={ttaEnabled}
        onToggleTta={(value) => { setTtaEnabled(value); setFailedStep(null); setError(null); lastExplanation.current = null; setPrediction(null); setHeatmapUrl(null); setNoActivation(false); setMaskWarning(""); setContourUrl(null); setInLungRatio(null); setExplanationAuditPass(null); }}
        connected={connected}
        disabled={loading || isExplaining}
      />

      <main className="max-w-7xl mx-auto p-3 sm:p-5 space-y-4">
        {/* ========================================================================= */}
        {/* SECTION NAVIGATION TABS (WORKSTATION vs FINDINGS & REPORT)                */}
        {/* ========================================================================= */}
        <div className="bg-white border border-slate-200 rounded-xl p-1.5 flex items-center justify-between gap-2 shadow-sm font-sans">
          <div className="flex items-center gap-1.5 w-full sm:w-auto">
            {/* Tab 1: Scan & Viewport Workstation */}
            <button
              type="button"
              onClick={() => setActiveSection("scan")}
              className={`flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                activeSection === "scan"
                  ? "bg-slate-200 text-sky-700 border border-slate-300 shadow-sm"
                  : "text-slate-600 hover:text-slate-800 hover:bg-slate-100"
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
                  ? "bg-slate-200 text-sky-700 border border-slate-300 shadow-sm"
                  : "text-slate-600 hover:text-slate-800 hover:bg-slate-100"
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
              <span>{t.section2Tab}</span>

              {/* Status Badge */}
              {prediction && (
                <span className="ml-1 px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-slate-100 text-cyan-400 border border-cyan-800 animate-pulse">
                  {findingsCount > 0 ? `${findingsCount}` : "✓"}
                </span>
              )}
            </button>
          </div>

          {/* Quick Context Summary */}
          <div className="hidden sm:flex items-center gap-2 text-[10px] text-slate-600">
            {file ? (
              <span className="truncate max-w-[200px] text-slate-700 font-medium">
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
              disabled={loading || isExplaining}
              hasFile={Boolean(file)}
            />

            <div className="flex flex-wrap items-center gap-3"><button type="button" onClick={handleAnalyze} disabled={!file || loading || isExplaining} className="rounded-xl bg-sky-600 px-6 py-3 text-white font-semibold hover:bg-sky-700 disabled:opacity-50">{loading ? "Đang phân tích…" : "Bắt đầu Phân tích AI"}</button><span className="text-sm text-slate-600">{connected === true ? "Đã kết nối API (Port 8000)" : connected === false ? "Chưa kết nối API" : "Chưa kiểm tra kết nối"}</span></div>
            <div className="grid gap-5 lg:grid-cols-[3fr_2fr]"><div className="space-y-3">
            {/* Prominent High-Precision X-ray & Heatmap Viewport */}
            <HeatmapViewer
              original={previewUrl}
              heatmap={heatmapUrl}
              heatmapHasAlpha={heatmapHasAlpha}
              contour={contourUrl}
              contourHasAlpha={contourHasAlpha}
              lesions={lesions}
              lesionAreaRatio={lesionAreaRatio}
              camResolution={camResolution}
              alpha={alpha}
              diseaseName={selectedDiseaseName}
              isGrounded={clinicalGrounding}
              inLungRatio={maskWarning ? null : (inLungRatio ?? audit?.in_lung_energy_ratio ?? null)}
              isExplaining={isExplaining || loading}
              isRejected={prediction?.safety?.decision === "REJECT"}
              isTargetPositive={isTargetPositive}
            />
            {noActivation && <div role="status" className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Heatmap hiện không có tín hiệu kích hoạt trong chế độ đang chọn. Có thể thử bản đồ gốc để kiểm tra; điều này không xác nhận ảnh bình thường.</div>}
            {maskWarning && <div role="status" className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">{maskWarning}{inLungRatio !== null && ` Tỷ lệ ước tính: ${(inLungRatio * 100).toFixed(1)}%.`}</div>}

            {/* Viewport Control Strip: Alpha Slider & Anatomical Grounding Filter */}
            {file && (
              <div className="space-y-2.5 font-sans">
                {/* Alpha Slider */}
                <AlphaSlider value={alpha} onChange={setAlpha} />

                {/* Grounding & Quick Jump Bar */}
                <div className="bg-white border border-slate-200 rounded-xl p-2.5 px-3 flex flex-wrap items-center justify-between gap-3 shadow-sm">
                  {/* Left: Anatomical Filter Switch */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] text-slate-600 uppercase font-semibold">
                      {t.groundingTitle}:
                    </span>
                    <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
                      <button
                        type="button"
                        onClick={() => handleToggleGrounding(true)}
                        disabled={isExplaining || loading}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                          clinicalGrounding
                            ? "bg-slate-200 text-white border border-slate-300 shadow-sm"
                            : "text-slate-600 hover:text-slate-800"
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
                            ? "bg-slate-200 text-white border border-slate-300 shadow-sm"
                            : "text-slate-600 hover:text-slate-800"
                        }`}
                      >
                        <ShieldAlert className="w-3 h-3 text-slate-600" />
                        <span>{t.rawBtn}</span>
                      </button>
                    </div>
                  </div>

                  {/* Right: CTA Button to jump to Section 2 (Report) */}
                  {prediction && (
                    <button
                      type="button"
                      onClick={() => setActiveSection("report")}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 border border-cyan-500/40 text-sky-700 text-xs font-semibold hover:bg-slate-850 hover:text-white transition-all shadow-sm group"
                    >
                      <span>{t.viewReportBtn}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  )}
                </div>
              </div>
            )}

            </div><aside className="space-y-3"><DiagnosisDashboard prediction={prediction} auditRatio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null} auditPass={explanationAuditPass} selectedHead={selectedHead} selectedClass={selectedClass} clinicalGrounding={clinicalGrounding} onSelectPathology={handleSelectPathology} onToggleGrounding={handleToggleGrounding} onNavigateToScan={() => setActiveSection("scan")} isExplaining={isExplaining || loading} /></aside></div>
            {/* Multi-Task Processing Indicator */}
            {loading && (
              <div className="text-center text-slate-600 py-3 flex items-center justify-center gap-2 font-sans text-xs bg-slate-100/60 border border-slate-200 rounded-lg">
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
              <div role="alert" className="bg-orange-50 border border-orange-200 text-orange-900 rounded-xl p-4 text-sm">
                {error} <button type="button" onClick={retryConnection} className="ml-3 underline font-semibold">Thử lại</button>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECTION 2: KẾT QUẢ & BÁO CÁO LÂM SÀNG (DIAGNOSTIC FINDINGS & REPORT)      */}
        {/* ========================================================================= */}
        {activeSection === "report" && (
          <div className="animate-in fade-in duration-200 space-y-4"><div className="rounded-xl border border-slate-200 bg-white p-6 text-slate-900"><h2 className="text-xl font-bold">DSP391 – LungRay CADx</h2><p className="mt-2 text-sm">Mã ảnh: {file?.name ?? "Chưa có ảnh"} · Model: {prediction?.model_display_name ?? selectedModel} · Thời gian suy luận: {prediction ? `${prediction.inference_time_ms.toFixed(0)} ms` : "—"}</p><p className="mt-2 text-sm text-slate-600">Kết luận sơ bộ: {isExplaining ? "Đang tạo bản đồ giải thích. Tạm ẩn kết luận tự động." : (inLungRatio !== null && inLungRatio < 0.8) || explanationAuditPass === false ? "Năng lượng heatmap đang chọn trong phổi dưới 80%. Tạm ẩn kết luận tự động; cần bác sĩ đối chiếu." : prediction?.report?.impression?.replace(/<[^>]*>/g, "") ?? "Chưa có kết quả phân tích"}</p>{maskWarning && <p role="status" className="mt-2 text-sm text-amber-800">{maskWarning}</p>}<p className="text-sm text-slate-600">Chữ ký: Hệ thống LungRay AI</p></div>
            {previewUrl && <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-200 bg-white p-4"><figure><figcaption className="mb-2 text-sm font-semibold">Ảnh gốc</figcaption><div className="relative aspect-square"><Image src={previewUrl} alt="Ảnh gốc" fill className="object-contain" /></div></figure><figure><figcaption className="mb-2 text-sm font-semibold">Grad-CAM</figcaption><div className="relative aspect-square">{heatmapUrl && <><Image src={previewUrl} alt="Ảnh gốc với Grad-CAM" fill className="object-contain" /><Image src={heatmapUrl} alt="Grad-CAM" fill className="object-contain" style={{ opacity: alpha / 100, mixBlendMode: heatmapHasAlpha ? "normal" : "screen" }} /></>}</div>{!heatmapUrl && <p className="text-sm text-slate-500">Chưa có bản đồ giải thích</p>}</figure></div>}
            {prediction && prediction.safety?.decision !== "REJECT" && <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-4"><h3 className="mb-3 font-semibold text-slate-900">Bảng gợi ý bệnh lý Head A</h3><table className="w-full text-left text-sm text-slate-700"><thead><tr className="border-b border-slate-200"><th>Bệnh lý</th><th>ICD-10</th><th>Điểm / ngưỡng</th><th>Trạng thái</th><th>Khuyến cáo</th></tr></thead><tbody>{NIH_14_DISEASES.map((disease) => { const score = prediction.head_a_prediction[disease.id]; const threshold = NIH_THRESHOLDS[disease.id]; return <tr key={disease.id} className="border-b border-slate-100"><td>{disease.nameVi}</td><td>{disease.icd10}</td><td>{score === undefined ? "—" : `${(score * 100).toFixed(1)}%`} / {(threshold * 100).toFixed(1)}%</td><td>{score === undefined ? "Không có dữ liệu" : score >= threshold ? "Vượt ngưỡng" : "Dưới ngưỡng"}</td><td>Đối chiếu bởi bác sĩ</td></tr>; })}</tbody></table><p className="mt-2 text-xs text-slate-500">Điểm mô hình và ngưỡng là thông tin hỗ trợ, không xác nhận chẩn đoán.</p></div>}
            {!isExplaining && !(inLungRatio !== null && inLungRatio < 0.8) && explanationAuditPass !== false && prediction?.report?.recommendations && prediction.report.recommendations.length > 0 && <div className="rounded-xl border border-slate-200 bg-white p-4 text-slate-700"><h3 className="font-semibold">Khuyến cáo từ báo cáo AI</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{prediction.report.recommendations.map((item, index) => <li key={index}>{item.replace(/<[^>]*>/g, "")}</li>)}</ul></div>}
            <footer className="rounded-xl border border-slate-200 bg-white p-4"><div className="mt-4 flex gap-3"><button type="button" onClick={() => window.print()} className="rounded-lg bg-sky-600 px-4 py-2 text-white">In phiếu</button><button type="button" onClick={() => window.print()} className="rounded-lg border border-slate-300 px-4 py-2">Xuất PDF</button></div><p className="mt-2 text-xs text-slate-500">Chọn “Lưu thành PDF” trong hộp thoại in để xuất PDF.</p></footer>
          </div>
        )}
      </main>
    </div>
  );
}
