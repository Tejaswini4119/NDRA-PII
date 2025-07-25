#!/usr/bin/env python
# coding: utf-8
# Phase 1B: Contextual Vectorization & Embedding using HF Transformer Inference and Persistent Indexing via Chroma Vector DB with Semantic Search Query Implementation.

import pickle
from sentence_transformers import SentenceTransformer
import chromadb

# Step 1: Load Chunks
with open("chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

print(f"Loaded {len(chunks)} chunks.")

# Step 2: Generate Embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedding_model.encode(chunks, show_progress_bar=True)

# Safety: Convert to list if numpy
embeddings = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

print(f"Generated {len(embeddings)} embeddings.")

# Step 3: Store in ChromaDB
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="ndr_chunks")

# If chunks.pkl is a list of plain strings (without metadata), use a fallback
# Otherwise, if you have per-chunk metadata (like [chunk_text, source]), use that.

# If you didn't yet modify Phase 1A to embed metadata, fallback source:
default_source = "multiple_docs"

ids = [f"chunk-{i}" for i in range(len(chunks))]
metadatas = [{"source": default_source} for _ in chunks]

collection.add(
    documents=chunks,
    embeddings=embeddings,
    ids=ids,
    metadatas=metadatas,
)

print("✅ Chunks + embeddings stored in persistent ChromaDB.")