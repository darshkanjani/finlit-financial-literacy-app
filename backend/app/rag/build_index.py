"""

Builds a FAISS vector index from local knowledge base files.

What this does:
- Reads docs from: app/rag/knowledge_base/sources/
- Splits them into chunks
- Embeds each chunk using a local sentence-transformers model
- Writes:
  - app/rag/knowledge_base/chunks.json   (chunk text + metadata)
  - app/rag/knowledge_base/index.faiss   (FAISS index over embeddings)

Why FAISS:
- Fast semantic search ("meaning", not keywords)
- Uni-project friendly: offline, repeatable, explainable

How to run:
  python -m app.rag.build_index

Notes:
- First run will download the embedding model (once) into your cache.
- Keep chunks.json committed? Up to you. Usually yes for reproducibility, or no if you prefer building in setup.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

# faiss-cpu
import faiss

# local embeddings
from sentence_transformers import SentenceTransformer


KB_DIR = Path(__file__).resolve().parent / "knowledge_base"
SOURCES_DIR = KB_DIR / "sources"
INDEX_PATH = KB_DIR / "index.faiss"
CHUNKS_PATH = KB_DIR / "chunks.json"

# Small + decent default. You can swap later if you want.
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking knobs (keep simple)
CHUNK_CHAR_LEN = 900
CHUNK_CHAR_OVERLAP = 120


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str


def _read_text_files(folder: Path) -> list[tuple[str, str]]:
    """
    Returns list of (filename, text).
    Supports .txt and .md.
    """
    out: list[tuple[str, str]] = []
    if not folder.exists():
        raise RuntimeError(f"knowledge_base/sources folder not found: {folder}")

    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".txt", ".md"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        out.append((p.name, text))
    return out


def _clean_text(s: str) -> str:
    # basic cleanup so embeddings aren’t garbage
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


def _chunk_text(text: str, *, chunk_len: int, overlap: int) -> Iterable[str]:
    """
    Naive char-based chunking with overlap.
    Good enough for a uni project, predictable.
    """
    if not text:
        return []
    text = _clean_text(text)
    if len(text) <= chunk_len:
        return [text]

    chunks = []
    i = 0
    while i < len(text):
        j = min(len(text), i + chunk_len)
        chunk = text[i:j].strip()
        if chunk:
            chunks.append(chunk)
        if j >= len(text):
            break
        i = max(0, j - overlap)
    return chunks


def _make_chunks() -> list[Chunk]:
    files = _read_text_files(SOURCES_DIR)
    chunks: list[Chunk] = []

    for fname, raw in files:
        for idx, chunk_text in enumerate(_chunk_text(raw, chunk_len=CHUNK_CHAR_LEN, overlap=CHUNK_CHAR_OVERLAP)):
            chunks.append(
                Chunk(
                    chunk_id=f"{fname}::chunk{idx}",
                    source=fname,
                    text=chunk_text,
                )
            )

    if not chunks:
        raise RuntimeError("No chunks created. Add .md/.txt files under knowledge_base/sources/")
    return chunks


def _embed(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    """
    Returns float32 embeddings shaped (n, dim).
    We normalize so cosine similarity becomes dot-product.
    """
    emb = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
    emb = emb.astype("float32")
    return emb


def main():
    KB_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[RAG] Reading sources from: {SOURCES_DIR}")
    chunks = _make_chunks()
    print(f"[RAG] Chunks: {len(chunks)}")

    print(f"[RAG] Loading embedding model: {DEFAULT_MODEL_NAME}")
    model = SentenceTransformer(DEFAULT_MODEL_NAME)

    texts = [c.text for c in chunks]
    emb = _embed(model, texts)
    dim = emb.shape[1]
    print(f"[RAG] Embedding dim: {dim}")

    # FAISS index for cosine similarity:
    # if embeddings are normalized, cosine sim = dot product
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    # Save index + chunk metadata
    faiss.write_index(index, str(INDEX_PATH))

    payload = [{"chunk_id": c.chunk_id, "source": c.source, "text": c.text} for c in chunks]
    CHUNKS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[RAG] Wrote: {INDEX_PATH}")
    print(f"[RAG] Wrote: {CHUNKS_PATH}")
    print("[RAG] Done.")


if __name__ == "__main__":
    main()
