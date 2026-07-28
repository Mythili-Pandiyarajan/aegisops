"""
Builds a FAISS index over rag/knowledge_base.py's KNOWLEDGE_BASE entries.

Run this once (and again any time the knowledge base changes):
    python rag/build_index.py

Uses sentence-transformers (all-MiniLM-L6-v2 -- small, fast, free, runs
locally, no API calls) to embed each document, then saves:
  - rag/index/faiss.index   -- the FAISS index itself
  - rag/index/docs.json     -- the original doc metadata, in the same
                                order as index vectors, so a FAISS search
                                result (an integer position) maps back to
                                the actual document text.
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss

from rag.knowledge_base import KNOWLEDGE_BASE

INDEX_DIR = Path(__file__).resolve().parent / "index"
INDEX_PATH = INDEX_DIR / "faiss.index"
DOCS_PATH = INDEX_DIR / "docs.json"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def build_index():
    INDEX_DIR.mkdir(exist_ok=True)

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [doc["text"] for doc in KNOWLEDGE_BASE]

    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dimension = embeddings.shape[1]

    # IndexFlatL2: exact nearest-neighbor search, no approximation --
    # fine at this corpus size (a few dozen docs); would swap for
    # IndexIVFFlat or similar only at much larger scale.
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    with open(DOCS_PATH, "w") as f:
        json.dump(KNOWLEDGE_BASE, f, indent=2)

    print(f"Indexed {len(KNOWLEDGE_BASE)} documents -> {INDEX_PATH}")


if __name__ == "__main__":
    build_index()
