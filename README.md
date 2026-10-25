# Evidence-Grounded Policy Research Assistant
### IMDA GenAI Engineer Technical Assessment (Sections 1 & 2)

An evidence-grounded policy intelligence assistant engineered for government policy researchers and economic analysts. Built to ingest mixed-format government statistics and strategy whitepapers, retrieve traceable evidence, execute deterministic calculations without arithmetic hallucination, handle empirical conflict, and resist adversarial prompt injection.

---

## 🌟 Key Highlights & Engineering Features

- **Mixed-Format Ingestion:** Ingests structured time-series CSVs (ICM Value Added, tech talent wages, SME digital adoption) and unstructured policy whitepapers (Singapore Digital Economy Report, National AI Strategy 2.0, PDPC AI Governance Guidelines, Workforce Displacement Dispute Brief).
- **Dual-Track Hybrid Retrieval:** Combines Okapi BM25 keyword matching with dense continuous semantic vectors using Reciprocal Rank Fusion (RRF: $k=60$) and cross-attribute re-ranking.
- **Deterministic Math Engine:** Explicitly forbids arithmetic in LLM prompt space. Routes CAGR, percentages, ratios, and differences to Python math functions, attaching complete audit expressions to outputs.
- **Principled Abstention & Conflict Handling:** Prunes low-relevance queries to abstain on out-of-scope or ambiguous questions without hallucination. Detects empirical contradictions across studies and provides balanced reconciliation.
- **Model Context Protocol (MCP v2.3.0):** Native MCP server exposing tools (`calculate_growth_rate`, `query_policy_statistics`, `verify_citation`) and resources (`policy://...`) over JSON-RPC 2.0, protected by untrusted payload isolation security envelopes.
- **Comprehensive Responsible AI Guardrails:** Blocks direct prompt injection attacks, redacts Singapore NRIC and PII (`[REDACTED_CONFIDENTIAL]`), and audits citation faithfulness.
- **Full Empirical Evaluation Suite:** 35-case benchmark stratified across 5 operational categories, comparing baseline vs advanced RAG across Recall@3, MRR, nDCG@3, Groundedness, and Task Accuracy.

---

## 📁 Repository Structure

```text
GenAI Engineer/
├── data/
│   ├── raw/
│   │   ├── structured/                 # Official tabular CSVs (Macro indicators, tech workforce, SME adoption)
│   │   └── unstructured/               # Markdown policy reports (SG-DER-2024, SG-NAIS-2023, PDPC, Dispute Brief)
│   ├── processed/                      # EDA report, benchmark JSON results, and indices
│   └── evaluation/
│       ├── test_cases_35.json          # 35 stratified benchmark test cases
│       ├── dev_split.json              # 10 development cases (leakage prevention)
│       └── eval_split.json             # 25 strictly held-out evaluation cases
├── src/
│   ├── config.py                       # Pinned configurations, random seeds, hyperparameters
│   ├── schema.py                       # Pydantic schemas (PolicyAnswer, Citation, CalculationStep, Conflict)
│   ├── ingestion/                      # CSV/Markdown parser, section-aware chunker, automated EDA
│   ├── retrieval/                      # Okapi BM25, Dense semantic retriever, Hybrid RRF, Policy reranker
│   ├── modeling/                       # Unified LLM abstraction, versioned prompts, Pydantic parser
│   ├── agent/                          # Bounded FSM workflow, deterministic math tools, observable state
│   ├── guardrails/                     # Prompt injection guard, PII redactor, conflict detector, citation verifier
│   ├── mcp/                            # MCP Server, MCP Client, JSON-RPC 2.0, security envelope
│   └── evaluation/                     # Metrics (Recall, MRR, nDCG, Groundedness), benchmark runner, human review
├── tests/                              # Pytest suite (32 unit, integration, and scenario tests)
├── notebooks/                          # Interactive Jupyter walkthrough notebook
├── cli.py                              # Interactive & scriptable Command-Line Interface
├── api.py                              # Lightweight FastAPI application with Swagger UI (/docs)
├── run_scenarios.py                    # Runner for all 10 Minimum Demonstration Scenarios
├── run_experiments.py                  # Benchmark comparison runner (Config A Baseline vs Config B Advanced RAG)
├── requirements.txt                    # Pinned package dependencies
├── pytest.ini                          # Pytest configuration
├── ARCHITECTURE.md                     # System architecture, data flow, Mermaid diagrams, threat model
├── DATASHEET.md                        # Gebru-style dataset documentation (provenance, schema, cleaning)
├── EVALUATION_REPORT.md                # Benchmark results, metric definitions, error analysis, failure modes
├── SYSTEM_CARD.md                      # Model/System Card (intended use, boundaries, safety, mitigations)
├── LIVE_DEMO_SCRIPT.md                 # 20-minute live demonstration script with timings & talking points
├── GENAI_CONCEPTS.md                   # Section 1.8 GenAI Concepts & Technology comprehensive deep-dive
└── INNOVATION_ASSESSMENT.md            # Section 2 Innovation Assessment (scaling in secure government environments)
```

---

## 🚀 Quickstart & Setup Guide

### 1. Environment Preparation
```bash
# Navigate to repository directory
cd "d:\workspace\IMDA\GenAI Engineer"

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # On Windows PowerShell

# Install pinned dependencies
pip install -r requirements.txt
```

### 2. Verify Installation via Automated Tests
Run the comprehensive test suite (32 automated unit, integration, and guardrail tests):
```bash
pytest -v
```

---

## 🎯 Running the 10 Minimum Demonstration Scenarios

The assessment requires demonstrating 10 specific operational scenarios. Run the automated scenario runner:
```bash
python run_scenarios.py
```

| # | Scenario | Demonstrated Capability |
| :-: | :--- | :--- |
| **1** | Factual Question Answering | Traceable citations referencing `SG-DER-2024` with exact section and quote. |
| **2** | Cross-Source Synthesis | Synthesizes enterprise AI adoption ($44\%$) with National AI Strategy talent targets. |
| **3** | Deterministic Calculation | Computes Value Added CAGR ($14.99\%$) via Python math with complete formula step. |
| **4** | Principled Abstention | Detects ungrounded query (agricultural rice quotas) and cleanly abstains with `UncertaintyLevel.HIGH`. |
| **5** | Conflicting Empirical Sources | Juxtaposes IMDA ($+22,000$ jobs) vs ILRI ($-18,500$ displaced) with methodological notes. |
| **6** | Prompt Injection Defense | Blocks direct prompt injection attacks at input boundary with security alert. |
| **7** | Tool Failure Recovery | Demonstrates retry limit and graceful recovery from simulated external tool timeout. |
| **8** | MCP Tool Invocation | Discovers tools, executes `calculate_growth_rate`, and wraps payload in security envelope. |
| **9** | MCP Error & Timeout Rejection | Rejects invalid negative inputs with code `-32602` and handles client timeout safely. |
| **10**| Poisoned MCP Output Defense | Detects and strips malicious instructions embedded inside untrusted MCP payloads. |

---

## 📊 Running the Controlled Empirical Benchmark (35 Cases)

To execute the controlled comparison between **Config A (Keyword Baseline)** and **Config B (Advanced Policy Assistant)** across the 35 stratified benchmark cases:
```bash
python run_experiments.py
```
This evaluates Recall@3, MRR, nDCG@3, Groundedness, Task Accuracy, Citation Precision, and Latency, saving the results to `data/processed/benchmark_comparison_results.json`.

---

## 💻 Interactive Usage

### 1. Command-Line Interface (CLI)
Ask any analytical policy research question:
```bash
# Query single question
python cli.py query "What was the Value Added generated by Singapore's Infocomm Media sector in 2023?"

# Launch interactive REPL session
python cli.py
```

### 2. Lightweight FastAPI REST API
Launch the API server with interactive Swagger documentation:
```bash
python api.py
```
Open **http://127.0.0.1:8000/docs** in your browser to interact with:
- `POST /query`: Submit policy questions and receive validated `PolicyAnswer` JSON.
- `GET /health`: Inspect corpus chunk count and service status.
- `GET /benchmark`: Retrieve full 35-case benchmark evaluation metrics.
- `GET /mcp/capabilities`: Inspect discovered MCP tools and resources.

### 3. Interactive Jupyter Notebook
Open `notebooks/policy_assistant_walkthrough.ipynb` in your IDE or Jupyter for a step-by-step interactive demonstration.

---

## 📚 Technical Documentation Index

For comprehensive details, refer to the dedicated specification documents:
- [ARCHITECTURE.md](file:///d:/workspace/IMDA/GenAI%20Engineer/ARCHITECTURE.md): System architecture, Mermaid diagrams, FSM state machine, threat model.
- [DATASHEET.md](file:///d:/workspace/IMDA/GenAI%20Engineer/DATASHEET.md): Gebru-style dataset provenance, schemas, transformations, and cleaning.
- [EVALUATION_REPORT.md](file:///d:/workspace/IMDA/GenAI%20Engineer/EVALUATION_REPORT.md): 35-case benchmark results, error analysis, and failure taxonomy.
- [SYSTEM_CARD.md](file:///d:/workspace/IMDA/GenAI%20Engineer/SYSTEM_CARD.md): Scope, boundaries, performance, and risk mitigations.
- [LIVE_DEMO_SCRIPT.md](file:///d:/workspace/IMDA/GenAI%20Engineer/LIVE_DEMO_SCRIPT.md): 20-minute presentation guide with talking points and commands.
- [GENAI_CONCEPTS.md](file:///d:/workspace/IMDA/GenAI%20Engineer/GENAI_CONCEPTS.md): Conceptual deep-dive covering all 7 GenAI technology pillars.
- [INNOVATION_ASSESSMENT.md](file:///d:/workspace/IMDA/GenAI%20Engineer/INNOVATION_ASSESSMENT.md): Section 2 Innovation Assessment on government scaling.

---

## 🔒 Limitations & Responsible Use Notes

1. **Corpus Boundaries:** The system is strictly grounded in the provided Singapore digital economy and AI governance documents. It will deliberately abstain on queries outside this scope.
2. **Deterministic Mode:** The system runs in fully deterministic, reproducible offline mode by default (zero paid API keys required). If a live frontier LLM is desired, set `GEMINI_API_KEY` or `OPENAI_API_KEY` in your environment.
3. **Government Security Notice:** This prototype is intended for public-release policy analysis. Do not upload classified, personal, or confidential information to external services.
