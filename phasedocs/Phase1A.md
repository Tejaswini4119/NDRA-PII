# Phase 1A: Document Preprocessing & Semantic Chunking Pipeline Design for Downstream Embedding

> This phase involves ingesting various types of documents, extracting raw text, and applying semantic chunking to prepare for vectorization in the upcoming embedding phase.

---

## 🧩 Step 1: Dependency Setup

**Tools & Libraries Used (conceptually):**
- PDF parsing (`pypdf`)
- DOCX parsing (`python-docx`)
- Native UTF-8 readers for `.txt` / `.md`
- LangChain’s `RecursiveCharacterTextSplitter` for semantic chunking

These ensure flexible document input and consistent chunking boundaries (newlines, sentences, spaces).

---

## 📂 Step 2: Load File

We supported the following formats: **`.pdf`, `.txt`, `.md`, `.docx`**.

Depending on the format:
- PDFs were read page-wise and concatenated.
- DOCX files were read paragraph-wise and joined.
- TXT/MD files were read directly.
- Any unsupported file type raised a clear error.

---

## ✂️ Step 3: Semantic Chunking

After text extraction, we split content using a **recursive, boundary-aware strategy** with:
- **Chunk size:** 500 characters  
- **Overlap:** 100 characters  
- **Separator priority:** `\n\n` → `\n` → `.` → ` ` → fallback

This kept semantic integrity intact and ensured downstream embeddings captured context correctly.

---

## 📥 Step 4: Chunk Output Snapshot

After running this pipeline on a sample policy PDF (`BAJHLIP23020V012223.pdf`), a few representative chunks looked like:

**Chunk 1 (sample):**
```
[Contextual policy clause text …]
```

**Chunk 2 (sample):**
```
[Continuation with overlap to maintain semantic continuity …]
```

**Chunk 3 (sample):**
```
[Further policy definitions / exclusions …]
```

> (Real chunk content redacted here; stored safely in `chunks.pkl` for the next phase.)

---

## 📊 Step 5: Persisting for Downstream Embeddings

- **Total chunks produced:** 481 (for the referenced document).  
- **Output saved as:** `chunks.pkl` (serialized for fast reuse in Phase 1B).

---

## ✅ Status

| Component             | Status                             |
|----------------------|-------------------------------------|
| Supported Formats    | PDF, DOCX, TXT, MD                  |
| Chunking Strategy    | ✅ Recursive, semantic-aware         |
| Overlap Handling     | ✅ 100 chars for continuity          |
| Persistence          | ✅ `chunks.pkl` for Phase 1B         |
| Ready for Embedding  | ✅ Yes                               |

---

## 🔬 Notes

This phase is the **foundation of NDRA's retrieval quality** — by ensuring every chunk is semantically coherent, Phase 1B can efficiently embed & index them for high-precision semantic search.

**Next → Phase 1B:** Contextual Vectorization & Embedding using HF Transformers + Chroma Vector DB with Semantic Search Query Implementation.
