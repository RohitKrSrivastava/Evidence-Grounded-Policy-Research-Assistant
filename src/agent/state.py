"""Agent state machine and execution telemetry."""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.schema import DocumentChunk, Citation, CalculationStep, PolicyAnswer

class AgentPhase(str, Enum):
    IDLE = "IDLE"
    GUARDRAIL_INPUT = "GUARDRAIL_INPUT"
    INTENT_ROUTING = "INTENT_ROUTING"
    RETRIEVING = "RETRIEVING"
    EXECUTING_TOOLS = "EXECUTING_TOOLS"
    SYNTHESIZING = "SYNTHESIZING"
    GUARDRAIL_OUTPUT = "GUARDRAIL_OUTPUT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ToolCallRecord(BaseModel):
    """Audit log of individual tool invocations."""
    tool_name: str
    inputs: Dict[str, Any]
    output: Any
    success: bool
    attempt_number: int
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

class StateTransition(BaseModel):
    """Tracks state changes throughout the bounded workflow."""
    from_phase: AgentPhase
    to_phase: AgentPhase
    reason: str
    timestamp_step: int

class AgentState(BaseModel):
    """Observable state machine for the policy research agent."""
    query: str
    current_phase: AgentPhase = AgentPhase.IDLE
    step_count: int = 0
    max_steps: int = 6
    transitions: List[StateTransition] = Field(default_factory=list)
    tool_history: List[ToolCallRecord] = Field(default_factory=list)
    retrieved_chunks: List[DocumentChunk] = Field(default_factory=list)
    calculations: List[CalculationStep] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    final_answer: Optional[PolicyAnswer] = None
    stopping_reason: str = ""
    is_terminal: bool = False

    def transition_to(self, new_phase: AgentPhase, reason: str = ""):
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.step_count += 1
        self.transitions.append(StateTransition(
            from_phase=old_phase,
            to_phase=new_phase,
            reason=reason,
            timestamp_step=self.step_count
        ))
        if new_phase in (AgentPhase.COMPLETED, AgentPhase.FAILED):
            self.is_terminal = True
