export interface HealthResponse {
  status: string;
  device: string;
  version: string;
  ood_failsafe_enabled?: boolean;
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
  covid_probability: number;
  is_positive: boolean;
}

export interface PredictionResponse {
  head_a_prediction: Record<string, number>;
  head_b_tb_screening: HeadBScreening;
  head_c_covidx: HeadCScreening;
  inference_time_ms: number;
  safety?: SafetyDecision;
  report?: ClinicalReport;
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
  heatmap_base64: string;
  overlay_base64: string;
  contour_base64?: string;
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
  audit_pass?: boolean;
  is_grounded?: boolean;
}

export interface AuditResponse {
  in_lung_energy_ratio: number;
  pass_80_percent: boolean;
  lung_mask_base64: string;
}
