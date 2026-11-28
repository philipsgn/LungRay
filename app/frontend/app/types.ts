export interface HealthResponse {
  status: string;
  device: string;
  version: string;
  ood_failsafe_enabled?: boolean;
}

export interface ModelInfo {
  id: string;
  name: string;
  role: string;
  metrics: Record<string, unknown>;
  description?: string;
  best_for?: string;
  checkpoint: string;
}

export interface SafetyDecision {
  decision: "ACCEPT" | "REJECT";
  is_safe: boolean;
  energy_score: number;
  entropy_score: number;
  rejection_reasons: string[];
}

export interface ClinicalReport {
  status: "GENERATED" | "BLOCKED";
  is_blocked: boolean;
  findings: string[];
  active_findings?: string[];
  anatomical_locations: string[];
  icd10_codes: string[];
  impression: string;
  recommendations: string[];
  disclaimer: string;
}

export interface HeadBScreening {
  tb_probability: number;
  is_positive: boolean;
}

export interface HeadCScreening {
  available?: boolean;
  status?: string;
  message?: string;
  covid_probability?: number;
  threshold?: number;
  is_positive?: boolean;
  model_is_positive?: boolean;
  clinical_suspicion?: boolean;
  guardrail_reasons?: string[];
  in_lung_energy_ratio?: number | null;
}

export interface PredictionResponse {
  inference_source?: "backend" | "unavailable";
  head_a_prediction: Record<string, number>;
  head_b_tb_screening: HeadBScreening;
  head_c_covidx: HeadCScreening;
  inference_time_ms: number;
  tta_enabled?: boolean;
  passes_executed?: number;
  calibration_temperature?: number;
  active_model?: string;
  model_display_name?: string;
  ensemble_agreement?: number;
  ensemble_models?: string[];
  individual_model_predictions?: Record<string, unknown>;
  safety?: SafetyDecision;
  report?: ClinicalReport;
  in_lung_energy_ratio?: number | null;
}

export interface LesionBBox {
  x: number;
  y: number;
  width: number;
  height: number;
  x2: number;
  y2: number;
}

export interface LesionMetadata {
  bbox: LesionBBox;
  centroid: { x: number; y: number };
  area_pixels: number;
  area_percent: number;
  confidence: number;
}

export interface ExplainResponse {
  inference_source?: "backend" | "unavailable";
  heatmap_base64: string;
  heatmap_rgba_base64?: string | null;
  heatmap_has_activation?: boolean | null;
  mask_source?: string;
  mask_warning?: string;
  overlay_base64: string;
  contour_base64?: string;
  contour_rgba_base64?: string;
  lesion_bounding_boxes?: LesionMetadata[];
  lesion_area_ratio?: number;
  cam_resolution?: string;
  target_head: string;
  target_class: number;
  target_disease_name?: string;
  target_probability?: number;
  target_threshold?: number;
  is_target_positive?: boolean;
  in_lung_energy_ratio?: number;
  audit_pass?: boolean | null;
  is_grounded?: boolean;
}

export interface AuditResponse {
  in_lung_energy_ratio: number;
  pass_80_percent: boolean;
  lung_mask_base64: string;
}


export interface RagKnowledgeCard {
  disease: string;
  icd10: string;
  hallmarks: string;
  differential: string;
  followup: string;
  coding_note: string;
  citations: string[];
}
export interface RagQueryRequest {
  question: string;
  active_findings: string[];
  anatomical_locations: string[];
  is_safe: boolean;
  in_lung_ratio?: number | null;
}
export interface RagEvidenceChunk {
  chunk_id: string;
  disease: string;
  facet: string;
  icd10: string;
  text: string;
  bm25_score: number;
  tfidf_cosine: number;
  rrf_score: number;
  relevance_score: number;
  citations: string[];
}
export interface RagQueryResponse {
  status: string;
  answer: string;
  citations: string[];
  retrieved_cards: RagKnowledgeCard[];
  retrieval_chunks?: RagEvidenceChunk[];
  graph_trace?: string[];
  graph_engine?: string;
  synthesis_mode?: string;
  faithfulness_verified?: boolean;
  hallucination_guard_triggered?: boolean;
  latency_ms?: number | null;
}
