## AI Data Analyst — Phase 1 (Stabilization & Architecture)

This project is an early-stage **AI Data Analyst** system. The goal is to
provide a clean, minimal foundation for an automated agent that can:

- **load a dataset**
- **inspect data quality**
- **compute basic statistics**
- **generate high-level insights using a local LLM (Ollama)**

Phase 1 focuses on stabilization and architecture, not exhaustive analysis.

---

### Folder Structure

- **`main.py`**: CLI entry point. Accepts a dataset path and prints a final structured report.
- **`orchestrator.py`**: Coordinates the Phase 1 pipeline  
  `dataset → data_cleaner → analyst → insight_agent → final result`
- **`agents/`**:
  - `data_cleaner.py`: inspects missing values and duplicate rows
  - `analyst.py`: computes simple descriptive statistics
  - `insight_agent.py`: LLM-powered insight generation + legacy class-based agent
  - other `agents/*.py` files: richer, later-phase capabilities (profiling, patterns, etc.)
- **`llm/`**:
  - `ollama_client.py`: centralized wrapper around the Ollama Python API
  - `prompts.py`: reusable prompt builders and system prompts
- **`loaders/`**:
  - `csv_loader.py`, `excel_loader.py`, `kaggle_loader.py`: thin helpers for loading data

All LLM calls go through `llm/ollama_client.py`. All higher-level prompts
are defined in `llm/prompts.py`.

---

### Standard Agent Output Format

Phase 1 agents (`data_cleaner`, `analyst`, and the function-based entrypoint
in `insight_agent`) all return a **structured dictionary**:

```python
{
    "summary": "short explanation of what was discovered",
    "metrics": {
        "mean": ...,
        "median": ...,
        "missing_values": ...
    },
    "insights": [
        "Insight 1",
        "Insight 2",
    ],
}
```

The orchestrator combines these into a final report with the same top-level
shape (`summary`, `metrics`, `insights`).

---

### Running the Phase 1 Pipeline

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

2. **Install and run Ollama** (for LLM-powered insights):

- Install Ollama from `https://ollama.ai`
- Pull a model (e.g. `llama3`)
- Ensure the Ollama service is running

3. **Run the CLI**:

```bash
python main.py path/to/data.csv
# or
python main.py kaggle:owner/dataset-name
```

You will see a pretty-printed JSON report containing:

- a high-level **summary**
- nested **metrics** (data cleaning + analysis)
- combined **insights** from all Phase 1 agents

---

### Next Steps (Beyond Phase 1)

The existing agents in `agents/` (profiling, pattern detection, outlier
detection, recommendations, reporting, etc.) can be gradually migrated to
the same standardized output format and plugged into the orchestrator as
the system grows.

