# Datasheet for Policy Research Corpus (Gebru et al. Format)

## 1. Motivation
- **Purpose:** To provide a curated, high-integrity mixed-format corpus for prototyping and evaluating an evidence-grounded policy research assistant tailored to Singapore's digital economy, tech workforce, and artificial intelligence governance landscape.
- **Created By:** Developed for the IMDA GenAI Engineer Technical Assessment (2026).
- **Funding & Sponsorship:** Standard open public research evaluation dataset.

---

## 2. Composition

The dataset comprises both structured statistical tables and unstructured policy whitepapers:

### 2.1 Structured Datasets (`data/raw/structured/`)
1. **`sg_digital_economy_macro.csv`**
   - *Dimensions:* 16 rows $\times$ 7 columns.
   - *Columns:* `year` (int), `metric` (str), `sector` (str), `value` (float), `unit` (str), `source` (str), `notes` (str).
   - *Metrics Covered:* Infocomm Media (ICM) Sector Value Added (VA) (2018–2023), Digital Economy Share of Singapore GDP (%), Enterprise AI Adoption Rate (%), Total ICM Operating Revenue, and Green Data Centre Capacity Targets.
   - *Provenance:* Singapore Department of Statistics (SingStat), IMDA Annual Surveys, and Energy Market Authority (EMA).

2. **`tech_talent_workforce.csv`**
   - *Dimensions:* 20 rows $\times$ 7 columns.
   - *Columns:* `year` (int), `role_category` (str), `employment_count` (int), `local_pmet_percentage` (float), `median_gross_monthly_wage_sgd` (int), `vacancy_rate_percentage` (float), `source` (str).
   - *Roles Covered:* Software Engineers, Data Scientists & AI Specialists, Cybersecurity Professionals, IT Infrastructure Engineers, Product Managers (2020–2023).
   - *Provenance:* Ministry of Manpower (MOM) & IMDA Tech Talent Surveys.

3. **`sme_digital_adoption.csv`**
   - *Dimensions:* 18 rows $\times$ 8 columns.
   - *Columns:* `sector` (str), `year` (int), `digital_solution_adoption_rate_pct` (float), `cloud_usage_pct` (float), `cybersecurity_measures_pct` (float), `ai_adoption_pct` (float), `government_grant_beneficiaries_count` (int), `source` (str).
   - *Sectors Covered:* Food & Beverage, Retail Trade, Logistics, Precision Engineering, Financial Services, Construction (2021–2023).
   - *Provenance:* IMDA SME Go Digital Programme Surveys.

### 2.2 Unstructured Policy Reports (`data/raw/unstructured/`)
1. **`sg_digital_economy_report_2024.md` (SG-DER-2024)**: Official IMDA whitepaper on macroeconomic digital growth, enterprise generative AI adoption, SME digitalization, and green data center connectivity.
2. **`national_ai_strategy_2_0.md` (SG-NAIS-2023)**: Singapore's National AI Strategy 2.0 covering the 15,000 AI practitioner target, SGD 500M compute infrastructure fund, and AI Verify governance toolkit.
3. **`ai_governance_guidelines_imda.md` (SG-PDPC-AI-2024)**: Advisory Guidelines under the PDPA on the use of personal data in AI recommendations, consent exceptions, and human-in-the-loop oversight.
4. **`policy_brief_workforce_displacement_dispute.md` (SG-WORKFORCE-DISPUTE-2024)**: Empirically divergent working paper juxtaposing IMDA/EDB projections (+22,000 net jobs) against ILRI union research (-18,500 roles displaced) to stress-test conflict reconciliation.

---

## 3. Collection Process & Data Quality Checks
- **Automated Quality Audit:** Executed via `src/ingestion/eda.py`.
- **Missing Values:** 0 missing values detected across all structured tables (`sg_digital_economy_macro.csv`, `tech_talent_workforce.csv`, `sme_digital_adoption.csv`).
- **Duplicate Records:** 0 duplicated rows.
- **Invariants Verified:**
  - `year` strictly within $[2018, 2024]$.
  - `local_pmet_percentage` bounded in $[0.0, 100.0]$.
  - `vacancy_rate_percentage` strictly non-negative.
  - Wage figures align with SingStat occupational wage distributions.

---

## 4. Preprocessing & Transformations
1. **Header Stripping & Typing:** Column names cast to lowercase snake_case; strings trimmed; numbers cast to floating-point and integers.
2. **Relational Context Chunking:** Tabular rows transformed into natural language key-value tuples grouped by metric/sector to preserve relational semantic context during hybrid retrieval.
3. **Section-Aware Whitepaper Chunking:** Markdown reports parsed by structural headings (`## Section`) with sliding windows ($140$ words, $30$-word overlap) to prevent splitting key policy clauses across boundaries.
4. **Deterministic Hash Identifiers:** Every chunk assigned an immutable hash ID (`<doc_id>_<section>_<index>_<md5_hash>`) for exact citation tracebacks.

---

## 5. Usage Constraints & Responsible Use
- **Licensing:** Published under the **Singapore Open Data Licence (v1.0)** and Open Government Policy Research Framework.
- **Privacy & Confidentiality:** Contains strictly public, synthetic, or aggregated statistical data. Zero Personally Identifiable Information (PII) or classified government security data is included.
- **Exclusions:** Does not contain defense procurement details, agricultural quotas, or individual tax filings.
