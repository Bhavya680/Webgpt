"""
ai_engine/embedder.py — Wrapper module for embedding scraped text into ChromaDB.

Provides an `embed_and_store` function for use by Django views.
"""

import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb


# ── Configuration ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 2500
CHUNK_OVERLAP = 250


# ── Singleton model cache ──────────────────────────────────────────
_embed_model = None


def _get_embedding_model() -> SentenceTransformer:
    """Load (and cache) the HuggingFace sentence-transformer model."""
    global _embed_model
    if _embed_model is None:
        print(f"[embedder] Loading embedding model: {EMBEDDING_MODEL} ...")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"[embedder] Model loaded — dim={_embed_model.get_sentence_embedding_dimension()}")
    return _embed_model


def chunk_text(text: str) -> list[str]:
    """Split *text* into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    print(f"[embedder] Split text into {len(chunks)} chunk(s)")
    return chunks


def embed_and_store(text: str, collection_name: str) -> None:
    """Chunk the text, embed it, and store vectors in ChromaDB.

    Parameters
    ----------
    text : str
        The cleaned text to embed.
    collection_name : str
        The ChromaDB collection name — typically str(bot.bot_id).
    """
    if not text or not text.strip():
        print("[embedder] No text to embed — skipping.")
        return

    chunks = chunk_text(text)
    model = _get_embedding_model()

    print(f"[embedder] Embedding {len(chunks)} chunk(s) ...")
    embeddings = model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)
    embeddings_list = [emb.tolist() for emb in embeddings]

    # Store in ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if present (re-scrape scenario)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_index": i} for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings_list,
        metadatas=metadatas,
    )
    print(f"[embedder] Stored {len(chunks)} vector(s) in collection '{collection_name}'")
