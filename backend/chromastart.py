# chroma_start.py

import chromadb

chroma_db = chromadb.ServerSettings(
    host="0.0.0.0",
    port=8000,
    allow_reset=True
)

chromadb.run(settings=chroma_db)
