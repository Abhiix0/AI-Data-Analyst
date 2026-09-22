# AI Data Analyst

> **Drop any dataset. Get a complete AI-powered analysis in seconds.**

A multi-agent data analysis tool built with **Python + Streamlit**. Upload a CSV/Excel file or fetch a public Kaggle dataset and get profiling, visualizations, AI insights, recommendations, and a downloadable report, with **no code required**.

## Demo

<img width="1908" height="1044" alt="Demo" src="https://github.com/user-attachments/assets/4f2c6fb3-5303-4f23-96a7-b09726d7d664" />

## Features

* 📋 **Dataset Profiling** — shape, types, missing values, duplicates, correlations, skewness
* 📈 **Auto Visualizations** — histograms, box plots, scatter plots, heatmaps
* 🔍 **Outlier Detection** — IQR-based detection across numeric columns
* 💡 **AI Insights** — LLM-generated findings using Groq
* 🎯 **Recommendations** — prioritized, data-grounded action items
* 💬 **Ask AI** — chat with your dataset using natural language
* 📅 **Datetime Detection** — identifies date columns and time-series structure
* 📄 **Report Export** — download the complete analysis as Markdown
* 🗂️ **Kaggle Integration** — load public datasets directly from Kaggle
* 🛡️ **Fallback Mode** — analysis continues with statistical insights when the LLM is unavailable

## Architecture

The system uses a **multi-agent pipeline** with a shared `AnalysisContext`. Each agent owns a single responsibility and communicates through the orchestrator.

```text
Dataset
   ↓
Orchestrator
   ├── Profiling Agent
   ├── Visualization Agent
   ├── Insight Agent ─────→ Groq LLM
   ├── Recommendation Agent
   └── Report Agent
   ↓
Streamlit Dashboard
```

### Agents

| Agent          | Responsibility                                         |
| -------------- | ------------------------------------------------------ |
| Profiling      | Statistics, correlations, outliers, datetime detection |
| Visualization  | Generates chart metadata                               |
| Insight        | Generates LLM-powered findings                         |
| Recommendation | Converts findings into actions                         |
| Report         | Builds the final Markdown report                       |

## Quick Start

### 1. Install

```bash
git clone https://github.com/your-github-username/ai-data-analyst
cd ai-data-analyst
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=your_groq_key

# Optional: Kaggle datasets
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

### 3. Run

```bash
streamlit run dashboard.py
```

Or use the CLI:

```bash
python main.py dataset.csv
python main.py kaggle:username/dataset-name
```

## Tech Stack

**Python** · **pandas** · **NumPy** · **Plotly** · **Streamlit** · **Groq API** · **Kaggle API**

## Project Structure

```text
ai-data-analyst/
├── apps/
│   ├── web/                      # Next.js frontend application
│   └── api/                      # FastAPI backend application
├── packages/
│   ├── analytics/                # Deterministic Polars analytics & DuckDB tools
│   ├── ingestion/                # Ingestion pipeline & Parquet conversion
│   ├── agent/                    # LangGraph analytical agent & tool registry
│   ├── evidence/                 # Evidence & Finding models and strength classification
│   ├── visualization/            # Chart selection & ChartSpec models
│   ├── shared/                   # Storage clients & LLM provider abstraction
│   └── legacy/                   # Transitional bridge for original prototype modules
├── docs/                         # Architecture, API, and decision records (ADRs)
├── tests/                        # Unit, Integration, and Evaluation test suites
├── infra/                        # Docker & database migration configuration
├── data/                         # Local dataset storage cache
├── outputs/reports/              # Generated reports
├── dashboard.py                  # Streamlit dashboard
├── main.py                       # CLI entry point
└── orchestrator.py               # Pipeline controller
```

## Sample Datasets

Included datasets:

* `WA_Fn-UseC_-Telco-Customer-Churn.csv`
* `netflix_titles.csv`
* `tested.csv`

## Limitations

* Outlier detection currently uses IQR only
* Datetime columns are analyzed but not forecasted
* Groq free-tier rate limits apply

## License

MIT
