# Phase 2B: Query Structuring & Intent Mapping

**Project**: Neuro-Semantic Document Research Assistant (NDRA)  
**Phase**: 2B  
**Goal**: Convert a user's vague natural language query into a structured format that includes:
  - A classified **intent**
  - Extracted **entities**
  - A **rewritten query** with enhanced clarity and context
  - A structured JSON-like **query object**
  - An **completeness score**

**Run Date**: July 24th, 2025  
**Author**: [@PardhuSreeRushiVarma20060119](https://github.com/PardhuSreeRushiVarma20060119/)

---

## 🔧 Components:

### 1. Intent Classification
- **Purpose:** Understand what the user wants (e.g., check eligibility, claim status).
- **Method:** Rule-based keywords or a lightweight LLM classification using prompt templates.
- **Example Output:**
  ```json
  "intent": "eligibility_check"
  ```

---

### 2. Entity Extraction
- **Entities:** incident, time, policy duration, location, subject, age, etc.
- **Method:** Regex-based, spaCy, or LLM-based extraction via prompt.
- **Example Output:**
  ```json
  "extracted_entities": {
    "incident": "accident",
    "incident_time": "last month"
  }
  ```

---

### 3. Rewritten Query Generation
- **Purpose:** Improve query understanding and retrieval by clarifying vague or incomplete questions.
- **Method:** Prompt-based LLM paraphrasing with context enhancement.
- **Example Output:**
  ```json
  "rewritten_query": "Can the vehicle be insured? Based on the context: bike accident last month… still eligible for vehicle insurance."
  ```

---

### 4. Structured Query Object
- **Purpose:** Encapsulate all extracted and generated data into a standard object for RAG and downstream logic.
- **Structure:**
  ```json
  {
    "original_query": "...",
    "rewritten_query": "...",
    "intent": "...",
    "subject": "...",
    "age": ...,
    "gender": ...,
    "procedure": "...",
    "location": "...",
    "policy_duration": "...",
    "extracted_entities": {...}
  }
  ```

---

### 5. [Optional] Completeness Score
- **Purpose:** Evaluate how complete the query is.
- **Method:** Fraction of fields populated in the structured object.
- **Example Output:**
  ```json
  "completeness_score": 0.17
  ```

---

## 🧪 Example End-to-End Output:

Input Query:
```
"bike accident last month… still eligible for vehicle insurance?"
```

Output:
```json
{
  "original_query": "bike accident last month… still eligible for vehicle insurance?",
  "rewritten_query": "Can the vehicle be insured? Based on the context: bike accident last month… still eligible for vehicle insurance.",
  "intent": "eligibility_check",
  "subject": "vehicle insurance",
  "age": null,
  "gender": null,
  "procedure": null,
  "location": null,
  "policy_duration": null,
  "extracted_entities": {
    "incident": "accident",
    "incident_time": "last month"
  },
  "completeness_score": 0.17
}
```

---

 
> **Role:** Natural Language Query Processing Engineer. 

> **Tools Used:** Langchain, Gemini LLM, Regex, Custom Prompt templates, ChatGoogleGenerativeAI, Jupyter Notebooks etc.
