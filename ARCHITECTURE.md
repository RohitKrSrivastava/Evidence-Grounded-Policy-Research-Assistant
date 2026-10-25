# Architecture & Technical Design: Evidence-Grounded Policy Research Assistant

## 1. Executive Summary & Design Philosophy
The **Evidence-Grounded Policy Research Assistant** is engineered for public sector policy analysts and economic researchers who synthesize multi-source government statistics, regulatory frameworks, and strategy whitepapers. 

The system prioritizes **grounded truth, verifiable citations, deterministic computation, and responsible AI guardrails** over superficial generation fluency. It replaces unconstrained LLM hallucinations with a bounded, observable Finite State Machine (FSM) architecture integrated with the standard Model Context Protocol (MCP).

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    UserQuery["User Policy Query / API Request"] --> IngressGuard["Input Guardrail Layer"]
    
    subgraph Guardrails ["1. Safety & Privacy Boundary"]
        IngressGuard --> InjectionCheck{"Prompt Injection Detector"}
        InjectionCheck -- "Adversarial Pattern" --> AbortSafe["Fast Rejection: Security Alert"]
        InjectionCheck -- "Safe Query" --> PIIRedact["PII Scanner & Redactor (NRIC, Email, Phone)"]
    end
    
    subgraph RetrievalEngine ["2. Hybrid Ingestion & Retrieval Pipeline"]
        PIIRedact --> QueryAnalysis["Topical & Entity Extractor"]
        QueryAnalysis --> BM25["Okapi BM25 Keyword Search"]
        QueryAnalysis --> DenseVector["Dense Semantic Vector Space (Cosine Similarity)"]
        BM25 --> RRF["Reciprocal Rank Fusion (RRF: k=60)"]
        DenseVector --> RRF
        RRF --> Reranker["Cross-Attribute Re-ranker & Metadata Filter"]
        Reranker --> RelThreshold{"Relevance Threshold (min=0.12)"}
        RelThreshold -- "Below Threshold" --> AbstainInsufficient["Principled Abstention (Insufficient Evidence)"]
        RelThreshold -- "Pass" --> CleanPassages["Retrieved Corpus Passages"]
    end

    subgraph AgenticCore ["3. Bounded FSM Agent & Deterministic Tools"]
        CleanPassages --> StateRouter["Agent State Router"]
        StateRouter --> ConflictCheck{"Contradiction Detector"}
        ConflictCheck -- "Divergent Studies" --> ReconcileEngine["Juxtaposition & Empirical Reconciliation"]
        
        StateRouter --> MathRouter{"Requires Quantitative Math?"}
        MathRouter -- "Yes (CAGR, %, Diff, Ratio)" --> PythonMathEngine["Deterministic Python Calculator (Zero Hallucination)"]
        MathRouter -- "No" --> LLMSynthesis["Grounded LLM Synthesis Engine"]
        PythonMathEngine --> LLMSynthesis
        ReconcileEngine --> LLMSynthesis
    end

    subgraph MCPServerSub ["4. Model Context Protocol (MCP) Integration"]
        MCPServer["MCP Server (JSON-RPC 2.0)"] <--> MCPClient["MCP Client with Schema Validation"]
        MCPClient --> SecurityEnvelope["Untrusted Payload Isolation Envelope"]
        SecurityEnvelope --> LLMSynthesis
    end

    subgraph OutputGuardrails ["5. Output Verification & Audit"]
        LLMSynthesis --> CitationAuditor["Citation Groundedness Verifier"]
        CitationAuditor --> PydanticValidator["Structured Schema Enforcement (PolicyAnswer)"]
        PydanticValidator --> StructuredOutput["Verified Policy Answer + Audit Trail"]
    end
```

---

## 3. Data Flow & Subsystem Breakdown

### 3.1 Input Guardrail Subsystem
- **Direct Prompt Injection Guard:** Employs regex heuristic automata and instruction boundary checks to detect jailbreak payloads (e.g., `DAN`, `Ignore previous instructions`, `Developer Mode`).
- **Privacy & PII Redactor:** Uses compiled regex recognizers for Singapore National Registration Identity Card (NRIC/FIN: `[STFGM]\d{7}[A-Z]`), Singapore phone numbers (`+65 6/8/9...`), and sensitive enterprise API tokens, redacting them to `[REDACTED_CONFIDENTIAL]` before ingestion into retrieval or reasoning layers.

### 3.2 Ingestion & Hybrid Retrieval Pipeline
- **Mixed-Format Corpus:**
  - *Structured Tables:* Ingests tabular CSVs (Macro digital indicators, tech workforce wage distributions, SME adoption surveys) and transforms rows into semantically enriched relational blocks preserving provenance headers.
  - *Unstructured Whitepapers:* Ingests markdown/text policy reports (`SG-DER-2024`, `SG-NAIS-2023`, `SG-PDPC-AI-2024`, `SG-WORKFORCE-DISPUTE-2024`), segmenting by structural sections (`## Section Heading`) and word-bounded sliding windows.
- **Dual-Track Retrieval:**
  - *Okapi BM25:* Deterministic inverse document frequency with Robertson-Spärck Jones weighting ($k_1=1.5, b=0.75$) and domain stopword filtering.
  - *Dense Semantic Retrieval:* Subword n-gram vector projection with L2 normalization and continuous cosine similarity matrix dot products.
  - *Reciprocal Rank Fusion (RRF):*
    $$\text{RRF}(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{1}{60 + \text{rank}_m(d)}$$
  - *Re-ranking & Strict Abstention:* Evaluates substantive keyword coverage (excluding meta-instruction verbs like *calculate*, *query*, *synthesize*). If substantive term coverage is $< 40\%$ or relevance score $< 0.12$, candidates are pruned, triggering principled abstention.

### 3.3 Bounded Agentic Workflow (Finite State Machine)
Rather than deploying autonomous, non-deterministic multi-agent swarms, the system implements a **bounded, single-agent Finite State Machine (FSM)**:

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> GUARDRAIL_INPUT : Receive Query
    GUARDRAIL_INPUT --> COMPLETED : Direct Injection Detected (Abstain)
    GUARDRAIL_INPUT --> RETRIEVING : Input Safe & PII Redacted
    RETRIEVING --> COMPLETED : Score < Threshold (Abstain)
    RETRIEVING --> EXECUTING_TOOLS : Candidates Pass Relevance Check
    EXECUTING_TOOLS --> EXECUTING_TOOLS : Tool Failure (Retry up to 3x)
    EXECUTING_TOOLS --> SYNTHESIZING : Tools Succeeded or Retries Exhausted
    SYNTHESIZING --> GUARDRAIL_OUTPUT : Raw Policy JSON Generated
    GUARDRAIL_OUTPUT --> COMPLETED : Grounded Citations & Schema Verified
    COMPLETED --> [*]
```

#### Deterministic Tool Execution Policy:
- **No LLM Arithmetic:** The LLM is explicitly forbidden from performing CAGR, percentages, ratios, or subtraction in prompt space.
- All calculations are delegated to the `DeterministicCalculator` in Python, returning a cryptographically verifiable `CalculationStep` containing:
  - Exact human-readable expression
  - Raw inputs and provenance
  - Deterministic floating-point result formatted with correct units.

### 3.4 Model Context Protocol (MCP) Architecture
The system integrates a compliant MCP server (`src/mcp/server.py`) and protocol client (`src/mcp/client.py`) implementing JSON-RPC 2.0:

```mermaid
sequenceDiagram
    participant LLMAgent as Policy Agent Core
    participant MCPClient as MCP Client
    participant SecEnv as Security Envelope
    participant MCPServer as MCP Server
    
    LLMAgent->>MCPClient: initialize()
    MCPClient->>MCPServer: {"method": "initialize", "protocolVersion": "2024-11-05"}
    MCPServer-->>MCPClient: {"capabilities": {"tools": {...}, "resources": {...}}}
    
    LLMAgent->>MCPClient: call_tool("calculate_growth_rate", args)
    MCPClient->>MCPServer: {"method": "tools/call", "params": {"name": "calculate_growth_rate", "arguments": args}}
    MCPServer-->>MCPClient: {"result": {"content": [{"type": "text", "text": "{\"cagr\": 14.99}"}]}}
    
    MCPClient->>SecEnv: inspect_and_wrap(raw_text)
    Note over SecEnv: Scans for embedded injection commands & wraps in untrusted boundary
    SecEnv-->>MCPClient: <untrusted_mcp_data origin='tool:calc'>...</untrusted_mcp_data>
    MCPClient-->>LLMAgent: Verified Structured Tool Result
```

---

## 4. Security & Trust Boundaries

| Boundary | Threat Vector | Mitigation Mechanism |
| :--- | :--- | :--- |
| **Ingress Boundary** | Direct Prompt Injection & Jailbreaks | Regex pattern matching against known override tokens; canary token validation. |
| **Privacy Boundary** | PII / Confidential Data Leaks | Pre-retrieval redaction of Singapore NRIC, phone numbers, emails, and credentials. |
| **Retrieval Boundary** | Indirect Data Poisoning in Corpus | Sanitization of delimiter tags (`<script>`, ````system```) and post-retrieval injection scan. |
| **Tool Execution Boundary** | Unsafe Code Execution (`eval`/OS commands) | Pure deterministic Python functions with strict Pydantic input schemas; zero arbitrary shell invocation. |
| **MCP Integration Boundary** | Malicious / Compromised MCP Servers | Isolation of all MCP outputs inside `<untrusted_mcp_data>` tags; explicit user confirmation for write operations. |
| **Generation Boundary** | Number / Citation Hallucination | Groundedness audit requiring token quote overlap $\ge 70\%$; Pydantic schema validation. |

---

## 5. Technology Stack & Architectural Justification

- **Language:** Python 3.14 (pinned dependencies)
- **Data Validation & Schemas:** Pydantic v2 (enforces strict typing, field invariants, and programmatic JSON serialization)
- **Protocol Interoperability:** Model Context Protocol (MCP v2.3.0) via JSON-RPC 2.0
- **Vector & Matrix Operations:** NumPy (cosine similarity dot products, L2 normalization)
- **Structured Data Processing:** Pandas (data quality audit, missing value checks, tabular pivots)
- **Testing & Verification:** Pytest (32 automated unit, integration, and scenario tests)
- **CLI & Visualization:** Rich & Tabulate (colorized telemetry, ASCII trend charts, and structured tables)
- **API Engine:** FastAPI & Uvicorn (lightweight RESTful endpoints with OpenAPI/Swagger documentation)
