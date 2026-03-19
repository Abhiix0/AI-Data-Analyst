# AI Data Analyst — Production Architecture

A professional, multi-agent data analysis system with clean architecture, extensible design, and LLM-powered insights.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (CLI)                          │
│                  Command-line interface                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  pipeline.py                                │
│            AnalysisPipeline (Orchestrator)                  │
│  • Manages agent execution order                            │
│  • Collects and combines results                            │
│  • Handles errors gracefully                                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
   │ Loaders │  │ Agents  │  │   LLM    │  │  Utils   │
   └─────────┘  └─────────┘  └──────────┘  └──────────┘
```

### Agent Pipeline Flow

```
1. DatasetUnderstandingAgent  → Infer domain & context
         ↓
2. DataCleanerAgent           → Identify quality issues
         ↓
3. AnalysisAgent              → Compute statistics
         ↓
4. ClusteringAgent            → Find natural groups
         ↓
5. AnomalyDetectionAgent      → Detect anomalies
         ↓
6. FeatureImportanceAgent     → Rank features
         ↓
7. InsightAgent               → Generate insights (LLM)
         ↓
8. VisualizationAgent         → Create charts
         ↓
9. RecommendationAgent        → Strategic advice
         ↓
10. ReportAgent               → Final report
```

## 📁 Project Structure

```
AI-Data-Analyst/
├── agents/                      # Analysis agents
│   ├── base_agent.py           # ⭐ Base class for all agents
│   ├── analysis_agent.py       # Statistical analysis
│   ├── anomaly_detection_agent.py
│   ├── clustering_agent.py
│   ├── data_cleaner_agent.py   # Data quality inspection
│   ├── data_loader_agent.py
│   ├── dataset_understanding_agent.py
│   ├── feature_importance_agent.py
│   ├── insight_agent.py        # LLM-powered insights
│   ├── outlier_detection_agent.py
│   ├── pattern_detection_agent.py
│   ├── profiling_agent.py
│   ├── query_agent.py          # Natural language queries
│   ├── recommendation_agent.py # Strategic recommendations
│   ├── report_agent.py
│   └── visualization_agent.py
│
├── llm/                        # LLM abstraction layer
│   ├── base_llm.py            # ⭐ Abstract LLM interface
│   ├── ollama_provider.py     # Ollama integration
│   ├── ollama_client.py       # Legacy compatibility
│   └── prompts.py             # Prompt templates
│
├── loaders/                    # Data loaders
│   ├── csv_loader.py
│   ├── excel_loader.py
│   └── kaggle_loader.py       # ⭐ Kaggle API integration
│
├── utils/                      # Shared utilities
│   ├── logging_utils.py       # ⭐ Logging configuration
│   ├── data_utils.py          # ⭐ Data manipulation helpers
│   └── file_utils.py          # ⭐ File operations
│
├── tests/                      # Test suite
│   ├── unit/                  # Unit tests
│   │   ├── test_llm_agent.py
│   │   └── test_llm_recommendation_agent.py
│   ├── integration/           # Integration tests
│   │   └── test_pipeline.py  # ⭐ Pipeline tests
│   └── data/                  # Test datasets
│       ├── test_data.csv
│       └── test_messy_data.xlsx
│
├── outputs/                    # Generated artifacts (gitignored)
│   ├── charts/
│   └── reports/
│
├── kaggle_downloads/          # Kaggle datasets (gitignored)
│
├── pipeline.py                # ⭐ New pipeline orchestrator
├── orchestrator.py            # Legacy orchestrator (backward compat)
├── orchestrator_v2.py         # ⭐ New orchestrator wrapper
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file

⭐ = New/Refactored in V2
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd AI-Data-Analyst

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Ollama for LLM features
# Download from https://ollama.ai
ollama pull llama3
```

### Basic Usage

```bash
# Analyze a CSV file
python main.py dataset.csv

# Analyze an Excel file
python main.py report.xlsx

# Download and analyze from Kaggle
python main.py kaggle:uciml/iris

# Run in test mode (no interactive Q&A)
python main.py dataset.csv --test
```

### Programmatic Usage

```python
from pipeline import AnalysisPipeline
from agents.data_cleaner_agent import DataCleanerAgent
from agents.analysis_agent import AnalysisAgent
import pandas as pd

# Load data
df = pd.read_csv("data.csv")

# Create pipeline
pipeline = AnalysisPipeline()
pipeline.add_agent(DataCleanerAgent())
pipeline.add_agent(AnalysisAgent())

# Run analysis
result = pipeline.run(df, dataset_name="my_data")

# Access results
print(result["summary"])
for insight in result["insights"]:
    print(f"- {insight}")
```

## 🔧 Architecture Improvements

### 1. BaseAgent Pattern

All agents now inherit from `BaseAgent`, ensuring consistent interface:

```python
from agents.base_agent import BaseAgent, AgentResult

class MyAgent(BaseAgent):
    def run(self, df: pd.DataFrame, **kwargs) -> AgentResult:
        # Your analysis logic
        return AgentResult(
            summary="Analysis complete",
            metrics={"count": len(df)},
            insights=["Key finding 1", "Key finding 2"]
        )
```

**Benefits:**
- Consistent interface across all agents
- Easy to add new agents
- Built-in validation and error handling
- Enable/disable agents dynamically

### 2. LLM Abstraction

Clean separation between LLM providers:

```python
from llm.base_llm import BaseLLM
from llm.ollama_provider import OllamaProvider

# Use any LLM provider
llm = OllamaProvider(model="llama3", timeout=5.0)
response = llm.generate(
    prompt="Analyze this data",
    system_prompt="You are a data analyst"
)
```

**Benefits:**
- Easy to swap LLM providers (Ollama, OpenAI, etc.)
- Consistent timeout handling
- Graceful fallback when LLM unavailable

### 3. Pipeline Orchestration

Flexible pipeline management:

```python
from pipeline import AnalysisPipeline

pipeline = AnalysisPipeline()

# Add agents
pipeline.add_agent(DataCleanerAgent())
pipeline.add_agent(AnalysisAgent())

# Remove agents
pipeline.remove_agent("DataCleanerAgent")

# Disable agents temporarily
agent = AnalysisAgent()
agent.disable()
pipeline.add_agent(agent)

# Run pipeline
result = pipeline.run(df)
```

**Benefits:**
- Dynamic agent management
- Easy to customize pipeline
- Graceful error handling
- Detailed logging

### 4. Utility Modules

Shared functionality in organized modules:

```python
from utils.data_utils import get_numeric_columns, detect_outliers_iqr
from utils.file_utils import ensure_directory, get_output_path
from utils.logging_utils import setup_logger

# Use utilities
numeric_cols = get_numeric_columns(df)
output_path = get_output_path("report.pdf", subdir="reports")
logger = setup_logger(__name__)
```

**Benefits:**
- No code duplication
- Consistent behavior
- Easy to test and maintain

### 5. Kaggle Integration

Proper Kaggle loader with caching:

```python
from loaders.kaggle_loader import load_kaggle

# Download and load Kaggle dataset
df = load_kaggle("uciml/iris")

# Automatically cached in kaggle_downloads/
# Subsequent loads use cached version
```

**Benefits:**
- Clean API
- Automatic caching
- Error handling
- Progress feedback

## 📊 Agent Details

### Core Agents

| Agent | Purpose | Output |
|-------|---------|--------|
| **DatasetUnderstandingAgent** | Infers domain, context, target variable | Domain insights, business context |
| **DataCleanerAgent** | Identifies missing values, duplicates | Data quality metrics |
| **AnalysisAgent** | Computes descriptive statistics | Mean, median, std, correlations |
| **ClusteringAgent** | Finds natural groupings | Cluster assignments, sizes |
| **AnomalyDetectionAgent** | Detects unusual patterns | Anomaly scores, outliers |
| **FeatureImportanceAgent** | Ranks feature significance | Importance scores |
| **InsightAgent** | Generates human insights (LLM) | Actionable insights |
| **VisualizationAgent** | Creates charts | PNG/PDF visualizations |
| **RecommendationAgent** | Strategic advice (LLM) | Recommendations |
| **ReportAgent** | Generates final report | Markdown/PDF report |

### Agent Output Format

All agents return standardized `AgentResult`:

```python
{
    "summary": "Brief description of findings",
    "metrics": {
        "metric1": value1,
        "metric2": value2,
        ...
    },
    "insights": [
        "Insight 1",
        "Insight 2",
        ...
    ],
    "metadata": {  # Optional
        "agent_name": "AnalysisAgent",
        "execution_time": 1.23
    }
}
```

## 🧪 Testing

### Run All Tests

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# Specific test
python tests/integration/test_pipeline.py
```

### Test Structure

```
tests/
├── unit/              # Test individual components
│   ├── test_agents.py
│   ├── test_loaders.py
│   └── test_llm.py
├── integration/       # Test complete workflows
│   └── test_pipeline.py
└── data/             # Test datasets
    ├── test_data.csv
    └── test_messy_data.xlsx
```

## 🔌 Adding a New Agent

1. **Create agent class** inheriting from `BaseAgent`:

```python
# agents/my_agent.py
from agents.base_agent import BaseAgent, AgentResult
import pandas as pd

class MyAgent(BaseAgent):
    def run(self, df: pd.DataFrame, **kwargs) -> AgentResult:
        # Your analysis logic here
        result_value = len(df)
        
        return AgentResult(
            summary=f"Analyzed {result_value} rows",
            metrics={"row_count": result_value},
            insights=["Dataset has data"]
        )
```

2. **Add to pipeline**:

```python
from pipeline import AnalysisPipeline
from agents.my_agent import MyAgent

pipeline = AnalysisPipeline()
pipeline.add_agent(MyAgent())
```

3. **Test your agent**:

```python
# tests/unit/test_my_agent.py
from agents.my_agent import MyAgent
import pandas as pd

def test_my_agent():
    df = pd.DataFrame({"x": [1, 2, 3]})
    agent = MyAgent()
    result = agent.run(df)
    
    assert result.metrics["row_count"] == 3
    assert len(result.insights) > 0
```

## 📝 Configuration

### Environment Variables

Create `.env` file:

```bash
# Kaggle API credentials
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# LLM settings (optional)
LLM_PROVIDER=ollama
LLM_MODEL=llama3
LLM_TIMEOUT=5.0
```

### Logging

Configure logging in your code:

```python
from utils.logging_utils import setup_logger
import logging

# Setup logger
logger = setup_logger(__name__, level=logging.DEBUG)

# Use logger
logger.info("Processing data")
logger.error("An error occurred")
```

## 🐛 Troubleshooting

### LLM Timeout Issues

If Ollama times out:
```bash
# Check Ollama is running
ollama list

# Pull model if needed
ollama pull llama3

# Increase timeout in code
from llm.ollama_provider import OllamaProvider
llm = OllamaProvider(timeout=10.0)
```

### Import Errors

```bash
# Ensure you're in project root
cd AI-Data-Analyst

# Activate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Kaggle API Issues

```bash
# Check credentials
cat ~/.kaggle/kaggle.json

# Or set environment variables
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_key
```

## 🤝 Contributing

1. Follow the `BaseAgent` pattern for new agents
2. Add type hints to all functions
3. Write docstrings for classes and methods
4. Add unit tests for new functionality
5. Update README with new features
6. Follow PEP 8 style guidelines

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Ollama for local LLM inference
- scikit-learn for ML capabilities
- Kaggle for dataset access
- pandas for data manipulation

---

**Version 2.0** — Refactored Architecture (2026)
