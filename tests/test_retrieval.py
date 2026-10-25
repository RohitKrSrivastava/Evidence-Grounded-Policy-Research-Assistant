"""Tests for BM25, Dense Semantic Retrieval, Hybrid Search, and Re-ranking."""
import pytest
from src.config import STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR
from src.ingestion.chunker import PolicyChunker
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseSemanticRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import PolicyReranker

@pytest.fixture(scope="module")
def corpus():
    chunker = PolicyChunker()
    return chunker.build_corpus_chunks(STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR)

def test_bm25_retrieval(corpus):
    bm25 = BM25Retriever(corpus)
    results = bm25.retrieve("Value Added Infocomm Media 2023", top_k=3)
    assert len(results) == 3
    top_chunk, score = results[0]
    assert score > 0.0
    assert "value added" in top_chunk.content.lower() or "infocomm" in top_chunk.content.lower()

def test_dense_semantic_retrieval(corpus):
    dense = DenseSemanticRetriever(corpus)
    results = dense.retrieve("artificial intelligence adoption enterprise", top_k=3)
    assert len(results) == 3
    top_chunk, score = results[0]
    assert score >= 0.0
    assert score <= 1.0

def test_hybrid_rrf_retrieval(corpus):
    hybrid = HybridRetriever(corpus)
    results = hybrid.retrieve_rrf("Green Data Centre Roadmap PUE 1.3", top_k=3)
    assert len(results) == 3
    top_chunk, score = results[0]
    assert score > 0.0
    assert any("data centre" in c.content.lower() for c, _ in results)

def test_reranker_and_metadata_filter(corpus):
    hybrid = HybridRetriever(corpus)
    reranker = PolicyReranker()
    candidates = hybrid.retrieve("CTO-as-a-Service SMEs", top_k=5)
    reranked = reranker.rerank("CTO-as-a-Service SMEs", candidates, top_n=2)
    assert len(reranked) <= 2
    assert "cto" in reranked[0][0].content.lower() or "sme" in reranked[0][0].content.lower()
