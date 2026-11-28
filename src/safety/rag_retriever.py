"""Lightweight Hybrid Retriever (Okapi BM25 + TF-IDF Word/Char Cosine + RRF).

No external model downloads; Python + NumPy. Latency is measured, not guaranteed.
Indexes 48 atomic clinical evidence chunks (16 LungRay pathologies x 3 facets)
from ``configs/clinical_rag_corpus.json``.
"""
from __future__ import annotations

import copy
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "configs" / "clinical_rag_corpus.json"

FACET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "imaging_hallmarks": (
        "hallmark",
        "hallmarks",
        "sign",
        "signs",
        "imaging",
        "radiograph",
        "radiographic",
        "appearance",
        "feature",
        "features",
        "hinh anh",
        "dau hieu",
        "tieu chuan",
    ),
    "differential_diagnosis": (
        "differential",
        "differentials",
        "mimic",
        "mimics",
        "distinguish",
        "fleischner",
        "vs",
        "versus",
        "phan biet",
        "chan doan phan biet",
    ),
    "clinical_workup_and_coding": (
        "followup",
        "follow up",
        "workup",
        "management",
        "treatment",
        "recommend",
        "recommended",
        "next step",
        "guideline",
        "icd",
        "icd10",
        "code",
        "coding",
        "xpert",
        "ct",
        "ultrasound",
        "xu tri",
        "can lam sang",
        "huong xu tri",
    ),
}

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "which",
        "with",
        "how",
        "should",
        "does",
        "do",
        "can",
        "key",
        "about",
    }
)


def normalize_text(text: str) -> str:
    """Fold Unicode accents (including Vietnamese đ) and normalize to lowercase alnum."""
    text = unicodedata.normalize("NFKD", text.lower().replace("đ", "d"))
    stripped = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", stripped).split())


def tokenize_words(text: str) -> list[str]:
    norm = normalize_text(text)
    return [tok for tok in norm.split() if len(tok) >= 2 and tok not in _STOPWORDS]


def extract_tfidf_features(text: str) -> list[str]:
    """Build hybrid word unigram/bigram + character 3-5 gram features."""
    norm = normalize_text(text)
    words = [tok for tok in norm.split() if len(tok) >= 2 and tok not in _STOPWORDS]
    feats: list[str] = [f"w:{w}" for w in words]
    # Word bigrams
    for i in range(len(words) - 1):
        feats.append(f"b:{words[i]}_{words[i + 1]}")
    # Character 3-5 grams over meaningful words (handles morphological variants)
    for w in words:
        if len(w) >= 4:
            padded = f"^{w}$"
            for n in (3, 4, 5):
                for i in range(len(padded) - n + 1):
                    feats.append(f"c{n}:{padded[i : i + n]}")
    return feats


def detect_query_facet(question: str) -> str | None:
    """Detect whether the query asks specifically for hallmarks, differential, or workup."""
    norm = normalize_text(question)
    scores: dict[str, int] = {}
    for facet, keywords in FACET_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", norm))
        if score > 0:
            scores[facet] = score
    if not scores:
        return None
    return max(scores.items(), key=lambda item: item[1])[0]


@dataclass(frozen=True)
class ClinicalChunk:
    chunk_id: str
    disease: str
    facet: str
    icd10: str
    text: str
    citations: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ScoredChunk:
    chunk: ClinicalChunk
    bm25_score: float
    tfidf_cosine: float
    rrf_score: float
    relevance_score: float


class HybridClinicalRetriever:
    """In-memory Hybrid BM25 + TF-IDF Cosine + RRF retriever over 48 curated chunks."""

    def __init__(self, corpus_path: Path | str = DEFAULT_CORPUS_PATH) -> None:
        self.corpus_path = Path(corpus_path)
        raw = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        self.guidelines: dict[str, str] = dict(raw["guidelines"])
        self.coding_note_default: str = raw["coding_note_default"]

        self.knowledge_base: dict[str, dict[str, Any]] = {}
        self.chunks: list[ClinicalChunk] = []

        for entry in raw["diseases"]:
            disease = entry["disease"]
            slug = entry["slug"]
            icd10 = entry["icd10"]
            aliases = tuple(entry["aliases"])
            citations = tuple(self.guidelines[key] for key in entry["citations"])
            coding_note = entry.get("coding_note", self.coding_note_default)

            self.knowledge_base[disease] = {
                "disease": disease,
                "icd10": icd10,
                "hallmarks": entry["hallmarks"],
                "differential": entry["differential"],
                "followup": entry["followup"],
                "aliases": list(aliases),
                "coding_note": coding_note,
                "citations": list(citations),
            }

            facet_texts = (
                ("imaging_hallmarks", f"{disease} imaging hallmarks: {entry['hallmarks']}"),
                ("differential_diagnosis", f"{disease} differential diagnosis (editorial reference): {entry['differential']}"),
                (
                    "clinical_workup_and_coding",
                    f"{disease} follow-up and clinical workup (ICD-10 {icd10}): {entry['followup']}",
                ),
            )
            for facet, text in facet_texts:
                suffix = facet.split("_")[0] if facet != "clinical_workup_and_coding" else "workup"
                if facet == "imaging_hallmarks":
                    suffix = "hallmarks"
                elif facet == "differential_diagnosis":
                    suffix = "differential"
                self.chunks.append(
                    ClinicalChunk(
                        chunk_id=f"{slug}_{suffix}",
                        disease=disease,
                        facet=facet,
                        icd10=icd10,
                        text=text,
                        citations=citations,
                        aliases=aliases,
                    )
                )

        # Precompute normalized alias lookup table
        self._alias_map: dict[str, set[str]] = {
            disease: {normalize_text(alias) for alias in card["aliases"]}
            for disease, card in self.knowledge_base.items()
        }

        # Build BM25 & TF-IDF indices
        self._build_bm25_index()
        self._build_tfidf_index()
        # Facet-routing terms are not sufficient evidence of a thoracic topic.
        generic = set(tokenize_words(" ".join(kw for words in FACET_KEYWORDS.values() for kw in words)))
        self._content_terms = [set(tokenize_words(ch.text)) - generic - {"clinical", "diagnosis", "follow", "up", "criteria", "fleischner", "icd", "10", "recommended", "assessment", "editorial", "reference"} for ch in self.chunks]

    def _chunk_index_text(self, chunk: ClinicalChunk) -> str:
        alias_str = " ".join(chunk.aliases)
        facet_hint = " ".join(FACET_KEYWORDS[chunk.facet][:6])
        return f"{chunk.disease} {alias_str} {chunk.icd10} {facet_hint} {chunk.text}"

    def _build_bm25_index(self) -> None:
        self._bm25_docs: list[Counter[str]] = []
        self._doc_lens: list[int] = []
        df: Counter[str] = Counter()

        for chunk in self.chunks:
            tokens = tokenize_words(self._chunk_index_text(chunk))
            tf = Counter(tokens)
            self._bm25_docs.append(tf)
            self._doc_lens.append(len(tokens))
            for term in tf:
                df[term] += 1

        n_docs = len(self.chunks)
        self._avgdl = sum(self._doc_lens) / max(n_docs, 1)
        self._bm25_idf: dict[str, float] = {
            term: math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def _build_tfidf_index(self) -> None:
        doc_feats: list[Counter[str]] = []
        df: Counter[str] = Counter()
        for chunk in self.chunks:
            feats = Counter(extract_tfidf_features(self._chunk_index_text(chunk)))
            doc_feats.append(feats)
            for feat in feats:
                df[feat] += 1

        n_docs = len(self.chunks)
        self._vocab: dict[str, int] = {feat: idx for idx, feat in enumerate(sorted(df.keys()))}
        self._tfidf_idf = np.array(
            [math.log((1.0 + n_docs) / (1.0 + df[feat])) + 1.0 for feat in sorted(df.keys())],
            dtype=np.float32,
        )

        matrix = np.zeros((n_docs, len(self._vocab)), dtype=np.float32)
        for row_idx, feats in enumerate(doc_feats):
            for feat, count in feats.items():
                col_idx = self._vocab[feat]
                matrix[row_idx, col_idx] = (1.0 + math.log(count)) * self._tfidf_idf[col_idx]
            norm = float(np.linalg.norm(matrix[row_idx]))
            if norm > 0.0:
                matrix[row_idx] /= norm
        self._tfidf_matrix = matrix

    def _bm25_scores(self, query: str, k1: float = 1.5, b: float = 0.75) -> np.ndarray:
        tokens = tokenize_words(query)
        scores = np.zeros(len(self.chunks), dtype=np.float64)
        if not tokens:
            return scores
        for i, tf_map in enumerate(self._bm25_docs):
            doc_len = self._doc_lens[i]
            denom_norm = k1 * (1.0 - b + b * (doc_len / max(self._avgdl, 1.0)))
            s = 0.0
            for tok in tokens:
                freq = tf_map.get(tok, 0)
                if freq > 0:
                    idf = self._bm25_idf.get(tok, 0.0)
                    s += idf * (freq * (k1 + 1.0)) / (freq + denom_norm)
            scores[i] = s
        return scores

    def _tfidf_cosine_scores(self, query: str) -> np.ndarray:
        feats = Counter(extract_tfidf_features(query))
        if not feats:
            return np.zeros(len(self.chunks), dtype=np.float64)
        q_vec = np.zeros(len(self._vocab), dtype=np.float32)
        for feat, count in feats.items():
            col_idx = self._vocab.get(feat)
            if col_idx is not None:
                q_vec[col_idx] = (1.0 + math.log(count)) * self._tfidf_idf[col_idx]
        norm = float(np.linalg.norm(q_vec))
        if norm == 0.0:
            return np.zeros(len(self.chunks), dtype=np.float64)
        q_vec /= norm
        return np.clip(self._tfidf_matrix @ q_vec, 0.0, 1.0).astype(np.float64)

    def _query_mentions(self, question: str) -> tuple[list[str], set[str]]:
        """Boundary-aware aliases with conservative ambiguity and local negation handling.

        This is reference-topic routing, not clinical negation extraction or diagnosis.
        """
        norm = normalize_text(re.sub(r"[.;!?]", " clauseboundary ", question))
        matched: list[str] = []
        negated: set[str] = set()
        clinical_anchor = bool(re.search(r"\b(lung|pulmonary|chest|thoracic|radiograph|radiographic|imaging|cxr|phoi)\b", norm))
        for disease, aliases in self._alias_map.items():
            for alias in sorted(aliases):
                if not alias:
                    continue
                # 'mass' is a physical quantity, and TB also denotes storage capacity.
                if alias == "mass" and normalize_text(question) != "mass" and not clinical_anchor:
                    continue
                if alias == "tb" and re.search(r"\b(storage|disk|drive|terabyte|ssd|capacity)\b", norm):
                    continue
                for match in re.finditer(r"\b" + re.escape(alias) + r"\b", norm):
                    # Keep conjunction scope, but stop at sentence punctuation or contrast.
                    prefix = norm[:match.start()].split("clauseboundary")[-1]
                    # Up to twelve preceding words; avoid treating a distant negation as global.
                    tail = " ".join(prefix.split()[-12:])
                    denied = bool(re.search(r"\b(no|not|without|denies|negative for|no evidence of|khong co|khong ghi nhan)\b[^.]*$", tail))
                    if re.search(r"\b(but|however|nhung)\b", tail):
                        denied = False
                    if denied:
                        negated.add(disease)
                    elif disease not in matched:
                        matched.append(disease)
        return [d for d in matched if d not in negated], negated

    def match_explicit_diseases(self, question: str) -> list[str]:
        """Resolve explicit non-negated reference topics; short aliases match whole words."""
        return self._query_mentions(question)[0]

    def match_active_findings(self, active_findings: list[str]) -> list[str]:
        """Resolve caller-supplied active finding labels to canonical LungRay disease names."""
        normalized_findings = {normalize_text(item) for item in active_findings if item}
        matched: list[str] = []
        for disease, alias_set in self._alias_map.items():
            if normalized_findings & alias_set:
                matched.append(disease)
        return matched

    def get_card(self, disease: str) -> dict[str, Any]:
        return copy.deepcopy(self.knowledge_base[disease])

    def retrieve(
        self,
        question: str,
        active_findings: list[str] | None = None,
        top_k: int = 6,
        rrf_k: int = 60,
    ) -> tuple[list[ScoredChunk], list[str], str | None]:
        """Hybrid BM25 + TF-IDF Cosine + RRF retrieval with clinical topic scoping.

        Returns:
            (scored_chunks, target_diseases, detected_facet)
        """
        if top_k < 1 or rrf_k < 0:
            raise ValueError("top_k must be positive and rrf_k must be nonnegative")
        if not normalize_text(question):
            return [], [], None
        explicit_diseases, negated = self._query_mentions(question)
        active_diseases = [d for d in self.match_active_findings(active_findings or []) if d not in negated]
        detected_facet = detect_query_facet(question)

        # Explicitly named diseases take precedence (treated as reference lookup,
        # not as an additional positive finding on the scan).
        scoped_diseases = explicit_diseases if explicit_diseases else active_diseases
        query_terms = set(tokenize_words(question))
        domain_overlap = any(len(query_terms & terms) >= 2 for terms in self._content_terms)
        if scoped_diseases and not explicit_diseases:
            generic = set(tokenize_words(" ".join(kw for words in FACET_KEYWORDS.values() for kw in words)))
            generic |= {"clinical", "please", "tell", "me", "findings", "detected", "study", "these", "those", "diagnoses", "criteria", "10"}
            confidence_query = any(term in normalize_text(question) for term in ("confidence", "tin cay", "giai phau", "energy ratio", "shortcut"))
            if len(query_terms - generic) >= 2 and not domain_overlap and not confidence_query:
                return [], [], detected_facet
        if not scoped_diseases:
            # Do not reintroduce negated topics via the open lexical search.
            if negated or not domain_overlap:
                return [], [], detected_facet
            # An ambiguous mass-only query cannot be rescued by character overlap.
            if "mass" in query_terms and not explicit_diseases and "Mass" not in active_diseases:
                return [], [], detected_facet

        # Build enriched query string for lexical + subword scoring
        query_for_scoring = question
        if scoped_diseases and not explicit_diseases:
            query_for_scoring = f"{question} {' '.join(scoped_diseases)}"

        bm25_raw = self._bm25_scores(query_for_scoring)
        tfidf_raw = self._tfidf_cosine_scores(query_for_scoring)

        # Candidate indices: restrict to scoped diseases if available; otherwise search all 48 chunks
        if scoped_diseases:
            scoped_set = set(scoped_diseases)
            candidate_indices = [i for i, ch in enumerate(self.chunks) if ch.disease in scoped_set]
        else:
            candidate_indices = list(range(len(self.chunks)))

        if detected_facet:
            candidate_indices = [i for i in candidate_indices if self.chunks[i].facet == detected_facet]
        top_k = max(top_k, len(scoped_diseases))

        # Compute ranks within candidate pool for RRF
        bm25_order = sorted((i for i in candidate_indices if bm25_raw[i] > 0), key=lambda idx: (-bm25_raw[idx], idx))
        tfidf_order = sorted((i for i in candidate_indices if tfidf_raw[i] > 0), key=lambda idx: (-tfidf_raw[idx], idx))
        bm25_rank = {idx: rank for rank, idx in enumerate(bm25_order, start=1)}
        tfidf_rank = {idx: rank for rank, idx in enumerate(tfidf_order, start=1)}

        scored: list[ScoredChunk] = []
        max_bm25 = float(max((bm25_raw[i] for i in candidate_indices), default=0.0))

        for idx in candidate_indices:
            chunk = self.chunks[idx]
            bm25_val = float(bm25_raw[idx])
            tfidf_val = float(tfidf_raw[idx])
            rrf_val = (1.0 / (rrf_k + bm25_rank[idx]) if idx in bm25_rank else 0.0) + (1.0 / (rrf_k + tfidf_rank[idx]) if idx in tfidf_rank else 0.0)

            # Normalized relevance score in [0, 1] combining lexical + subword + scoping + facet match
            bm25_norm = (bm25_val / max_bm25) if max_bm25 > 0.0 else 0.0
            base_signal = 0.45 * min(tfidf_val * 2.2, 1.0) + 0.35 * bm25_norm + 0.20 * min(rrf_val * 30.0, 1.0)

            # When diseases are explicitly named or active findings are supplied, boost matching chunks
            if scoped_diseases:
                facet_bonus = 0.22 if (detected_facet and chunk.facet == detected_facet) else 0.08
                relevance = min(1.0, 0.55 + 0.35 * base_signal + facet_bonus)
            else:
                # Open-ended clinical query without active findings: require genuine lexical/subword match
                if bm25_val <= 0.0 and tfidf_val < 0.08:
                    relevance = 0.0
                else:
                    # Weight absolute BM25 strength so unrelated queries don't inflate via max_bm25
                    bm25_abs = min(bm25_val / 6.0, 1.0)
                    facet_bonus = 0.08 if (detected_facet and chunk.facet == detected_facet) else 0.0
                    relevance = min(1.0, 0.55 * min(tfidf_val * 2.5, 1.0) + 0.45 * bm25_abs + facet_bonus)

            scored.append(
                ScoredChunk(
                    chunk=chunk,
                    bm25_score=bm25_val,
                    tfidf_cosine=tfidf_val,
                    rrf_score=rrf_val,
                    relevance_score=relevance,
                )
            )

        scored.sort(
            key=lambda item: (
                -item.relevance_score,
                -item.rrf_score,
                -item.tfidf_cosine,
                item.chunk.chunk_id,
            )
        )

        # Ensure multi-pathology coverage when scoped_diseases > 1 (at least 1 best chunk per disease)
        if len(scoped_diseases) > 1 and top_k >= len(scoped_diseases):
            chosen: list[ScoredChunk] = []
            seen_ids: set[str] = set()
            for disease in scoped_diseases:
                for item in scored:
                    if item.chunk.disease == disease and item.chunk.chunk_id not in seen_ids:
                        chosen.append(item)
                        seen_ids.add(item.chunk.chunk_id)
                        break
            for item in scored:
                if len(chosen) >= top_k:
                    break
                if item.chunk.chunk_id not in seen_ids:
                    chosen.append(item)
                    seen_ids.add(item.chunk.chunk_id)
            top_chunks = chosen[:top_k]
        else:
            top_chunks = scored[:top_k]

        resolved_diseases = scoped_diseases or list(dict.fromkeys(item.chunk.disease for item in top_chunks if item.relevance_score > 0))
        return top_chunks, resolved_diseases, detected_facet


_RETRIEVER_SINGLETON: HybridClinicalRetriever | None = None


def get_clinical_retriever() -> HybridClinicalRetriever:
    global _RETRIEVER_SINGLETON
    if _RETRIEVER_SINGLETON is None:
        _RETRIEVER_SINGLETON = HybridClinicalRetriever()
    return _RETRIEVER_SINGLETON
