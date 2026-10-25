"""Okapi BM25 implementation for deterministic keyword retrieval."""
import math
import re
from typing import List, Dict, Tuple
from src.schema import DocumentChunk
from src.config import CONFIG

class BM25Retriever:
    """Okapi BM25 retrieval engine."""

    def __init__(self, chunks: List[DocumentChunk], k1: float = None, b: float = None):
        self.chunks = chunks
        self.k1 = k1 if k1 is not None else CONFIG.retrieval.bm25_k1
        self.b = b if b is not None else CONFIG.retrieval.bm25_b
        self.corpus_size = len(chunks)
        self.doc_lens = [len(self._tokenize(c.content)) for c in chunks]
        self.avg_doc_len = sum(self.doc_lens) / max(self.corpus_size, 1)

        # Inverted index: term -> list of (doc_index, term_frequency)
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs: List[Dict[str, int]] = []
        self._build_index()

    STOPWORDS = {
        "what", "is", "the", "in", "of", "to", "and", "a", "an", "for", "are", "on",
        "with", "by", "at", "from", "that", "this", "it", "as", "be", "was", "were",
        "or", "how", "why", "which", "who", "when", "where", "does", "did", "has", "have", "had", "singapore"
    }

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """Normalize and tokenize text into lowercase word tokens, stripping stopwords."""
        clean_text = re.sub(r"[^\w\s\$\%\.]", " ", text.lower())
        tokens = [
            t.strip("._") for t in clean_text.split()
            if len(t.strip("._")) > 1 and t.strip("._") not in cls.STOPWORDS
        ]
        return tokens

    def _build_index(self):
        """Constructs inverted term index and document frequencies."""
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.content)
            tf: Dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.term_freqs.append(tf)

            for token in tf.keys():
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

    def _idf(self, term: str) -> float:
        """Calculates Robertson-Spärck Jones IDF with smoothing."""
        df = self.doc_freqs.get(term, 0)
        return math.log(((self.corpus_size - df + 0.5) / (df + 0.5)) + 1.0)

    def score(self, query: str) -> List[Tuple[DocumentChunk, float]]:
        """Scores all chunks against the query using Okapi BM25."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [(c, 0.0) for c in self.chunks]

        scores = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.doc_freqs:
                continue
            idf = self._idf(token)
            for idx in range(self.corpus_size):
                tf = self.term_freqs[idx].get(token, 0)
                if tf == 0:
                    continue
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[idx] / max(self.avg_doc_len, 1e-6)))
                scores[idx] += idf * (num / denom)

        ranked = sorted(zip(self.chunks, scores), key=lambda x: x[1], reverse=True)
        return ranked

    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[DocumentChunk, float]]:
        """Returns top-k documents matching the query."""
        k = top_k or CONFIG.retrieval.top_k
        results = self.score(query)
        return results[:k]
