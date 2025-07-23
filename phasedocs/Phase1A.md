# Phase 1A: Document Preprocessing & Semantic Chunking Pipeline Design for Downstream Embedding
> This phase involves ingesting documents of various formats, extracting clean text, and performing semantic chunking to prepare for downstream embedding and vector storage.

## 🧩 Step 1: Import Dependencies

```python
from pypdf import PdfReader
from docx import Document
import os
import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter
```

---

## 📂 Step 2: Load File Based on Extension

Supports `.pdf`, `.txt`, `.md`, and `.docx` formats. Uses `pypdf`, `docx`, and standard file reading mechanisms.

```python
def load_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        reader = PdfReader(file_path)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    elif ext == '.txt' or ext == '.md':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
        
    elif ext == '.docx':
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")
```

---

## ✂️ Step 3: Semantic Chunking via LangChain

Uses `RecursiveCharacterTextSplitter` for intelligent chunking based on semantic boundaries (newlines, periods, spaces, etc.)

```python
def chunk_text(text, chunk_size=500, overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)
```

---

## 📥 Step 4: Load File and Apply Chunking

Update `file_path` to your target document. Prints first 5 chunks for inspection.

```python
file_path = "BAJHLIP23020V012223.pdf"  # change this to your file path
raw_text = load_file(file_path)
chunks = chunk_text(raw_text)

for i, chunk in enumerate(chunks[:5]):
    print(f"Chunk {i+1}:\n{chunk}\n{'-'*80}")
```

---

## 📊 Step 5: Store Chunked Output for Next Phase

```python
print(f"Total Chunks: {len(chunks)}")

with open("chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)

print("✅ Saved chunks as chunks.pkl")
```

---

## ✅ Status

- Document format support: `.pdf`, `.txt`, `.md`, `.docx`
- Text extracted and chunked using LangChain
- Chunked output saved in `chunks.pkl` for downstream embedding phase

---

## 🔬 Notes

> This is a **prototype version** for Phase 1A. The output will be used in:
> **Phase 1B: Contextual Vectorization & Embedding Pipeline Engineering using HF Transformer Inference with Persistent Indexing via Chroma Vector DB**
