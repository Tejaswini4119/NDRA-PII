# Phase 1B: Contextual Vectorization & Embedding using HF Transformer Inference and Persistent Indexing via Chroma Vector DB with Semantic Search Query Implementation.

This notebook demonstrates how to:

- Load pre-processed document chunks.
- Generate semantic embeddings using HuggingFace transformer models.
- Persistently store these embeddings and chunks into Chroma Vector Database.
- Perform semantic search using a natural language query.

---

## 📂 Step 1: Load Preprocessed Chunks

```python
import pickle

with open("chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

print(f"Loaded {len(chunks)} chunks.")
```

---

## 🧠 Step 2: Generate Embeddings Using HuggingFace Transformers

```python
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedding_model.encode(chunks, show_progress_bar=True)

print(f"Generated {len(embeddings)} embeddings.")
```

---

## 🗃️ Step 3a: Start Chroma Server
```bash
PS C:\Users\pardh\Desktop\NDRA> .venv\Scripts\activate
(.venv) PS C:\Users\pardh\Desktop\NDRA> chroma run --path ./chroma_db


                (((((((((    (((((####
             ((((((((((((((((((((((#########
           ((((((((((((((((((((((((###########
         ((((((((((((((((((((((((((############
        (((((((((((((((((((((((((((#############
        (((((((((((((((((((((((((((#############
         (((((((((((((((((((((((((##############
         ((((((((((((((((((((((((##############
           (((((((((((((((((((((#############
             ((((((((((((((((##############
                (((((((((    #########

Saving data to: ./chroma_db
Connect to Chroma at: http://localhost:8000
Getting started guide: https://docs.trychroma.com/docs/overview/getting-started                                                                                                        

OpenTelemetry is not enabled because it is missing from the config.
Listening on localhost:8000
```

## 🗃️ Step 3b: Store in Chroma Vector DB (Persistent Collection)

```python
import chromadb

chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="ndr_chunks")

ids = [f"chunk-{i}" for i in range(len(chunks))]

collection.add(
    documents=chunks,
    embeddings=embeddings.tolist(),
    ids=ids
)

print("✅ Chunks + embeddings stored in persistent ChromaDB.")
```

---

## 🔍 Step 4: Semantic Search Query Execution

```python
from sentence_transformers import SentenceTransformer
import chromadb

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

query_text = "TABLE OF BENEFITS FOR DOMESTIC COVER"
query_embedding = embedding_model.encode(query_text)

chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_collection(name="ndr_chunks")

results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=5,
    include=["documents", "distances"]
)

for i, doc in enumerate(results["documents"][0]):
    print(f"\n🔍 Result {i+1}")
    print(f"🆔 ID: {results['ids'][0][i]}")
    print(f"📏 Distance: {results['distances'][0][i]:.4f}")
    print(f"📄 Document:\n{doc}")
    print("-" * 60)
```

---

## ✅ Outcome:

- Vector embeddings created and persisted using ChromaDB.
- Natural language semantic queries return top-matching document chunks based on cosine similarity.

---

## 🧠 Tools Used:

- `sentence-transformers (all-MiniLM-L6-v2)`
- `ChromaDB`
- `pickle`

> This phase establishes a fully working semantic document vectorization and retrieval pipeline.
