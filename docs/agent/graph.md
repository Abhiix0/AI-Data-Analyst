# LangGraph Analytical Agent Architecture

This document specifies the core LangGraph state machine driving the analytical agent, its nodes, deterministic tool orchestration, evidence ledgering, and the hard evidence validation gate.

---

## 1. Overview & Core Philosophy

The analytical agent is structured around deterministic, code-first data operations rather than unrestricted free-form generation.

```
       [ START ]
           │
     load_context
           │
  understand_question
           │
      create_plan
           │
    ┌─► select_tool
    │      │
    │  execute_tool (Polars/DuckDB/SciPy via Registry)
    │      │
    │  inspect_result
    │      │
    └──(More steps?)──► synthesize_finding
                              │
                      validate_evidence ◄────────┐
                              │                  │ (Retry gate)
                    (Pass/Fail max retries) ─────┘
                              │
                        final_response
                              │
                           [ END ]
```

---

## 2. State Definition (`AgentState`)

The state schema (`packages/agent/state.py`) flows through all nodes:

| Field | Type | Purpose |
| :--- | :--- | :--- |
| `question` | `str` | Original user analytical question |
| `parquet_path` | `str` | Absolute path to the immutable Parquet dataset |
| `schema_info` | `Dict[str, str]` | Column names mapped to Polars data types |
| `sample_records` | `List[Dict[str, Any]]` | First 5 rows for contextual grounding |
| `intent_summary` | `str` | Analytical goal extracted from question |
| `target_columns` | `List[str]` | Columns relevant to the question |
| `plan_steps` | `List[str]` | Ordered analytical tasks |
| `current_step_index` | `int` | Index of active step |
| `pending_tool_call` | `Optional[ToolCallRecord]` | Tool queued for execution |
| `executed_tool_calls` | `List[ToolCallRecord]` | Execution log with status/timings |
| `evidence_ledger` | `List[Evidence]` | Immutable ledger of grounded numerical facts |
| `synthesized_findings` | `List[Finding]` | Structured analytical findings |
| `validation_passed` | `bool` | Flag from Hard Evidence Gate |
| `validation_notes` | `List[str]` | Audit trail of metric verification |
| `final_response` | `str` | Final markdown output with citations |

---

## 3. Node Specifications

### 3.1 `load_context`
- Inspects Parquet schema and loads first 5 records into state.
- Computes row and column counts.

### 3.2 `understand_question`
- Resolves question intent and matches column names against schema.

### 3.3 `create_plan`
- Builds a targeted 1 to 3 step analytical plan to answer the question with deterministic tools.

### 3.4 `select_tool`
- Selects the exact registered tool from `packages/agent/tool_registry.py` and populates typed parameters.

### 3.5 `execute_tool`
- Executes tool over Polars DataFrame / DuckDB Parquet engine.
- Encapsulates result into a typed `Evidence` record with a unique UUID.
- Appends to `evidence_ledger`.

### 3.6 `inspect_result`
- Advances step counter and iteration counter.

### 3.7 `synthesize_finding`
- Synthesizes findings grounded strictly in `evidence_ledger` entries.
- Assigns evidence IDs to each `Finding`.

### 3.8 `validate_evidence` (Hard Evidence Gate)
- **Zero Hallucination Guarantee**: Extracts all numeric tokens from narrative text and findings descriptions.
- Checks each number against values in `evidence_ledger` within ±2% tolerance or exact match.
- If ungrounded numbers are found, routes back to `synthesize_finding` for correction.

### 3.9 `final_response`
- Assembles markdown response with findings, metrics, and citations linking back to evidence ledger IDs.

---

## 4. LLM Provider Flexibility

The agent supports:
- **Groq**: Fast inference (`llama-3.3-70b-versatile`)
- **OpenAI**: `gpt-4o` with strict structured outputs
- **Anthropic**: `claude-3-5-sonnet`
- **Mock / Offline**: Fallback heuristics for deterministic unit testing without external API calls.
