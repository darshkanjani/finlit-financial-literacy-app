"""

Runtime retriever for FAISS-based RAG.

What this does:
- Loads chunks.json and index.faiss
- Embeds the user query with the same model
- Searches FAISS for top-k similar chunks
- Returns chunks + metadata (for "sources")

Design notes:
- Keep it small: return text + source + score
- Advice/chat service can attach these chunks into the LLM prompt
- If index files are missing, return [] (so app still runs)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


KB_DIR = Path(__file__).resolve().parent / "knowledge_base"
INDEX_PATH = KB_DIR / "index.faiss"
CHUNKS_PATH = KB_DIR / "chunks.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class RetrievedChunk:
    chunk_id: str
    source: str
    text: str
    score: float


_model: SentenceTransformer | None = None
_index: faiss.Index | None = None
_chunks: list[dict] | None = None


def _load_once() -> None:
    global _model, _index, _chunks

    if _model is not None and _index is not None and _chunks is not None:
        return

    if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        # RAG optional. App should still work without it.
        _model = None
        _index = None
        _chunks = None
        return

    _model = SentenceTransformer(MODEL_NAME)
    _index = faiss.read_index(str(INDEX_PATH))
    _chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))


def _embed_query(q: str) -> np.ndarray:
    assert _model is not None
    v = _model.encode([q], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    return v


def retrieve(query: str, *, top_k: int = 4, min_score: float = 0.25) -> list[RetrievedChunk]:
    """
    Returns best matching chunks for the query.

    Scores are cosine-like (dot product on normalized vectors).
    Typical useful range is ~0.25 to ~0.75 depending on content.
    """
    _load_once()
    if _model is None or _index is None or _chunks is None:
        return []

    qv = _embed_query(query)
    scores, idxs = _index.search(qv, top_k)

    out: list[RetrievedChunk] = []
    for score, i in zip(scores[0].tolist(), idxs[0].tolist()):
        if i < 0:
            continue
        if score < min_score:
            continue
        ch = _chunks[i]
        out.append(
            RetrievedChunk(
                chunk_id=str(ch["chunk_id"]),
                source=str(ch["source"]),
                text=str(ch["text"]),
                score=float(score),
            )
        )
    return out


def _make_kb_url(source: str, chunk_id: str) -> str:
    """
    AdviceSource requires a URL string.
    We use a stable pseudo-URL so frontend can display/copy it.
    """
    # example: kb://budgeting_basics.md#c12
    return f"kb://{source}#{chunk_id}"


def to_advice_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    """
    STRICT shape for AdviceOut.sources: list[AdviceSource]
    AdviceSource = { title: str, url: str }
    """
    return [{"title": c.source, "url": _make_kb_url(c.source, c.chunk_id)} for c in chunks]


def to_chat_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    """
    Richer sources for chat (ChatOut.sources is list[dict]).
    """
    return [
        {
            "title": c.source,
            "url": _make_kb_url(c.source, c.chunk_id),
            "chunk_id": c.chunk_id,
            "score": round(c.score, 3),
        }
        for c in chunks
    ]
