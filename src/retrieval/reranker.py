"""Re-ranking and metadata filtering layer for high-precision policy evidence retrieval."""
import re
from typing import List, Tuple, Dict, Any, Optional
from src.schema import DocumentChunk
from src.config import CONFIG

class PolicyReranker:
    """Applies domain-specific metadata filtering and heuristic cross-attribute re-ranking."""

    def __init__(self, min_threshold: float = None):
        self.min_threshold = min_threshold or CONFIG.retrieval.min_relevance_threshold

    @staticmethod
    def filter_by_metadata(
        candidates: List[Tuple[DocumentChunk, float]],
        year: Optional[int] = None,
        doc_type: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Filters candidate chunks based on structural metadata tags."""
        filtered = []
        for chunk, score in candidates:
            # Year check
            if year is not None:
                content = chunk.content
                if str(year) not in content and str(year) not in str(chunk.metadata):
                    continue

            # Doc type check
            if doc_type is not None and chunk.doc_type != doc_type:
                continue

            # Source ID check
            if source_id is not None and source_id.lower() not in chunk.source_id.lower():
                continue

            filtered.append((chunk, score))
        return filtered

    INSTRUCTION_WORDS = {
        "what", "is", "the", "in", "of", "to", "and", "a", "an", "for", "are", "on",
        "with", "by", "at", "from", "that", "this", "it", "as", "be", "was", "were",
        "or", "how", "why", "which", "who", "when", "where", "does", "did", "has", "have", "had",
        "singapore", "please", "can", "you", "tell", "me", "between", "under", "per",
        "calculate", "query", "synthesize", "analyze", "compare", "provide", "detail",
        "explain", "summarize", "find", "show", "year", "years", "fiscal", "yesterday", "across"
    }

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[DocumentChunk, float]],
        top_n: int = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Re-scores candidate chunks with query phrase alignment and semantic density."""
        n = top_n or CONFIG.retrieval.rerank_top_n
        query_lower = query.lower()
        query_tokens = [w for w in re.findall(r"\w+", query_lower) if len(w) > 2]
        topical_words = {w for w in query_tokens if w not in self.INSTRUCTION_WORDS and not w.isdigit()}

        reranked = []
        for chunk, base_score in candidates:
            boost = 0.0
            content_lower = chunk.content.lower()
            sec_lower = chunk.section.lower()

            # Check topical matches
            if topical_words:
                matched_topical = {w for w in topical_words if w in content_lower or w in sec_lower}
                # If query has distinctive topical terms, but this chunk has zero overlap, disqualify
                if not matched_topical:
                    reranked.append((chunk, 0.0))
                    continue

                topical_coverage = len(matched_topical) / len(topical_words)
                # If user asks specific out-of-scope query like "agricultural rice quotas" (matches 1 of 4), disqualify
                if len(topical_words) >= 3 and topical_coverage < 0.40:
                    reranked.append((chunk, 0.0))
                    continue
                boost += 0.50 * topical_coverage

            # 1. Exact query phrase presence
            if len(query.strip()) > 5 and query_lower in content_lower:
                boost += 0.35

            # 2. Section heading relevance
            if any(w in sec_lower for w in topical_words):
                boost += 0.30

            # 3. Numerical/Statistical density for quantitative queries
            has_numbers = bool(re.search(r"\d+(\.\d+)?%?", query))
            if has_numbers and bool(re.search(r"\d+(\.\d+)?", content_lower)):
                boost += 0.20

            final_score = base_score * (1.0 + boost)
            reranked.append((chunk, final_score))

        reranked = sorted(reranked, key=lambda x: x[1], reverse=True)
        # Apply strict minimum threshold - if no candidate meets threshold, return empty list
        valid = [item for item in reranked if item[1] >= self.min_threshold]
        return valid[:n]
