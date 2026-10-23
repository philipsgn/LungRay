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
  const [alpha, setAlpha] = useState<number>(40);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    setHeatmapUrl(null);
    setPrediction(null);
    setAudit(null);

    setLoading(true);
    try {
      const predictionResult = await predictImage(selectedFile);
      setPrediction(predictionResult);

      const explainResult = await explainImage(selectedFile, "head_c", 0);
      setHeatmapUrl(`data:image/png;base64,${explainResult.heatmap_base64}`);

      const auditResult = await auditImage(selectedFile);
      setAudit(auditResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <PacsHeader />
      <main className="max-w-7xl mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <UploadDropzone onFileSelect={handleFileSelect} />
          <HeatmapViewer original={previewUrl} heatmap={heatmapUrl} alpha={alpha} />
          {file && <AlphaSlider value={alpha} onChange={setAlpha} />}
          {loading && (
            <div className="text-center text-slate-400 py-4">
              Analyzing image with backend API...
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
            auditRatio={audit?.in_lung_energy_ratio ?? null}
            auditPass={audit?.pass_80_percent ?? null}
          />
        </div>
      </main>
    </div>
  );
}
