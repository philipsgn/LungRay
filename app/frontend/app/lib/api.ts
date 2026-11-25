"use client";

import {
  AuditResponse,
  ExplainResponse,
  HealthResponse,
  ModelInfo,
  PredictionResponse,
  RagQueryRequest,
  RagQueryResponse,
} from "../types";
import {
  edgeExplainImage,
  edgePredictImage,
  edgeQueryClinicalRag,
} from "./edgeFallback";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => "Unknown error");
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await fetchWithTimeout(`${API_BASE}/health`, {
    method: "GET",
    cache: "no-store",
  }, 3000);
  return handleResponse<HealthResponse>(response);
}

export const checkHealth = checkBackendHealth;

export async function getModels(): Promise<ModelInfo[]> {
  const response = await fetch(`${API_BASE}/api/v1/models`, {
    method: "GET",
    cache: "no-store",
  });
  return handleResponse<ModelInfo[]>(response);
}

export async function predictImage(
  file: File,
  model: string = "standard",
  failsafeEnabled: boolean = true,
  ttaEnabled: boolean = true
): Promise<PredictionResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetchWithTimeout(
      `${API_BASE}/api/v1/predict?model=${encodeURIComponent(model)}&failsafe_enabled=${failsafeEnabled}&tta_enabled=${ttaEnabled}`,
      {
        method: "POST",
        body: formData,
      },
      12000
    );
    return await handleResponse<PredictionResponse>(response);
  } catch {
    return edgePredictImage(file, model, failsafeEnabled, ttaEnabled);
  }
}

export async function explainImage(
  file: File,
  targetHead: string,
  targetClass: number,
  clinicalGrounding: boolean = true,
  targetDiseaseName: string = "",
  model: string = "standard"
): Promise<ExplainResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_head", targetHead);
    formData.append("target_class", String(targetClass));
    formData.append("clinical_grounding", String(clinicalGrounding));
    formData.append("model", model);
    if (targetDiseaseName) {
      formData.append("target_disease_name", targetDiseaseName);
    }
    const response = await fetchWithTimeout(`${API_BASE}/api/v1/explain`, {
      method: "POST",
      body: formData,
    }, 12000);
    return await handleResponse<ExplainResponse>(response);
  } catch {
    return edgeExplainImage(file, targetHead, targetClass, targetDiseaseName);
  }
}

export async function auditImage(file: File): Promise<AuditResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/v1/audit`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<AuditResponse>(response);
}


export async function queryClinicalRag(payload: RagQueryRequest): Promise<RagQueryResponse> {
  try {
    const response = await fetchWithTimeout(`${API_BASE}/api/v1/rag-query`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, 6000);
    return await handleResponse<RagQueryResponse>(response);
  } catch {
    return edgeQueryClinicalRag(payload);
  }
}
