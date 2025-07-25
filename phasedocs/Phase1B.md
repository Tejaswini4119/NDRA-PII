# Phase 1B: Contextual Vectorization & Embedding using HF Transformer Inference and Persistent Indexing via Chroma Vector DB with Semantic Search Query Implementation.
---

**Project**: Neuro-Semantic Document Reasoning Assistant (NDRA)  
**Phase**: 1B    
**Run Date**: July 23, 2025  
**Author**: [@PardhuSreeRushiVarma20060119](https://github.com/PardhuSreeRushiVarma20060119/)

---

This notebook demonstrates how to:

- Load pre-processed document chunks.
- Generate semantic embeddings using HuggingFace transformer models.
- Persistently store these embeddings and chunks into Chroma Vector Database.
- Perform semantic search using a natural language query.

---

## 📂 Step 1: Load Preprocessed Chunks

**We successfully loaded over 450 semantic document chunks generated during Phase 1A. These chunks represent coherent units of policy information ready for downstream embedding.**
- *✅ Loaded 481 semantic chunks (chunks.pkl).*
- *Each chunk captures self-contained context from policy documents, ensuring high-quality vector embeddings.*

---

## 🧠 Step 2: Generate Embeddings Using HuggingFace Transformers

**Using the lightweight and efficient all-MiniLM-L6-v2 model from HuggingFace's sentence-transformers, we encoded each chunk into a dense vector representation.**
- *✅ Generated 481 high-dimensional embeddings.*
- *These embeddings reflect the semantic essence of each chunk, enabling meaning-based retrieval (not just keyword match).*



---

## 🗃️ Step 3: Chroma Server

**We ran a local ChromaDB instance and created a persistent collection named ndr_chunks to store:**
- *All 481 chunks.*
- *Their corresponding vector embeddings.*
- *Unique IDs (chunk-0, chunk-1, ...).*

**ChromaDB was configured to persist data to disk (./chroma_db), ensuring long-term retrievability of indexed content.**
- *✅ Successfully added all embeddings + chunks to persistent ChromaDB.*
- *Future queries can now operate without repeating embedding generation.*


---

## 🔍 Step 4: Semantic Search Query Execution

**We tested the system with a natural query:**

> “TABLE OF BENEFITS FOR DOMESTIC COVER”
- *The query was encoded into an embedding, and matched against the stored vectors using cosine similarity.*

**Top 5 Results returned semantically relevant sections like:**

- *📄 “Sum Insured under Domestic Coverage Plan”*
- *📄 “Breakdown of hospital expenses by treatment type”*
- *📄 “Table A vs Table B benefit comparison”*

**Each result included a similarity score, helping rank relevance.**
- *✅ Demonstrated effective semantic retrieval.*
- *The system can now interpret natural queries and fetch the most semantically related policy content.*


---

## ✅ Outcome:

- Vector embeddings created and persisted using ChromaDB.
- Semantic queries return top-matching document chunks based on cosine similarity.

---

## 🧠 Tools Used:

- `sentence-transformers (all-MiniLM-L6-v2)`
- `ChromaDB`
- `pickle`

> This phase establishes a fully working semantic document vectorization and persistance storage pipeline for further retrieval.
