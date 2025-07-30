## Phase 3 : Semantic RAG Engineering & Speed Optimization.

## Overview

Phase 3 focused on converting semantically processed policy chunks into intelligent responses to vague human queries. The pipeline integrates **prompt-based RAG**, **LLM-driven clause synthesis**, **structured JSON generation**, and **speed failovers**.

> 🎯 **Goal**: Accurate, explainable, structured decision-making for vague insurance queries using semantic search + LLM synthesis — all within **<7 seconds**.

---

## 🔹 Stage 1: Answer/Response Synthesis Engineering (RAG Part 1)

### 🎯 Objective:
Generate accurate answers from matched semantic chunks using carefully constructed prompts. Support clause-aware LLM responses.

### 🔨 Key Tasks:
- Construct `RAG Prompt` using:
  - Rewritten query
  - Structured query info
  - Top N matching semantic clauses
- Guide LLM with:
  - YES/NO clarity
  - Justification referencing matched clauses
  - Final conclusion considering implicit coverage
- Enable clause-aware language behavior (e.g., if clause mentions “hospitalization” or “day care” infer surgery relevance)

### Implementation:
- `rag_prompt()` builder merges all fields into a structured LLM-ready prompt.
- Prompts ensure LLM gives output in a **3-point form**:
  1. YES/NO
  2. Explanation using clause references
  3. Final logical conclusion

### 📈 Example Output:
```
1. YES

- Clause under Section C, Part B, mentions coverage of "Day Care Procedures", which includes surgeries like knee surgery.
- No explicit exclusions were found for knee procedures.
- Policy also covers pre-hospitalization consultations & diagnostics.

Conclusion: The knee surgery is covered, subject to policy conditions.
```

---

## 🔹 Stage 2: Decisioning Mechanics & Output Structuring (RAG Part 2)

### 🎯 Objective:
Extract structured outputs from raw LLM responses and align them into JSON-friendly, machine-readable form.

### 🔨 Key Tasks:
- Build `wrap_llm_response_to_json()`:
  - Regex-based parsing for YES/NO/Depends/Unknown
  - Free-text justification
  - Attach traceable clauses from original results using string similarity
  - Add clause-level metadata (source, file ID, etc.)
  - Compute completeness score of structured query

### Output Format:
```json
{
  "answer": "YES",
  "justification": "...",
  "supporting_clauses": [...],
  "completeness_score": 0.33
}
```

### Support Logic:
- Tracing is based on similarity between justification and clause content
- Adds top 3 relevant clauses from source context

---

## 🔹 Stage 3: Speed Optimization & Failsafe Engineering (RAG + LLM)

### 🎯 Objective:
Reduce overall latency (<7s) and ensure LLM robustness via fallback logic.

---

### Primary Model:
- Fast LLM: `mistralai/mistral-7b-instruct:free` via OpenRouter  
- Runtime: ~2–5 seconds inference (depending on prompt)

### Fallback:
- `Gemini 2.5 Flash Lite`
- Triggered automatically if primary fails (e.g. 4xx/5xx, OpenRouter unresponsive)

### Optimizations:

| Component           | Optimization                              |
|---------------------|-------------------------------------------|
| Semantic Search     | ThreadPoolExecutor for clause trim        |
| Clause Embedding    | sentence-transformers/all-MiniLM-L6-v2   |
| Vector DB           | Pre-warmed Chroma over 2000+ chunks      |
| LLM Failover Logic  | Try/Except logic wrapped in generate_llm_response() |
| Prompt Engineering  | Token-efficient, minimal redundancy      |
| Timing Benchmark    | Structured timing log with total, inference, and search |

---

### Real Output Example:

| Metric                 | Value    |
|------------------------|----------|
| Semantic Search Time   | 0.09s    |
| LLM Inference Time     | 4.13s    |
| Total Time             | 6.63s    |
| Fallback Used?         | ❌ No    |
| Completeness Score     | 0.33     |

---

## Architecture Flow

```text
    A[User Query] --> B[Query Rewriter]
    B --> C[Structured Query Generator]
    C --> D[Vector Search (Chroma)]
    D --> E[Clause Trimmer]
    E --> F[RAG Prompt Builder]
    F --> G{FastLLM Success?}
    G -->|Yes| H[Parse & Format JSON]
    G -->|No| I[Gemini Fallback]
    I --> H
    H --> J[Final Output JSON]
```

---

## Summary

| Stage   | Focus                                 | Status       |
|---------|----------------------------------------|--------------|
| Stage 1 | Clause-aware Prompt + LLM Output       | ✅ Complete  |
| Stage 2 | JSON Wrapping + Clause Tracing         | ✅ Complete  |
| Stage 3 | Speed + Fallback + Parallel Processing | ✅ Complete  |

---

## Key Achievements

- ⚡ Achieved consistent <7s total execution time
- 🔁 Robust fallback ensures no crash on LLM failure
- 💡 Intelligent clause interpretation (even vague ones)
- 📦 Output ready for audit, explainability, and front-end rendering
- 📊 Structured JSON output with completeness scoring
