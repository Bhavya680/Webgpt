"""
embedder.py — Embedding pipeline + ChromaDB vector store for WebBot AI.

Reads cleaned text from data/scraped.txt, chunks it with LangChain's
RecursiveCharacterTextSplitter, embeds the chunks using HuggingFace
all-MiniLM-L6-v2, and persists the vectors in a local ChromaDB instance
(chroma_db/ folder).

Usage:
    python embedder.py              # Embed scraped.txt into ChromaDB
    python embedder.py --query      # Interactive query mode (skip re-embedding)

Day 2 of the 7-day WebBot AI sprint.
"""

import os
import sys

from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb


# ── Configuration ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRAPED_FILE = os.path.join(PROJECT_ROOT, "data", "scraped.txt")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

COLLECTION_NAME = "webbot_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ~500 words ≈ ~2 500 characters (average 5 chars/word)
CHUNK_SIZE = 2500        # in characters
CHUNK_OVERLAP = 250      # ~50 words overlap to keep context continuity


# ── Text loading ────────────────────────────────────────────────────
def load_text(path: str) -> str:
    """Load the full text from *path* and return it as a single string."""
    if not os.path.exists(path):
        print(f"[!] File not found: {path}")
        print("    Run scraper.py first to generate data/scraped.txt")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read().strip()

    if not text:
        print(f"[!] {path} is empty. Scrape a page first.")
        sys.exit(1)

    print(f"[*] Loaded {len(text):,} characters from {path}")
    return text


# ── Chunking ────────────────────────────────────────────────────────
def chunk_text(text: str) -> list[str]:
    """Split *text* into overlapping chunks using LangChain's
    RecursiveCharacterTextSplitter.

    The splitter tries to split along paragraph breaks (``\\n\\n``),
    then single newlines, then sentences, then words — in that order —
    to keep each chunk as semantically coherent as possible.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    print(f"[*] Split text into {len(chunks)} chunk(s)  "
          f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


# ── Embedding ───────────────────────────────────────────────────────
def get_embedding_model() -> SentenceTransformer:
    """Load (and cache) the HuggingFace sentence-transformer model."""
    print(f"[*] Loading embedding model: {EMBEDDING_MODEL} ...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"[*] Model loaded — embedding dimension: {model.get_sentence_embedding_dimension()}")
    return model


def embed_chunks(model: SentenceTransformer, chunks: list[str]) -> list[list[float]]:
    """Return dense vector embeddings for each chunk."""
    print(f"[*] Embedding {len(chunks)} chunk(s) ...")
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_numpy=True)
    return [emb.tolist() for emb in embeddings]


# ── ChromaDB vector store ──────────────────────────────────────────
def get_chroma_collection(reset: bool = False) -> chromadb.Collection:
    """Return (or create) the ChromaDB collection.

    Parameters
    ----------
    reset : bool
        If True, delete the existing collection first so we start fresh.
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[*] Deleted old collection '{COLLECTION_NAME}'")
        except Exception:
            pass  # collection didn't exist yet

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )
    print(f"[*] ChromaDB collection '{COLLECTION_NAME}' ready  "
          f"(persist_dir={CHROMA_DIR})")
    return collection


def store_vectors(
    collection: chromadb.Collection,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """Upsert chunk texts + their embeddings into ChromaDB."""
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": SCRAPED_FILE, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"[*] Stored {len(chunks)} vector(s) in ChromaDB")


# ── Full pipeline ──────────────────────────────────────────────────
def run_pipeline() -> tuple[chromadb.Collection, SentenceTransformer]:
    """End-to-end: load → chunk → embed → store.  Returns collection + model."""
    text = load_text(SCRAPED_FILE)
    chunks = chunk_text(text)
    model = get_embedding_model()
    embeddings = embed_chunks(model, chunks)
    collection = get_chroma_collection(reset=True)
    store_vectors(collection, chunks, embeddings)
    return collection, model


# ── Query / CLI test ────────────────────────────────────────────────
def query_loop(
    collection: chromadb.Collection,
    model: SentenceTransformer,
    top_k: int = 3,
) -> None:
    """Interactive loop: user types a question → embed → retrieve top-k chunks."""
    print("\n" + "=" * 72)
    print("  INTERACTIVE QUERY MODE  (type 'exit' or 'quit' to stop)")
    print("=" * 72 + "\n")

    while True:
        try:
            question = input("❓ Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question or question.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break

        # Embed the question
        q_embedding = model.encode([question], convert_to_numpy=True)[0].tolist()

        # Retrieve from ChromaDB
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"],
        )

        documents = results["documents"][0]
        distances = results["distances"][0]

        if not documents:
            print("  ⚠  No matching chunks found.\n")
            continue

        print(f"\n  Top {len(documents)} result(s):\n")
        for rank, (doc, dist) in enumerate(zip(documents, distances), start=1):
            similarity = 1 - dist   # cosine distance → cosine similarity
            preview = doc[:200].replace("\n", " ")
            if len(doc) > 200:
                preview += " ..."
            print(f"  [{rank}]  similarity={similarity:.4f}")
            print(f"       {preview}")
            print()


# ── Entry point ─────────────────────────────────────────────────────
def main() -> None:
    query_only = "--query" in sys.argv

    if query_only:
        # Skip re-embedding; just open existing collection + model
        print("[*] Query-only mode — loading existing ChromaDB + model ...")
        model = get_embedding_model()
        collection = get_chroma_collection(reset=False)
        if collection.count() == 0:
            print("[!] Collection is empty. Run  python embedder.py  first (no --query).")
            sys.exit(1)
    else:
        collection, model = run_pipeline()

    query_loop(collection, model)


if __name__ == "__main__":
    main()
