"""Groundedness and citation verification engine."""
from typing import List, Tuple
from src.schema import Citation, DocumentChunk

class GroundednessGuard:
    """Verifies that citations and factual claims are strictly grounded in retrieved evidence."""

    @staticmethod
    def verify_citation_quote(quote: str, chunk_content: str) -> Tuple[bool, float]:
        """Calculates token overlap and verbatim substring match."""
        if not quote or not chunk_content:
            return False, 0.0

        quote_clean = quote.strip().lower()
        content_clean = chunk_content.lower()

        # Exact substring match
        if quote_clean in content_clean:
            return True, 1.0

        # Sub-phrase token overlap match
        quote_words = set(quote_clean.split())
        content_words = set(content_clean.split())
        if not quote_words:
            return False, 0.0

        overlap = len(quote_words.intersection(content_words)) / len(quote_words)
        is_grounded = (overlap >= 0.70)
        return is_grounded, round(overlap, 3)

    def verify_answer_citations(
        self,
        citations: List[Citation],
        retrieved_chunks: List[DocumentChunk]
    ) -> Tuple[bool, float, List[str]]:
        """Audits all citations against the retrieved candidate chunks."""
        if not citations:
            return True, 1.0, []

        chunk_lookup = {c.chunk_id: c.content for c in retrieved_chunks}
        # Also map by source_id
        source_lookup = {}
        for c in retrieved_chunks:
            source_lookup.setdefault(c.source_id, []).append(c.content)

        verified_count = 0
        issues = []

        for cit in citations:
            matched_content = chunk_lookup.get(cit.chunk_id)
            if not matched_content and cit.source_id in source_lookup:
                matched_content = " ".join(source_lookup[cit.source_id])

            if not matched_content:
                issues.append(f"Citation {cit.source_id} refers to chunk {cit.chunk_id} not present in retrieved context.")
                continue

            grounded, score = self.verify_citation_quote(cit.quote, matched_content)
            if grounded:
                verified_count += 1
            else:
                issues.append(f"Citation quote '{cit.quote[:40]}...' has low overlap ({score}) with source {cit.source_id}.")

        groundedness_ratio = verified_count / max(len(citations), 1)
        passed = (groundedness_ratio >= 0.85)
        return passed, round(groundedness_ratio, 3), issues
