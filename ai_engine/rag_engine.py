import os
import chromadb
from sentence_transformers import SentenceTransformer
from ai_engine.model_loader import get_custom_pipeline

def get_answer(question: str, bot_id: str) -> str:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    client = chromadb.PersistentClient(path='./chroma_db/')
    try:
        collection = client.get_collection(name=str(bot_id))
        if collection.count() == 0:
            return "I don't have enough information yet. Please wait for the website to finish processing."
    except Exception:
        return "I don't have enough information yet. Please wait for the website to finish processing."
        
    q_embedding = embedder.encode([question], convert_to_numpy=True)[0].tolist()
    
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=15
    )
    
    documents = results["documents"][0] if results and "documents" in results and results["documents"] else []
    
    if not documents:
        return "I could not find relevant information to answer your question."
        
    chunks_block = "\n\n".join(documents)
    
    prompt = (
        "<start_of_turn>user\n"
        "You are a helpful assistant. Answer using ONLY the context below.\n"
        "If the answer is not in the context, say: I don't have that information.\n\n"
        "Context:\n"
        f"{chunks_block}\n\n"
        f"Question: {question}\n"
        "<end_of_turn>\n"
        "<start_of_turn>model\n"
    )
    
    pipe = get_custom_pipeline()
    
    outputs = pipe(
        prompt,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True
    )
    
    generated_text = outputs[0]["generated_text"]
    
    marker = "<start_of_turn>model\n"
    if marker in generated_text:
        answer = generated_text.split(marker)[-1].strip()
    else:
        answer = generated_text.replace(prompt, "").strip()
        
    return answer
