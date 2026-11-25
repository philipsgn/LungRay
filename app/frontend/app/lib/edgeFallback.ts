"use client";

import { ExplainResponse, PredictionResponse, RagQueryRequest, RagQueryResponse } from "../types";

// A transparent RGBA PNG indicates absence of explanation; it is never a CAM.
const TRANSPARENT_RGBA = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg==";
const UNAVAILABLE = "Inference backend unavailable. No model prediction, OOD measurement or localization was performed. Please retry when the service is available.";

export async function edgePredictImage(
  _file: File, _model: string, _failsafeEnabled: boolean, _ttaEnabled: boolean
): Promise<PredictionResponse> {
  void _file; void _model; void _failsafeEnabled; void _ttaEnabled;
  return {
    inference_source: "unavailable", head_a_prediction: {},
    head_b_tb_screening: { tb_probability: 0, is_positive: false },
    head_c_covidx: { available: false, status: "UNAVAILABLE", message: UNAVAILABLE },
    inference_time_ms: 0, tta_enabled: false, passes_executed: 0,
    active_model: "unavailable", model_display_name: "Backend unavailable — analysis not performed",
    safety: { decision: "REJECT", is_safe: false, energy_score: 0, entropy_score: 0,
      rejection_reasons: [UNAVAILABLE, "Numeric safety values are unmeasured placeholders."] },
    report: { status: "BLOCKED", is_blocked: true, findings: [], active_findings: [],
      anatomical_locations: [], icd10_codes: [], impression: UNAVAILABLE,
      recommendations: ["Reconnect the inference backend and analyze the image again."],
      disclaimer: "No clinical interpretation is available." },
    in_lung_energy_ratio: null,
  };
}

export async function edgeExplainImage(
  _file: File, targetHead: string, targetClass: number, targetDiseaseName: string
): Promise<ExplainResponse> {
  void _file;
  return { inference_source: "unavailable", heatmap_base64: TRANSPARENT_RGBA,
    heatmap_rgba_base64: TRANSPARENT_RGBA, contour_base64: TRANSPARENT_RGBA,
    contour_rgba_base64: TRANSPARENT_RGBA, overlay_base64: TRANSPARENT_RGBA,
    heatmap_has_activation: false, mask_source: "unavailable", mask_warning: UNAVAILABLE,
    cam_resolution: "unavailable", target_head: targetHead, target_class: targetClass,
    target_disease_name: targetDiseaseName, audit_pass: null, is_grounded: false };
}

export async function edgeQueryClinicalRag(payload: RagQueryRequest): Promise<RagQueryResponse> {
  if (!payload.is_safe) return { status: "BLOCKED_OOD", answer: "Safety lockout: no disease interpretation. Verify the input and repeat analysis.", citations: [], retrieved_cards: [] };
  return { status: "UNAVAILABLE", answer: "Knowledge backend unavailable. No clinical guidance was retrieved; please retry.", citations: [], retrieved_cards: [] };
}
