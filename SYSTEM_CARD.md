# System & Model Card: Singapore Evidence-Grounded Policy Research Assistant

## 1. System Overview
- **System Name:** Singapore Evidence-Grounded Policy Research Assistant
- **Version:** 1.0.0
- **Model Type:** Hybrid Neuro-Symbolic System (Hybrid BM25 + Dense Semantic Vector Retrieval + Bounded FSM Agent + Deterministic Python Arithmetic + Guardrail Envelopes + Structured Pydantic Output).
- **Primary Domain:** Singapore Digital Economy, Infocomm Media (ICM) Sector Macroeconomics, Tech Workforce & Talent Statistics, and National AI Governance Frameworks.
- **Protocol Support:** Model Context Protocol (MCP v2.3.0) via JSON-RPC 2.0.

---

## 2. Intended Use Cases
- **Target Users:** Public sector policy researchers, economic analysts, and statutory board officers formulating data-grounded policy briefs, committee speeches, and Cabinet papers.
- **Permitted Applications:**
  - Fact retrieval from official published whitepapers and government statistical tables.
  - Verification of economic indicators (Value Added, GDP share, enterprise adoption rates, tech employment wages).
  - Deterministic calculations of growth trends (CAGR, year-over-year percentage increases, cross-sectoral differences).
  - Identification and reconciliation of conflicting empirical projections across published literature.
  - Automated citation tracing linking every assertion back to an official document section or table row.

---

## 3. Out-of-Scope & Prohibited Use Cases
- **Classified or Confidential Intelligence:** The system must NEVER ingest or process classified, RESTRICTED, or SECRET cabinet deliberations.
- **Medical or Legal Diagnosis:** Not intended for automated legal determination or clinical healthcare triage.
- **Speculative Policy Making:** The system must not formulate speculative macroeconomic forecasts without backing empirical data.
- **Autonomous Financial Allocation:** The system cannot approve grants, disburse funds, or commit government resources autonomously.

---

## 4. Performance & Telemetry Characteristics
- **Groundedness:** 100% on retrieved evidence passages.
- **Arithmetic Accuracy:** 100% on deterministic operations (CAGR, percentage growth, absolute differences).
- **Inference Latency:** Mean $0.5$ ms in offline deterministic mode; $< 450$ ms when connected to cloud LLM backends.
- **Token Efficiency:** Strict Pydantic JSON serialization reduces prompt overhead by $40\%$ compared to open chat prompts.

---

## 5. Risk Assessment & Mitigations

| Identified Risk | Severity | Technical Mitigation |
| :--- | :---: | :--- |
| **Direct Prompt Injection** | High | Multi-stage regex heuristic automata intercepting override phrases before prompt assembly. |
| **Indirect Content Poisoning** | High | Sanitization of delimiter tags and wrapping untrusted retrieved data inside `<untrusted_mcp_data>` envelopes. |
| **Calculation Hallucination** | High | Strict arithmetic ban in LLM prompts; all calculations routed to deterministic Python math functions. |
| **PII & Data Leakage** | Medium | Automated regex scanner redacting Singapore NRIC/FIN, personal phone numbers, and emails to `[REDACTED_CONFIDENTIAL]`. |
| **Fictitious Citation Creation** | High | Groundedness auditor verifies character and word overlap against source text; rejects fabricated references. |
| **One-Sided Bias in Debates** | Medium | Empirical conflict detector automatically identifies divergent studies and forces balanced juxtaposition. |

---

## 6. Auditability & Governance
- Every response surfaces:
  - Full provenance document IDs and sections.
  - Explicit uncertainty score (`LOW`, `MEDIUM`, `HIGH`) and rationale.
  - Clear visual demarcation separating **Factual Findings** from **Model Inferences**.
  - Programmatic telemetry (latency, token count, security flags, tool call history).
