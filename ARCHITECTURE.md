# AI Data Analyst - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │   main.py    │         │  Jupyter     │                    │
│  │   (CLI)      │         │  Notebook    │                    │
│  └──────┬───────┘         └──────┬───────┘                    │
└─────────┼────────────────────────┼────────────────────────────┘
          │                        │
          └────────────┬───────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AnalysisPipeline (pipeline.py)              │  │
│  │                                                          │  │
│  │  • Manages agent execution order                        │  │
│  │  • Collects and combines results                        │  │
│  │  • Handles errors gracefully                            │  │
│  │  • Provides logging and monitoring                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│   LOADERS    │ │  AGENTS  │ │   LLM    │
└──────────────┘ └──────────┘ └──────────┘
```

## Agent Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LOADING PHASE                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  CSV Loader      │
                    │  Excel Loader    │
                    │  Kaggle Loader   │
                    └────────┬─────────┘
                             │
                             ▼
                      [DataFrame]
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    ANALYSIS PIPELINE                            │
│                                                                 │
│  Step 1: Dataset Understanding                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DatasetUnderstandingAgent                               │  │
│  │  • Infers domain and business context                    │  │
│  │  • Identifies potential target variables                 │  │
│  │  • Suggests analysis objectives                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 2: Data Quality                                          │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  DataCleanerAgent                                        │  │
│  │  • Identifies missing values                             │  │
│  │  • Detects duplicates                                    │  │
│  │  • Checks data types                                     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 3: Statistical Analysis                                  │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  AnalysisAgent                                           │  │
│  │  • Computes descriptive statistics                       │  │
│  │  • Calculates correlations                               │  │
│  │  • Identifies distributions                              │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 4: Clustering                                            │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  ClusteringAgent                                         │  │
│  │  • Finds natural groupings                               │  │
│  │  • Determines optimal cluster count                      │  │
│  │  • Assigns cluster labels                                │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 5: Anomaly Detection                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  AnomalyDetectionAgent                                   │  │
│  │  • Detects unusual patterns                              │  │
│  │  • Identifies outliers                                   │  │
│  │  • Flags anomalous records                               │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 6: Feature Importance                                    │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  FeatureImportanceAgent                                  │  │
│  │  • Ranks feature significance                            │  │
│  │  • Identifies key drivers                                │  │
│  │  • Suggests feature engineering                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 7: Insight Generation (LLM)                              │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  InsightAgent                                            │  │
│  │  • Generates human-readable insights                     │  │
│  │  • Synthesizes findings                                  │  │
│  │  • Provides context and interpretation                   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 8: Visualization                                         │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  VisualizationAgent                                      │  │
│  │  • Creates charts and plots                              │  │
│  │  • Generates visual summaries                            │  │
│  │  • Exports to PNG/PDF                                    │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 9: Recommendations (LLM)                                 │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  RecommendationAgent                                     │  │
│  │  • Provides strategic advice                             │  │
│  │  • Suggests next steps                                   │  │
│  │  • Identifies opportunities                              │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  Step 10: Report Generation                                    │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  ReportAgent                                             │  │
│  │  • Compiles final report                                 │  │
│  │  • Formats output (Markdown/PDF)                         │  │
│  │  • Includes all findings                                 │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
                  [Final Analysis Report]
```

## Component Architecture

### 1. Agent Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                         BaseAgent                               │
│                    (Abstract Base Class)                        │
│                                                                 │
│  + run(df: DataFrame, **kwargs) -> AgentResult                 │
│  + validate_input(df: DataFrame) -> None                       │
│  + enable() / disable()                                        │
│  + is_enabled() -> bool                                        │
└─────────────────────────────────────────────────────────────────┘
                            △
                            │ inherits
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│ DataCleanerAgent │ │AnalysisAgent│ │ InsightAgent   │
│                  │ │             │ │                │
│ • Check quality  │ │ • Statistics│ │ • LLM insights │
│ • Find missing   │ │ • Correlate │ │ • Synthesize   │
│ • Detect dupes   │ │ • Summarize │ │ • Interpret    │
└──────────────────┘ └─────────────┘ └────────────────┘
```

### 2. LLM Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                          BaseLLM                                │
│                    (Abstract Base Class)                        │
│                                                                 │
│  + generate(prompt, system_prompt) -> str                      │
│  + is_available() -> bool                                      │
│  + chat(messages) -> str                                       │
└─────────────────────────────────────────────────────────────────┘
                            △
                            │ implements
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│ OllamaProvider   │ │OpenAIProvider│ │AnthropicProvider│
│                  │ │  (future)   │ │   (future)     │
│ • Local LLM     │ │ • GPT-4     │ │ • Claude       │
│ • Timeout: 5s   │ │ • API key   │ │ • API key      │
│ • Fallback      │ │ • Cloud     │ │ • Cloud        │
└──────────────────┘ └─────────────┘ └────────────────┘
```

### 3. Loader Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Loaders                               │
└─────────────────────────────────────────────────────────────────┘
          │                 │                 │
┌─────────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│   CSVLoader      │ │ ExcelLoader │ │ KaggleLoader   │
│                  │ │             │ │                │
│ • Read CSV       │ │ • Read XLSX │ │ • Download     │
│ • Detect delim   │ │ • Read XLS  │ │ • Cache        │
│ • Handle encode  │ │ • Multi-sheet│ │ • API auth     │
└──────────────────┘ └─────────────┘ └────────────────┘
                            │
                            ▼
                      [DataFrame]
```

### 4. Utility Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                        Utilities                                │
└─────────────────────────────────────────────────────────────────┘
          │                 │                 │
┌─────────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│ logging_utils    │ │ data_utils  │ │  file_utils    │
│                  │ │             │ │                │
│ • setup_logger   │ │ • validate  │ │ • ensure_dir   │
│ • get_logger     │ │ • get_cols  │ │ • get_ext      │
│ • formatting     │ │ • outliers  │ │ • output_path  │
└──────────────────┘ └─────────────┘ └────────────────┘
```

## Data Flow

```
┌──────────┐
│  User    │
│  Input   │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  main.py (CLI)   │
│  • Parse args    │
│  • Load config   │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  Loader          │
│  • CSV/Excel     │
│  • Kaggle        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  DataFrame       │
└────┬─────────────┘
     │
     ▼
┌──────────────────────────────────┐
│  AnalysisPipeline                │
│  ┌────────────────────────────┐  │
│  │  Agent 1: Understanding    │  │
│  └──────────┬─────────────────┘  │
│             ▼                    │
│  ┌────────────────────────────┐  │
│  │  Agent 2: Cleaning         │  │
│  └──────────┬─────────────────┘  │
│             ▼                    │
│  ┌────────────────────────────┐  │
│  │  Agent 3: Analysis         │  │
│  └──────────┬─────────────────┘  │
│             ▼                    │
│  ┌────────────────────────────┐  │
│  │  Agent N: Report           │  │
│  └──────────┬─────────────────┘  │
└─────────────┼────────────────────┘
              │
              ▼
┌──────────────────────────────────┐
│  Combined Results                │
│  • Summary                       │
│  • Metrics                       │
│  • Insights                      │
│  • Visualizations                │
│  • Recommendations               │
└──────────────────────────────────┘
```

## Error Handling Flow

```
┌──────────────────┐
│  Agent.run()     │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  validate_input()│
│  • Check None    │
│  • Check empty   │
└────┬─────────────┘
     │
     ├─ Error ──────────┐
     │                  │
     ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  Process data    │  │  Log error       │
└────┬─────────────┘  │  Return graceful │
     │                │  fallback        │
     ├─ Error ────────┤                  │
     │                └──────────────────┘
     ▼
┌──────────────────┐
│  Return result   │
└──────────────────┘
```

## LLM Integration Flow

```
┌──────────────────┐
│  Agent needs LLM │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  Check available │
│  llm.is_available()│
└────┬─────────────┘
     │
     ├─ Available ───────┐
     │                   │
     ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│  Call LLM        │  │  Use rule-based  │
│  • Timeout: 5s   │  │  fallback        │
│  • Thread-safe   │  │                  │
└────┬─────────────┘  └──────────────────┘
     │
     ├─ Timeout/Error ───┘
     │
     ▼
┌──────────────────┐
│  Return result   │
└──────────────────┘
```

## Class Hierarchy

```
BaseAgent (ABC)
├── DataCleanerAgent
├── AnalysisAgent
├── DatasetUnderstandingAgent
├── ClusteringAgent
├── AnomalyDetectionAgent
├── FeatureImportanceAgent
├── InsightAgent
├── OutlierDetectionAgent
├── PatternDetectionAgent
├── ProfilingAgent
├── QueryAgent
├── RecommendationAgent
├── ReportAgent
└── VisualizationAgent

BaseLLM (ABC)
├── OllamaProvider
├── OpenAIProvider (future)
└── AnthropicProvider (future)

AgentResult
└── (Data container)

AnalysisPipeline
└── (Orchestrator)
```

## Module Dependencies

```
main.py
  ├── pipeline.py
  │   ├── agents/base_agent.py
  │   │   └── agents/*_agent.py
  │   ├── utils/logging_utils.py
  │   └── utils/data_utils.py
  │
  ├── loaders/
  │   ├── csv_loader.py
  │   ├── excel_loader.py
  │   └── kaggle_loader.py
  │
  └── llm/
      ├── base_llm.py
      │   └── ollama_provider.py
      └── prompts.py
```

---

This architecture provides:
- ✅ Clean separation of concerns
- ✅ Easy to extend and modify
- ✅ Testable components
- ✅ Flexible configuration
- ✅ Graceful error handling
- ✅ Production-ready design
