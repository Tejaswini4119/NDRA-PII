# 🧠 NDRA – Neural Document Research Assistant

**NDRA (Neural Document Research Assistant)** is an LLM-powered system designed to process natural language queries and extract decision-critical information from large unstructured documents such as policy files, contracts, and emails.

---

## 🚀 HackRx 6.0 – Ideate • Co-create • Impact

**The Next Gen of GenAI Starts Here!**  
Built as a solution submission for **HackRx 6.0** organized by **Bajaj Finserv Health Limited**.

> *“Ready to Create What's Never Been Coded?”*


---

## 🎯 Hackathon Objective

The goal is to build a system that can:

- Parse plain-text user queries (e.g., *“46-year-old male, knee surgery in Pune, 3-month-old policy”*)
- Identify key entities like age, procedure, location, and policy duration
- Retrieve relevant clauses using semantic understanding (not just keyword matching)
- Evaluate logic in the document to determine an outcome (e.g., approval or rejection)
- Return a structured, interpretable JSON response with:
  - **Decision**
  - **Payout (if any)**
  - **Justification with clause references**

---

## 🧩 Core Capabilities

- Multi-format document ingestion: PDFs, DOCX, plain text, and emails
- Context-aware chunking and vectorization using Transformer models
- Semantic retrieval using embeddings stored in a vector database (Chroma)
- Natural language query understanding, including vague/incomplete queries
- RAG-based decision logic synthesis with full clause traceability

---

## 🚀 Our Enhancements

To stand out from a basic RAG system, NDRA integrates several **advanced components**:

### ✅ Phase-Based Modular Architecture
- **Phase 1A**: Document Preprocessing & Semantic Chunking  
- **Phase 1B**: Contextual Embedding Engineering using Hugging Face Transformers + Chroma
- **Phase 2A**: Natural Language Query Understanding & Re-Modelling
- **Phase 2B**: Query Structuring & Intent Mapping
- **Phase 3A**: RAG Implementations

### 🧠 Semantic Understanding Boosts
- Uses **Transformer-based embeddings** (e.g., Sentence Transformers) instead of static embeddings
- Chunking strategy ensures **semantic boundary preservation**, improving retrieval quality

### 🔍 Clause Traceability
- Output includes **clause-to-decision mapping**  
- Every answer is backed by actual document excerpts, aiding **auditability and transparency**

### 🔄 Robust Query Handling
- Supports **vague or incomplete inputs** using entity extraction and query normalization
- Designed to work on **real-world, noisy documents**

### 📊 Output Format (JSON)
```json
{
  "decision": "Approved",
  "amount": "₹50,000",
  "justification": {
    "matched_clauses": [
      {
        "text": "Knee surgeries are covered after a 90-day waiting period...",
        "location": "Page 4, Clause 7.2"
      }
    ],
    "reasoning": "Query indicates a 3-month policy; clause confirms eligibility."
  }
}
