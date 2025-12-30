
> This Project Has Been Archived, And No Longer Under Active Development & Maintenance
---

# Neuro-Semantic Document Research Assistance (NDRA)
> *“NDRA: Neuro-semantic intelligence to interpret large unstructured documents.”*

NDRA (Neuro-Semantic Document Research Assistance) is a semantic, transformer-based retrieval and reasoning system designed to extract structured knowledge from large, unstructured textual documents such as insurance policies, legal contracts, and corporate communications. It leverages **Domain-Adapted Embedding Models**, **Contextual Chunking Strategies**, and **Retrieval-Augmented Generation (RAG) Pipelines** to align vague or under-specified user queries with document clauses, enabling high-fidelity question answering and policy decision support.

---

## Objective

To build a robust system capable of:

- Understanding vague user queries like:  
  _“46-year-old male, knee surgery in Pune, 3-month-old policy”_
- Extracting structured data: age, procedure, gender, location, duration
- Mapping those fields to relevant policy clauses
- Evaluating eligibility logic from the document
- Producing a structured JSON response that includes:
  - Approval or rejection
  - Eligible amount (if any)
  - Clause-level justification for the decision

---

## System Architecture Overview

NDRA follows a modular, phase-based pipeline for ai-core divided into four major components:

1. **Document Preprocessing and Chunking**
2. **Embedding Generation and Storage**
3. **Query Understanding and Structuring**
4. **Retrieval-Augmented Generation (RAG) and Decision Engine**

---

## AI Core – Semantic Pipeline

### Role: Semantic & RAG Pipeline Engineer

This module powers the brain of NDRA, enabling contextual matching and semantic interpretation of queries and document content.

- Transformer-based chunking with semantic boundary awareness
- Embedding generation using `sentence-transformers` (e.g., all-MiniLM-L6-v2)
- Chroma vector store for persistent semantic retrieval
- LangChain-based RAG pipeline for context retrieval
- LLM (Gemini) for synthesizing final decision + justification
- Clause traceability ensured via mapping top-K chunks to source metadata

**Enhancements:**

- Query Understanding and Intent Mapping
- Document Ingestion and Preprocessing
- Semantic-aware chunking improves retrieval precision
- Context window optimization for LLM input (RAG prompt design)
- Handles vague/incomplete queries with structured fallback logic


## Backend – FastAPI Service Layer

### Role 1: Backend Development 
- Developed ingestion pipeline in FastAPI.
- Handled file parsing logic for PDF, DOCX, and email formats.
- Connected parsed output to AI chunking and embedding modules.
- Integrated Chroma vector store endpoints with FastAPI.
- Maintains modular pipeline routing for document preprocessing.

### Role 2: API Dev
- Built user-facing endpoints for:
  - Document upload
  - Query submission
  - Final JSON output retrieval
- Implemented structured logging, validation, and error handling.
- Connected API endpoints to internal semantic pipeline and LLM decision modules.

**Enhancements:**
- Multi-domain policy support (Health, Motor, etc.)
- Robust fallback for missing fields and vague queries.
- Entity extraction and dynamic field structuring into JSON.
- Rate-limiting and async task queuing (if time permits).


---


## Project Structure

### AI / Semantic Core Engineering (Handled by Member 2)
Everything from Phase 1A to 3B is covered under Semantic & RAG Pipeline Engineering.

#### ✅ Phase 1A – Preprocessing & Chunking
- Cleaned raw documents (PDF, DOCX, Emails).
- Removed noise like headers, footers, signatures.
- Applied semantic-aware chunking pipeline.
- Output stored as `chunks.pkl`.

#### ✅ Phase 1B – Embedding & Vector Store
- Used HuggingFace model (`all-MiniLM-L6-v2`) for contextual vectorization.
- Stored embeddings in Chroma Vector Database.
- Enabled semantic search with vector indexing.

#### ✅ Phase 2A – Query Understanding
- Parsed user queries using LLM (e.g., Gemini Pro).
- Domain detection: Health, Motor, etc.
- Rewritten for structured understanding and improved answerability.

#### ✅ Phase 2B – Intent Mapping
- Mapped query to structured JSON:
  - Fields like age, gender, location, procedure, policy duration.
- Tagged missing/ambiguous values for LLM-based fill.
- Matched queries with document types.

#### ✅ Phase 3A – Contextual Response Synthesis (RAG-P1)
- Retrieved top-k relevant chunks via semantic search.
- Combined chunks + structured query.
- Prompted LLM to synthesize answer with citation traces.

#### ✅ Phase 3B – Decision Logic & Output Structuring (RAG-P2)
- Extended RAG to include:
  - Conflict detection
  - Missing field detection
  - Edge case fallback logic
- Final output generated as:
  - Structured JSON
  - Natural language explanation

#### ✅ Phase 3C – Speed Optimisation
- Speed Up The Response Time Period <8s
  - Parllell Processing
  - FastLLM via OpenRouter
  - Failsafe Gemini Fallback
  - Optimisations

---

### Backend Engineering (Handled by Member 3 & Member 4)

- API endpoints for:
  - Document upload & ingestion
  - User query processing
  - LLM-based semantic routing
  - Final JSON output delivery
- Manages communication with AI module.
- Error handling & Modular Pipeline Routing.

---

### Frontend (Streamlit Interface) (Handled by Member 1)

- Upload policy documents (PDF, DOCX, Email).
- Input vague or natural language queries.
- Display final structured output:
  - Approved/Rejected
  - Amount covered
  - Cited clause justification
- Fast, minimal UI for demo and hackathon judging.

---

> *“Information isn’t knowledge until it’s interpretable. NDRA bridges that gap using AI.”*

-Team NDRA


