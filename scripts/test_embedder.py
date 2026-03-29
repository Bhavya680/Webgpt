import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Smoke test for the Day 2 embedding pipeline — no interactive input needed."""
from embedder import (
    load_text, chunk_text, get_embedding_model, embed_chunks,
    get_chroma_collection, store_vectors, SCRAPED_FILE,
)

# 1. Run the full pipeline
text = load_text(SCRAPED_FILE)
chunks = chunk_text(text)
model = get_embedding_model()
embeddings = embed_chunks(model, chunks)
collection = get_chroma_collection(reset=True)
store_vectors(collection, chunks, embeddings)

print(f"\n{'='*60}")
print(f"  PIPELINE COMPLETE")
print(f"  Chunks: {len(chunks)}  |  Vectors stored: {collection.count()}")
print(f"{'='*60}\n")

# 2. Automated query test
test_questions = [
    "What is Python used for?",
    "How do vector databases work?",
    "What web frameworks does Python have?",
]

for q in test_questions:
    q_emb = model.encode([q], convert_to_numpy=True)[0].tolist()
    results = collection.query(
        query_embeddings=[q_emb], n_results=3,
        include=["documents", "distances"],
    )
    docs = results["documents"][0]
    dists = results["distances"][0]

    print(f"Q: {q}")
    for i, (doc, d) in enumerate(zip(docs, dists)):
        sim = 1 - d
        preview = doc[:180].replace("\n", " ")
        if len(doc) > 180:
            preview += " ..."
        print(f"  [{i+1}] sim={sim:.4f}  {preview}")
    print()

print("All tests passed!")

