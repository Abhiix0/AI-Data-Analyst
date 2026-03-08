# AI Data Analyst

An intelligent, multi-agent data analysis system that automatically analyzes datasets and generates insights using LLM-powered reasoning with rule-based fallbacks.

## Overview

The AI Data Analyst is a production-ready pipeline that combines multiple specialized agents to perform comprehensive data analysis. The system intelligently uses LLM reasoning when available (via Ollama) and gracefully falls back to rule-based analysis when needed.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (CLI)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  orchestrator.py                            │
│  Coordinates the multi-agent analysis pipeline              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
   │  Data   │  │Analysis │  │Reasoning │  │Reporting │
   │ Agents  │  │ Agents  │  │ Agents   │  │ Agents   │
   └─────────┘  └─────────┘  └──────────┘  └──────────┘
```

### Agent Categories

#### Data Agents (`agents/data/`)
- `data_loader_agent.py` — Dataset loading orchestration
- `dataset_understanding_agent.py` — High-level dataset comprehension
- `profiling_agent.py` — Comprehensive data profiling
- `data_cleaner.py` — Data quality inspection

#### Analysis Agents (`agents/analysis/`)
- `analyst.py` — Descriptive statistical analysis
- `clustering_agent.py` — Unsupervised clustering analysis
- `anomaly_detection_agent.py` — Anomaly detection
- `feature_importance_agent.py` — Feature importance ranking
- `outlier_detection_agent.py` — Outlier identification
- `pattern_detection_agent.py` — Pattern and correlation discovery

#### Reasoning Agents (`agents/reasoning/`)
- `insight_agent.py` — LLM-powered insights with rule-based fallback
- `recommendation_agent.py` — Strategic recommendations with fallback
- `query_agent.py` — Natural language query answering

#### Reporting Agents (`agents/reporting/`)
- `report_agent.py` — Report generation
- `visualization_agent.py` — Chart and visualization creation

## Pipeline Flow

```
1. Load Dataset (CSV, Excel, or Kaggle)
         ↓
2. Dataset Understanding
         ↓
3. Data Quality Analysis
         ↓
4. Statistical Analysis
         ↓
5. Clustering Analysis
         ↓
6. Anomaly Detection
         ↓
7. Feature Importance
         ↓
8. Insight Generation (LLM/Rule-based)
         ↓
9. Structured Report Output
```

## Supported Dataset Formats

- **CSV files** (`.csv`)
- **Excel files** (`.xlsx`, `.xls`)
- **Kaggle datasets** (`kaggle:owner/dataset-name`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI-Data-Analyst
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Install Ollama for LLM-powered insights:
   - Download from https://ollama.ai
   - Pull a model: `ollama pull llama3`
   - Ensure Ollama service is running

## Usage

### Basic Analysis

Analyze a local CSV file:
```bash
python main.py data.csv
```

Analyze an Excel file:
```bash
python main.py report.xlsx
```

Analyze a Kaggle dataset:
```bash
python main.py kaggle:username/dataset-name
```

### Interactive Query Mode

After the initial analysis, the system enters an interactive Q&A mode where you can ask natural language questions about your dataset:

```
ask> What are the main patterns in this data?
ask> Which columns have the most missing values?
ask> What correlations exist between variables?
ask> exit
```

## Output Format

All agents return a standardized structure:

```python
{
    "summary": "Brief description of findings",
    "metrics": {
        "mean": ...,
        "median": ...,
        "missing_values": ...,
        # ... agent-specific metrics
    },
    "insights": [
        "Insight 1",
        "Insight 2",
        # ... actionable insights
    ]
}
```

The orchestrator combines all agent outputs into a comprehensive final report.

## Configuration

### Environment Variables

Create a `.env` file for configuration:
```
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

### LLM Configuration

The system uses Ollama by default with the `llama3` model. To customize:

1. Edit `llm/ollama_client.py` to change the default model
2. Ensure your chosen model is pulled: `ollama pull <model-name>`

## Project Structure

```
AI-Data-Analyst/
├── agents/
│   ├── data/           # Data loading and profiling
│   ├── analysis/       # Statistical and ML analysis
│   ├── reasoning/      # LLM-powered insights
│   └── reporting/      # Visualization and reports
├── llm/
│   ├── ollama_client.py    # Centralized LLM interface
│   └── prompts.py          # Reusable prompt templates
├── loaders/
│   ├── csv_loader.py
│   ├── excel_loader.py
│   └── kaggle_loader.py
├── outputs/
│   ├── charts/         # Generated visualizations
│   └── reports/        # Generated reports
├── main.py             # CLI entry point
├── orchestrator.py     # Pipeline coordinator
└── requirements.txt    # Python dependencies
```

## Development

### Adding New Agents

1. Create your agent in the appropriate category folder
2. Follow the standard output format (summary, metrics, insights)
3. Add imports to the category's `__init__.py`
4. Update `orchestrator.py` to include your agent in the pipeline

### Testing

Run the system with test datasets:
```bash
python main.py test_data.csv
python main.py tests/datasets/sample.xlsx
```

## Features

- **Automatic data quality assessment**
- **Comprehensive statistical analysis**
- **Clustering and segmentation**
- **Anomaly and outlier detection**
- **Feature importance ranking**
- **LLM-powered insights with intelligent fallback**
- **Natural language query interface**
- **Support for multiple data formats**
- **Extensible agent architecture**

## Requirements

- Python 3.8+
- pandas
- numpy
- scikit-learn
- matplotlib
- seaborn
- openpyxl (for Excel support)
- kaggle (for Kaggle dataset support)
- ollama (optional, for LLM features)

See `requirements.txt` for complete dependency list.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
