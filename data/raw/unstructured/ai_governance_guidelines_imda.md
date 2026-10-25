# Advisory Guidelines on Use of Personal Data in AI Recommendations and Decision Systems
**Author:** Personal Data Protection Commission (PDPC) & IMDA
**Publication Date:** March 2024
**Classification:** Open / Regulatory Advisory
**Doc ID:** SG-PDPC-AI-2024

## 1. Scope and Legal Baseline
These Advisory Guidelines provide operational guidance under the Personal Data Protection Act (PDPA) for organizations leveraging machine learning and generative artificial intelligence systems to make recommendations, predictions, or automated decisions affecting individuals. Organizations retain ultimate legal accountability for compliance with data protection provisions, regardless of model complexity or vendor licensing terms.

## 2. Consent, Legitimate Interests, and Business Improvement Exceptions
Organizations training or fine-tuning models on personal data may rely on the Business Improvement Exception under Section 21 of the PDPA, provided:
- The purpose cannot reasonably be achieved without using personal data in identifiable form.
- The use does not adversely affect individuals, and a reasonable person would consider the use appropriate.
- Robust data minimisation and de-identification measures are implemented prior to training.
- Synthetic data or Privacy-Enhancing Technologies (PETs) such as differential privacy must be considered where feasible.

## 3. Transparency, Explainability, and User Notifications
Organizations must adopt a risk-proportionate approach to transparency:
- **Low-impact systems** (e.g., e-commerce product recommendations): General disclosures in privacy policies suffice.
- **High-impact systems** (e.g., employment screening, credit underwriting, tenant eligibility): Organizations must provide clear, human-understandable explanations detailing the primary factors, logic, and user data influencing the automated outcome.

## 4. Human-in-the-Loop Safeguards for Automated Decisions
Where an automated AI system makes decisions that significantly affect an individual's rights, legal status, or economic livelihood:
1. **Mandatory Human Oversight:** A trained human reviewer must possess meaningful authority and operational capacity to override the model's recommendation.
2. **Hallucination and Groundedness Audits:** Generative AI solutions used for evidence synthesis or policy advice must implement traceable citation mechanisms linking every claim to an authoritative source document.
3. **Prompt Injection & Data Poisoning Controls:** Organizations must separate untrusted user inputs or retrieved third-party text from system instruction channels to mitigate indirect prompt injection risks.
