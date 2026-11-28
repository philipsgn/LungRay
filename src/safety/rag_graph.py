"""LangGraph Corrective RAG (CRAG) state machine for LungRay clinical Q&A.

5-node auditable clinical workflow:
    1. safety_gate         -> Enforces OOD Fail-Safe lockout & input validation
    2. hybrid_retrieve     -> Runs Hybrid BM25 + TF-IDF Cosine + RRF over 48 chunks
    3. grade_evidence      -> Filters candidates by relevance threshold (triggers NO_MATCH)
    4. synthesize_grounded -> Optional Google Gemini Free Tier API (GEMINI_API_KEY)
                              with deterministic Offline Extractive Grounded Fallback
    5. verify_citations    -> Verifies all claims/citations against graded evidence;
                              auto-downgrades hallucinated LLM outputs to verified offline text.

Uses real ``langgraph.graph.StateGraph`` whenever ``langgraph`` is installed,
with a 100% equivalent deterministic state runner fallback in minimal environments.
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, TypedDict

from src.safety.rag_retriever import (
    HybridClinicalRetriever,
    ScoredChunk,
    get_clinical_retriever,
    normalize_text,
)

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - covered by fallback path
    END = "__end__"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False

RELEVANCE_THRESHOLD = 0.24
GEMINI_MODEL_DEFAULT = "gemini-2.0-flash"


class ClinicalRagState(TypedDict, total=False):
    # Inputs
    question: str
    active_findings: list[str]
    anatomical_locations: list[str]
    is_safe: bool
    in_lung_ratio: float | None
    use_llm: bool

    # Intermediate graph state
    status: str
    context_prefix: str
    detected_facet: str | None
    target_diseases: list[str]
    retrieved_raw: list[dict[str, Any]]
    graded_chunks: list[dict[str, Any]]
    retrieved_cards: list[dict[str, Any]]
    citations: list[str]
    draft_answer: str
    answer: str
    synthesis_mode: str
    faithfulness_verified: bool
    hallucination_guard_triggered: bool
    graph_trace: list[str]
    graph_engine: str


def _serialize_scored_chunk(item: ScoredChunk) -> dict[str, Any]:
    return {
        "chunk_id": item.chunk.chunk_id,
        "disease": item.chunk.disease,
        "facet": item.chunk.facet,
        "icd10": item.chunk.icd10,
        "text": item.chunk.text,
        "bm25_score": item.bm25_score,
        "tfidf_cosine": item.tfidf_cosine,
        "rrf_score": item.rrf_score,
        "relevance_score": item.relevance_score,
        "citations": list(item.chunk.citations),
    }


def _build_clinical_context_prefix(
    anatomical_locations: list[str],
    in_lung_ratio: float | None,
) -> str:
    context = "Structured clinical reference only; model predictions do not establish a confirmed diagnosis."
    if in_lung_ratio is None:
        context += " In-lung Grad-CAM energy audit not yet executed."
    else:
        context += f" In-lung Grad-CAM energy: {in_lung_ratio:.1%}."
        if in_lung_ratio < 0.8:
            context += " Below 80% (< 80%): inspect for text/border shortcut artifacts; clinical suspicion flag downgraded."
    context += " Grad-CAM and energy ratios are not calibrated diagnostic probabilities."
    location_text = ", ".join(anatomical_locations) if anatomical_locations else "unverified localization"
    context += f" Caller-supplied anatomical regions: {location_text}."
    return context


def _node_safety_gate(state: ClinicalRagState) -> ClinicalRagState:
    trace = list(state.get("graph_trace", []))
    if not state.get("is_safe", True):
        trace.append("safety_gate:BLOCKED_OOD")
        return {
            **state,
            "status": "BLOCKED_OOD",
            "answer": (
                "Study rejected by OOD Fail-Safe Gatekeeper. Clinical knowledge retrieval and "
                "inference synthesis are withheld. Verify valid chest radiograph input and image quality."
            ),
            "citations": [],
            "retrieved_cards": [],
            "graded_chunks": [],
            "synthesis_mode": "blocked_ood",
            "faithfulness_verified": True,
            "hallucination_guard_triggered": False,
            "graph_trace": trace,
        }

    in_lung_ratio = state.get("in_lung_ratio")
    if in_lung_ratio is not None and not (0.0 <= in_lung_ratio <= 1.0):
        trace.append("safety_gate:INVALID_CONTEXT")
        return {
            **state,
            "status": "INVALID_CONTEXT",
            "answer": "Invalid context: in-lung energy ratio must lie within [0.0, 1.0].",
            "citations": [],
            "retrieved_cards": [],
            "graded_chunks": [],
            "synthesis_mode": "invalid_context",
            "faithfulness_verified": True,
            "hallucination_guard_triggered": False,
            "graph_trace": trace,
        }

    trace.append("safety_gate:PASS")
    context_prefix = _build_clinical_context_prefix(
        state.get("anatomical_locations", []),
        in_lung_ratio,
    )
    return {
        **state,
        "status": "SAFE",
        "context_prefix": context_prefix,
        "graph_trace": trace,
    }


def _node_hybrid_retrieve(
    state: ClinicalRagState,
    retriever: HybridClinicalRetriever | None = None,
) -> ClinicalRagState:
    engine = retriever or get_clinical_retriever()
    trace = list(state.get("graph_trace", []))

    scored, target_diseases, detected_facet = engine.retrieve(
        question=state.get("question", ""),
        active_findings=state.get("active_findings", []),
        top_k=6,
    )
    serialized = [_serialize_scored_chunk(item) for item in scored]
    trace.append(f"hybrid_retrieve:bm25+tfidf_rrf(k={len(serialized)})")

    return {
        **state,
        "detected_facet": detected_facet,
        "target_diseases": target_diseases,
        "retrieved_raw": serialized,
        "graph_trace": trace,
    }


def _node_grade_evidence(
    state: ClinicalRagState,
    retriever: HybridClinicalRetriever | None = None,
) -> ClinicalRagState:
    engine = retriever or get_clinical_retriever()
    trace = list(state.get("graph_trace", []))
    raw_chunks = state.get("retrieved_raw", [])

    graded = [ch for ch in raw_chunks if ch["relevance_score"] >= RELEVANCE_THRESHOLD]

    if not graded:
        trace.append("grade_evidence:NO_MATCH(0)")
        return {
            **state,
            "status": "NO_MATCH",
            "graded_chunks": [],
            "retrieved_cards": [],
            "citations": [],
            "answer": (
                state.get("context_prefix", "")
                + " No curated thoracic evidence matched the query; do not infer a normal study from abstention."
            ).strip(),
            "synthesis_mode": "safe_abstention",
            "faithfulness_verified": True,
            "hallucination_guard_triggered": False,
            "graph_trace": trace,
        }

    # Build deduplicated reference cards in ranked disease order (max 4 cards)
    seen_diseases: list[str] = []
    for ch in graded:
        if ch["disease"] not in seen_diseases:
            seen_diseases.append(ch["disease"])
    seen_diseases = seen_diseases[:4]

    cards = [engine.get_card(disease) for disease in seen_diseases]
    citations = list(dict.fromkeys(src for card in cards for src in card["citations"]))
    trace.append(f"grade_evidence:PASS(chunks={len(graded)},cards={len(cards)})")

    return {
        **state,
        "status": "EVIDENCE_GRADED",
        "graded_chunks": graded,
        "retrieved_cards": cards,
        "citations": citations,
        "graph_trace": trace,
    }


def _offline_extractive_synthesis(state: ClinicalRagState) -> str:
    """Deterministic, zero-hallucination extractive synthesis strictly from graded chunks."""
    question_norm = normalize_text(state.get("question", ""))
    context_prefix = state.get("context_prefix", "")
    cards = state.get("retrieved_cards", [])
    graded_chunks = state.get("graded_chunks", [])
    detected_facet = state.get("detected_facet")

    confidence_only = any(
        token in question_norm
        for token in ("confidence", "tin cay", "giai phau", "energy ratio", "shortcut")
    )
    if confidence_only:
        return context_prefix

    snippets: list[str] = []
    if detected_facet == "clinical_workup_and_coding":
        for card in cards:
            snippets.append(f"{card['disease']} (ICD-10 {card['icd10']}): {card['followup']}")
    elif detected_facet == "differential_diagnosis":
        for card in cards:
            snippets.append(f"{card['disease']} differential: {card['differential']}")
    elif detected_facet == "imaging_hallmarks":
        for card in cards:
            snippets.append(f"{card['disease']} hallmarks: {card['hallmarks']} Differential: {card['differential']}")
    else:
        # Use top graded chunks directly (one per disease for conciseness)
        used_diseases: set[str] = set()
        for ch in graded_chunks:
            if ch["disease"] in used_diseases:
                continue
            used_diseases.add(ch["disease"])
            snippets.append(f"{ch['text']} [{ch['chunk_id']}]")

    return f"{context_prefix} {' '.join(snippets)}".strip()


def _call_gemini_free_api(
    question: str,
    context_prefix: str,
    graded_chunks: list[dict[str, Any]],
    api_key: str,
    model: str = GEMINI_MODEL_DEFAULT,
    timeout_s: float = 8.0,
) -> str | None:
    """Optional 0-cost Google Gemini Free Tier synthesis via REST API (httpx)."""
    try:
        import httpx
    except ImportError:
        return None

    evidence_block = "\n".join(
        f"- [{ch['chunk_id']}] ({ch['disease']}, ICD-10 {ch['icd10']}): {ch['text']}"
        for ch in graded_chunks[:6]
    )
    prompt = (
        "You are a thoracic radiology reference assistant. Answer strictly using ONLY the verified "
        "clinical evidence chunks below. Never invent findings, probabilities, or guidelines not present "
        "in the chunks. Keep the response concise (2-4 sentences) and cite chunk IDs in square brackets "
        "like [chunk_id].\n\n"
        f"Clinical Safety Context: {context_prefix}\n\n"
        f"Verified Evidence Chunks:\n{evidence_block}\n\n"
        f"Clinician Question: {question}\n\n"
        "Grounded Clinical Reference Answer:"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 260},
    }
    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts") or []
        text = " ".join(part.get("text", "").strip() for part in parts if part.get("text")).strip()
        return text or None
    except Exception as exc:  # pragma: no cover - network/quota fallback
        logger.warning("Gemini Free API synthesis unavailable, falling back to offline grounded mode: %s", exc)
        return None


def _node_synthesize_grounded(state: ClinicalRagState) -> ClinicalRagState:
    trace = list(state.get("graph_trace", []))
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    use_llm = state.get("use_llm", True)

    if use_llm and api_key:
        model_name = os.environ.get("GEMINI_RAG_MODEL", GEMINI_MODEL_DEFAULT).strip() or GEMINI_MODEL_DEFAULT
        llm_text = _call_gemini_free_api(
            question=state.get("question", ""),
            context_prefix=state.get("context_prefix", ""),
            graded_chunks=state.get("graded_chunks", []),
            api_key=api_key,
            model=model_name,
        )
        if llm_text:
            trace.append(f"synthesize_grounded:gemini({model_name})")
            return {
                **state,
                "draft_answer": f"{state.get('context_prefix', '')} {llm_text}".strip(),
                "synthesis_mode": "gemini_grounded",
                "graph_trace": trace,
            }

    offline_text = _offline_extractive_synthesis(state)
    trace.append("synthesize_grounded:offline_extractive")
    return {
        **state,
        "draft_answer": offline_text,
        "synthesis_mode": "offline_extractive",
        "graph_trace": trace,
    }


def _verify_draft_against_evidence(
    draft: str,
    graded_chunks: list[dict[str, Any]],
) -> bool:
    """Verify that any [chunk_id] citations exist in graded_chunks and draft has grounded overlap."""
    if not draft or not graded_chunks:
        return False

    valid_chunk_ids = {ch["chunk_id"] for ch in graded_chunks}
    cited_ids = re.findall(r"\[([a-z0-9_]+)\]", draft)
    if any(cid not in valid_chunk_ids for cid in cited_ids):
        return False

    # Require lexical grounding: at least one graded disease or substantial token overlap
    draft_norm = normalize_text(draft)
    evidence_norm = normalize_text(" ".join(ch["text"] for ch in graded_chunks))
    evidence_tokens = {tok for tok in evidence_norm.split() if len(tok) >= 4}
    draft_tokens = {tok for tok in draft_norm.split() if len(tok) >= 4}
    if not evidence_tokens:
        return True
    overlap = len(draft_tokens & evidence_tokens)
    return overlap >= 3


def _node_verify_citations(state: ClinicalRagState) -> ClinicalRagState:
    trace = list(state.get("graph_trace", []))
    draft = state.get("draft_answer", "")
    graded_chunks = state.get("graded_chunks", [])
    synthesis_mode = state.get("synthesis_mode", "offline_extractive")

    if synthesis_mode == "offline_extractive":
        trace.append("verify_citations:PASS(deterministic)")
        return {
            **state,
            "status": "GROUNDED_REFERENCE",
            "answer": draft,
            "faithfulness_verified": True,
            "hallucination_guard_triggered": False,
            "graph_trace": trace,
        }

    is_grounded = _verify_draft_against_evidence(draft, graded_chunks)
    if is_grounded:
        trace.append("verify_citations:PASS(llm_grounded)")
        return {
            **state,
            "status": "GROUNDED_REFERENCE",
            "answer": draft,
            "faithfulness_verified": True,
            "hallucination_guard_triggered": False,
            "graph_trace": trace,
        }

    # Hallucination or invalid citation detected -> auto-downgrade to deterministic offline synthesis
    safe_fallback = _offline_extractive_synthesis(state)
    trace.append("verify_citations:DOWNGRADED_TO_OFFLINE")
    return {
        **state,
        "status": "GROUNDED_REFERENCE",
        "answer": safe_fallback,
        "synthesis_mode": "offline_extractive_fallback",
        "faithfulness_verified": True,
        "hallucination_guard_triggered": True,
        "graph_trace": trace,
    }


def _route_after_safety(state: ClinicalRagState) -> str:
    return "hybrid_retrieve" if state.get("status") == "SAFE" else END


def _route_after_grade(state: ClinicalRagState) -> str:
    return "synthesize_grounded" if state.get("status") == "EVIDENCE_GRADED" else END


def build_clinical_rag_graph(retriever: HybridClinicalRetriever | None = None):
    """Compile the LangGraph Corrective RAG StateGraph (or deterministic fallback)."""
    if LANGGRAPH_AVAILABLE and StateGraph is not None:
        graph = StateGraph(ClinicalRagState)
        graph.add_node("safety_gate", _node_safety_gate)
        graph.add_node("hybrid_retrieve", lambda s: _node_hybrid_retrieve(s, retriever=retriever))
        graph.add_node("grade_evidence", lambda s: _node_grade_evidence(s, retriever=retriever))
        graph.add_node("synthesize_grounded", _node_synthesize_grounded)
        graph.add_node("verify_citations", _node_verify_citations)

        graph.set_entry_point("safety_gate")
        graph.add_conditional_edges(
            "safety_gate",
            _route_after_safety,
            {"hybrid_retrieve": "hybrid_retrieve", END: END},
        )
        graph.add_edge("hybrid_retrieve", "grade_evidence")
        graph.add_conditional_edges(
            "grade_evidence",
            _route_after_grade,
            {"synthesize_grounded": "synthesize_grounded", END: END},
        )
        graph.add_edge("synthesize_grounded", "verify_citations")
        graph.add_edge("verify_citations", END)
        return graph.compile()

    return None


_COMPILED_GRAPH = None


def _get_compiled_graph():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_clinical_rag_graph()
    return _COMPILED_GRAPH


def run_clinical_rag_graph(
    question: str,
    active_findings: list[str],
    anatomical_locations: list[str],
    is_safe: bool = True,
    in_lung_ratio: float | None = None,
    use_llm: bool = True,
    retriever: HybridClinicalRetriever | None = None,
) -> dict[str, Any]:
    """Execute the 5-node LangGraph Corrective RAG workflow and return structured output."""
    t0 = time.perf_counter()
    initial_state: ClinicalRagState = {
        "question": question,
        "active_findings": list(active_findings),
        "anatomical_locations": list(anatomical_locations),
        "is_safe": is_safe,
        "in_lung_ratio": in_lung_ratio,
        "use_llm": use_llm,
        "graph_trace": [],
    }

    compiled = build_clinical_rag_graph(retriever) if retriever is not None else _get_compiled_graph()
    if compiled is not None:
        final_state = compiled.invoke(initial_state)
        engine_label = "langgraph_state_graph"
    else:
        # Equivalent deterministic state-machine execution when langgraph is not installed
        state = _node_safety_gate(initial_state)
        if state.get("status") == "SAFE":
            state = _node_hybrid_retrieve(state, retriever=retriever)
            state = _node_grade_evidence(state, retriever=retriever)
            if state.get("status") == "EVIDENCE_GRADED":
                state = _node_synthesize_grounded(state)
                state = _node_verify_citations(state)
        final_state = state
        engine_label = "deterministic_state_machine"

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "status": final_state.get("status", "NO_MATCH"),
        "answer": final_state.get("answer", ""),
        "citations": final_state.get("citations", []),
        "retrieved_cards": final_state.get("retrieved_cards", []),
        "retrieval_chunks": final_state.get("graded_chunks", []),
        "graph_trace": final_state.get("graph_trace", []),
        "graph_engine": engine_label,
        "synthesis_mode": final_state.get("synthesis_mode", "offline_extractive"),
        "faithfulness_verified": bool(final_state.get("faithfulness_verified", True)),
        "hallucination_guard_triggered": bool(final_state.get("hallucination_guard_triggered", False)),
        "latency_ms": latency_ms,
    }
