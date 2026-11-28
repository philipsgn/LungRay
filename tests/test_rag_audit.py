"""Independent adversarial, mathematical and graph-branch checks for clinical RAG."""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfTransformer

from scripts.evaluate_rag import _score_case, evaluate_golden_benchmark
from src.safety import rag_graph
from src.safety.rag_knowledge import query_clinical_rag
from src.safety.rag_retriever import extract_tfidf_features, get_clinical_retriever, tokenize_words

ROOT = Path(__file__).resolve().parents[1]


def test_bm25_agrees_with_hand_computed_okapi_formula():
    r = get_clinical_retriever()
    scores = r._bm25_scores("pneumonia")
    lengths = [sum(tf.values()) for tf in r._bm25_docs]
    n = len(lengths)
    df = sum("pneumonia" in tf for tf in r._bm25_docs)
    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
    for idx, tf in enumerate(r._bm25_docs):
        frequency = tf.get("pneumonia", 0)
        expected = idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * lengths[idx] / np.mean(lengths)))
        assert scores[idx] == pytest.approx(expected)
    assert np.allclose(r._bm25_scores("pneumonia pneumonia"), 2 * scores)
    assert tokenize_words("!!!") == []


def test_tfidf_matches_independent_sklearn_transformer():
    r = get_clinical_retriever()
    counts = np.zeros_like(r._tfidf_matrix)
    for idx, chunk in enumerate(r.chunks):
        for feature, count in Counter(extract_tfidf_features(r._chunk_index_text(chunk))).items():
            counts[idx, r._vocab[feature]] = count
    transformer = TfidfTransformer(sublinear_tf=True, smooth_idf=True, norm="l2")
    expected = transformer.fit_transform(counts).toarray()
    assert np.allclose(expected, r._tfidf_matrix, atol=1e-6)
    assert "c5:^pneu" in extract_tfidf_features("pneumonia")
    query = counts[0:1]
    expected_scores = expected @ transformer.transform(query).toarray()[0]
    assert np.allclose(r._tfidf_cosine_scores(r._chunk_index_text(r.chunks[0])), expected_scores, atol=1e-6)


def test_rrf_has_one_based_ranks_and_no_credit_for_zero_score(monkeypatch):
    r = get_clinical_retriever()
    bm25 = np.zeros(len(r.chunks)); bm25[:3] = [3, 2, 1]
    cosine = np.zeros(len(r.chunks)); cosine[:3] = [0.1, 0.3, 0.2]
    monkeypatch.setattr(r, "_bm25_scores", lambda _: bm25)
    monkeypatch.setattr(r, "_tfidf_cosine_scores", lambda _: cosine)
    scored, _, _ = r.retrieve("sharp white peripheral bronchovascular markings", top_k=48)
    actual = {item.chunk.chunk_id: item.rrf_score for item in scored}
    for index, ranks in enumerate([(1, 3), (2, 1), (3, 2)]):
        expected = sum(1 / (60 + rank) for rank in ranks)
        assert actual[r.chunks[index].chunk_id] == pytest.approx(expected, abs=1e-6)
    assert actual[r.chunks[3].chunk_id] == 0
    with pytest.raises(ValueError):
        r.retrieve("TB", top_k=0)


@pytest.mark.parametrize("question", ["", "!!!", "🩻", "mass of Jupiter", "normal blood pressure management", "write a treatment plan for broken computer hardware", "clinical followup management", "tbird", "outbound", "1 TB storage", "No pneumonia", "No effusion or pneumothorax", "khong co viem phoi"])
def test_irrelevant_empty_or_negated_queries_abstain(question):
    result = query_clinical_rag(question, [], [])
    assert result["status"] == "NO_MATCH"
    assert result["retrieval_chunks"] == result["retrieved_cards"] == result["citations"] == []


def test_negation_does_not_cross_sentences_and_short_alias_has_boundaries():
    r = get_clinical_retriever()
    assert r.match_explicit_diseases("No effusion. Pneumonia imaging hallmarks?") == ["Pneumonia"]
    assert r.match_explicit_diseases("not pneumonia but effusion") == ["Effusion"]
    assert r.match_explicit_diseases("outbound tbird") == []
    assert r.match_explicit_diseases("TB") == ["Tuberculosis"]


def test_all_sixteen_topics_have_evidence_cards_without_silent_truncation():
    diseases = list(get_clinical_retriever().knowledge_base)
    result = query_clinical_rag("What are the imaging hallmarks?", diseases, [])
    assert {card["disease"] for card in result["retrieved_cards"]} == set(diseases)
    assert {ch["disease"] for ch in result["retrieval_chunks"]} == set(diseases)
    assert all(ch["facet"] == "imaging_hallmarks" for ch in result["retrieval_chunks"])
    for chunk in result["retrieval_chunks"]:
        assert f"[{chunk['chunk_id']}]" in result["answer"]


@pytest.mark.parametrize("ratio", [-0.01, 1.01, float("nan"), float("inf"), "0.5", True])
def test_core_rejects_invalid_ratios(ratio):
    result = query_clinical_rag("TB", [], [], in_lung_ratio=ratio)
    assert result["status"] == "INVALID_CONTEXT"
    assert result["retrieved_cards"] == []


def test_ood_short_circuits_before_retrieval_llm_and_ratio(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("OOD must stop here")
    monkeypatch.setattr(rag_graph, "_node_hybrid_retrieve", forbidden)
    monkeypatch.setattr(rag_graph, "_call_gemini_free_api", forbidden)
    result = query_clinical_rag("TB", ["Tuberculosis"], [], is_safe=False, in_lung_ratio=2)
    assert result["status"] == "BLOCKED_OOD"
    assert result["graph_trace"] == ["safety_gate:BLOCKED_OOD"]


@pytest.mark.parametrize("draft", [
    "Tuberculosis chest clinical assessment is cured by drinking bleach.",
    "Tuberculosis chest clinical assessment is cured by bleach [tuberculosis_workup].",
    "Tuberculosis chest clinical assessment is 100% certain [TUBERCULOSIS_WORKUP].",
    "Tuberculosis chest clinical assessment is normal [tuberculosis_workup]. Added secret treatment.",
])
def test_verifier_rejects_uncited_valid_id_and_numeric_hallucinations(draft, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("GEMINI_RAG_MODEL", "test-model")
    monkeypatch.setattr(rag_graph, "_call_gemini_free_api", lambda **kwargs: draft)
    result = rag_graph.run_clinical_rag_graph("TB workup", [], [], use_llm=True)
    assert result["hallucination_guard_triggered"] is True
    assert result["synthesis_mode"] == "offline_extractive_fallback"
    assert "bleach" not in result["answer"] and "100% certain" not in result["answer"]


def test_exact_evidence_copy_with_appended_claim_still_fails():
    chunks = query_clinical_rag("TB workup", [], [])["retrieval_chunks"]
    valid = chunks[0]["text"] + " [" + chunks[0]["chunk_id"] + "]"
    assert rag_graph._verify_draft_against_evidence(valid, chunks)
    for invalid in [valid + " The patient is cured.", "Not " + valid, valid.replace("Xpert", "poison"), valid.replace("A16.2", "A99.9")]:
        assert not rag_graph._verify_draft_against_evidence(invalid, chunks)


def test_no_timing_is_deterministic_even_with_key_and_llm_requested(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("GEMINI_RAG_MODEL", "test-model")
    def forbidden(**kwargs):
        raise AssertionError("No external synthesis in deterministic mode")
    monkeypatch.setattr(rag_graph, "_call_gemini_free_api", forbidden)
    a = query_clinical_rag("TB", [], [], use_llm=True, include_timing=False)
    b = query_clinical_rag("TB", [], [], use_llm=True, include_timing=False)
    assert a == b and "latency_ms" not in a
    assert a["synthesis_mode"] == "offline_extractive"


def test_metrics_do_not_use_cards_or_self_reported_faithfulness():
    corpus = {ch.chunk_id: ch for ch in get_clinical_retriever().chunks}
    case = dict(id="metric-probe", category="audit", question="TB hallmarks", expected_status="GROUNDED_REFERENCE", expected_diseases=["Tuberculosis"], expected_facets=["imaging_hallmarks"])
    result = query_clinical_rag("Pneumonia", [], [])
    result["retrieved_cards"].append(get_clinical_retriever().get_card("Tuberculosis"))
    result["faithfulness_verified"] = True
    result["answer"] += " Invented medical advice."
    scored = _score_case(case, result, corpus)
    assert scored["recall_at_3"] == scored["reciprocal_rank"] == 0.0
    assert scored["source_copy_compliant"] is False


def test_real_graph_and_fallback_parity_when_installed():
    if not rag_graph.LANGGRAPH_AVAILABLE:
        assert rag_graph.build_clinical_rag_graph() is None
        return
    for filename in ["rag_eval_golden.json", "rag_eval_adversarial.json"]:
        cases = json.loads((ROOT / "configs" / filename).read_text(encoding="utf-8"))["cases"]
        for case in cases:
            kwargs = {key: case[key] for key in ("question", "active_findings", "anatomical_locations", "is_safe", "in_lung_ratio") if key in case}
            kwargs.setdefault("active_findings", []); kwargs.setdefault("anatomical_locations", [])
            actual = []
            for backend in ("langgraph", "fallback"):
                result = rag_graph.run_clinical_rag_graph(**kwargs, graph_backend=backend, include_timing=False)
                result.pop("graph_engine")
                actual.append(result)
            assert actual[0] == actual[1], case["id"]


def test_adversarial_suite_is_separate_from_original_golden_cases():
    result = evaluate_golden_benchmark(ROOT / "configs/rag_eval_adversarial.json", report_path=None)
    assert result["total_cases"] == 24
    assert result["metrics"]["status_accuracy"] == 1.0
    assert result["metrics"]["ood_and_abstention_accuracy"] == 1.0
    # Six relevant topics cannot all fit in three ranked chunks. Never pad this metric with cards.
    assert result["metrics"]["recall_at_3"] < 1.0

def test_gemini_key_is_in_header_and_not_url_or_error_log(monkeypatch, caplog):
    import httpx
    sent = {}
    class Client:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            sent.update(url=url, **kwargs)
            raise RuntimeError("private-fake-key must not be logged")
    monkeypatch.setattr(httpx, "Client", Client)
    assert rag_graph._call_gemini_free_api("TB", "reference", [], "private-fake-key", model="test-model") is None
    assert "key=" not in sent["url"]
    assert sent["headers"]["x-goog-api-key"] == "private-fake-key"
    assert "private-fake-key" not in caplog.text

def test_relevance_threshold_is_inclusive_without_rounding_up():
    r = get_clinical_retriever()
    chunks = [rag_graph._serialize_scored_chunk(item) for item in r.retrieve("TB workup")[0]]
    below = dict(chunks[0], relevance_score=rag_graph.RELEVANCE_THRESHOLD - 0.0001)
    boundary = dict(chunks[0], relevance_score=rag_graph.RELEVANCE_THRESHOLD)
    assert rag_graph._node_grade_evidence({"retrieved_raw": [below]})["status"] == "NO_MATCH"
    assert rag_graph._node_grade_evidence({"retrieved_raw": [boundary]})["status"] == "EVIDENCE_GRADED"

def test_active_findings_do_not_force_references_for_an_unrelated_query():
    result = query_clinical_rag("write a treatment plan for broken computer hardware", ["Tuberculosis"], [])
    assert result["status"] == "NO_MATCH"
    assert result["retrieved_cards"] == []

def test_llm_must_not_silently_omit_topics_from_multi_pathology_answer(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("GEMINI_RAG_MODEL", "test-model")
    monkeypatch.setattr(rag_graph, "_call_gemini_free_api", lambda **kwargs: kwargs["graded_chunks"][0]["text"] + " [" + kwargs["graded_chunks"][0]["chunk_id"] + "]")
    diseases = list(get_clinical_retriever().knowledge_base)[:6]
    result = rag_graph.run_clinical_rag_graph("Imaging hallmarks?", diseases, [], use_llm=True)
    assert result["hallucination_guard_triggered"] is True
    assert {c["disease"] for c in result["retrieved_cards"]} == set(diseases)
    assert result["synthesis_mode"] == "offline_extractive_fallback"

def test_legacy_response_defaults_are_backward_compatible_and_unverified():
    from app.backend.schemas import RagQueryResponse
    response = RagQueryResponse(status="GROUNDED_REFERENCE", answer="legacy", citations=[], retrieved_cards=[])
    assert response.retrieval_chunks == response.graph_trace == []
    assert response.graph_engine == "unknown"
    assert response.faithfulness_verified is False
    assert response.verification_scope == "not_verified"
