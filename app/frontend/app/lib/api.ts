"use client";

import {
  AuditResponse,
  ExplainResponse,
  HealthResponse,
  PredictionResponse,
} from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => "Unknown error");
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`, {
    method: "GET",
    cache: "no-store",
  });
  return handleResponse<HealthResponse>(response);
}

export async function predictImage(file: File): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/v1/predict`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<PredictionResponse>(response);
}

export async function explainImage(
  file: File,
  targetHead: string,
  targetClass: number,
  clinicalGrounding: boolean = true,
  targetDiseaseName: string = ""
): Promise<ExplainResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_head", targetHead);
  formData.append("target_class", String(targetClass));
  formData.append("clinical_grounding", String(clinicalGrounding));
  if (targetDiseaseName) {
    formData.append("target_disease_name", targetDiseaseName);
  }
  const response = await fetch(`${API_BASE}/api/v1/explain`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<ExplainResponse>(response);
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
