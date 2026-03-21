# AI Data Analyst — Analysis Report

**Generated:** 2026-03-21 16:22:58
**Dataset:** `layoffs`

---
## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Rows | 4,317 |
| Columns | 11 |
| Duplicate Rows | 0 |
| Missing Columns | 8 |
| Outlier Columns | 3 |

**Dataset Summary:** 4,317 rows x 11 columns

### Column Types

| Column | Type |
|--------|------|
| company | str |
| location | str |
| total_laid_off | float64 |
| date | str |
| percentage_laid_off | float64 |
| industry | str |
| source | str |
| stage | str |
| funds_raised | float64 |
| country | str |
| date_added | str |

---
## 2. Data Quality

### Missing Values

| Column | Missing Count | Missing % |
|--------|--------------|-----------|
| location | 1 | 0.02% |
| total_laid_off | 1,487 | 34.45% |
| percentage_laid_off | 1,597 | 36.99% |
| industry | 2 | 0.05% |
| source | 3 | 0.07% |
| stage | 5 | 0.12% |
| funds_raised | 491 | 11.37% |
| country | 2 | 0.05% |

### Outliers

| Column | Count | % | Lower Bound | Upper Bound |
|--------|-------|---|-------------|-------------|
| total_laid_off | 325 | 11.48% | -200.0 | 440.0 |
| percentage_laid_off | 395 | 14.52% | -0.245 | 0.675 |
| funds_raised | 428 | 11.19% | -586.5 | 1121.5 |

---
## 3. Key Insights

1. Here are the insights based on the provided dataset:
2. The dataset contains 3,588 missing values, accounting for 7.56% of all cells, which may lead to biased analysis if not properly addressed, particularly in columns like 'percentage_laid_off' with 36.99% missing values.
3. Among the missing columns, 'percentage_laid_off' is the worst, with 1597 missing values, indicating a potential data quality issue that requires attention to avoid skewing analysis results.
4. The correlation between 'total_laid_off' and 'funds_raised' is relatively weak at 0.1096, suggesting that layoffs and funding may not be directly related, contradicting conventional wisdom in the industry.
5. The 'total_laid_off' column is heavily right-skewed, with a skew of 10.6449, implying that a small number of extreme values are pulling the mean away from the median, which is 90.0.
6. The presence of 1,148 outliers across three numeric columns ('total_laid_off', 'percentage_laid_off', and 'funds_raised') indicates a need for robust analysis techniques to handle these values, particularly in columns like 'percentage_laid_off' with 14.52% outliers.
7. The 'percentage_laid_off' column has a high percentage of outliers (14.52%) and missing values (36.99%), suggesting that this column may be the most problematic in the dataset and requires careful handling.
8. Both 'total_laid_off' and 'funds_raised' columns are heavily right-skewed (skew=10.6449 and skew=20.6085, respectively), indicating that these columns may be sensitive to the presence of extreme values, which could be driving the observed correlations.
9. The 'funds_raised' column has a high standard deviation of 4557.755, indicating significant variation in the data, which may be related to the column's skewness (skew=20.6085) and the presence of outliers.
10. The top company (Amazon) accounts for 18 layoffs, followed by Google (17) and Microsoft (16), suggesting that these companies are the most affected by layoffs in the dataset.
11. The 'stage' of companies (Post-IPO) has the highest count of 1016, followed by Unknown (725) and Series B (478), indicating that post-IPO companies are the most represented in the dataset.
12. The 'country' with the highest count is the United States (2733), followed by India (332) and Canada (172), suggesting that the majority of layoffs in the dataset occur in US-based companies.
13. The 'industry' of Finance has the highest count of 509 layoffs, followed by Retail (347) and Healthcare (326), indicating that Finance is the most affected industry in the dataset.

---
## 4. Recommendations

1. Based on the dataset analysis insights, I recommend the following prioritized, concrete, and actionable recommendations:
2. Implement data quality fixes for the 'percentage_laid_off' column**: The 'percentage_laid_off' column has the highest percentage of missing values (36.99%) and outliers (14.52%), indicating a potential data quality issue. **WHO:** Data engineers and data quality team **WHAT:** Investigate and address the data quality issue by data cleaning and imputation techniques, such as mean or median imputation, or using more advanced techniques like regression imputation or machine learning-based imputation methods.
3. Develop a robust analysis plan to handle outliers in 'total_laid_off', 'percentage_laid_off', and 'funds_raised' columns**: The presence of 1,148 outliers across these columns requires careful handling to ensure accurate analysis results. **WHO:** Data scientists and analysts **WHAT:** Apply robust regression techniques, such as Huber regression or Theil-Sen estimator, to handle outliers and gain insights into the relationship between these variables.
4. Investigate the relationship between 'total_laid_off' and 'funds_raised' using advanced statistical techniques**: The weak correlation between these variables (r=0.1096) contradicts conventional wisdom and warrants further investigation. **WHO:** Data scientists and analysts **WHAT:** Apply techniques like generalized additive models (GAMs) or non-linear regression to explore the potential non-linear relationship between 'total_laid_off' and 'funds_raised'.
5. Develop a predictive model to forecast layoffs based on company characteristics**: The insights into company characteristics, such as industry (Finance), stage (Post-IPO), and location (United States), suggest opportunities for predictive modeling. **WHO:** Data scientists and analysts **WHAT:** Develop a regression-based model using company characteristics and historical data to forecast future layoffs.
6. Explore the impact of 'funds_raised' on layoffs using a more advanced analysis technique**: The high standard deviation (4557.755) and skewness (20.6085) of the 'funds_raised' column indicate potential non-linear relationships. **WHO:** Data scientists and analysts **WHAT:** Apply techniques like generalized additive models (GAMs) or non-linear regression to explore the potential non-linear relationship between 'funds_raised' and layoffs.
7. Identify the most affected companies and industries by layoffs**: The insights into top companies (Amazon, Google, Microsoft) and industries (Finance) suggest opportunities for targeted business decisions. **WHO:** Business leaders and stakeholders **WHAT:** Use the analysis results to inform business decisions, such as adjusting business strategies or providing support to affected companies and industries.
8. Develop a data dashboard to visualize key insights and monitor data quality**: The data profile summary highlights the need for a data dashboard to track missing values, outliers, and other quality metrics. **WHO:** Data engineers and data quality team **WHAT:** Develop a data dashboard using visualization tools like Tableau or Power BI to monitor data quality and provide easy access to key insights.
9. Consider data augmentation techniques to handle missing values in 'percentage_laid_off' column**: The high percentage of missing values (36.99%) in the 'percentage_laid_off' column may benefit from data augmentation techniques, such as imputation or interpolation. **WHO:** Data scientists and analysts **WHAT:** Apply data augmentation techniques to handle missing values and improve the overall quality of the 'percentage_laid_off' column.

---
## 5. Visualizations

### hist_funds_raised.png
![hist_funds_raised.png](../charts/hist_funds_raised.png)

### hist_total_laid_off.png
![hist_total_laid_off.png](../charts/hist_total_laid_off.png)

### hist_percentage_laid_off.png
![hist_percentage_laid_off.png](../charts/hist_percentage_laid_off.png)

### box_total_laid_off.png
![box_total_laid_off.png](../charts/box_total_laid_off.png)

### box_percentage_laid_off.png
![box_percentage_laid_off.png](../charts/box_percentage_laid_off.png)

### box_funds_raised.png
![box_funds_raised.png](../charts/box_funds_raised.png)

### correlation_heatmap.png
![correlation_heatmap.png](../charts/correlation_heatmap.png)

### bar_stage.png
![bar_stage.png](../charts/bar_stage.png)
