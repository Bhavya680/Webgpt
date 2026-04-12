"""
ai_engine/embedder.py — Wrapper module for embedding scraped text into ChromaDB.

Provides an `embed_and_store` function for use by Django views.
"""

import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb


# ── Configuration ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 150


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
    """Split *text* into chunks using semantic-tag-aware boundaries.
    
    Priority split points:
      1. '### ITEM POINT' boundaries (each item = one chunk)
      2. Semantic block tags ([NAVIGATION_MENU], [PRODUCT_GRID], ## TABLE)
      3. Fallback to RecursiveCharacterTextSplitter for remaining content
    """
    # First try: split on semantic boundaries
    semantic_separators = [
        '### ITEM POINT',      # Product/item blocks
        '[ROW]',               # Descriptive row blocks
        '[SITE_NAVIGATION]',   # Navigation blocks
        '[/SITE_NAVIGATION]',
        '## DATA TABLE',       # Data table heading
        '## RAW PAGE CONTENT', # Raw text section
        '[FOOTER]',            # Footer
        '[/FOOTER]',
    ]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=semantic_separators + ["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    
    # Filter out tiny/empty chunks
    chunks = [c.strip() for c in chunks if c.strip() and len(c.strip()) > 20]
    
    print(f"[embedder] Split text into {len(chunks)} chunk(s)")
    return chunks



def clear_collection(collection_name: str) -> None:
    """Deletes an entire collection to prepare for a fresh scrape."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(collection_name)
        print(f"[embedder] Cleared existing collection '{collection_name}'")
    except Exception:
        pass


def embed_and_store(text: str, collection_name: str, source_url: str = "") -> int:
    """Chunk the text, embed it, and store vectors in ChromaDB.

    Parameters
    ----------
    text : str
        The cleaned text to embed.
    collection_name : str
        The ChromaDB collection name — typically str(bot.bot_id).
    source_url : str
        The source URL to tag these vectors with.

    Returns
    -------
    int
        The number of chunks embedded.
    """
    if not text or not text.strip():
        print("[embedder] No text to embed — skipping.")
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0
        
    model = _get_embedding_model()

    print(f"[embedder] Embedding {len(chunks)} chunk(s) ...")
    embeddings = model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)
    embeddings_list = [emb.tolist() for emb in embeddings]

    # Store in ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Note: Collection clearing is now handled externally via clear_collection()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    import uuid
    ids = [f"chunk_{uuid.uuid4().hex[:8]}" for _ in chunks]
    metadatas = [{"source": source_url, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings_list,
        metadatas=metadatas,
    )
    print(f"[embedder] Stored {len(chunks)} vector(s) in collection '{collection_name}'")
    return len(chunks)
