"""Quantitative evaluation suite for LungRay LangGraph Corrective RAG (CRAG).

Executes the live 5-node CRAG workflow against ``configs/rag_eval_golden.json``
(40 clinical Q&A cases across 6 categories) and exports real, reproducible metrics
to ``results/rag_evaluation_report.json``.

Usage:
    python scripts/evaluate_rag.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.safety.rag_graph import LANGGRAPH_AVAILABLE, run_clinical_rag_graph

GOLDEN_PATH = PROJECT_ROOT / "configs" / "rag_eval_golden.json"
REPORT_PATH = PROJECT_ROOT / "results" / "rag_evaluation_report.json"


def evaluate_golden_benchmark(
    golden_path: Path = GOLDEN_PATH,
    report_path: Path | None = REPORT_PATH,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Run all Golden Clinical Q&A cases and compute verified IR + Safety metrics."""
    benchmark = json.loads(golden_path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = benchmark["cases"]

    retrieval_cases = 0
    recall_at_3_hits = 0
    mrr_scores: list[float] = []
    context_precisions: list[float] = []
    facet_total = 0
    facet_hits = 0
    citation_total = 0
    citation_hits = 0
    faithfulness_hits = 0
    status_hits = 0
    ood_total = 0
    ood_hits = 0
    guardrail_total = 0
    guardrail_hits = 0
    latencies_ms: list[float] = []
    per_case_results: list[dict[str, Any]] = []

    for case in cases:
        res = run_clinical_rag_graph(
            question=case["question"],
            active_findings=case.get("active_findings", []),
            anatomical_locations=case.get("anatomical_locations", []),
            is_safe=case.get("is_safe", True),
            in_lung_ratio=case.get("in_lung_ratio"),
            use_llm=use_llm,
        )
        latencies_ms.append(float(res.get("latency_ms", 0.0)))

        expected_status = case["expected_status"]
        status_ok = res["status"] == expected_status
        if status_ok:
            status_hits += 1

        if res.get("faithfulness_verified", False):
            faithfulness_hits += 1

        expected_diseases = case.get("expected_diseases", [])
        expected_facets = case.get("expected_facets", [])
        chunks = res.get("retrieval_chunks", [])
        cards = res.get("retrieved_cards", [])

        case_recall_at_3: float | None = None
        case_rr: float | None = None
        case_precision: float | None = None

        if expected_status == "GROUNDED_REFERENCE" and expected_diseases:
            retrieval_cases += 1
            top3_diseases = list(dict.fromkeys(ch["disease"] for ch in chunks[:3]))
            card_diseases = [c["disease"] for c in cards[:3]]
            combined_top3 = set(top3_diseases) | set(card_diseases)
            expected_set = set(expected_diseases)

            hit_all = expected_set.issubset(combined_top3)
            case_recall_at_3 = 1.0 if hit_all else len(expected_set & combined_top3) / len(expected_set)
            if hit_all:
                recall_at_3_hits += 1

            # Reciprocal Rank of first expected disease chunk
            rr = 0.0
            for rank, ch in enumerate(chunks, start=1):
                if ch["disease"] in expected_set:
                    rr = 1.0 / rank
                    break
            case_rr = rr
            mrr_scores.append(rr)

            # Context precision across graded chunks
            if chunks:
                prec = sum(1 for ch in chunks if ch["disease"] in expected_set) / len(chunks)
            else:
                prec = 0.0
            case_precision = prec
            context_precisions.append(prec)

            if expected_facets:
                facet_total += 1
                top_facets = {ch["facet"] for ch in chunks[: max(2, len(expected_diseases))]}
                if any(f in top_facets for f in expected_facets):
                    facet_hits += 1

            expected_cit = case.get("expected_citation_substring")
            if expected_cit:
                citation_total += 1
                if any(expected_cit in c for c in res.get("citations", [])):
                    citation_hits += 1

            expected_ans = case.get("expected_answer_substring")
            if expected_ans:
                guardrail_total += 1
                if expected_ans in res.get("answer", ""):
                    guardrail_hits += 1
        else:
            ood_total += 1
            if status_ok and not cards and not res.get("citations"):
                ood_hits += 1

        per_case_results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "expected_status": expected_status,
                "actual_status": res["status"],
                "status_ok": status_ok,
                "recall_at_3": case_recall_at_3,
                "reciprocal_rank": case_rr,
                "context_precision": case_precision,
                "faithfulness_verified": res.get("faithfulness_verified", False),
                "latency_ms": res.get("latency_ms", 0.0),
                "top_chunks": [ch["chunk_id"] for ch in chunks[:3]],
            }
        )

    summary = {
        "benchmark_name": benchmark["benchmark_name"],
        "version": benchmark["version"],
        "total_cases": len(cases),
        "retrieval_cases": retrieval_cases,
        "ood_and_abstention_cases": ood_total,
        "graph_engine": "langgraph_state_graph" if LANGGRAPH_AVAILABLE else "deterministic_state_machine",
        "synthesis_mode": "gemini_grounded" if use_llm else "offline_extractive",
        "metrics": {
            "status_accuracy": round(status_hits / max(len(cases), 1), 4),
            "recall_at_3": round(recall_at_3_hits / max(retrieval_cases, 1), 4),
            "mrr": round(float(np.mean(mrr_scores)) if mrr_scores else 0.0, 4),
            "context_precision": round(float(np.mean(context_precisions)) if context_precisions else 0.0, 4),
            "facet_routing_accuracy": round(facet_hits / max(facet_total, 1), 4),
            "citation_accuracy": round(citation_hits / max(citation_total, 1), 4),
            "faithfulness_rate": round(faithfulness_hits / max(len(cases), 1), 4),
            "ood_and_abstention_accuracy": round(ood_hits / max(ood_total, 1), 4),
            "guardrail_compliance": round(guardrail_hits / max(guardrail_total, 1), 4),
            "mean_latency_ms": round(float(np.mean(latencies_ms)) if latencies_ms else 0.0, 3),
            "p95_latency_ms": round(float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0, 3),
        },
        "cases": per_case_results,
    }

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


if __name__ == "__main__":
    report = evaluate_golden_benchmark()
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
