# Evidence Model & Strength Categorization

## Core Principle: No Fabricated Confidence
In traditional LLM analytical apps, the model invents explanations or guesses confidence percentages (e.g. "I am 90% confident"). In the AI Data Analyst platform, **all evidence is typed, deterministic, and computed strictly before LLM interpretation**.

An LLM interprets evidence; it does not invent numbers.

## Evidence & Finding Model

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Finding                                                                │
│ ────────────────────────────────────────────────────────────────────── │
│ id: UUID                                                               │
│ claim: "Columns 'tenure' and 'total_charges' have a strong correlation" │
│ evidence_strength: "strong" | "moderate" | "weak" | "insufficient"     │
│ source_columns: ["tenure", "total_charges"]                            │
│ dataset_version_id: UUID                                               │
│                                                                        │
│ evidence: [                                                            │
│   Evidence(                                                            │
│     metric_name="pearson_correlation",                                 │
│     value=0.8258,                                                      │
│     source_tool="calculate_correlation",                               │
│     source_columns=["tenure", "total_charges"]                         │
│   ),                                                                   │
│   Evidence(                                                            │
│     metric_name="sample_size",                                         │
│     value=7043,                                                        │
│     source_tool="calculate_correlation",                               │
│     source_columns=["tenure", "total_charges"]                         │
│   )                                                                    │
│ ]                                                                      │
└────────────────────────────────────────────────────────────────────────┘
```

## Strength Categorization Matrix

### 1. Correlation Strength (`classify_correlation_strength`)
- **Strong**: $|r| \ge 0.70$ AND $n \ge 30$
- **Moderate**: $|r| \ge 0.40$ AND $n \ge 15$
- **Weak**: $|r| < 0.40$ OR $n < 15$
- **Insufficient**: $n \le 4$ (sample too small for correlation inference)

### 2. Outlier Severity (`classify_outlier_strength`)
- **Strong**: $\ge 10\%$ outliers AND count $\ge 5$
- **Moderate**: $2.0\% - 9.99\%$ outliers
- **Weak**: $< 2.0\%$ outliers

### 3. Missingness Severity (`classify_missingness_strength`)
- **Strong**: $\ge 30\%$ null values (critical data quality concern)
- **Moderate**: $5.0\% - 29.99\%$ null values
- **Weak**: $< 5.0\%$ null values

### 4. Skewness Severity (`classify_skew_strength`)
- **Strong**: $|\text{skew}| \ge 2.0$ (highly asymmetric)
- **Moderate**: $1.0 \le |\text{skew}| < 2.0$
- **Weak**: $|\text{skew}| < 1.0$
