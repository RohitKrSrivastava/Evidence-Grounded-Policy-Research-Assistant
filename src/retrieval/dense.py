"""Dense semantic vector retrieval module using continuous embeddings and cosine similarity."""
import math
import re
from typing import List, Tuple, Dict
import numpy as np
from src.schema import DocumentChunk
from src.config import CONFIG

class DenseSemanticRetriever:
    """Dense vector retriever using hashed subword/token embeddings and cosine similarity."""

    def __init__(self, chunks: List[DocumentChunk], embedding_dim: int = 256):
        self.chunks = chunks
        self.embedding_dim = embedding_dim
        self.chunk_embeddings = np.zeros((len(chunks), embedding_dim), dtype=np.float32)
        self._encode_corpus()

    @staticmethod
    def _clean_tokens(text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s\$\%\.]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 1]

    def _embed_text(self, text: str) -> np.ndarray:
        """Projects text into an L2-normalized dense continuous vector."""
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        tokens = self._clean_tokens(text)
        if not tokens:
            return vec

        for idx, token in enumerate(tokens):
            # Positional & semantic feature hashing
            hash_val = hash(token)
            dim_idx = abs(hash_val) % self.embedding_dim
            sign = 1.0 if (hash_val // self.embedding_dim) % 2 == 0 else -1.0
            weight = 1.0 / (1.0 + 0.05 * idx)  # Early query words carry slightly higher focus
            vec[dim_idx] += sign * weight

            # Sub-word character n-grams (3-grams) for vocabulary resilience
            if len(token) >= 4:
                for i in range(len(token) - 2):
                    sub = token[i : i + 3]
                    s_hash = hash(sub)
                    s_dim = abs(s_hash) % self.embedding_dim
                    vec[s_dim] += 0.3 * (1.0 if s_hash % 2 == 0 else -1.0)

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        return vec

    def _encode_corpus(self):
        """Precomputes dense embedding matrix for all chunks."""
        for idx, chunk in enumerate(self.chunks):
            # Combine title, section, and content for rich semantic representation
            rich_text = f"{chunk.doc_title} {chunk.section} {chunk.content}"
            self.chunk_embeddings[idx] = self._embed_text(rich_text)

    def score(self, query: str) -> List[Tuple[DocumentChunk, float]]:
        """Calculates cosine similarity between query and all chunks."""
        q_vec = self._embed_text(query)
        q_norm = np.linalg.norm(q_vec)
        if q_norm < 1e-9:
            return [(c, 0.0) for c in self.chunks]

        # Cosine similarity via matrix multiplication
        sims = np.dot(self.chunk_embeddings, q_vec)
        # Scale to [0, 1] range: 0.5 * (sim + 1)
        normalized_sims = np.clip((sims + 1.0) / 2.0, 0.0, 1.0)

        results = [(self.chunks[i], float(normalized_sims[i])) for i in range(len(self.chunks))]
        ranked = sorted(results, key=lambda x: x[1], reverse=True)
        return ranked

    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[DocumentChunk, float]]:
        """Retrieves top-k dense semantic chunks."""
        k = top_k or CONFIG.retrieval.top_k
        return self.score(query)[:k]
