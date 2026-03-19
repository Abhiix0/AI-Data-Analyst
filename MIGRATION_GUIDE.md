# Migration Guide: V1 → V2 Architecture

This guide helps you migrate from the old function-based architecture to the new class-based, pipeline architecture.

## Overview of Changes

### V1 (Old Architecture)
- Function-based agents (`def run(df)`)
- Direct orchestrator calls
- No base class
- Inconsistent naming
- Limited extensibility

### V2 (New Architecture)
- Class-based agents (inherit from `BaseAgent`)
- Pipeline orchestration
- Standardized interface
- Consistent naming (`*_agent.py`)
- Highly extensible

## Backward Compatibility

**Good news:** V2 maintains backward compatibility! Your existing code will continue to work.

### Old Code Still Works

```python
# V1 style - still works!
from agents import data_cleaner, analyst
import pandas as pd

df = pd.read_csv("data.csv")
result1 = data_cleaner.run(df)
result2 = analyst.run(df)
```

### New Code (Recommended)

```python
# V2 style - recommended
from agents.data_cleaner_agent import DataCleanerAgent
from agents.analysis_agent import AnalysisAgent
from pipeline import AnalysisPipeline
import pandas as pd

df = pd.read_csv("data.csv")

pipeline = AnalysisPipeline()
pipeline.add_agent(DataCleanerAgent())
pipeline.add_agent(AnalysisAgent())

result = pipeline.run(df)
```

## Migration Steps

### Step 1: Update Imports

**Old:**
```python
from agents import data_cleaner, analyst, insight_agent
```

**New:**
```python
from agents.data_cleaner_agent import DataCleanerAgent
from agents.analysis_agent import AnalysisAgent
from agents.insight_agent import InsightAgent
```

### Step 2: Use Class Instances

**Old:**
```python
result = data_cleaner.run(df)
```

**New:**
```python
agent = DataCleanerAgent()
result = agent.run(df)
```

### Step 3: Use Pipeline (Optional but Recommended)

**Old:**
```python
# Manual orchestration
result1 = data_cleaner.run(df)
result2 = analyst.run(df)
result3 = insight_agent.run(df, result1, result2, None)
```

**New:**
```python
# Pipeline orchestration
from pipeline import AnalysisPipeline

pipeline = AnalysisPipeline()
pipeline.add_agent(DataCleanerAgent())
pipeline.add_agent(AnalysisAgent())
pipeline.add_agent(InsightAgent())

result = pipeline.run(df, dataset_name="my_data")
```

### Step 4: Update LLM Usage

**Old:**
```python
from llm.ollama_client import generate

response = generate(prompt="Analyze this", model="llama3")
```

**New (still works, but better):**
```python
from llm.ollama_provider import OllamaProvider

llm = OllamaProvider(model="llama3", timeout=5.0)
response = llm.generate(prompt="Analyze this")
```

### Step 5: Use Utilities

**Old:**
```python
# Duplicated code in multiple places
numeric_cols = df.select_dtypes(include="number").columns.tolist()
```

**New:**
```python
from utils.data_utils import get_numeric_columns

numeric_cols = get_numeric_columns(df)
```

## File Renames

| Old Name | New Name | Status |
|----------|----------|--------|
| `agents/analyst.py` | `agents/analysis_agent.py` | ✅ Created (old kept for compat) |
| `agents/data_cleaner.py` | `agents/data_cleaner_agent.py` | ✅ Created (old kept for compat) |
| `llm/ollama_client.py` | `llm/ollama_provider.py` | ✅ Created (old kept for compat) |
| `orchestrator.py` | `orchestrator_v2.py` + `pipeline.py` | ✅ Created (old kept for compat) |

## Creating Custom Agents

### Old Way (V1)

```python
# agents/my_agent.py
def run(df):
    # Analysis logic
    return {
        "summary": "...",
        "metrics": {...},
        "insights": [...]
    }
```

### New Way (V2)

```python
# agents/my_agent.py
from agents.base_agent import BaseAgent, AgentResult
import pandas as pd

class MyAgent(BaseAgent):
    def __init__(self, name="MyAgent", llm=None):
        super().__init__(name=name, llm=llm)
    
    def run(self, df: pd.DataFrame, **kwargs) -> AgentResult:
        self.validate_input(df)
        
        # Analysis logic
        
        return AgentResult(
            summary="Analysis complete",
            metrics={"count": len(df)},
            insights=["Finding 1", "Finding 2"]
        )
```

**Benefits of V2:**
- Type hints
- Input validation
- Consistent interface
- Enable/disable functionality
- Better error handling

## Testing Migration

### Old Tests

```python
# test_agent.py
from agents import data_cleaner
import pandas as pd

def test_data_cleaner():
    df = pd.DataFrame({"x": [1, 2, 3]})
    result = data_cleaner.run(df)
    assert "summary" in result
```

### New Tests

```python
# tests/unit/test_agents.py
from agents.data_cleaner_agent import DataCleanerAgent
import pandas as pd

def test_data_cleaner_agent():
    df = pd.DataFrame({"x": [1, 2, 3]})
    agent = DataCleanerAgent()
    result = agent.run(df)
    
    assert result.summary is not None
    assert isinstance(result.metrics, dict)
    assert isinstance(result.insights, list)
```

## Common Migration Issues

### Issue 1: Import Errors

**Problem:**
```python
ImportError: cannot import name 'data_cleaner' from 'agents'
```

**Solution:**
```python
# Use new import style
from agents.data_cleaner_agent import DataCleanerAgent

# Or use backward-compatible function
from agents import data_cleaner
result = data_cleaner.run(df)  # Still works!
```

### Issue 2: Result Format Changed

**Problem:**
```python
# Old code expects dict
result = agent.run(df)
print(result["summary"])  # AttributeError
```

**Solution:**
```python
# New agents return AgentResult
result = agent.run(df)
print(result.summary)  # Use attribute

# Or convert to dict
result_dict = result.to_dict()
print(result_dict["summary"])
```

### Issue 3: Agent Not Found in Pipeline

**Problem:**
```python
pipeline.get_result("data_cleaner")  # Returns None
```

**Solution:**
```python
# Use class name, not module name
pipeline.get_result("DataCleanerAgent")
```

## Gradual Migration Strategy

You don't need to migrate everything at once! Here's a gradual approach:

### Phase 1: Keep Using Old Code
- No changes needed
- Everything still works
- Take time to learn new architecture

### Phase 2: Mix Old and New
```python
# Mix old and new styles
from agents import data_cleaner  # Old
from agents.analysis_agent import AnalysisAgent  # New

df = pd.read_csv("data.csv")

# Old style
result1 = data_cleaner.run(df)

# New style
agent = AnalysisAgent()
result2 = agent.run(df)
```

### Phase 3: Migrate to Pipeline
```python
# Use pipeline for new code
from pipeline import AnalysisPipeline
from agents.data_cleaner_agent import DataCleanerAgent
from agents.analysis_agent import AnalysisAgent

pipeline = AnalysisPipeline()
pipeline.add_agent(DataCleanerAgent())
pipeline.add_agent(AnalysisAgent())

result = pipeline.run(df)
```

### Phase 4: Full Migration
- All agents use new class-based style
- All orchestration uses Pipeline
- Tests updated to new format
- Remove old compatibility code (optional)

## Benefits of Migrating

1. **Better Type Safety**: Type hints catch errors early
2. **Easier Testing**: Mock and test individual agents
3. **More Flexible**: Enable/disable agents dynamically
4. **Cleaner Code**: Consistent patterns across codebase
5. **Better Logging**: Built-in logging utilities
6. **Extensibility**: Easy to add new agents
7. **Error Handling**: Graceful failure handling
8. **Documentation**: Self-documenting code with docstrings

## Need Help?

- Check `README_V2.md` for full documentation
- Look at `tests/integration/test_pipeline.py` for examples
- Review `agents/base_agent.py` for agent interface
- See `pipeline.py` for orchestration details

## Timeline

- **Now**: V1 and V2 coexist (backward compatible)
- **Future**: V2 becomes default
- **Later**: V1 compatibility layer may be removed (with notice)

**Recommendation:** Start using V2 for new code, migrate old code gradually.
