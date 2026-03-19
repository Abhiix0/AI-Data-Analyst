# AI Data Analyst

An intelligent, multi-agent data analysis system that automatically analyzes datasets and generates insights using LLM-powered reasoning with rule-based fallbacks.

## Project Overview

The AI Data Analyst is a production-ready pipeline that combines multiple specialized agents to perform comprehensive data analysis. The system intelligently uses LLM reasoning when available (via Ollama) and gracefully falls back to rule-based analysis when the LLM service is unavailable.

## System Architecture

```
main.py (CLI Entry Point)
    ↓
orchestrator.py (Pipeline Coordinator)
    ↓
┌───────────────────────────────────────────────────────┐
│              Multi-Agent Pipeline                      │
├───────────────────────────────────────────────────────┤
│  1. Dataset Understanding Agent                        │
│  2. Data Cleaner Agent                                 │
│  3. Statistical Analyst Agent                          │
│  4. Clustering Agent                                   │
│  5. Anomaly Detection Agent                            │
│  6. Feature Importance Agent                           │
│  7. Insight Agent (LLM/Rule-based)                     │
└───────────────────────────────────────────────────────┘
    ↓
Structured JSON Report + Interactive Q&A Mode
```

### Agent Descriptions

- **Dataset Understanding Agent**: Infers dataset domain, business context, and analysis objectives
- **Data Cleaner**: Inspects data quality, missing values, and duplicates
- **Analyst**: Computes descriptive statistics (mean, median, std, correlations)
- **Clustering Agent**: Performs unsupervised clustering analysis
- **Anomaly Detection Agent**: Identifies anomalous patterns in the data
- **Feature Importance Agent**: Ranks features by importance
- **Insight Agent**: Generates human-readable insights (LLM-powered with rule-based fallback)
- **Query Agent**: Answers natural language questions about the dataset
- **Recommendation Agent**: Provides strategic recommendations
- **Visualization Agent**: Creates charts and visualizations
- **Report Agent**: Generates comprehensive analysis reports

## Pipeline Steps

1. **Load Dataset** — CSV, Excel, or Kaggle dataset
2. **Dataset Understanding** — Infer domain and business context
3. **Data Quality Analysis** — Check for missing values, duplicates
4. **Statistical Analysis** — Compute descriptive statistics
5. **Clustering Analysis** — Identify natural groupings
6. **Anomaly Detection** — Find unusual patterns
7. **Feature Importance** — Rank feature significance
8. **Insight Generation** — Generate actionable insights
9. **Report Output** — Structured JSON report
10. **Interactive Q&A** — Ask questions about your data

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

# On Windows:
.venv\Scripts\activate

# On Linux/Mac:
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Install Ollama for LLM-powered insights:
   - Download from https://ollama.ai
   - Pull a model: `ollama pull llama3`
   - Ensure Ollama service is running
   - **Note**: The system works without Ollama using rule-based fallbacks

## Usage

### Basic Analysis

Analyze a local CSV file:
```bash
python main.py dataset.csv
```

Analyze an Excel file:
```bash
python main.py report.xlsx
```

Analyze a Kaggle dataset:
```bash
python main.py kaggle:uciml/iris
```

### Test Mode (Non-Interactive)

Run the pipeline without entering interactive Q&A mode:
```bash
python main.py dataset.csv --test
```

This is useful for:
- Automated testing
- CI/CD pipelines
- Batch processing

### Interactive Query Mode

After the initial analysis, the system enters an interactive Q&A mode where you can ask natural language questions about your dataset:

```
ask> What are the main patterns in this data?
ask> Which columns have the most missing values?
ask> What correlations exist between variables?
ask> exit
```

Type `exit`, `quit`, or press `Ctrl+C` to leave the interactive mode.

## Example Usage

```bash
# Analyze a CSV file
python main.py test_data.csv

# Analyze an Excel file in test mode
python main.py test_messy_data.xlsx --test

# Download and analyze a Kaggle dataset
python main.py kaggle:uciml/iris
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

Create a `.env` file for Kaggle API configuration:
```
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

### LLM Configuration

The system uses Ollama by default with the `llama3` model. The LLM client includes:
- Automatic timeout handling (5 seconds)
- Graceful fallback to rule-based analysis
- Thread-safe execution

If Ollama is not available, all agents automatically use rule-based logic.

## Project Structure

```
AI-Data-Analyst/
├── agents/
│   ├── analyst.py                      # Statistical analysis
│   ├── anomaly_detection_agent.py      # Anomaly detection
│   ├── clustering_agent.py             # Clustering analysis
│   ├── data_cleaner.py                 # Data quality inspection
│   ├── data_loader_agent.py            # Data loading orchestration
│   ├── dataset_understanding_agent.py  # Dataset comprehension
│   ├── feature_importance_agent.py     # Feature ranking
│   ├── insight_agent.py                # Insight generation
│   ├── outlier_detection_agent.py      # Outlier identification
│   ├── pattern_detection_agent.py      # Pattern discovery
│   ├── profiling_agent.py              # Data profiling
│   ├── query_agent.py                  # Natural language queries
│   ├── recommendation_agent.py         # Strategic recommendations
│   ├── report_agent.py                 # Report generation
│   └── visualization_agent.py          # Chart creation
├── llm/
│   ├── ollama_client.py                # Centralized LLM interface
│   └── prompts.py                      # Reusable prompt templates
├── loaders/
│   ├── csv_loader.py                   # CSV file loader
│   ├── excel_loader.py                 # Excel file loader
│   └── kaggle_loader.py                # Kaggle dataset loader
├── outputs/
│   ├── charts/                         # Generated visualizations
│   └── reports/                        # Generated reports
├── kaggle_downloads/                   # Downloaded Kaggle datasets
├── main.py                             # CLI entry point
├── orchestrator.py                     # Pipeline coordinator
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## Features

- **Automatic data quality assessment**
- **Comprehensive statistical analysis**
- **Clustering and segmentation**
- **Anomaly and outlier detection**
- **Feature importance ranking**
- **LLM-powered insights with intelligent fallback**
- **Natural language query interface**
- **Support for multiple data formats (CSV, Excel, Kaggle)**
- **Extensible agent architecture**
- **Non-blocking LLM calls with timeout handling**
- **Test mode for automated workflows**

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

## Troubleshooting

### LLM Timeout Issues

If you see "Ollama service is not responding" messages:
1. Check if Ollama is running: `ollama list`
2. Ensure the model is downloaded: `ollama pull llama3`
3. The system will automatically fall back to rule-based analysis

### Kaggle API Issues

If Kaggle downloads fail:
1. Ensure you have a Kaggle account
2. Create API credentials at https://www.kaggle.com/account
3. Set environment variables or create `.env` file with credentials

### Import Errors

If you encounter import errors:
```bash
# Ensure you're in the project root directory
cd AI-Data-Analyst

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

## Testing

Run the system with test datasets:
```bash
# CSV test
python main.py test_data.csv --test

# Excel test
python main.py test_messy_data.xlsx --test

# Kaggle test
python main.py kaggle:uciml/iris --test
```

## Contributing

Contributions are welcome! Please ensure:
- All agents follow the standard output format (summary, metrics, insights)
- LLM calls include proper timeout handling
- Fallback logic is implemented for offline operation
- Code is tested with CSV, Excel, and Kaggle datasets

## License

[Add your license information here]

## Acknowledgments

- Built with Ollama for local LLM inference
- Uses scikit-learn for machine learning capabilities
- Kaggle API for dataset access
