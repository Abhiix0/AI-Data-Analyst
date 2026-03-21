# AI Data Analyst Assistant

> Drop any dataset. Get a complete AI-powered analysis in seconds.

A multi-agent data analysis tool that automatically profiles datasets, generates interactive visualizations, produces LLM-powered insights, and compiles a full report — all surfaced through a clean Streamlit dashboard.

---

## Demo

![Dashboard Screenshot](docs/screenshot.png)

> TODO: Add a screenshot of the running dashboard here. Run `streamlit run dashboard.py`, upload a dataset, and capture the result.

---

## What It Does

| Feature | Description |
|---|---|
| 📋 **Dataset Profiling** | Shape, types, missing values, duplicates, stats |
| 📈 **Interactive Charts** | Histograms, box plots, scatter plots, heatmaps |
| 🔍 **Outlier Detection** | IQR method across all numeric columns |
| 💡 **AI Insights** | LLM-generated findings via Groq (free tier) |
| 🎯 **Recommendations** | Prioritized, actionable suggestions |
| 💬 **Chat Interface** | Ask free-form questions about your dataset |
| 📄 **Report Export** | Full markdown report, downloadable from dashboard |
| 🗂️ **Kaggle Integration** | Fetch datasets directly via Kaggle API |

---

## Architecture

Multi-agent pipeline. Each agent owns one responsibility. Central orchestrator manages execution order.

```
Dataset Input
      ↓
 Orchestrator
      ↓
Profiling Agent → Visualization Agent → Insight Agent → Recommendation Agent → Report Agent
      ↓
Streamlit Dashboard (6 tabs: Overview, Data Quality, Insights, Charts, Report, Ask AI)
```

## Why This Architecture?

Each agent is a single-responsibility module — profiling never touches LLM calls, and the LLM agents never touch raw data. This separation makes the system easy to test, swap, and extend: you can replace the Groq client with any other LLM provider without touching the agents, or add a new agent (e.g. forecasting) without modifying existing ones. The orchestrator acts as a thin coordinator, which means pipeline failures in one agent are isolated and don't cascade. This design mirrors production ML pipelines and is intentionally resume-worthy because it demonstrates system thinking, not just scripting.

---

## Quick Start

### 1. Clone and install

```bash
# TODO: replace "your-github-username" with your actual GitHub username
git clone https://github.com/your-github-username/ai-data-analyst
cd ai-data-analyst
pip install -r requirements.txt
```

### 2. Set up API keys

```bash
cp .env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=your_groq_key      # Free at https://console.groq.com
KAGGLE_USERNAME=your_username   # Optional — only for Kaggle datasets
KAGGLE_KEY=your_kaggle_key      # Optional
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
- **pandas / numpy** — data processing
- **plotly / matplotlib / seaborn** — visualization
- **Groq API** (llama-3.1-8b-instant) — AI insights
- **Streamlit** — dashboard
- **Kaggle API** — dataset fetching

---

## Project Structure

```
ai-data-analyst/
├── agents/                  # Specialized analysis agents
│   ├── profiling_agent.py
│   ├── visualization_agent.py
│   ├── insight_agent.py
│   ├── recommendation_agent.py
│   └── report_agent.py
├── core/
│   └── context.py           # Shared AnalysisContext dataclass
├── llm/
│   ├── groq_client.py       # Groq API wrapper
│   └── prompts.py           # All LLM prompts
├── loaders/                 # CSV, Excel, Kaggle loaders
├── outputs/
│   └── reports/             # Markdown reports
├── dashboard.py             # Streamlit app (main entry point)
├── main.py                  # CLI entry point
└── orchestrator.py          # Pipeline controller
```

---

## Sample Datasets

Try it with the included samples:

- `kaggle_downloads/WA_Fn-UseC_-Telco-Customer-Churn.csv` — telecom churn data
- `kaggle_downloads/netflix_titles.csv` — Netflix content catalog (has datetime columns)
- `kaggle_downloads/tested.csv` — Titanic test dataset

---

## Known Limitations

- Outlier detection uses IQR only — no Z-score, isolation forest, or DBSCAN options
- No time-series forecasting — datetime columns are profiled but not modeled
- Free-tier Groq rate limits apply — large datasets may hit token limits on the 8b model; switch to a larger model in the sidebar if needed

---

## License

MIT
