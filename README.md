# AI Data Analyst Assistant

> Drop any dataset. Get a complete AI-powered analysis in seconds.

A multi-agent data analysis tool that automatically profiles datasets, generates interactive visualizations, produces LLM-powered insights, and compiles a full report — all surfaced through a clean Streamlit dashboard.

---

## What It Does

| Feature | Description |
|---|---|
| 📋 **Dataset Profiling** | Shape, types, missing values, duplicates, stats |
| 📈 **Interactive Charts** | Histograms, box plots, scatter plots, heatmaps |
| 🔍 **Outlier Detection** | IQR method across all numeric columns |
| 💡 **AI Insights** | LLM-generated findings via Groq (free tier) |
| 🎯 **Recommendations** | Prioritized, actionable suggestions |
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
Streamlit Dashboard
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/yourusername/ai-data-analyst
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
│   ├── charts/              # Generated chart files
│   └── reports/             # Markdown reports
├── dashboard.py             # Streamlit app (main entry point)
├── main.py                  # CLI entry point
└── orchestrator.py          # Pipeline controller
```

---

## Sample Datasets

Try it with the included samples:

- `kaggle_downloads/WA_Fn-UseC_-Telco-Customer-Churn.csv` — telecom churn data
- `kaggle_downloads/netflix_titles.csv` — Netflix content catalog
- `kaggle_downloads/tested.csv` — Titanic test dataset

---

## License

MIT
