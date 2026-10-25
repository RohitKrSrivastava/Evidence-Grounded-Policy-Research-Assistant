# Exploratory Data Analysis & Data Quality Report

## 1. Data Quality and Schema Verification

| Dataset | Rows | Columns | Missing Values | Duplicate Rows |
|---------|------|---------|----------------|----------------|
| macro_indicators | 16 | 7 | False | 0 |
| tech_talent | 20 | 7 | False | 0 |
| sme_adoption | 18 | 8 | False | 0 |

## 2. Key Analytical Findings & Visualizations

### Finding 1: Non-Linear Acceleration in Enterprise AI Adoption (2020-2023)

Enterprise AI adoption more than tripled from 14.2% in 2020 to 44.0% in 2023. Concurrently, ICM Value Added grew from SGD 25.4B to SGD 38.6B (+52.0%), reflecting surging productivity and commercial deployment across enterprise workflows.

```text
AI Adoption Trajectory (% of Enterprises adopting AI):
2020 | [====] 14.2%
2021 | [=======] 22.5%
2022 | [==========] 31.8%
2023 | [============== ] 44.0%
```

### Finding 2: Deep Tech Wage Divergence and Rapid Expansion in AI Roles

Data Scientists & AI Specialists experienced the highest headcount expansion (+104.2% from 12,000 to 24,500) and highest median monthly wage increase (+41.7% from SGD 7,200 to SGD 10,200). In contrast, IT Infrastructure roles grew more moderately (+23.4% headcount, +27.6% wage), highlighting shifting national demand towards generative and analytical capabilities.

```text
Tech Wage Growth (2020 -> 2023 Median Gross Monthly SGD):
Data Science & AI:   $7,200 -> $10,200 (+41.7%) [===================]
Software Engineers:  $6,500 -> $8,600  (+32.3%) [==============]
Cybersecurity:       $6,800 -> $9,100  (+33.8%) [===============]
Product & Digital:   $7,500 -> $9,800  (+30.7%) [==============] 
IT Infrastructure:   $5,800 -> $7,400  (+27.6%) [============]
```

### Finding 3: SME Sectoral Digital Divide in AI Readiness

While Financial Services SMEs lead with 56.0% AI adoption and 98.1% general digital solutions, traditional sectors lag behind: Food & Beverage (14.8% AI) and Construction (11.5% AI). This indicates targeted interventions are needed for low-margin service sectors.

