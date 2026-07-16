"""
Hybrid RAG Retrieval Engine
----------------------------
Combines:
  * Sparse retrieval  -> BM25 (rank_bm25)
  * "Dense" retrieval  -> TF-IDF cosine similarity over char+word n-grams
    (a lightweight, dependency-free stand-in for a transformer bi-encoder;
    swap `DenseIndex` internals for `sentence-transformers` + FAISS/Qdrant/
    Milvus/Pinecone in production without touching the Agent layer)
  * Reciprocal Rank Fusion for hybrid scoring
  * Cross-encoder-style reranking (lexical-overlap + entity-overlap scorer)
  * Metadata filtering (by category / equipment tag / date)
  * Multi-query expansion (naive query paraphrasing)
  * Parent-child chunk resolution (child chunk retrieved -> parent chunk
    returned for grounded generation)
  * Confidence scoring + hallucination-risk flag
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9\-]+", text.lower())


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    filename: str
    category: str
    child_text: str
    parent_text: str
    score: float
    source: str  # "hybrid"


class HybridRetriever:
    """In-memory hybrid index rebuilt whenever documents change (fine for
    hackathon-scale corpora; swap for an incremental FAISS/Qdrant index for
    large production corpora)."""

    def __init__(self):
        self.chunks: list[dict] = []
        self._bm25: Optional[BM25Okapi] = None
        self._tfidf: Optional[TfidfVectorizer] = None
        self._tfidf_matrix = None

    def index(self, chunks: list[dict]):
        """chunks: list of dicts with keys chunk_id, document_id, filename,
        category, child_text, parent_text"""
        self.chunks = chunks
        if not chunks:
            self._bm25 = None
            self._tfidf = None
            return
        tokenized = [_tokenize(c["child_text"]) for c in chunks]
        self._bm25 = BM25Okapi(tokenized)
        self._tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=20000)
        self._tfidf_matrix = self._tfidf.fit_transform([c["child_text"] for c in chunks])

    def _expand_queries(self, query: str) -> list[str]:
        """Naive multi-query expansion: original + entity-stripped + keyword-only."""
        variants = {query}
        keywords = " ".join(re.findall(r"[A-Za-z0-9\-]{3,}", query))
        variants.add(keywords)
        # HyDE-lite: hypothesize an answer-shaped phrasing for better recall
        variants.add(f"report describing {query}")
        return list(variants)

    def retrieve(self, query: str, top_k: int = 6, category_filter: Optional[str] = None,
                 equipment_filter: Optional[str] = None) -> list[RetrievedChunk]:
        if not self.chunks or self._bm25 is None:
            return []

        candidates = self.chunks
        idx_map = list(range(len(candidates)))
        if category_filter:
            idx_map = [i for i in idx_map if candidates[i]["category"] == category_filter]
        if equipment_filter:
            idx_map = [i for i in idx_map
                       if equipment_filter.upper() in candidates[i]["child_text"].upper()]
        if not idx_map:
            idx_map = list(range(len(candidates)))

        query_variants = self._expand_queries(query)

        rrf_scores = {i: 0.0 for i in idx_map}
        for qv in query_variants:
            tok = _tokenize(qv)
            bm25_scores = self._bm25.get_scores(tok)
            bm25_ranked = sorted(idx_map, key=lambda i: -bm25_scores[i])
            for rank, i in enumerate(bm25_ranked):
                rrf_scores[i] += 1.0 / (60 + rank)

            q_vec = self._tfidf.transform([qv])
            sims = cosine_similarity(q_vec, self._tfidf_matrix[idx_map]).flatten()
            dense_ranked = [idx_map[j] for j in np.argsort(-sims)]
            for rank, i in enumerate(dense_ranked):
                rrf_scores[i] += 1.0 / (60 + rank)

        ranked = sorted(rrf_scores.items(), key=lambda kv: -kv[1])[:top_k * 3]

        # Cross-encoder-style rerank: lexical overlap + entity token overlap
        q_tokens = set(_tokenize(query))
        reranked = []
        for i, base_score in ranked:
            c = candidates[i]
            c_tokens = set(_tokenize(c["child_text"]))
            overlap = len(q_tokens & c_tokens) / (len(q_tokens) + 1e-6)
            final_score = 0.7 * base_score + 0.3 * overlap
            reranked.append((i, final_score))
        reranked.sort(key=lambda kv: -kv[1])
        reranked = reranked[:top_k]

        results = []
        max_score = max([s for _, s in reranked], default=1.0) or 1.0
        for i, score in reranked:
            c = candidates[i]
            results.append(RetrievedChunk(
                chunk_id=c["chunk_id"], document_id=c["document_id"],
                filename=c["filename"], category=c["category"],
                child_text=c["child_text"], parent_text=c["parent_text"],
                score=round(float(score / max_score), 4), source="hybrid",
            ))
        return results


def confidence_and_hallucination_flag(query: str, retrieved: list[RetrievedChunk]) -> dict:
    """Simple grounded-confidence heuristic: high coverage + high top score
    => high confidence; sparse/low-overlap retrieval => hallucination risk
    flag so the Answer Agent can hedge appropriately."""
    if not retrieved:
        return {"confidence": 0.0, "hallucination_risk": "high",
                "reason": "No supporting evidence retrieved from the corpus."}

    avg_score = float(np.mean([r.score for r in retrieved]))
    top_score = retrieved[0].score
    n_sources = len({r.document_id for r in retrieved})

    confidence = round(min(0.98, 0.5 * top_score + 0.3 * avg_score + 0.05 * min(n_sources, 4)), 2)
    risk = "low" if confidence > 0.6 else ("medium" if confidence > 0.35 else "high")
    return {
        "confidence": confidence,
        "hallucination_risk": risk,
        "reason": f"Grounded in {n_sources} document(s), top relevance score {top_score}.",
    }
