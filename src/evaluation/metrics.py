"""Evaluation metrics for retrieval quality, generation groundedness, and task accuracy."""
import math
from typing import List, Set, Dict, Any
from src.schema import PolicyAnswer, DocumentChunk

class EvaluationMetrics:
    """Computes retrieval and generation metrics for policy assistant evaluation."""

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 3) -> float:
        """Recall@k: Proportion of relevant documents present in top-k."""
        if not ground_truth_ids:
            # If query is out-of-scope (no relevant docs), recall is 1.0 if system abstained
            return 1.0

        top_k_retrieved = set(retrieved_ids[:k])
        gt_set = set(ground_truth_ids)
        # Match if source filename or doc id is in retrieved
        hits = 0
        for gt in gt_set:
            if any(gt.lower() in ret.lower() or ret.lower() in gt.lower() for ret in top_k_retrieved):
                hits += 1
        return hits / len(gt_set)

    @staticmethod
    def mean_reciprocal_rank(retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
        """MRR: Reciprocal of the rank of the first relevant document."""
        if not ground_truth_ids:
            return 1.0

        for rank, ret_id in enumerate(retrieved_ids, start=1):
            if any(gt.lower() in ret_id.lower() or ret_id.lower() in gt.lower() for gt in ground_truth_ids):
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 3) -> float:
        """nDCG@k: Normalized Discounted Cumulative Gain at rank k."""
        if not ground_truth_ids:
            return 1.0

        dcg = 0.0
        for rank, ret_id in enumerate(retrieved_ids[:k], start=1):
            is_rel = 1 if any(gt.lower() in ret_id.lower() or ret_id.lower() in gt.lower() for gt in ground_truth_ids) else 0
            if is_rel:
                dcg += 1.0 / math.log2(rank + 1)

        # Ideal DCG
        ideal_hits = min(len(ground_truth_ids), k)
        idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1))
        if idcg == 0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def evaluate_groundedness(answer: PolicyAnswer, retrieved_chunks: List[DocumentChunk]) -> float:
        """Calculates factual groundedness score of citations against retrieved passages."""
        if answer.abstention and answer.abstention.is_abstained:
            return 1.0

        if not answer.citations:
            return 0.5 if answer.factual_findings else 0.8

        all_text = " ".join(c.content.lower() for c in retrieved_chunks)
        grounded_count = 0
        for cit in answer.citations:
            quote_clean = cit.quote.strip().lower()
            if quote_clean in all_text:
                grounded_count += 1
            else:
                words = set(quote_clean.split())
                if words and len(words.intersection(set(all_text.split()))) / len(words) >= 0.7:
                    grounded_count += 1

        return grounded_count / len(answer.citations)

    @staticmethod
    def evaluate_task_accuracy(answer: PolicyAnswer, expected_contains: List[str], should_abstain: bool) -> float:
        """Evaluates whether the direct answer contains expected target facts or abstains appropriately."""
        # Case 1: Should abstain
        if should_abstain:
            if answer.abstention and answer.abstention.is_abstained:
                return 1.0
            # Check text indicators
            text_lower = answer.direct_answer.lower()
            if any(term in text_lower for term in ["abstain", "outside the scope", "rejected", "guardrail", "insufficient", "ambiguous"]):
                return 1.0
            return 0.0

        # Case 2: Standard answer verification
        text = answer.direct_answer
        matches = sum(1 for exp in expected_contains if exp.lower() in text.lower())
        return 1.0 if matches >= max(1, len(expected_contains) // 2) else 0.0

    @staticmethod
    def citation_precision(answer: PolicyAnswer, expected_source: str) -> float:
        """Measures whether citations reference the true authoritative source."""
        if not answer.citations:
            return 1.0 if expected_source == "NONE" or expected_source == "GUARDRAIL" else 0.0

        hits = sum(1 for c in answer.citations if expected_source.lower() in c.source_id.lower() or expected_source.lower() in c.document_title.lower())
        return hits / len(answer.citations)
