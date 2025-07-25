# ragqexec.py
# NDRA | Phase 3A : Contextual Response Synthesis (Clause Retrieval & RAG Prompting)

import os
import time
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from querygenai import extract_query_info_llm, rewrite_query
from strqgen import build_structured_query, compute_completeness_score
from chromadb import Client
from chromadb.config import Settings
import google.generativeai as genai  # ✅ fixed alias
from dotenv import load_dotenv

# --- Environment Setup ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# 🔹 Initialize HuggingFace Embeddings (same model used during indexing)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embed_func = embedding_model.embed_query

# 🔹 Connect to local persistent Chroma DB
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="ndr_chunks")
print("Chroma Collection Count:", collection.count())


def semantic_search(query: str, top_k=5):
    """
    Perform semantic search on Chroma DB to retrieve top-k relevant clauses.
    """
    query_vec = embed_func(query)
    results = collection.query(query_embeddings=[query_vec], n_results=top_k)
    return results["documents"][0], results["metadatas"][0]


def rag_prompt(rewritten_query: str, chunks: list[str], structured_info: dict) -> str:
    """
    Generate a context-aware prompt for the LLM using relevant document clauses and query metadata.
    """
    prompt = f"""
You are an Advanced Policy Document Assistant.

A user asked: "{structured_info['original_query']}"

Structured query details:
- Intent: {structured_info['intent']}
- Subject: {structured_info.get('subject')}
- Age: {structured_info.get('age')}
- Gender: {structured_info.get('gender')}
- Procedure: {structured_info.get('procedure')}
- Location: {structured_info.get('location')}
- Policy Duration: {structured_info.get('policy_duration')}

Relevant clauses:
{chr(10).join(f"- {clause.strip()}" for clause in chunks)}

Based on the above, you must provide:
1. A clear YES/NO answer (if applicable)
2. Explanation referencing the clause
3. Final decision

Return only final answer with short justification.
"""
    return prompt.strip()


def generate_llm_response(prompt: str) -> str:
    """
    Generate an LLM response using Gemini Pro model.
    """
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)
    return response.text.strip()


def run_rag_pipeline(user_query: str):
    overall_start = time.time()
    """
    End-to-end RAG pipeline: 
    → extract intent and fields 
    → rewrite and structure query 
    → retrieve relevant clauses 
    → generate contextual response.
    """
    info = extract_query_info_llm(user_query)
    rewritten = rewrite_query(info, user_query)
    structured = build_structured_query(info, rewritten, user_query)
    completeness = compute_completeness_score(structured)

    print("🔍 Semantic Search Initiated...")
    search_start = time.time()
    top_chunks, metadata = semantic_search(rewritten)
    search_end = time.time()

    print("🧠 Prompting LLM with context...")
    llm_start = time.time()
    prompt = rag_prompt(rewritten, top_chunks, structured)
    llm_response = generate_llm_response(prompt)
    llm_end = time.time()

    overall_end = time.time()

    return {
        "query": user_query,
        "rewritten_query": rewritten,
        "intent": structured["intent"],
        "matched_clauses": top_chunks,
        "answer": llm_response,
        "completeness_score": completeness,
        "metadata": metadata,
        "timing": {
            "semantic_search": round(search_end - search_start, 4),
            "llm_inference": round(llm_end - llm_start, 4),
            "total": round(overall_end - overall_start, 4)
        }
    }


# 🔹 Optional CLI test
if __name__ == "__main__":
    query = "Does this policy cover knee surgery, and what are the conditions?"
    result = run_rag_pipeline(query)

    print("\n🧾 Final Output:")
    for key, val in result.items():
        print(f"{key.upper()}:\n{val}\n")


    print("📊 Time Breakdown:")
    print("🔎 Vector Search: {}s".format(result["timing"]["semantic_search"]))
    print("🧠 LLM Inference: {}s".format(result["timing"]["llm_inference"]))
    print("⏱️ Total: {}s".format(result["timing"]["total"]))


## test code (remove later)

import chromadb
from sentence_transformers import SentenceTransformer

# Connect to ChromaDB HTTP server
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(name="ndr_chunks")

# Use sentence-transformers to embed the query
model = SentenceTransformer("all-MiniLM-L6-v2")
query = "Does this policy cover knee surgery, and what are the conditions?"
query_embedding = model.encode(query).tolist()

# Perform similarity search using query embedding
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    include=["documents", "distances"],
)

# Display results
documents = results.get("documents", [[]])[0]
distances = results.get("distances", [[]])[0]

print(f"🔎 Total results found: {len(documents)}")

if not documents:
    print("⚠️ No relevant chunks were found for your query.")
else:
    for i, (doc, dist) in enumerate(zip(documents, distances)):
        print(f"\n--- Match {i+1} (similarity score: {1 - dist:.4f}) ---")  # Higher is better
        print(doc[:500])

