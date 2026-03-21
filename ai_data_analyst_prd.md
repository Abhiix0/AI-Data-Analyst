# Product Requirement Document (PRD)
# AI Data Analyst Assistant — v2.0

---

## 1. Product Summary

**AI Data Analyst Assistant** is an AI-powered data analysis tool that takes any structured dataset and automatically profiles it, generates visualizations, detects patterns and outliers, and produces human-readable insights and recommendations — all surfaced through an interactive Streamlit dashboard.

The system is built on a modular multi-agent pipeline. Each agent owns one responsibility. A central orchestrator manages execution order and data flow. The Streamlit dashboard is the primary user interface and the main deliverable.

**Core value:** Drop in a dataset → get a full analysis in seconds, no code required.

---

## 2. Goals

### Primary
- Deliver a portfolio-grade, fully functional data analysis tool
- Dashboard is the main product surface — it must look and feel professional
- AI-generated insights using Groq API (free tier, `llama-3.1-8b-instant`)
- Support CSV, Excel, and Kaggle datasets

### Non-Goals (for this version)
- No user authentication
- No database storage
- No multi-file comparison
- No natural language querying

---

## 3. Target Users

1. **Portfolio reviewers / recruiters** — primary audience, must impress
2. Students and developers doing exploratory data analysis
3. Hackathon participants needing fast dataset understanding

---

## 4. System Architecture

### 4.1 Architecture Style
- **Multi-agent modular pipeline**
- **Central orchestrator** controls execution order and passes shared context
- **Shared context object** (`AnalysisContext`) carries the DataFrame and all agent outputs through the pipeline
- Streamlit dashboard sits on top — calls the orchestrator and renders results

### 4.2 Agent Pipeline

```
User uploads dataset (via Dashboard or CLI)
            ↓
    [ Orchestrator ]
            ↓
  1. Data Loader Agent       → DataFrame
  2. Profiling Agent         → Metadata + Stats
  3. Visualization Agent     → Charts (saved + returned)
  4. Pattern Detection Agent → Correlation summaries
  5. Outlier Detection Agent → Outlier flags per column
  6. Insight Agent           → AI-generated insights (Groq API)
  7. Recommendation Agent    → Actionable suggestions
  8. Report Agent            → Markdown report
            ↓
    [ Dashboard renders all outputs ]
```

### 4.3 Shared Context Object

All agents read from and write to a single `AnalysisContext` object:

```python
AnalysisContext:
  - df: DataFrame
  - file_name: str
  - profile: dict          # from Profiling Agent
  - charts: list[Figure]   # from Visualization Agent
  - patterns: dict         # from Pattern Detection Agent
  - outliers: dict         # from Outlier Detection Agent
  - insights: list[str]    # from Insight Agent
  - recommendations: list[str]  # from Recommendation Agent
  - report_path: str       # from Report Agent
```

---

## 5. Agent Specifications

### 5.1 Data Loader Agent
**Input:** File path or Kaggle dataset reference  
**Output:** Populated `df` in AnalysisContext

Responsibilities:
- Auto-detect file type (CSV, XLSX, XLS)
- Load via Kaggle API if a Kaggle reference is provided
- Validate: reject empty files, unsupported formats
- Return clean pandas DataFrame

### 5.2 Profiling Agent
**Input:** `df`  
**Output:** `profile` dict

Captures:
- Shape (rows × columns)
- Column names and data types
- Missing value count and percentage per column
- Duplicate row count
- Descriptive statistics (mean, median, std, min, max) for numeric columns
- Value counts for top categorical columns (top 5)

### 5.3 Visualization Agent
**Input:** `df`, `profile`  
**Output:** `charts` list of matplotlib/seaborn figures

Generates (auto-selected based on data types):
- **Histograms** — all numeric columns
- **Box plots** — all numeric columns (outlier visibility)
- **Correlation heatmap** — if 2+ numeric columns exist
- **Bar charts** — top categorical columns (top 10 values)
- **Scatter plots** — top 2 highest-correlated numeric pairs

All charts saved to `outputs/charts/`. Figures also returned in context for dashboard rendering.

### 5.4 Pattern Detection Agent
**Input:** `df`, `profile`  
**Output:** `patterns` dict

Detects:
- Pearson correlation matrix
- Strong correlations (|r| > 0.7) flagged with column pairs and values
- Skewness per numeric column (flag if |skew| > 1)
- Class imbalance in categorical columns (flag if dominant category > 80%)

### 5.5 Outlier Detection Agent
**Input:** `df`  
**Output:** `outliers` dict

Method: **IQR (Interquartile Range)**
- Compute Q1, Q3, IQR per numeric column
- Flag values below Q1 - 1.5×IQR or above Q3 + 1.5×IQR
- Output: `{column_name: [outlier_values]}` + count per column

### 5.6 Insight Agent (AI-Powered)
**Input:** `profile`, `patterns`, `outliers`  
**Output:** `insights` list of strings

LLM: **Groq API** — `llama-3.1-8b-instant` (free tier)

Workflow:
1. Construct a structured stats summary from profile + patterns + outliers
2. Send to Groq with a focused system prompt
3. Parse response into a clean bullet list of 6–10 insights
4. Fallback: if API fails, generate rule-based insights from the stats

System prompt strategy:
```
You are a data analyst. Given the following dataset statistics, 
generate 6-10 concise, specific, human-readable insights. 
Focus on: correlations, anomalies, distribution issues, and notable patterns.
Return only a numbered list. No preamble.
```

### 5.7 Recommendation Agent
**Input:** `insights`, `patterns`, `outliers`, `profile`  
**Output:** `recommendations` list of strings

Rule-based generation (no LLM needed here — keeps it fast and reliable):
- High missing values → recommend imputation strategy
- Strong correlation detected → flag for multicollinearity if ML is intended
- High outlier count → recommend investigation or removal
- Class imbalance → recommend resampling if classification task
- Skewed distribution → recommend log transformation

### 5.8 Report Agent
**Input:** Full `AnalysisContext`  
**Output:** `outputs/reports/analysis_report.md`

Report structure:
```
1. Dataset Overview
2. Data Quality Issues
3. Key Statistical Findings
4. Patterns & Correlations
5. Outlier Summary
6. AI-Generated Insights
7. Recommendations
8. Visualizations (embedded references)
```

---

## 6. Dashboard Specification (Main Deliverable)

**Framework:** Streamlit  
**File:** `dashboard.py`

### 6.1 Layout

```
┌─────────────────────────────────────────┐
│  Header: AI Data Analyst Assistant      │
│  Subtitle + Upload Widget               │
├──────────┬──────────────────────────────┤
│ Sidebar  │  Main Content Area           │
│          │                              │
│ Nav:     │  [Active Section]            │
│ Overview │                              │
│ Charts   │                              │
│ Insights │                              │
│ Recs     │                              │
└──────────┴──────────────────────────────┘
```

### 6.2 Sections

**Section 1 — Dataset Overview**
- File name, shape, memory usage
- Interactive table: column | type | missing % | unique values
- Summary stats table (expandable)

**Section 2 — Interactive Charts**
- Rendered inline from `context.charts`
- Chart selector (dropdown or tabs per chart type)
- Plotly used for interactivity where possible (hover, zoom)

**Section 3 — AI Insights Panel**
- Clean card-style display of each insight
- Groq model badge + "Generated by AI" label
- Loading spinner during API call

**Section 4 — Recommendations Panel**
- Color-coded by severity (info / warning / critical)
- Each recommendation in an expandable card

**Global:**
- Download Report button → serves `analysis_report.md`
- Progress bar during pipeline execution
- Error messages displayed inline (not crashes)

---

## 7. Folder Structure

```
ai-data-analyst/
│
├── agents/
│   ├── data_loader_agent.py
│   ├── profiling_agent.py
│   ├── visualization_agent.py
│   ├── pattern_detection_agent.py
│   ├── outlier_detection_agent.py
│   ├── insight_agent.py
│   ├── recommendation_agent.py
│   └── report_agent.py
│
├── loaders/
│   ├── csv_loader.py
│   ├── excel_loader.py
│   └── kaggle_loader.py
│
├── core/
│   ├── context.py          # AnalysisContext dataclass
│   └── orchestrator.py     # Pipeline execution controller
│
├── outputs/
│   ├── charts/
│   └── reports/
│
├── dashboard.py            # Streamlit app (main entry point)
├── main.py                 # CLI entry point
├── requirements.txt
├── .env.example            # GROQ_API_KEY placeholder
└── README.md
```

---

## 8. Technology Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| Data | pandas, numpy |
| Visualization | matplotlib, seaborn, plotly |
| ML/Stats | scikit-learn, scipy |
| LLM (Insights) | Groq API — llama-3.1-8b-instant |
| Dashboard | Streamlit |
| Dataset Access | Kaggle API |
| Config | python-dotenv |

---

## 9. Configuration & Environment

`.env` file (never committed):
```
GROQ_API_KEY=your_key_here
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_kaggle_api_key
```

Setup:
```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your keys
streamlit run dashboard.py
```

---

## 10. Error Handling

| Scenario | Behavior |
|---|---|
| Unsupported file format | Show error in dashboard, stop pipeline |
| Empty dataset | Show error, prompt re-upload |
| Groq API failure | Fallback to rule-based insights, show warning |
| Kaggle API failure | Show descriptive error message |
| Corrupted file | Catch pandas read error, display message |
| No numeric columns | Skip numeric-only agents, continue pipeline |

---

## 11. Success Criteria

- [ ] Full pipeline runs end-to-end on any valid CSV/Excel dataset
- [ ] Dashboard renders all 4 sections without errors
- [ ] AI insights generated via Groq in under 5 seconds
- [ ] At least 4 charts generated per dataset
- [ ] Markdown report downloadable from dashboard
- [ ] Kaggle dataset fetch works via API
- [ ] Handles datasets up to 50MB without crashing
- [ ] Graceful error handling — no unhandled exceptions visible to user

---

## 12. Deliverables

1. `dashboard.py` — Streamlit app (primary deliverable)
2. `main.py` — CLI interface (secondary)
3. All 8 agent files
4. Orchestrator + AnalysisContext
5. Sample output: charts + markdown report
6. `README.md` with setup instructions and demo screenshots

---

## 13. Out of Scope (v1)

- User authentication
- Database persistence
- Natural language querying
- Multi-file analysis
- Automated ML modeling
- Deployment / hosting setup