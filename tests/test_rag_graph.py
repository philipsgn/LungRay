"""Unit tests for LungRay Hybrid Clinical Retriever, LangGraph CRAG, and Golden Benchmark."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.safety import rag_graph
from src.safety.rag_graph import run_clinical_rag_graph
from src.safety.rag_retriever import HybridClinicalRetriever, get_clinical_retriever


def test_corpus_has_16_pathologies_and_48_atomic_chunks() -> None:
    retriever = get_clinical_retriever()
    assert len(retriever.knowledge_base) == 16
    assert len(retriever.chunks) == 48
    facets = {ch.facet for ch in retriever.chunks}
    assert facets == {"imaging_hallmarks", "differential_diagnosis", "clinical_workup_and_coding"}


def test_hybrid_retriever_matches_freeform_radiographic_signs() -> None:
    retriever = HybridClinicalRetriever()
    scored, diseases, _ = retriever.retrieve(
        "thin sharp white visceral pleural line with absent peripheral lung markings",
        active_findings=[],
    )
    assert scored
    assert scored[0].chunk.disease == "Pneumothorax"
    assert "Pneumothorax" in diseases

    scored_edema, _, _ = retriever.retrieve(
        "bilateral perihilar bat-wing airspace opacities with Kerley B septal lines",
        active_findings=[],
    )
    assert scored_edema[0].chunk.disease == "Edema"


def test_crag_graph_trace_and_multi_pathology_coverage() -> None:
    res = run_clinical_rag_graph(
        question="What are the key imaging hallmarks?",
        active_findings=["Cardiomegaly", "Effusion", "Edema"],
        anatomical_locations=["Cardiac Silhouette", "Bilateral Bases"],
        is_safe=True,
        in_lung_ratio=0.89,
        use_llm=False,
    )
    assert res["status"] == "GROUNDED_REFERENCE"
    assert res["faithfulness_verified"] is True
    assert res["hallucination_guard_triggered"] is False
    assert any(step.startswith("safety_gate:PASS") for step in res["graph_trace"])
    assert any(step.startswith("hybrid_retrieve:") for step in res["graph_trace"])
    assert any(step.startswith("grade_evidence:PASS") for step in res["graph_trace"])
    assert any(step.startswith("verify_citations:PASS") for step in res["graph_trace"])
    card_diseases = {card["disease"] for card in res["retrieved_cards"]}
    assert {"Cardiomegaly", "Effusion", "Edema"}.issubset(card_diseases)


def test_crag_verifier_downgrades_hallucinated_llm_citation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    monkeypatch.setenv("GEMINI_RAG_MODEL", "test-model")
    monkeypatch.setattr(
        rag_graph,
        "_call_gemini_free_api",
        lambda **kwargs: "Invented diagnosis requiring surgery [nonexistent_chunk_999].",
    )
    res = run_clinical_rag_graph(
        question="Recommended follow-up and clinical workup?",
        active_findings=["Tuberculosis"],
        anatomical_locations=["Right Upper Lobe"],
        is_safe=True,
        in_lung_ratio=0.92,
        use_llm=True,
    )
    assert res["status"] == "GROUNDED_REFERENCE"
    assert res["hallucination_guard_triggered"] is True
    assert res["synthesis_mode"] == "offline_extractive_fallback"
    assert res["faithfulness_verified"] is True
    assert "nonexistent_chunk_999" not in res["answer"]
    assert "Xpert" in res["answer"]
    assert any("DOWNGRADED_TO_OFFLINE" in step for step in res["graph_trace"])


def test_crag_verifier_accepts_grounded_llm_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    monkeypatch.setenv("GEMINI_RAG_MODEL", "test-model")
    monkeypatch.setattr(
        rag_graph,
        "_call_gemini_free_api",
        lambda **kwargs: next(ch["text"] + " [" + ch["chunk_id"] + "]" for ch in kwargs["graded_chunks"] if ch["chunk_id"] == "tuberculosis_workup"),
    )
    res = run_clinical_rag_graph(
        question="Recommended follow-up and clinical workup?",
        active_findings=["Tuberculosis"],
        anatomical_locations=["Right Apex"],
        is_safe=True,
        in_lung_ratio=0.91,
        use_llm=True,
    )
    assert res["status"] == "GROUNDED_REFERENCE"
    assert res["hallucination_guard_triggered"] is False
    assert res["synthesis_mode"] == "gemini_grounded"
    assert res["faithfulness_verified"] is True
    assert "[tuberculosis_workup]" in res["answer"]


def test_golden_benchmark_script_runs_and_meets_quality_bars(tmp_path: Path) -> None:
    from scripts.evaluate_rag import evaluate_golden_benchmark

    out_file = tmp_path / "rag_eval.json"
    summary = evaluate_golden_benchmark(report_path=out_file, use_llm=False)
    assert out_file.is_file()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded["total_cases"] == 40
    metrics = loaded["metrics"]
    assert metrics["status_accuracy"] >= 0.95
    assert metrics["recall_at_3"] >= 0.95
    assert metrics["mrr"] >= 0.95
    assert metrics["faithfulness_rate"] == 1.0
    assert metrics["ood_and_abstention_accuracy"] == 1.0
    assert metrics["mean_latency_ms"] >= 0.0
    assert loaded["evaluation_protocol"] == "strict-chunk-facet-v2"
