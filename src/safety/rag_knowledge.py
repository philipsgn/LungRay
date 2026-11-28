"""Clinical RAG facade backed by LungRay's LangGraph Corrective RAG (CRAG) engine.

ICD-10 references are candidate categories, never an automated coded diagnosis.
Follow-up text is editorial clinical context; Fleischner defines terminology,
not a treatment protocol. Runs 100% deterministically offline by default, with
optional Google Gemini Free Tier synthesis when GEMINI_API_KEY is configured.
"""
from __future__ import annotations

from typing import Any

from src.safety.rag_graph import run_clinical_rag_graph
from src.safety.rag_retriever import get_clinical_retriever, normalize_text

_RETRIEVER = get_clinical_retriever()

ICD = _RETRIEVER.guidelines["ICD"]
FLEISCHNER = _RETRIEVER.guidelines["FLEISCHNER"]
TB_WHO = _RETRIEVER.guidelines["TB_WHO"]
COVID_WHO = _RETRIEVER.guidelines["COVID_WHO"]
BTS_PLEURAL = _RETRIEVER.guidelines["BTS_PLEURAL"]

# Backward-compatible map of all 16 LungRay pathologies
CLINICAL_KNOWLEDGE_BASE: dict[str, dict[str, Any]] = _RETRIEVER.knowledge_base


def _normalize(text: str) -> str:
    return normalize_text(text)


def query_clinical_rag(
    question: str,
    active_findings: list[str],
    anatomical_locations: list[str],
    is_safe: bool = True,
    in_lung_ratio: float | None = None,
    use_llm: bool = True,
    include_timing: bool = False,
) -> dict[str, Any]:
    """Execute the 5-node LangGraph Corrective RAG workflow.

    When ``include_timing`` is False (default), ``latency_ms`` is omitted from
    the returned dictionary so repeated offline calls remain strictly deterministic.
    """
    result = run_clinical_rag_graph(
        question=question,
        active_findings=active_findings,
        anatomical_locations=anatomical_locations,
        is_safe=is_safe,
        in_lung_ratio=in_lung_ratio,
        use_llm=use_llm,
    )
    if not include_timing:
        result.pop("latency_ms", None)
    return result
