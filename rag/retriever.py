"""
Loads the FAISS index built by rag/build_index.py and exposes a simple
retrieve(query, k) function for the RAG Agent to call.
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss

INDEX_DIR = Path(__file__).resolve().parent / "index"
INDEX_PATH = INDEX_DIR / "faiss.index"
DOCS_PATH = INDEX_DIR / "docs.json"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_index = None
_docs = None


def _load():
    global _model, _index, _docs
    if _model is None:
        if not INDEX_PATH.exists() or not DOCS_PATH.exists():
            raise FileNotFoundError(
                f"No FAISS index found at {INDEX_PATH}. "
                "Run `python rag/build_index.py` first to build it."
            )
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        _index = faiss.read_index(str(INDEX_PATH))
        with open(DOCS_PATH) as f:
            _docs = json.load(f)
    return _model, _index, _docs


def retrieve(query: str, k: int = 5) -> list:
    """
    Returns the top-k most similar documents as a list of dicts:
    [{"id": ..., "category": ..., "type": ..., "text": ..., "score": float}, ...]

    score is L2 distance -- LOWER is more similar (it's a distance, not a
    similarity score), sorted ascending.
    """
    model, index, docs = _load()

    query_embedding = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:  # FAISS returns -1 if fewer than k docs exist
            continue
        doc = dict(docs[idx])
        doc["score"] = float(dist)
        results.append(doc)

    return results
