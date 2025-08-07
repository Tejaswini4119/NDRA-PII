# ragqexec.py
# NDRA | Phase 3B : Fast RAG Pipeline (<4s) + fastllm Primary + Gemini Fallback | Deployments

import os
import time
import re
import chromadb
from chromadb import HttpClient
from dotenv import load_dotenv
from pprint import pprint
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
from langchain_huggingface import HuggingFaceEmbeddings
from querygenai import extract_query_info_llm, rewrite_query
from strqgen import build_structured_query, compute_completeness_score
import google.generativeai as genai
from fastllm import fast_chat  # ✅ Fast Local/API LLM


# --- Load Environment Variables ---
load_dotenv()

# --- Gemini Setup (Fallback) ---
genai_key = os.getenv("GOOGLE_API_KEY")
if genai_key:
    genai.configure(api_key=genai_key)

# --- Embedding Setup ---
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embed_func = embedding_model.embed_query

# Get Chroma host details
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
CHROMA_SSL = os.getenv("CHROMA_SSL", "False").lower() == "true"
# --- Chroma DB Setup ---
chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=CHROMA_SSL)
collection = chroma_client.get_or_create_collection(name="ndr_chunks")
print("Chroma Collection Count:", collection.count())

# --- Wrap LLM Response into JSON Format ---
def wrap_llm_response_to_json(llm_output: str) -> dict:
    try:
        # Try multiple patterns to match "Yes" or "No"
        patterns = [
            r"\*\*1\..*?\*\*\s*(Yes|No)",         # Original format: **1.** Yes
            r"^1\.\s*(Yes|No)",                   # Loose numbered format: 1. Yes
            r"^Answer:\s*(Yes|No)",               # Answer: Yes
            r"^\s*(Yes|No)\b"                     # Just a line starting with Yes/No
        ]

        answer = None
        for pattern in patterns:
            match = re.search(pattern, llm_output, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip().capitalize()
                break

        # If still nothing, fallback to default
        if not answer:
            answer = "No"  # or "Unknown" if you want to be conservative

        # Justification block
        justification_match = re.search(r"\*\*2\..*?\*\*\s*(.*?)(?=\n\s*\*\*3|\Z)", llm_output, re.IGNORECASE | re.DOTALL)
        justification = justification_match.group(1).strip() if justification_match else llm_output.strip()

        return {
            "answer": answer,
            "justification": justification
        }

    except Exception as e:
        return {
            "answer": "No",
            "justification": f"Parsing failed: {str(e)}"
        }


# --- Support Clause Tracing ---
def trace_supporting_clauses(justification: str, clauses: list[str], top_k: int = 3):
    scored = [(i, SequenceMatcher(None, justification.lower(), clause.lower()).ratio()) for i, clause in enumerate(clauses)]
    top_indices = sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]
    return [clauses[i] for i, _ in top_indices]

# --- Semantic Search with Trim in Parallel ---
def semantic_search_parallel(query: str, top_k=5):
    query_vec = embed_func(query)
    results = collection.query(query_embeddings=[query_vec], n_results=top_k)
    raw_chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    def clean(c): return " ".join(c.strip().split())[:400]
    with ThreadPoolExecutor() as executor:
        trimmed_chunks = list(executor.map(clean, raw_chunks))

    return trimmed_chunks, metadatas

# --- RAG Prompt Builder ---
def rag_prompt(rewritten_query: str, clauses: list[str], structured_info: dict) -> str:
    return f"""
You are an Advanced Policy Document Assistant.

A user asked: "{structured_info['original_query']}"
Rewritten query (for clarity): "{rewritten_query}"

Structured query details:
- Intent: {structured_info['intent']}
- Subject: {structured_info.get('subject')}
- Age: {structured_info.get('age')}
- Gender: {structured_info.get('gender')}
- Procedure: {structured_info.get('procedure')}
- Location: {structured_info.get('location')}
- Policy Duration: {structured_info.get('policy_duration')}

Relevant clauses:
{chr(10).join(f"- {clause.strip()}" for clause in clauses)}

Instructions:
1. If the clauses mention surgeries in general (e.g., "in-patient surgeries", "orthopedic procedures"), and the user procedure fits within that category (e.g., knee surgery), consider it as covered unless excluded.
2. If multiple clauses apply, combine reasoning.
3. If unsure, explain what’s missing.

⚠️ If a clause **indirectly implies** a category (orthopedic, musculoskeletal, joint surgeries), assume it's relevant — even if not stated as "knee surgery".

Answer clearly:
1. YES/NO
2. Explanation referencing clauses
3. Final conclusion
""".strip()

# --- Main LLM Inference Handler ---
def generate_llm_response(prompt: str) -> str:
    try:
        # ✅ FastLLM Primary
        return fast_chat(prompt)
    except Exception as fast_error:
        print(f"⚠️ Fast LLM failed, falling back to Gemini: {fast_error}")
        try:
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as gemini_error:
            return f"❌ Both LLMs failed. Gemini error: {str(gemini_error)}"

# --- Full Pipeline ---
def run_rag_pipeline(user_query: str):
    overall_start = time.time()

    # Extract and transform query
    info = extract_query_info_llm(user_query)
    rewritten = rewrite_query(info, user_query)
    structured = build_structured_query(info, rewritten, user_query)
    completeness = compute_completeness_score(structured)

    # Semantic search
    search_start = time.time()
    top_chunks, metadata = semantic_search_parallel(rewritten)
    search_end = time.time()

    # RAG inference
    llm_start = time.time()
    prompt = rag_prompt(rewritten, top_chunks, structured)
    llm_response = generate_llm_response(prompt)
    llm_end = time.time()

    # Parse & explain
    answer_data = wrap_llm_response_to_json(llm_response)
    answer_data["supporting_clauses"] = trace_supporting_clauses(answer_data["justification"], top_chunks)

    overall_end = time.time()

    return {
        "query": user_query,
        "rewritten_query": rewritten,
        "intent": structured["intent"],
        "matched_clauses": top_chunks,
        "answer_structured": answer_data,
        "raw_answer": llm_response,
        "metadata": metadata,
        "timing": {
            "semantic_search": round(search_end - search_start, 4),
            "llm_inference": round(llm_end - llm_start, 4),
            "total": round(overall_end - overall_start, 4)
        }
    }
# --- Backend Model Wrapper ---
from backend.models import QueryResponse

def run_pipeline(query: str, metadata: dict = None) -> QueryResponse:
    result = run_rag_pipeline(query)

    return QueryResponse(
        question=result["query"],
        structured_query={
            "intent": result["intent"]
        },
        final_answer=result["answer_structured"]["answer"],
        matched_clause="\n\n".join(result["answer_structured"]["supporting_clauses"]),
        reason=result["answer_structured"]["justification"],
        metadata={
            "raw_answer": result["raw_answer"],
            "timing": result["timing"],
            "doc_title": metadata.get("doc_title") if metadata else "Unknown"
        }
    )
# --- Example Usage ---  
# if __name__ == "__main__":
#    query = "Does this policy cover brain surgery, and what are the conditions? and policies?"
#    result = run_rag_pipeline(query)
#
#    print("\n🧾 Final Output:")
#    for key, val in result.items():
#        print(f"{key.upper()}:")
#        if isinstance(val, dict):
#            pprint(val)
#        elif isinstance(val, list):
#            for i, v in enumerate(val):
#                if isinstance(v, str):
#                    print(f"  [{i+1}] {v.strip()[:300]}...\n")
#                elif isinstance(v, dict):
#                    print(f"  [{i+1}] Source: {v.get('source', 'N/A')}\n")
#                else:
#                    print(f"  [{i+1}] [Unsupported metadata format]\n")
#        else:
#            print(val)
#        print()
#
#    print("📊 Time Breakdown:")
#    print("🔎 Vector Search: {}s".format(result["timing"]["semantic_search"]))
#    print("🧠 LLM Inference: {}s".format(result["timing"]["llm_inference"]))
#    print("⏱️ Total: {}s".format(result["timing"]["total"]))