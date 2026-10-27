"use client";

import { useState } from "react";
import AlphaSlider from "./components/AlphaSlider";
import DiagnosisDashboard from "./components/DiagnosisDashboard";
import HeatmapViewer from "./components/HeatmapViewer";
import PacsHeader from "./components/PacsHeader";
import UploadDropzone from "./components/UploadDropzone";
import { auditImage, explainImage, predictImage } from "./lib/api";
import { AuditResponse, PredictionResponse } from "./types";

export default function Home() {
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

  const fetchExplanation = async (
    currentFile: File,
    head: string,
    classIdx: number,
    diseaseName: string,
    grounding: boolean
  ) => {
    setIsExplaining(true);
    try {
      const explainResult = await explainImage(
        currentFile,
        head,
        classIdx,
        grounding,
        diseaseName
      );
      setHeatmapUrl(`data:image/png;base64,${explainResult.heatmap_base64}`);
      setSelectedHead(explainResult.target_head);
      setSelectedClass(explainResult.target_class);
      setSelectedDiseaseName(explainResult.target_disease_name || diseaseName);
      setClinicalGrounding(Boolean(explainResult.is_grounded));
      if (explainResult.in_lung_energy_ratio !== undefined) {
        setInLungRatio(explainResult.in_lung_energy_ratio);
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
    setPrediction(null);
    setAudit(null);
    setInLungRatio(null);

    setLoading(true);
    try {
      const [predResult, auditResult] = await Promise.all([
        predictImage(selectedFile),
        auditImage(selectedFile),
      ]);
      setPrediction(predResult);
      setAudit(auditResult);

      // Default explanation: Head C COVID-19 with Clinical Grounding
      await fetchExplanation(selectedFile, "head_c", 0, "COVID-19", true);
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
      newGrounding
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <PacsHeader />
      <main className="max-w-7xl mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <UploadDropzone onFileSelect={handleFileSelect} />
          <HeatmapViewer
            original={previewUrl}
            heatmap={heatmapUrl}
            alpha={alpha}
            diseaseName={selectedDiseaseName}
            isGrounded={clinicalGrounding}
            inLungRatio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null}
            isExplaining={isExplaining}
          />
          {file && <AlphaSlider value={alpha} onChange={setAlpha} />}
          {loading && (
            <div className="text-center text-slate-400 py-4 flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5 text-cyan-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Analyzing CXR with multi-task CADx pipeline & generating clinical maps...</span>
            </div>
          )}
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 text-rose-200 rounded-lg p-3 text-sm">
              {error}
            </div>
          )}
        </div>
        <div className="lg:col-span-1">
          <DiagnosisDashboard
            prediction={prediction}
            auditRatio={inLungRatio ?? audit?.in_lung_energy_ratio ?? null}
            auditPass={audit?.pass_80_percent ?? null}
            selectedHead={selectedHead}
            selectedClass={selectedClass}
            clinicalGrounding={clinicalGrounding}
            onSelectPathology={handleSelectPathology}
            onToggleGrounding={handleToggleGrounding}
            isExplaining={isExplaining || loading}
          />
        </div>
      </main>
    </div>
  );
}
