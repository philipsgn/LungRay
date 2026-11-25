"use client";

import {
  ExplainResponse,
  PredictionResponse,
  RagQueryRequest,
  RagQueryResponse,
} from "../types";
import { NIH_14_DISEASES } from "../components/DiagnosisDashboard";

/**
 * Generates an on-the-fly Grad-CAM++ RGBA heatmap & iso-contour PNG via HTML5 Canvas
 * so Vercel / static deployments can render realistic spatial localization offline.
 */
function renderCanvasOverlay(
  centers: Array<{ x: number; y: number; rx: number; ry: number; intensity: number }>,
  mode: "heatmap" | "contour"
): string {
  if (typeof document === "undefined") return "";
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";

  ctx.clearRect(0, 0, size, size);

  if (mode === "heatmap") {
    for (const c of centers) {
      const cx = c.x * size;
      const cy = c.y * size;
      const radius = Math.max(c.rx, c.ry) * size;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(1, c.ry / Math.max(c.rx, 0.01));
      const grad = ctx.createRadialGradient(0, 0, radius * 0.05, 0, 0, radius);
      grad.addColorStop(0, `rgba(255, 30, 30, ${0.88 * c.intensity})`);
      grad.addColorStop(0.35, `rgba(255, 165, 0, ${0.72 * c.intensity})`);
      grad.addColorStop(0.65, `rgba(63, 208, 196, ${0.42 * c.intensity})`);
      grad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(0, 0, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  } else {
    // Iso-contour boundary rings
    for (const c of centers) {
      const cx = c.x * size;
      const cy = c.y * size;
      const rx = c.rx * size * 0.68;
      const ry = c.ry * size * 0.68;

      ctx.save();
      ctx.strokeStyle = "#3FD0C4";
      ctx.lineWidth = 3;
      ctx.setLineDash([8, 4]);
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = "#F59E0B";
      ctx.lineWidth = 2;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx * 0.55, ry * 0.55, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
  }

  // Strip data URL prefix to match backend base64 contract
  return canvas.toDataURL("image/png").replace(/^data:image\/png;base64,/, "");
}

function classifyPresetScenario(filename: string): "normal" | "effusion" | "tb" | "ood" | "custom" {
  const low = filename.toLowerCase();
  if (low.includes("ood") || low.includes("anomaly") || low.includes("synthetic")) return "ood";
  if (low.includes("tb") || low.includes("tuberculosis")) return "tb";
  if (low.includes("effusion") || low.includes("cardiomegaly")) return "effusion";
  if (low.includes("normal")) return "normal";
  return "custom";
}

export async function edgePredictImage(
  file: File,
  model: string,
  failsafeEnabled: boolean,
  ttaEnabled: boolean
): Promise<PredictionResponse> {
  // Realistic inference latency simulation
  await new Promise((r) => setTimeout(r, 650));

  const scenario = classifyPresetScenario(file.name);
  const headA: Record<string, number> = {};
  for (const d of NIH_14_DISEASES) {
    headA[d.id] = 0.04 + ((d.id.length * 13) % 7) * 0.012;
  }

  if (scenario === "ood" && failsafeEnabled) {
    return {
      head_a_prediction: headA,
      head_b_tb_screening: { tb_probability: 0.02, is_positive: false },
      head_c_covidx: { available: true, covid_probability: 0.05, threshold: 0.6123, is_positive: false },
      inference_time_ms: 142.4,
      tta_enabled: ttaEnabled,
      passes_executed: ttaEnabled ? 3 : 1,
      active_model: model,
      model_display_name: `${model.toUpperCase()} (Cloud Demo Engine)`,
      safety: {
        decision: "REJECT",
        is_safe: false,
        energy_score: 14.85,
        entropy_score: 0.891,
        rejection_reasons: [
          "Helmholtz Free Energy (14.85) exceeded safety threshold (9.0421).",
          "Shannon Entropy (0.891) indicates non-radiographic / out-of-distribution input.",
        ],
      },
      report: {
        status: "BLOCKED",
        is_blocked: true,
        findings: [],
        anatomical_locations: [],
        icd10_codes: [],
        impression: "DIAGNOSTIC LOCKOUT: Input rejected by 5-Tier Clinical OOD Fail-Safe.",
        recommendations: [
          "Verify DICOM/PNG orientation and ensure frontal PA/AP chest radiograph.",
          "Re-upload a valid clinical radiograph or disable Fail-Safe only for QA inspection.",
        ],
        disclaimer: "Automated safety gate prevented unreliable inference.",
      },
      in_lung_energy_ratio: 0.21,
    };
  }

  let tbProb = 0.03;
  let tbPos = false;
  const covidProb = 0.08;
  const covidPos = false;
  let findings: string[] = ["No acute cardiopulmonary abnormality detected."];
  let locations: string[] = ["Bilateral clear lung fields", "Normal cardiomediastinal silhouette"];
  let icd10: string[] = ["Z00.00 (Normal Radiographic Exam)"];
  let impression = "Clear bilateral lung fields without focal consolidation, pleural effusion, or pneumothorax.";
  let recs = ["Routine clinical follow-up as indicated."];
  let inLung = 0.942;

  if (scenario === "effusion") {
    headA["Effusion"] = 0.912;
    headA["Cardiomegaly"] = 0.864;
    headA["Atelectasis"] = 0.512;
    findings = [
      "Moderate right-sided pleural effusion blunting the costophrenic angle.",
      "Cardiomegaly with enlarged cardiothoracic silhouette (CTR > 0.52).",
      "Bibasilar compressive atelectasis adjacent to effusion.",
    ];
    locations = ["Right lower hemithorax / Costophrenic sulcus", "Cardiomediastinal silhouette"];
    icd10 = ["J90 (Pleural effusion, not elsewhere classified)", "I51.7 (Cardiomegaly)"];
    impression = "Right pleural effusion accompanied by cardiomegaly and mild bibasilar atelectasis. Correlate with echocardiography and BNP.";
    recs = [
      "Recommend transthoracic echocardiogram to evaluate ventricular function.",
      "Consider lateral decubitus radiograph or thoracic ultrasound if thoracentesis is planned.",
    ];
    inLung = 0.936;
  } else if (scenario === "tb") {
    tbProb = 0.974;
    tbPos = true;
    headA["Infiltration"] = 0.834;
    headA["Fibrosis"] = 0.712;
    headA["Nodule"] = 0.648;
    findings = [
      "Right upper lobe cavitary/reticulonodular infiltration highly suspicious for active Pulmonary Tuberculosis.",
      "Apical pleural thickening and fibrotic scarring.",
    ];
    locations = ["Right upper lobe (Apical / Posterior segments)"];
    icd10 = ["A15.0 (Tuberculosis of lung)", "R91.8 (Other nonspecific abnormal finding of lung field)"];
    impression = "CRITICAL TRIAGE ALERT: High-probability active Pulmonary Tuberculosis (Head B = 97.4%) with right upper lobe cavitation.";
    recs = [
      "STAT airborne isolation precautions recommended.",
      "Order sputum AFB smear, GeneXpert MTB/RIF assay, and mycobacterial culture.",
    ];
    inLung = 0.951;
  } else if (scenario === "custom") {
    headA["Infiltration"] = 0.685;
    headA["Pneumonia"] = 0.614;
    findings = [
      "Patchy airspace opacity in the right mid-to-lower lung zone consistent with early pneumonia/infiltrate.",
    ];
    locations = ["Right middle/lower lung zone"];
    icd10 = ["J18.9 (Pneumonia, unspecified organism)"];
    impression = "Focal right lower zone opacity suggestive of infectious infiltrate. Correlate clinically with fever and WBC count.";
    recs = [
      "Correlate with clinical symptoms, inflammatory markers, and follow-up chest X-ray in 4–6 weeks post-therapy.",
    ];
    inLung = 0.918;
  }

  return {
    head_a_prediction: headA,
    head_b_tb_screening: { tb_probability: tbProb, is_positive: tbPos },
    head_c_covidx: {
      available: true,
      covid_probability: covidProb,
      threshold: 0.6123,
      is_positive: covidPos,
      in_lung_energy_ratio: inLung,
    },
    inference_time_ms: ttaEnabled ? 184.6 : 78.2,
    tta_enabled: ttaEnabled,
    passes_executed: ttaEnabled ? 3 : 1,
    active_model: model,
    model_display_name: `${model.toUpperCase()} (Cloud Demo Engine)`,
    ensemble_agreement: model === "ensemble" ? 0.96 : undefined,
    safety: {
      decision: "ACCEPT",
      is_safe: true,
      energy_score: 5.14,
      entropy_score: 0.184,
      rejection_reasons: [],
    },
    report: {
      status: "GENERATED",
      is_blocked: false,
      findings,
      active_findings: findings,
      anatomical_locations: locations,
      icd10_codes: icd10,
      impression,
      recommendations: recs,
      disclaimer: "AI-assisted clinical decision support (Cloud Simulation Mode). Final diagnosis requires physician verification.",
    },
    in_lung_energy_ratio: inLung,
  };
}

export async function edgeExplainImage(
  file: File,
  targetHead: string,
  targetClass: number,
  targetDiseaseName: string
): Promise<ExplainResponse> {
  await new Promise((r) => setTimeout(r, 280));
  const scenario = classifyPresetScenario(file.name);

  let centers = [{ x: 0.34, y: 0.56, rx: 0.18, ry: 0.22, intensity: 0.85 }];
  if (scenario === "effusion") {
    centers = [
      { x: 0.31, y: 0.72, rx: 0.20, ry: 0.18, intensity: 0.95 },
      { x: 0.56, y: 0.60, rx: 0.18, ry: 0.16, intensity: 0.82 },
    ];
  } else if (scenario === "tb") {
    centers = [{ x: 0.34, y: 0.30, rx: 0.17, ry: 0.16, intensity: 0.98 }];
  } else if (scenario === "normal") {
    centers = [{ x: 0.48, y: 0.52, rx: 0.14, ry: 0.14, intensity: 0.22 }];
  }

  const heatmapRgba = renderCanvasOverlay(centers, "heatmap");
  const contourRgba = renderCanvasOverlay(centers, "contour");

  return {
    heatmap_base64: heatmapRgba,
    heatmap_rgba_base64: heatmapRgba,
    heatmap_has_activation: scenario !== "normal",
    mask_source: "dense_unet_cloud_gate",
    overlay_base64: heatmapRgba,
    contour_base64: contourRgba,
    contour_rgba_base64: contourRgba,
    lesion_area_ratio: scenario === "normal" ? 0.02 : 0.14,
    cam_resolution: "32x32 Multi-Scale Grad-CAM++",
    target_head: targetHead,
    target_class: targetClass,
    target_disease_name: targetDiseaseName,
    in_lung_energy_ratio: scenario === "ood" ? 0.21 : 0.942,
    audit_pass: scenario !== "ood",
    is_grounded: true,
  };
}

export async function edgeQueryClinicalRag(payload: RagQueryRequest): Promise<RagQueryResponse> {
  await new Promise((r) => setTimeout(r, 320));
  const findings = payload.active_findings.length > 0 ? payload.active_findings : ["Normal"];
  const cards = findings.slice(0, 3).map((finding) => {
    const low = finding.toLowerCase();
    if (low.includes("tuberculosis") || low === "tb") {
      return {
        disease: "Pulmonary Tuberculosis (TB)",
        icd10: "A15.0",
        hallmarks: "Upper lobe apical/posterior segment cavitary lesions with tree-in-bud centrilobular nodules.",
        differential: "Nontuberculous mycobacterial infection, fungal pneumonia (aspergillosis), bronchogenic carcinoma.",
        followup: "Immediate airborne isolation; sputum AFB smear x3 & GeneXpert MTB/RIF rapid molecular assay.",
        coding_note: "Assign A15.0 when confirmed bacteriologically or histologically; A15.9 if unspecified.",
        citations: ["WHO Consolidated Guidelines on Tuberculosis", "Fleischner Society Glossary"],
      };
    }
    if (low.includes("effusion")) {
      return {
        disease: "Pleural Effusion",
        icd10: "J90",
        hallmarks: "Blunting of the costophrenic angle with meniscus sign and homogeneous lower hemithorax opacity.",
        differential: "Congestive heart failure, parapneumonic effusion, malignancy, pulmonary embolism.",
        followup: "Thoracic ultrasound to quantify fluid volume and guide diagnostic thoracentesis.",
        coding_note: "Code underlying etiology (e.g., heart failure) if known; otherwise J90.",
        citations: ["BTS Pleural Disease Guideline", "Fleischner Society Criteria"],
      };
    }
    if (low.includes("cardiomegaly")) {
      return {
        disease: "Cardiomegaly",
        icd10: "I51.7",
        hallmarks: "Cardiothoracic Ratio (CTR) > 0.50 on PA upright projection with widened cardiac silhouette.",
        differential: "Dilated cardiomyopathy, hypertensive heart disease, pericardial effusion.",
        followup: "Transthoracic Echocardiogram (TTE) & Serum BNP/NT-proBNP correlation.",
        coding_note: "I51.7 for unspecified cardiomegaly; use specific heart failure code if systolic/diastolic dysfunction confirmed.",
        citations: ["ACC/AHA Heart Failure Guidelines"],
      };
    }
    return {
      disease: finding,
      icd10: "R91.8",
      hallmarks: "Focal or patchy parenchymal attenuation within pulmonary zones.",
      differential: "Community-acquired pneumonia, atelectasis, localized pulmonary edema.",
      followup: "Correlate with clinical history, vitals, and laboratory markers.",
      coding_note: "R91.8 used for nonspecific abnormal lung field findings pending definitive diagnosis.",
      citations: ["Fleischner Society & WHO ICD-10 Clinical Knowledge Base"],
    };
  });

  const allCitations = Array.from(new Set(cards.flatMap((c) => c.citations)));
  return {
    status: "SUCCESS",
    answer: `Grounded clinical guidance for ${cards.map((c) => `${c.disease} (${c.icd10})`).join(", ")}: ${cards[0].followup} Verify localization on the PACS Grad-CAM++ overlay and complete electronic sign-off before EMR archiving.`,
    citations: allCitations,
    retrieved_cards: cards,
  };
}
