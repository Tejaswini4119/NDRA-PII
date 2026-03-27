# Phase 2A: Natural Language Query Understanding & Re-Modelling
---
**Project**: Neuro-Semantic Document Research Assistant (NDRA)  
**Phase**: 2A  
**Run Date**: July 24th, 2025  
**Author**: [@PardhuSreeRushiVarma20060119](https://github.com/PardhuSreeRushiVarma20060119/)

---

## ✅ 2A Goals Achieved

| Task | Status |
|------|--------|
| 🔍 Parse vague user queries into structured info using Gemini | ✅ Done |
| 🧠 Identify key fields: age, gender, procedure, policy duration, etc. | ✅ Done |
| 🎯 Understand query intent (e.g., eligibility vs. coverage) | ✅ Done |
| 🌐 Detect domain (health, motor, property, etc.) | ✅ Done |
| ✍️ Rewrite the query response into clear, user-facing language | ✅ Done |
| 💬 Fallback handling for missing fields | ✅ Gracefully handled |

---

## 📦 Final Output from Phase 2A

### Example 1

**Input (Vague Query):**

```text
"Dad had a bypass, can he get insurance?"
```

**Extracted Structure:**

```python
{
  'age': None,
  'gender': 'male',
  'procedure': 'bypass surgery',
  'location': None,
  'policy_duration': None,
  'subject': 'insurance eligibility'
}
```

**Response:**

*Can your father be insured? Based on the context: male, had bypass surgery. Eligibility may depend on age, pre-existing conditions, waiting periods, and current health status. Check hospitalization expenses, surgery costs, pre-existing condition clauses, and coverage exclusions.*

---

### Example 2

**Input (Vague Query):**

```text
"bike accident last month… still eligible for vehicle insurance?"
```

**Extracted Structure:**

```python
{
  'age': None,
  'gender': None,
  'procedure': None,
  'location': None,
  'policy_duration': None,
  'subject': 'vehicle insurance'
}
```

**Response:**

*Can the vehicle be insured? Based on the context: bike accident last month… still eligible for vehicle insurance. Eligibility may depend on vehicle condition, registration location, and past claims history. Check coverage for accidents, third-party liability, own damage, and add-ons like zero depreciation.*

---

> **Role:** NLP & Query Re-Modelling Engineer  

> **Tools Used:** LangChain, Gemini LLM, prompt templates, jupyter

