export interface HealthResponse {
  status: string;
  device: string;
  version: string;
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
}

export interface ExplainResponse {
  heatmap_base64: string;
  overlay_base64: string;
  target_head: string;
  target_class: number;
}

export interface AuditResponse {
  in_lung_energy_ratio: number;
  pass_80_percent: boolean;
  lung_mask_base64: string;
}
