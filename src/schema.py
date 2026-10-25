"""Structured Pydantic schemas for evidence-grounded policy synthesis, citations, and evaluation."""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class AbstentionReason(str, Enum):
    NONE = "NONE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    ADVERSARIAL_INJECTION = "ADVERSARIAL_INJECTION"
    CONFIDENTIAL_RESTRICTION = "CONFIDENTIAL_RESTRICTION"

class UncertaintyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Citation(BaseModel):
    """Traceable citation to an authoritative passage or dataset cell."""
    source_id: str = Field(description="Document ID or Dataset filename (e.g. SG-DER-2024 or sg_digital_economy_macro.csv)")
    document_title: str = Field(description="Title of the source work")
    section: str = Field(description="Section heading or table row identifier")
    chunk_id: str = Field(description="Unique deterministic chunk identifier")
    quote: str = Field(description="Verbatim supporting text or exact numerical fact")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score in the citation match")

class CalculationStep(BaseModel):
    """Audit trail for deterministic arithmetic and numerical transformations."""
    operation: str = Field(description="e.g. CAGR, PERCENTAGE_GROWTH, RATIO, DIFFERENCE, SUM")
    expression: str = Field(description="Human readable arithmetic expression")
    inputs: Dict[str, Any] = Field(description="Raw input numbers with provenance")
    result: float = Field(description="Deterministic calculation result")
    formatted_result: str = Field(description="Result with unit (e.g. 15.0%, SGD 19.4B)")

class EvidenceConflict(BaseModel):
    """Analysis of conflicting sources or divergent empirical projections."""
    has_conflict: bool = False
    source_a: str = Field(default="", description="First authoritative source")
    claim_a: str = Field(default="", description="Claim or projection from source A")
    source_b: str = Field(default="", description="Second authoritative source")
    claim_b: str = Field(default="", description="Contradicting claim from source B")
    reconciliation_guidance: str = Field(default="", description="Analytical advice explaining underlying assumptions")

class AbstentionDetails(BaseModel):
    """Structured refusal or abstention metadata."""
    is_abstained: bool = False
    reason: AbstentionReason = AbstentionReason.NONE
    explanation: str = Field(default="", description="Clear explanation for why the system abstains or seeks clarification")

class PolicyAnswer(BaseModel):
    """Complete, evidence-grounded policy research answer."""
    query: str
    direct_answer: str = Field(description="Synthesized answer or abstention statement")
    factual_findings: List[str] = Field(default_factory=list, description="Strict factual findings verified against sources")
    model_inferences: List[str] = Field(default_factory=list, description="Analytic insights or extrapolations explicitly labeled as model inferences")
    citations: List[Citation] = Field(default_factory=list, description="Evidence citations linking back to verified text")
    calculations: List[CalculationStep] = Field(default_factory=list, description="Deterministic calculations performed by Python engine")
    conflict_analysis: Optional[EvidenceConflict] = None
    abstention: Optional[AbstentionDetails] = None
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW
    uncertainty_rationale: str = ""
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    estimated_cost_usd: float = 0.0
    guardrails_passed: bool = True
    security_flags: List[str] = Field(default_factory=list)

class DocumentChunk(BaseModel):
    """Ingested knowledge chunk with rich metadata for retrieval & citations."""
    chunk_id: str
    source_id: str
    doc_title: str
    doc_type: str  # structured_csv | policy_report | regulatory_guideline
    section: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: int = 0
