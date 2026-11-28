import type { PredictionResponse, RagQueryResponse } from "../types";

/** A changed case or audit ratio must start a fresh RAG request/session. */
export function clinicalRagContextKey(prediction: PredictionResponse, ratio: number | null): string {
  return JSON.stringify([prediction, ratio]);
}

/** Legacy/offline responses never gain an unearned verification badge. */
export function ragVerificationLabel(result: RagQueryResponse | null): string {
  if (result?.status === "BLOCKED_OOD") return "OOD blocked";
  if (result?.status === "UNAVAILABLE") return "Reference unavailable";
  if (result?.status === "NO_MATCH") return "No evidence matched";
  if (result?.status === "GROUNDED_REFERENCE" && result.faithfulness_verified === true && result.verification_scope === "extractive_source_match") return "Source text checked";
  return "Not verified";
}

export function ragSynthesisLabel(result: RagQueryResponse | null): string | null {
  if (result?.synthesis_mode === "gemini_grounded") return "Gemini source selection";
  if (result?.synthesis_mode === "offline_extractive_fallback") return "Offline fallback";
  if (result?.synthesis_mode === "offline_extractive") return "Offline extractive";
  return null;
}
