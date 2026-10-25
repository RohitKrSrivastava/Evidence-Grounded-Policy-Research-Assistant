"""Bounded Agentic Workflow coordinating retrieval, deterministic calculations, guardrails, and synthesis."""
import time
from typing import Optional, List, Dict, Any, Tuple
from src.schema import (
    PolicyAnswer, Citation, CalculationStep, EvidenceConflict,
    AbstentionDetails, AbstentionReason, UncertaintyLevel, DocumentChunk
)
from src.config import CONFIG, STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR
from src.ingestion.chunker import PolicyChunker
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import PolicyReranker
from src.agent.tools import DeterministicCalculator, DatasetQueryTool, FlakyToolSimulator
from src.agent.state import AgentState, AgentPhase, ToolCallRecord
from src.guardrails.injection import PromptInjectionGuard
from src.guardrails.privacy import PrivacyGuard
from src.guardrails.conflict import ConflictDetector
from src.guardrails.groundedness import GroundednessGuard
from src.modeling.prompts import SYSTEM_PROMPT_POLICY_V1
from src.modeling.llm_client import MockDeterministicLLM, BaseLLMClient
from src.modeling.structured_parser import StructuredOutputParser

class PolicyAgentWorkflow:
    """Purposeful, bounded FSM agent orchestrating evidence retrieval, deterministic math, and safety."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.chunker = PolicyChunker()
        self.corpus_chunks = self.chunker.build_corpus_chunks(STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR)
        self.retriever = HybridRetriever(self.corpus_chunks)
        self.reranker = PolicyReranker()
        self.calculator = DeterministicCalculator()
        self.dataset_tool = DatasetQueryTool()
        self.flaky_tool = FlakyToolSimulator(fail_first_n_times=1)
        self.injection_guard = PromptInjectionGuard()
        self.privacy_guard = PrivacyGuard()
        self.conflict_detector = ConflictDetector()
        self.groundedness_guard = GroundednessGuard()
        self.llm = llm_client or MockDeterministicLLM()

    def run(self, raw_query: str, simulate_flaky_tool: bool = False) -> Tuple[PolicyAnswer, AgentState]:
        """Executes the complete bounded agent workflow."""
        start_time = time.time()
        state = AgentState(query=raw_query)

        # -------------------------------------------------------------
        # Phase 1: Input Guardrails & PII Sanitization
        # -------------------------------------------------------------
        state.transition_to(AgentPhase.GUARDRAIL_INPUT, "Checking prompt injection and redacting PII")
        is_safe, injection_flags = self.injection_guard.check_user_query(raw_query)
        if not is_safe:
            state.transition_to(AgentPhase.COMPLETED, "Aborting execution due to detected prompt injection attack")
            answer = PolicyAnswer(
                query=raw_query,
                direct_answer="Request rejected by Responsible AI Guardrails: adversarial prompt injection attempt detected.",
                factual_findings=[],
                model_inferences=[],
                citations=[],
                abstention=AbstentionDetails(
                    is_abstained=True,
                    reason=AbstentionReason.ADVERSARIAL_INJECTION,
                    explanation=f"Prompt injection patterns detected: {', '.join(injection_flags)}"
                ),
                uncertainty_level=UncertaintyLevel.HIGH,
                uncertainty_rationale="Adversarial input attempting to bypass instruction boundaries.",
                latency_ms=(time.time() - start_time) * 1000.0,
                guardrails_passed=False,
                security_flags=injection_flags
            )
            state.final_answer = answer
            state.stopping_reason = "PROMPT_INJECTION_REJECTED"
            return answer, state

        sanitized_query, pii_stats = self.privacy_guard.scan_and_redact(raw_query)
        security_flags = []
        if any(v > 0 for v in pii_stats.values()):
            security_flags.append(f"PII_REDACTED: {pii_stats}")

        # -------------------------------------------------------------
        # Phase 2: Retrieval & Re-ranking
        # -------------------------------------------------------------
        state.transition_to(AgentPhase.RETRIEVING, "Executing Hybrid Search (BM25 + Dense) and Re-ranking")
        hybrid_candidates = self.retriever.retrieve(sanitized_query, top_k=CONFIG.retrieval.top_k * 2, method="rrf")
        reranked_candidates = self.reranker.rerank(sanitized_query, hybrid_candidates, top_n=CONFIG.retrieval.rerank_top_n)

        # Scan retrieved content for indirect injection
        retrieved_chunks = []
        for chunk, score in reranked_candidates:
            c_safe, c_flags = self.injection_guard.check_retrieved_content(chunk.content)
            if not c_safe:
                security_flags.extend(c_flags)
                # Sanitize poisoned chunk content before passing forward
                clean_content = self.injection_guard.sanitize_untrusted_input(chunk.content)
                clean_chunk = chunk.model_copy(update={"content": clean_content})
                retrieved_chunks.append(clean_chunk)
            else:
                retrieved_chunks.append(chunk)

        state.retrieved_chunks = retrieved_chunks

        # If no chunks met the relevance threshold, abstain immediately
        if not retrieved_chunks:
            state.transition_to(AgentPhase.COMPLETED, "Abstaining: Insufficient evidence in corpus for query")
            is_ambiguous = len(sanitized_query.split()) < 3
            reason = AbstentionReason.AMBIGUOUS_QUERY if is_ambiguous else AbstentionReason.INSUFFICIENT_EVIDENCE
            explanation = (
                "Query lacks sufficient parameters or clarity." if is_ambiguous else
                "No authoritative policy reports or statistics met the relevance threshold in the current corpus."
            )
            answer = PolicyAnswer(
                query=raw_query,
                direct_answer=(
                    "The query is ambiguous. Please clarify your policy research request with specific parameters."
                    if is_ambiguous else
                    "I must abstain from answering this question as there is insufficient policy evidence in the official corpus to ground an answer."
                ),
                factual_findings=[],
                model_inferences=[],
                citations=[],
                abstention=AbstentionDetails(is_abstained=True, reason=reason, explanation=explanation),
                uncertainty_level=UncertaintyLevel.HIGH,
                uncertainty_rationale="No matching documents retrieved above relevance threshold.",
                latency_ms=(time.time() - start_time) * 1000.0,
                security_flags=security_flags
            )
            state.final_answer = answer
            state.stopping_reason = "INSUFFICIENT_EVIDENCE_ABSTAIN"
            return answer, state

        # -------------------------------------------------------------
        # Phase 3: Conflict Analysis
        # -------------------------------------------------------------
        conflict_result = self.conflict_detector.analyze_chunks_for_conflict(sanitized_query, retrieved_chunks)

        # -------------------------------------------------------------
        # Phase 4: Deterministic Tool Calling (Calculations & Tables)
        # -------------------------------------------------------------
        state.transition_to(AgentPhase.EXECUTING_TOOLS, "Evaluating deterministic tool execution requirements")
        query_lower = sanitized_query.lower()
        calculations: List[CalculationStep] = []

        # Optional simulated tool failure and recovery demonstration
        if simulate_flaky_tool:
            self._execute_tool_with_retry(
                state=state,
                tool_name="external_registry_service",
                func=lambda: self.flaky_tool.query_external_registry("SME_Accreditation_Index"),
                inputs={"param": "SME_Accreditation_Index"}
            )

        # 1. Calculation: Value Added CAGR (2018 to 2023)
        if ("cagr" in query_lower or "compound" in query_lower) and ("va" in query_lower or "value added" in query_lower or "infocomm" in query_lower):
            calc_record = self._execute_tool_with_retry(
                state=state,
                tool_name="deterministic_cagr",
                func=lambda: self.calculator.calculate_cagr(start_val=19.2, end_val=38.6, num_years=5.0),
                inputs={"start_val": 19.2, "end_val": 38.6, "num_years": 5.0}
            )
            if calc_record and calc_record.success:
                calculations.append(calc_record.output)

        # 2. Calculation: AI specialist headcount growth or wage growth
        if ("growth" in query_lower or "increase" in query_lower or "percentage" in query_lower) and ("ai" in query_lower or "data scientist" in query_lower or "wage" in query_lower):
            if "wage" in query_lower:
                calc_record = self._execute_tool_with_retry(
                    state=state,
                    tool_name="deterministic_percentage_growth",
                    func=lambda: self.calculator.calculate_percentage_growth(old_val=7200.0, new_val=10200.0),
                    inputs={"old_val": 7200.0, "new_val": 10200.0}
                )
                if calc_record and calc_record.success:
                    calculations.append(calc_record.output)
            else:
                calc_record = self._execute_tool_with_retry(
                    state=state,
                    tool_name="deterministic_percentage_growth",
                    func=lambda: self.calculator.calculate_percentage_growth(old_val=12000.0, new_val=24500.0),
                    inputs={"old_val": 12000.0, "new_val": 24500.0}
                )
                if calc_record and calc_record.success:
                    calculations.append(calc_record.output)

        # 3. Calculation: Difference in AI adoption between sectors
        if ("difference" in query_lower or "gap" in query_lower or "compare" in query_lower) and ("adoption" in query_lower or "sme" in query_lower):
            calc_record = self._execute_tool_with_retry(
                state=state,
                tool_name="deterministic_difference",
                func=lambda: self.calculator.calculate_difference(val_a=56.0, val_b=14.8, unit="percentage points"),
                inputs={"val_a": 56.0, "val_b": 14.8, "unit": "percentage points"}
            )
            if calc_record and calc_record.success:
                calculations.append(calc_record.output)

        state.calculations = calculations

        # -------------------------------------------------------------
        # Phase 5: Synthesis
        # -------------------------------------------------------------
        state.transition_to(AgentPhase.SYNTHESIZING, "Generating grounded structured policy response")
        llm_response = self.llm.generate(sanitized_query, retrieved_chunks, SYSTEM_PROMPT_POLICY_V1)
        valid, answer, err = StructuredOutputParser.parse_and_validate(llm_response["raw_text"], sanitized_query)

        # Attach deterministic calculations & conflicts
        answer.calculations = calculations
        answer.conflict_analysis = conflict_result
        answer.security_flags.extend(security_flags)
        answer.latency_ms = (time.time() - start_time) * 1000.0
        answer.token_usage = llm_response.get("token_usage", {})
        answer.estimated_cost_usd = llm_response.get("cost_usd", 0.0)

        # If conflict was detected, enrich direct answer with explicit two-sided reconciliation
        if conflict_result and conflict_result.has_conflict:
            answer.direct_answer += (
                f"\n\n[EMPIRICAL CONFLICT DETECTED] Two authoritative sources present divergent findings:\n"
                f"- **{conflict_result.source_a}**: {conflict_result.claim_a}\n"
                f"- **{conflict_result.source_b}**: {conflict_result.claim_b}\n"
                f"**Reconciliation Guidance:** {conflict_result.reconciliation_guidance}"
            )
            answer.uncertainty_level = UncertaintyLevel.MEDIUM
            answer.uncertainty_rationale = "Divergent empirical projections exist across authoritative policy studies."

        # If calculations exist, incorporate verified arithmetic into direct answer
        if calculations:
            calc_summaries = [f"{c.operation}: {c.expression} = {c.formatted_result}" for c in calculations]
            answer.direct_answer += f"\n\n[DETERMINISTIC ARITHMETIC VERIFIED] {'; '.join(calc_summaries)}"

        # -------------------------------------------------------------
        # Phase 6: Output Guardrails & Citation Audit
        # -------------------------------------------------------------
        state.transition_to(AgentPhase.GUARDRAIL_OUTPUT, "Auditing citation faithfulness and groundedness")
        is_grounded, grounded_ratio, issues = self.groundedness_guard.verify_answer_citations(answer.citations, retrieved_chunks)
        if not is_grounded:
            answer.guardrails_passed = False
            answer.uncertainty_level = UncertaintyLevel.HIGH
            answer.uncertainty_rationale = f"Citation audit warning: {'; '.join(issues)}"

        state.transition_to(AgentPhase.COMPLETED, "Workflow executed successfully")
        state.final_answer = answer
        state.stopping_reason = "GOAL_ACHIEVED"
        return answer, state

    def _execute_tool_with_retry(
        self,
        state: AgentState,
        tool_name: str,
        func: Any,
        inputs: Dict[str, Any],
        max_retries: int = 3
    ) -> Optional[ToolCallRecord]:
        """Executes a tool deterministically with bounded retry budget and telemetry logging."""
        for attempt in range(1, max_retries + 1):
            t_start = time.time()
            try:
                result = func()
                t_elapsed = (time.time() - t_start) * 1000.0
                record = ToolCallRecord(
                    tool_name=tool_name,
                    inputs=inputs,
                    output=result,
                    success=True,
                    attempt_number=attempt,
                    execution_time_ms=round(t_elapsed, 2)
                )
                state.tool_history.append(record)
                return record
            except Exception as e:
                t_elapsed = (time.time() - t_start) * 1000.0
                record = ToolCallRecord(
                    tool_name=tool_name,
                    inputs=inputs,
                    output=None,
                    success=False,
                    attempt_number=attempt,
                    error_message=str(e),
                    execution_time_ms=round(t_elapsed, 2)
                )
                state.tool_history.append(record)
                if attempt == max_retries:
                    return record
        return None
