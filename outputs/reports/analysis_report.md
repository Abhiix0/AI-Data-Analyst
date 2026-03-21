# AI Data Analyst — Analysis Report

**Generated:** 2026-03-19 19:16:24
**Dataset:** `kaggle_downloads/WA_Fn-UseC_-Telco-Customer-Churn.csv`

---
## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Rows | 7,043 |
| Columns | 21 |
| Duplicate Rows | 0 |
| Missing Columns | 1 |
| Outlier Columns | 1 |

**Dataset Summary:** Dataset 'WA_Fn-UseC_-Telco-Customer-Churn' with 7,043 rows and 21 columns.

### Column Types

| Column | Type |
|--------|------|
| customerID | str |
| gender | str |
| SeniorCitizen | int64 |
| Partner | str |
| Dependents | str |
| tenure | int64 |
| PhoneService | str |
| MultipleLines | str |
| InternetService | str |
| OnlineSecurity | str |
| OnlineBackup | str |
| DeviceProtection | str |
| TechSupport | str |
| StreamingTV | str |
| StreamingMovies | str |
| Contract | str |
| PaperlessBilling | str |
| PaymentMethod | str |
| MonthlyCharges | float64 |
| TotalCharges | float64 |
| Churn | str |

---
## 2. Data Quality

### Missing Values

| Column | Missing Count | Missing % |
|--------|--------------|-----------|
| TotalCharges | 11 | 0.16% |

### Outliers

| Column | Count | % | Lower Bound | Upper Bound |
|--------|-------|---|-------------|-------------|
| SeniorCitizen | 1142 | 16.21% | 0.0 | 0.0 |

### Strong Correlations (|r| >= 0.7)

| Column A | Column B | r | Direction |
|----------|----------|---|-----------|
| tenure | TotalCharges | 0.8259 | positive |

---
## 3. Key Insights

1. Claude unavailable: Gemini API call failed: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\nPlease retry in 37.466021233s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'model': 'gemini-2.0-flash', 'location': 'global'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'model': 'gemini-2.0-flash', 'location': 'global'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '37s'}]}}

---
## 4. Recommendations

1. Claude unavailable: Gemini API call failed: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\nPlease retry in 37.318159847s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '37s'}]}}

---
## 5. Visualizations

### hist_SeniorCitizen.png
![hist_SeniorCitizen.png](../charts/hist_SeniorCitizen.png)

### hist_TotalCharges.png
![hist_TotalCharges.png](../charts/hist_TotalCharges.png)

### hist_tenure.png
![hist_tenure.png](../charts/hist_tenure.png)

### hist_MonthlyCharges.png
![hist_MonthlyCharges.png](../charts/hist_MonthlyCharges.png)

### box_SeniorCitizen.png
![box_SeniorCitizen.png](../charts/box_SeniorCitizen.png)

### scatter_tenure_vs_TotalCharges.png
![scatter_tenure_vs_TotalCharges.png](../charts/scatter_tenure_vs_TotalCharges.png)

### scatter_MonthlyCharges_vs_TotalCharges.png
![scatter_MonthlyCharges_vs_TotalCharges.png](../charts/scatter_MonthlyCharges_vs_TotalCharges.png)

### correlation_heatmap.png
![correlation_heatmap.png](../charts/correlation_heatmap.png)

### bar_gender.png
![bar_gender.png](../charts/bar_gender.png)

### bar_Partner.png
![bar_Partner.png](../charts/bar_Partner.png)

### bar_Dependents.png
![bar_Dependents.png](../charts/bar_Dependents.png)

### bar_PhoneService.png
![bar_PhoneService.png](../charts/bar_PhoneService.png)
