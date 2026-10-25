"""Configuration and hyperparameter management for Evidence-Grounded Policy Assistant."""
from pathlib import Path
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STRUCTURED_DATA_DIR = RAW_DATA_DIR / "structured"
UNSTRUCTURED_DATA_DIR = RAW_DATA_DIR / "unstructured"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EVALUATION_DATA_DIR = DATA_DIR / "evaluation"

class RetrievalConfig(BaseModel):
    """Retrieval pipeline hyperparameters."""
    chunk_size_words: int = 140
    chunk_overlap_words: int = 30
    top_k: int = 4
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    hybrid_alpha: float = 0.55  # Weight given to dense semantic retrieval (1-alpha to BM25)
    rerank_top_n: int = 3
    min_relevance_threshold: float = 0.12

class AgentConfig(BaseModel):
    """Agent workflow and execution limits."""
    max_steps: int = 5
    max_retries_per_tool: int = 3
    timeout_seconds: float = 15.0
    deterministic_calc_only: bool = True
    require_human_confirmation_for_write: bool = True

class ModelConfig(BaseModel):
    """LLM generation settings."""
    model_name: str = "policy-grounded-evaluator-v1"
    temperature: float = 0.0  # Zero temperature for deterministic grounded synthesis
    top_p: float = 1.0
    max_output_tokens: int = 1024
    random_seed: int = 42

class SecurityConfig(BaseModel):
    """Responsible AI, guardrails and PII settings."""
    enable_prompt_injection_guard: bool = True
    enable_pii_redaction: bool = True
    enable_untrusted_content_isolation: bool = True
    pii_redaction_token: str = "[REDACTED_CONFIDENTIAL]"

class AppConfig(BaseModel):
    """Root application configuration."""
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

CONFIG = AppConfig()
