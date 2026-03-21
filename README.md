# AI Data Analyst

> Drop any dataset. Get a complete AI-powered analysis in seconds.

A multi-agent data analysis tool built with Python and Streamlit. Upload any CSV or Excel file and get automatic dataset profiling, interactive visualizations, LLM-generated insights, prioritized recommendations, and a downloadable report — no code required.

---

## Demo

<img width="1908" height="1044" alt="Demo" src="https://github.com/user-attachments/assets/4f2c6fb3-5303-4f23-96a7-b09726d7d664" />

---

## Features

| | Feature | Description |
|---|---|---|
| 📋 | **Dataset Profiling** | Shape, types, missing values, duplicates, correlations, skewness |
| 📈 | **Interactive Charts** | Histograms, box plots, scatter plots, heatmaps — auto-selected by data type |
| 🔍 | **Outlier Detection** | IQR method across all numeric columns |
| 💡 | **AI Insights** | LLM-generated findings via Groq (`llama-3.1-8b-instant`, free tier) |
| 🎯 | **Recommendations** | Prioritized, actionable suggestions grounded in the data |
| 💬 | **Ask AI** | Chat interface — ask free-form questions about your dataset |
| 📅 | **Datetime Detection** | Auto-detects date columns, computes range, flags time-series structure |
| 📄 | **Report Export** | Full markdown report, downloadable from the dashboard |
| 🗂️ | **Kaggle Integration** | Fetch any public dataset directly via Kaggle API |

---

## Architecture

Multi-agent pipeline. Each agent owns one responsibility. A central orchestrator manages execution order and passes a shared `AnalysisContext` object through the pipeline — no agent touches another agent's output directly.

```
User Input (CSV / Excel / Kaggle)
              ↓
       [ Orchestrator ]
              ↓
  Profiling Agent          →  shape, stats, correlations, outliers, datetime
  Visualization Agent      →  chart metadata (rendered as Plotly in dashboard)
  Insight Agent            →  LLM-generated findings via Groq API
  Recommendation Agent     →  prioritized action items
  Report Agent             →  markdown report
              ↓
  Streamlit Dashboard
  [ Overview | Data Quality | Insights | Charts | Report | Ask AI ]
```

The LLM agents have a rule-based fallback — if the Groq API is unavailable, the pipeline completes using statistical findings only.

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-github-username/ai-data-analyst
cd ai-data-analyst
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_groq_key       # Free at https://console.groq.com
KAGGLE_USERNAME=your_username    # Optional — only needed for Kaggle datasets
KAGGLE_KEY=your_kaggle_api_key   # Optional
```

### 3. Run the dashboard

```bash
streamlit run dashboard.py
```

### 4. Or use the CLI

```bash
python main.py path/to/dataset.csv
python main.py kaggle:username/dataset-name
```

---

## Tech Stack

- **Python 3.10+**
- **pandas / numpy** — data processing and statistical profiling
- **Plotly** — interactive dashboard charts
- **Groq API** (`llama-3.1-8b-instant`) — LLM-powered insights
- **Streamlit** — dashboard UI
- **Kaggle API** — dataset fetching

---

## Project Structure

```
ai-data-analyst/
├── agents/
│   ├── profiling_agent.py       # Stats, correlations, outliers, datetime detection
│   ├── visualization_agent.py   # Chart metadata generation
│   ├── insight_agent.py         # Groq LLM insight generation
│   ├── recommendation_agent.py  # Actionable recommendations
│   └── report_agent.py          # Markdown report assembly
├── core/
│   └── context.py               # Shared AnalysisContext dataclass
├── llm/
│   ├── groq_client.py           # Groq API wrapper
│   └── prompts.py               # All LLM prompt builders
├── loaders/
│   ├── csv_loader.py
│   ├── excel_loader.py
│   └── kaggle_loader.py
├── outputs/
│   └── reports/                 # Generated markdown reports
├── dashboard.py                 # Streamlit app — main entry point
├── main.py                      # CLI entry point
├── orchestrator.py              # Pipeline controller
├── requirements.txt
└── .env.example
```

---

## Sample Datasets

Three datasets are included to test with immediately:

| File | Description |
|---|---|
| `kaggle_downloads/WA_Fn-UseC_-Telco-Customer-Churn.csv` | Telecom churn — good for classification insights |
| `kaggle_downloads/netflix_titles.csv` | Netflix catalog — triggers datetime detection |
| `kaggle_downloads/tested.csv` | Titanic test set — clean numeric + categorical mix |

---

## Known Limitations

- Outlier detection uses IQR only — no Z-score, Isolation Forest, or DBSCAN
- Datetime columns are profiled and described but not modeled or forecasted
- Free-tier Groq rate limits apply — on very large datasets, switch to `llama-3.3-70b-versatile` in the model selector if the 8b model truncates output

---

## License

MIT
