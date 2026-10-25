"""Hybrid retrieval integrating Okapi BM25 and Dense Semantic Search."""
from typing import List, Tuple, Dict
from src.schema import DocumentChunk
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseSemanticRetriever
from src.config import CONFIG

class HybridRetriever:
    """Hybrid search combining keyword (BM25) and dense semantic representations."""

    def __init__(self, chunks: List[DocumentChunk], alpha: float = None):
        self.chunks = chunks
        self.alpha = alpha if alpha is not None else CONFIG.retrieval.hybrid_alpha
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseSemanticRetriever(chunks)

    def retrieve_bm25(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        return self.bm25.retrieve(query, top_k=top_k)

    def retrieve_dense(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        return self.dense.retrieve(query, top_k=top_k)

    def retrieve_rrf(self, query: str, top_k: int = None, k_rrf: int = 60) -> List[Tuple[DocumentChunk, float]]:
        """Reciprocal Rank Fusion (RRF) merging BM25 and dense rankings."""
        k = top_k or CONFIG.retrieval.top_k
        bm25_ranked = self.bm25.score(query)
        dense_ranked = self.dense.score(query)

        rrf_scores: Dict[str, float] = {c.chunk_id: 0.0 for c in self.chunks}
        chunk_map = {c.chunk_id: c for c in self.chunks}

        # Accumulate BM25 reciprocal ranks
        for rank, (chunk, _) in enumerate(bm25_ranked, start=1):
            rrf_scores[chunk.chunk_id] += 1.0 / (k_rrf + rank)

        # Accumulate Dense reciprocal ranks
        for rank, (chunk, _) in enumerate(dense_ranked, start=1):
            rrf_scores[chunk.chunk_id] += 1.0 / (k_rrf + rank)

        # Normalize RRF scores to [0, 1] relative to theoretical max: 2.0 / (k_rrf + 1)
        rrf_max = 2.0 / (k_rrf + 1.0)
        ranked = sorted(
            [(chunk_map[cid], score / rrf_max) for cid, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        return ranked[:k]

    def retrieve_convex(self, query: str, top_k: int = None, alpha: float = None) -> List[Tuple[DocumentChunk, float]]:
        """Convex linear combination of min-max normalized scores: alpha * dense + (1 - alpha) * bm25."""
        k = top_k or CONFIG.retrieval.top_k
        weight = alpha if alpha is not None else self.alpha

        bm25_results = dict(self.bm25.score(query))
        dense_results = dict(self.dense.score(query))

        # Normalize BM25 scores to [0, 1]
        bm25_max = max(bm25_results.values()) if bm25_results and max(bm25_results.values()) > 0 else 1.0
        bm25_min = min(bm25_results.values()) if bm25_results else 0.0
        bm25_range = max(bm25_max - bm25_min, 1e-6)

        chunk_map = {c.chunk_id: c for c in self.chunks}
        hybrid_scores = []

        for chunk in self.chunks:
            b_norm = (bm25_results.get(chunk, 0.0) - bm25_min) / bm25_range
            d_norm = dense_results.get(chunk, 0.0)
            combined = (weight * d_norm) + ((1.0 - weight) * b_norm)
            hybrid_scores.append((chunk, float(combined)))

        ranked = sorted(hybrid_scores, key=lambda x: x[1], reverse=True)
        return ranked[:k]

    def retrieve(self, query: str, top_k: int = None, method: str = "rrf") -> List[Tuple[DocumentChunk, float]]:
        """Unified retrieval interface."""
        if method == "bm25":
            return self.retrieve_bm25(query, top_k=top_k)
        elif method == "dense":
            return self.retrieve_dense(query, top_k=top_k)
        elif method == "convex":
            return self.retrieve_convex(query, top_k=top_k)
        else:
            return self.retrieve_rrf(query, top_k=top_k)
