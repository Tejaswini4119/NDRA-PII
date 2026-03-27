#!/usr/bin/env python
# coding: utf-8
# Phase 1A: Document Preprocessing & Semantic Chunking Pipeline Design for Downstream Embedding.


from pypdf import PdfReader
from docx import Document
import glob
import os
import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        reader = PdfReader(file_path)
        return "\n".join([
            page.extract_text() or "" for page in reader.pages
        ])

    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif ext == '.docx':
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text: str, chunk_size=500, overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_text(text)

if __name__ == "__main__":
    doc_dir = "doc/"
    pdf_files = glob.glob(os.path.join(doc_dir, "*.pdf"))

    all_chunks = []

    for file_path in pdf_files:
        print(f"📄 Loading: {file_path}")
        raw_text = load_file(file_path)
        chunks = chunk_text(raw_text)
        all_chunks.extend(chunks)

    # Preview first 5 chunks
    for i, chunk in enumerate(all_chunks[:5]):
        print(f"Chunk {i+1}:\n{chunk}\n{'-'*80}")

    print(f"Total Chunks: {len(all_chunks)}")

    # Save all chunks to a pickle file
    with open("chunks.pkl", "wb") as f:
        pickle.dump(all_chunks, f)

    print("✅ Saved chunks as chunks.pkl")