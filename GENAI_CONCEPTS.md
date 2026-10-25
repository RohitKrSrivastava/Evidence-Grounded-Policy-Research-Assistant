# GenAI Engineering Foundations: Concepts, Architectures, and Trade-Offs

This technical reference provides an in-depth examination of the core applied machine learning, retrieval, agentic systems, protocol, and production concepts underpinning the Evidence-Grounded Policy Research Assistant.

---

## 1. LLM Fundamentals & Model Mechanics

### 1.1 Tokenisation & Context Windows
- **Tokenisation Mechanics:** Modern Large Language Models operate over discrete tokens generated via algorithms like Byte-Pair Encoding (BPE) or WordPiece. A token is not equivalent to a word: in English policy prose, $1,000$ words typically corresponds to $\approx 1,300 - 1,400$ tokens. Numbers, acronyms (e.g. `IMDA`, `PDPA`, `NAIS`), and special punctuation often fracture into multiple sub-tokens, impacting both inference latency and representation quality.
- **Context Windows & Attention Complexity:** Self-attention scales quadratically $\mathcal{O}(N^2)$ with sequence length $N$ in standard Transformer architectures (or $\mathcal{O}(N)$ in FlashAttention / linear approximations). As context windows expand from $8\text{k}$ to $1\text{M}+$ tokens, models encounter the *"Lost in the Middle"* degradation: retrieval accuracy drops when critical evidence passages are buried in the center of long contexts rather than near the prompt boundaries.
- **Engineering Trade-off:** Packing massive raw documents directly into long-context LLMs incurs excessive token costs, high time-to-first-token (TTFT) latency, and increased hallucination risk. A targeted, hybrid retrieval architecture that retrieves $3 - 5$ high-relevance chunks ($500 - 1,500$ tokens total) consistently outperforms brute-force long-context feeding in groundedness and latency.

### 1.2 Sampling Controls & Determinism
- **Temperature ($T$):** Modulates the softmax probability distribution over vocabulary logits:
  $$P(w_i) = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$
  For evidence-grounded policy synthesis, temperature must be set to **$T = 0.0$** (greedy decoding / argmax), ensuring deterministic, reproducible outputs across repeated evaluations.
- **Top-$p$ (Nucleus Sampling):** Selects tokens from the smallest cumulative probability mass $p$. For factual compliance, $p = 1.0$ when $T = 0.0$.
- **Seed Pinning:** While API providers expose random seeds (e.g. `seed=42`), floating-point non-determinism across distributed GPU kernels (CUDA thread scheduling) can still introduce subtle variations. Bounded deterministic systems isolate calculations in Python rather than relying on LLM internal sampling.

### 1.3 Structured Generation & Common Failure Modes
- **Constrained Decoding & Grammar Masking:** Standard LLMs generate unconstrained free text. Enforcing JSON or Pydantic schemas via grammar-guided decoding (e.g., JSON schema regex or logit masking) guarantees syntactically valid payloads at the token generation layer.
- **Common Failure Modes in Policy Tasks:**
  1. *Arithmetic Hallucination:* LLMs predict numerical tokens based on statistical co-occurrence rather than calculating arithmetic, frequently erring on compound growth, percentages, and subtractions.
  2. *Citation Fabrication:* Inventing fictitious authors, years, or document titles to satisfy prompt pressure.
  3. *Overconfidence on OOD Queries:* Fabricating plausible-sounding answers for out-of-distribution queries rather than abstaining.

---

## 2. Embeddings and Retrieval Architectures

### 2.1 Similarity Metrics
- **Cosine Similarity:**
  $$\text{Cosine}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
  Measures angular alignment in vector space, invariant to text length when vectors are L2-normalized.
- **Dot Product & Euclidean Distance:** Equivalent to cosine similarity under unit normalization, but dot products can bias toward longer text chunks if vectors are unnormalized.

### 2.2 Chunking Strategies & Provenance
- **Fixed-Size Chunking:** Simple windowing (e.g. 200 words) frequently cuts sentences or policy clauses in half, destroying grammatical and semantic cohesion.
- **Structural / Section-Aware Chunking:** Segments text at structural Markdown headings (`## Header`), preserving semantic units.
- **Provenance Metadata:** Every chunk must maintain an immutable schema: `chunk_id`, `source_id`, `doc_title`, `doc_type`, `section`, `row_metadata`, and `word_count`.

### 2.3 Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
- **Keyword (BM25) vs Dense Semantic Retrieval:**
  - *BM25:* Excels at exact numerical terms, acronyms (`SG-DER-2024`, `PUE 1.3`), and unique entity IDs. Fails on synonyms or semantic paraphrase.
  - *Dense Embeddings:* Excels at conceptual semantics (`economic expansion`, `talent development`), but can miss exact keyword anchors or numerical matches.
- **Reciprocal Rank Fusion (RRF):** Merges disparate ranking lists without requiring score calibration:
  $$\text{RRF\_Score}(d) = \sum_{m \in \mathcal{M}} \frac{1}{k + \text{rank}_m(d)} \quad (k=60)$$
- **Re-ranking Layer:** Candidate chunks from hybrid search are passed through a cross-attribute re-ranker evaluating substantive term overlap, section title relevance, and numerical density.

### 2.4 Retrieval vs. Generation Error Disentanglement
When a RAG system outputs an erroneous answer, error analysis must isolate the failure stage:
1. *Retrieval Failure:* The relevant passage was not retrieved into top-$k$ context (low Recall@k).
2. *Context Packing Failure:* Relevant passage was retrieved but pruned by context window limits or re-ranking thresholds.
3. *Comprehension / Synthesis Failure:* The passage was present in context, but the LLM misread the numbers or prioritized parametric memory.
4. *Guardrail Failure:* An invalid answer bypassed output verification.

---

## 3. Prompt and Context Engineering

### 3.1 Instruction Hierarchy & Boundary Security
To withstand prompt injection and adversarial attacks, prompts must establish a strict instruction hierarchy:
- **Level 1 (System Invariants):** Safety, untrusted data boundary rules, and refusal criteria that cannot be overridden by user or retrieved content.
- **Level 2 (Grounding Invariants):** Mandatory citations, prohibition against arithmetic in prompt space, and explicit abstention mandates.
- **Level 3 (Task Directives):** User query intent synthesis.
- **Level 4 (Untrusted Content):** Retrieved documents encapsulated inside clear boundaries (`<untrusted_content>...</untrusted_content>`).

### 3.2 Few-Shot In-Context Examples
Providing $1 - 2$ complete demonstrations of input context $\rightarrow$ verified reasoning $\rightarrow$ structured JSON output anchors the model's output formatting and calibrates citation style.

### 3.3 Prompt Versioning and Context Caching
- **Prompt Versioning:** All prompts must be tracked in version control as software code (`SYSTEM_PROMPT_POLICY_V1`), enabling regression testing across changes.
- **Prefix / Context Caching:** Frontier model APIs (e.g. Gemini, Anthropic) support prompt caching for invariant system instructions and corpus prefixes, reducing input latency by up to $80\%$ and costs by up to $50\%$.

---

## 4. Evaluation Methodologies & Error Analysis

### 4.1 Offline vs. Online Evaluation
- **Offline Evaluation:** Run against standardized, frozen benchmark test sets (e.g., our 35-case suite) to measure Recall@k, MRR, nDCG@k, and groundedness before code deployment.
- **Online Evaluation:** Continuously monitors live production traffic, collecting telemetry on latency, user thumbs up/down, citation click-through rates, and abstention frequencies.

### 4.2 Deterministic vs. Model-Based Judges (LLM-as-a-Judge)
- **Deterministic Judges:** Unit tests, exact substring matches, mathematical formula checkers, regex validations. 100% reproducible and fast, but rigid for open semantic synthesis.
- **Model-Based Judges:** Using a frontier LLM (e.g. GPT-4o or Gemini Pro) to score answer relevance and faithfulness on a 1–5 scale.
- **Judge Biases:**
  - *Position Bias:* Favoring the first option in pairwise comparisons.
  - *Verbosity Bias:* Preferring longer, wordy answers over concise, accurate ones.
  - *Self-Enhancement Bias:* Systemic tendency to rate responses from the same model family higher.
- **Mitigation:** Calibrate model judges against human double-blind audits, measuring inter-annotator agreement (Cohen's Kappa $\kappa \ge 0.80$).

### 4.3 Test-Set Leakage Prevention
Ensuring zero contamination between development tuning and benchmark scoring. Our system enforces a strict partition between `dev_split.json` (10 cases) and `eval_split.json` (25 cases).

---

## 5. Agentic Systems & Orchestration Patterns

### 5.1 Workflow vs. Agent Design
- **Autonomous Multi-Agent Swarms:** Unbounded agents communicating freely often suffer from compounding non-determinism, circular delegation, state explosion, and runaway token costs.
- **Bounded Workflow / Finite State Machine (FSM):** A structured, single-agent FSM with deterministic state transitions (`Plan -> Retrieve -> Tool Execution -> Synthesize -> Guardrail`) provides:
  - Predictable execution bounds (max steps, timeouts)
  - Explicit retry budgets
  - Complete execution telemetry and auditability.

### 5.2 Deterministic Tool Calling & Idempotency
- **Separation of Concerns:** The LLM serves purely as a semantic router and synthesizer. All quantitative transformations (CAGR, percentages, ratios) run in deterministic Python functions.
- **Idempotency:** Tool calls (e.g. database lookups, calculation functions) are idempotent, allowing safe retries upon network or transient timeout failures without side effects.

---

## 6. Model Context Protocol (MCP)

### 6.1 Roles & Protocol Mechanics
The **Model Context Protocol (MCP)**, open-sourced by Anthropic, standardizes how AI applications discover and consume tools and context from external data providers:
- **Host / Client:** The agent runtime (`PolicyMCPClient`) that discovers capabilities, initiates JSON-RPC 2.0 requests, and integrates results into reasoning.
- **Server:** A lightweight daemon (`PolicyMCPServer`) exposing:
  - *Tools:* Executable functions with JSON schemas (`query_policy_statistics`, `calculate_growth_rate`).
  - *Resources:* Read-only documents/data feeds addressed via custom URIs (`policy://statistics/digital_economy_2024`).
  - *Prompts:* Reusable prompt templates (`policy_synthesis_prompt`).

### 6.2 MCP vs. Direct API Integration Trade-offs

| Dimension | Model Context Protocol (MCP) | Direct Hardcoded Function / REST API |
| :--- | :--- | :--- |
| **Interoperability** | Universal JSON-RPC 2.0 interface; works across any MCP-compliant client (IDE, CLI, Agent). | Tightly coupled to specific codebase or proprietary SDK. |
| **Capability Discovery**| Dynamic reflection via `tools/list` and `resources/list`. | Static compile-time binding. |
| **Security Boundaries** | Uniform schema validation, authorization envelopes, and untrusted payload isolation. | Ad-hoc per-endpoint validation; variable security standards. |
| **Latency Overhead** | Minor serialization / IPC overhead ($\approx 1 - 2$ ms). | Direct in-memory function call ($< 0.1$ ms). |
| **Architectural Choice**| Preferred for enterprise ecosystems, multi-tool sharing, and extensible statutory data services. | Preferred for tightly-coupled, ultra-low-latency internal mathematical primitives. |

### 6.3 Security Boundaries for MCP
External MCP servers represent untrusted external boundaries. Our implementation enforces:
1. Wrap all tool/resource payloads in `<untrusted_mcp_data>` security envelopes.
2. Scan tool outputs for embedded prompt injection commands (`Ignore previous instructions`).
3. Enforce client-side timeouts (e.g., $2.0$ seconds) and reject invalid argument payloads before transmission.

---

## 7. Production Engineering Considerations

### 7.1 Observability & Telemetry
Every transaction produces an immutable telemetry trace capturing:
- End-to-end latency (ms) decomposed by subsystem (retrieval, tool execution, LLM synthesis, guardrails).
- Token usage (prompt tokens, completion tokens, total tokens) and estimated USD cost.
- State transitions and tool retry history.
- Active security flags and redaction counts.

### 7.2 Rate Limits, Fallbacks & Model Routing
- **Tiered Model Routing:** Routing simple factual lookups to lightweight, low-cost models (or offline deterministic extraction) and complex multi-hop synthesis to frontier models.
- **Circuit Breakers & Graceful Degradation:** If an external LLM API encounters rate limits (HTTP 429) or service outages (HTTP 503), the agent falls back to offline deterministic rule-and-knowledge extractors, ensuring zero service disruption for critical policy queries.
