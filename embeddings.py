# embeddings.py

import os
import pickle
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from chromadb import HttpClient

# ✅ Load environment variables
load_dotenv()

# ✅ Read .env values
CHROMA_HOST = os.getenv("CHROMA_HOST")  # should be: ndra-production.up.railway.app
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 443))  # default 443 if missing
CHROMA_SSL = os.getenv("CHROMA_SSL", "true").lower() == "true"

if not CHROMA_HOST:
    raise ValueError("CHROMA_HOST must be set")

# ✅ Connect to remote Chroma
chroma_client = HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT,
    ssl=CHROMA_SSL,
)

# ✅ Create or get the collection
collection = chroma_client.get_or_create_collection(name="ndr_chunks")

# ✅ Load chunks
with open("chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

print(f"Loaded {len(chunks)} chunks.")

# ✅ Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks, show_progress_bar=True)
embeddings = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

print(f"Generated {len(embeddings)} embeddings.")

# ✅ Create IDs and metadata
ids = [f"chunk-{i}" for i in range(len(chunks))]
metadatas = [{"source": "NDRA_docs"} for _ in chunks]

# ✅ Add to Chroma
collection.add(
    documents=chunks,
    embeddings=embeddings,
    ids=ids,
    metadatas=metadatas
)

print("✅ Successfully pushed chunks to ChromaDB remote server.")
print("Total chunks in collection:", collection.count())