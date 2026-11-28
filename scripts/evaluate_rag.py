"""Reproduce development-set retrieval metrics; these are not clinical validation.

The immutable original 40 cases and a separate adversarial regression set are
reported separately. Source-copy checks are independent of the engine's flag.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.safety.rag_graph import run_clinical_rag_graph
from src.safety.rag_retriever import get_clinical_retriever

GOLDEN_PATH = PROJECT_ROOT / "configs/rag_eval_golden.json"
ADVERSARIAL_PATH = PROJECT_ROOT / "configs/rag_eval_adversarial.json"
REPORT_PATH = PROJECT_ROOT / "results/rag_evaluation_report.json"


def _source_copy_check(case: dict, result: dict, corpus: dict) -> bool:
    """Check exact source spans and trusted framing, not semantic medical truth."""
    if result.get("status") != "GROUNDED_REFERENCE":
        return False
    chunks = result.get("retrieval_chunks", [])
    if not chunks or any(ch.get("chunk_id") not in corpus or ch.get("text") != corpus[ch["chunk_id"]].text for ch in chunks):
        return False
    text = result.get("answer", "")
    # An independently enumerated allowlist of deterministic context statements.
    frame = ["Structured clinical reference only; model predictions do not establish a confirmed diagnosis."]
    ratio = case.get("in_lung_ratio")
    if ratio is None:
        frame.append("In-lung Grad-CAM energy audit not yet executed.")
    else:
        frame.append(f"In-lung Grad-CAM energy: {ratio:.1%} (rounded).")
        if ratio < 0.8:
            frame.append("Below 80% (< 80%): inspect for text/border shortcut artifacts; reference caution only; this RAG endpoint does not change the model clinical flag.")
    frame.append("Grad-CAM and energy ratios are not calibrated diagnostic probabilities.")
    frame.append("Caller-supplied anatomical regions: " + (", ".join(case.get("anatomical_locations", [])) or "unverified localization") + ".")
    prefix = " ".join(frame)
    if not text.startswith(prefix):
        return False
    remaining = text[len(prefix):].strip()
    if not remaining:
        return any(word in case["question"].lower() for word in ("confidence", "tin cậy", "giải phẫu", "energy ratio", "shortcut"))
    valid = {ch["chunk_id"]: ch["text"] for ch in chunks}
    while remaining:
        match = re.match(r"(.+?)\s*\[([A-Za-z0-9_]+)\]", remaining, re.DOTALL)
        if not match or valid.get(match[2]) != match[1].strip():
            return False
        remaining = remaining[match.end():].strip()
    return True


def _score_case(case: dict, result: dict, corpus: dict) -> dict[str, Any]:
    expected = set(case.get("expected_diseases", []))
    facets = set(case.get("expected_facets", []))
    relevant_ids = set(case.get("expected_chunk_ids", [])) or {
        cid for cid, ch in corpus.items() if ch.disease in expected and (not facets or ch.facet in facets)
    }
    chunks = result.get("retrieval_chunks", [])
    # Only the ranked evidence is evaluated. Cards never rescue a retrieval miss.
    ids = list(dict.fromkeys(ch["chunk_id"] for ch in chunks))
    top3 = set(ids[:3])
    grounded_case = case["expected_status"] == "GROUNDED_REFERENCE" and bool(expected)
    recall = len(top3 & relevant_ids) / len(relevant_ids) if grounded_case and relevant_ids else None
    rr = next((1.0 / rank for rank, cid in enumerate(ids, 1) if cid in relevant_ids), 0.0) if grounded_case else None
    precision = sum(cid in relevant_ids for cid in ids) / len(ids) if grounded_case and ids else (0.0 if grounded_case else None)
    allowed_citations = {citation for ch in chunks if ch.get("chunk_id") in corpus for citation in corpus[ch["chunk_id"]].citations}
    citations = result.get("citations", [])
    expected_citation = case.get("expected_citation_substring")
    citation_ok = bool(citations) and all(c in allowed_citations for c in citations) and (not expected_citation or any(expected_citation in c for c in citations))
    status_ok = result.get("status") == case["expected_status"]
    return {
        "id": case["id"], "category": case["category"],
        "expected_status": case["expected_status"], "actual_status": result.get("status"), "status_ok": status_ok,
        "recall_at_3": recall, "reciprocal_rank": rr, "context_precision": precision,
        "facet_ok": facets.issubset({ch["facet"] for ch in chunks[:3]}) if grounded_case and facets else None,
        "citation_ok": citation_ok if grounded_case else None,
        "source_copy_compliant": _source_copy_check(case, result, corpus) if grounded_case else None,
        "abstention_ok": status_ok and not chunks and not result.get("retrieved_cards") and not citations if not grounded_case else None,
        "guardrail_ok": case["expected_answer_substring"] in result.get("answer", "") if case.get("expected_answer_substring") else None,
        "latency_ms": result.get("latency_ms"), "top_chunks": ids[:3],
        "actual_card_diseases": [card["disease"] for card in result.get("retrieved_cards", [])],
    }


def evaluate_golden_benchmark(
    golden_path: Path = GOLDEN_PATH,
    report_path: Path | None = REPORT_PATH,
    use_llm: bool = False,
    graph_backend: str = "auto",
) -> dict[str, Any]:
    """Measure strict chunk/facet Recall@3, MRR, precision and source-copy compliance."""
    benchmark = json.loads(golden_path.read_text(encoding="utf-8"))
    retriever = get_clinical_retriever()
    corpus = {ch.chunk_id: ch for ch in retriever.chunks}
    cold = run_clinical_rag_graph("Tuberculosis", [], [], use_llm=False, graph_backend=graph_backend)
    rows, engines, modes = [], set(), set()
    for case in benchmark["cases"]:
        result = run_clinical_rag_graph(
            question=case["question"], active_findings=case.get("active_findings", []),
            anatomical_locations=case.get("anatomical_locations", []), is_safe=case.get("is_safe", True),
            in_lung_ratio=case.get("in_lung_ratio"), use_llm=use_llm, graph_backend=graph_backend,
        )
        rows.append(_score_case(case, result, corpus))
        engines.add(result["graph_engine"])
        modes.add(result["synthesis_mode"])

    def mean(key):
        values = [row[key] for row in rows if row[key] is not None]
        return round(float(np.mean(values)), 4) if values else None

    latencies = [row["latency_ms"] for row in rows]
    summary = {
        "benchmark_name": benchmark["benchmark_name"], "version": benchmark["version"],
        "evaluation_protocol": "strict-chunk-facet-v2",
        "limitations": "Development/regression cases, not an independent clinical holdout. Queries share vocabulary and aliases with the curated corpus. Scores do not establish medical accuracy or generalization; adversarial cases are regressions used during this audit.",
        "known_annotation_issues": ["Original golden cases expect 'WHO consolidated guidelines on tuberculosis' for ISBN 9789240110991; the WHO source is actually the operational handbook. Five citation-presence checks therefore fail without editing the original labels.", "Some differential questions name multiple topics but original relevance labels list only one; judgments are not exhaustive."],
        "metric_definitions": {
            "recall_at_3": "Macro mean of relevant chunk IDs retrieved among the first three / all relevant chunk IDs; disease AND requested facet define relevance. Cards excluded.",
            "mrr": "First relevant chunk reciprocal rank using the same disease/facet judgments.",
            "context_precision": "Relevant chunk IDs / all returned graded evidence IDs, macro averaged.",
            "faithfulness_rate": "Legacy alias of source_copy_compliance. Exact source-text/citation/frame matching, independent of engine flags; NOT semantic or clinical faithfulness.",
            "citation_accuracy": "Allowed corpus citation membership and expected citation presence; NOT validation of source entailment.",
            "latency": "One separately timed setup call excluded from warmed aggregates; warmed per-case graph latency excludes facade import/index construction. Cold call reported separately. Hardware/runtime dependent.",
        },
        "corpus_sha256": hashlib.sha256(retriever.corpus_path.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(golden_path.read_bytes()).hexdigest(),
        "source_sha256": {name: hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest() for name in ("src/safety/rag_retriever.py", "src/safety/rag_graph.py", "src/safety/rag_knowledge.py", "scripts/evaluate_rag.py")},
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()},
        "total_cases": len(rows), "retrieval_cases": sum(row["recall_at_3"] is not None for row in rows),
        "ood_and_abstention_cases": sum(row["abstention_ok"] is not None for row in rows),
        "graph_engine": ",".join(sorted(engines)), "synthesis_modes": sorted(modes),
        "cold_call_latency_ms": cold["latency_ms"],
        "metrics": {
            "status_accuracy": mean("status_ok"), "recall_at_3": mean("recall_at_3"),
            "mrr": mean("reciprocal_rank"), "context_precision": mean("context_precision"),
            "facet_routing_accuracy": mean("facet_ok"), "citation_accuracy": mean("citation_ok"),
            "source_copy_compliance": mean("source_copy_compliant"), "faithfulness_rate": mean("source_copy_compliant"),
            "ood_and_abstention_accuracy": mean("abstention_ok"), "guardrail_compliance": mean("guardrail_ok"),
            "mean_latency_ms": round(float(np.mean(latencies)), 3), "p95_latency_ms": round(float(np.percentile(latencies, 95)), 3),
        },
        "cases": rows,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    report = evaluate_golden_benchmark(report_path=None)
    if ADVERSARIAL_PATH.exists():
        report["adversarial"] = evaluate_golden_benchmark(ADVERSARIAL_PATH, report_path=None)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"cases", "adversarial", "metric_definitions"}}, indent=2))
    if "adversarial" in report:
        print("Adversarial metrics:", json.dumps(report["adversarial"]["metrics"]))
