# Day 3 — Custom RAG Engine + CLI Chatbot

## Goal
Connect our custom fine-tuned SLM (QLoRA adapter on Gemma-2B-IT) to the existing ChromaDB vector store and build an interactive CLI chatbot that performs Retrieval-Augmented Generation.

## Key Discoveries

| Item | Value |
|------|-------|
| Base model (from adapter_config) | `unsloth/gemma-2b-it-bnb-4bit` |
| Adapter location | `./finetuning/my_adapter/` |
| ChromaDB persist dir | `./chroma_db/` |
| Collection name | `webbot_docs` |
| Embedding model | `all-MiniLM-L6-v2` |
| Similarity metric | cosine |

> [!IMPORTANT]
> The adapter's `base_model_name_or_path` is `unsloth/gemma-2b-it-bnb-4bit` — this is Unsloth's pre-quantized 4-bit variant of `google/gemma-2b-it`. We'll use this as our base model to ensure adapter weight compatibility.

## Proposed Changes

---

### Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/Admin/Desktop/Webgpt/requirements.txt)
Add the following packages:
- `transformers` — HuggingFace model loading & pipeline
- `torch` — PyTorch backend
- `accelerate` — efficient model loading/offloading
- `peft` — LoRA/QLoRA adapter support
- `bitsandbytes` — 4-bit quantization (BitsAndBytesConfig)

---

### AI Engine Package

#### [NEW] [\_\_init\_\_.py](file:///c:/Users/Admin/Desktop/Webgpt/ai_engine/__init__.py)
Empty init file to make `ai_engine/` a Python package.

#### [NEW] [model_loader.py](file:///c:/Users/Admin/Desktop/Webgpt/ai_engine/model_loader.py)
- `get_custom_pipeline()` function:
  1. Configure `BitsAndBytesConfig` for 4-bit NF4 quantization with float16 compute dtype
  2. Load base model `unsloth/gemma-2b-it-bnb-4bit` using `AutoModelForCausalLM.from_pretrained()` with quantization config
  3. Load tokenizer from the adapter directory (it has a local tokenizer)
  4. Attach the QLoRA adapter via `PeftModel.from_pretrained(model, "./finetuning/my_adapter/")`
  5. Wrap in `transformers.pipeline("text-generation", ...)` and return

#### [NEW] [rag_engine.py](file:///c:/Users/Admin/Desktop/Webgpt/ai_engine/rag_engine.py)
- Connect to existing ChromaDB at `./chroma_db/`, collection `webbot_docs`
- Load `all-MiniLM-L6-v2` for query embedding (same model used during indexing)
- `while True:` CLI loop:
  1. Accept user question from terminal
  2. Embed the question with sentence-transformers
  3. Query ChromaDB for top 3 matching chunks
  4. Construct prompt: system instruction ("Answer the user's question using ONLY the provided context.") + retrieved context + user question
  5. Pass to `get_custom_pipeline()` for generation
  6. Print the generated answer

## Open Questions

> [!WARNING]
> **GPU Requirement**: 4-bit quantized Gemma-2B requires a CUDA-capable GPU with ~3-4 GB VRAM. Does your machine have a compatible NVIDIA GPU? If not, we may need to adjust the approach (e.g., CPU-only mode with a smaller model, or use GGUF quantization with llama-cpp).

> [!IMPORTANT]
> **bitsandbytes on Windows**: The `bitsandbytes` library historically had limited Windows support. The latest versions (0.43+) include Windows wheels. If installation fails, we may need `bitsandbytes-windows` or an alternative approach.

## Verification Plan

### Automated Tests
```bash
# 1. Verify imports work
python -c "from ai_engine.model_loader import get_custom_pipeline; print('Import OK')"

# 2. Verify ChromaDB connection
python -c "from ai_engine.rag_engine import connect_chroma; c = connect_chroma(); print(f'Chunks: {c.count()}')"
```

### Manual Verification
- Run `python -m ai_engine.rag_engine` and test with questions related to the scraped content
- Verify the model loads the adapter correctly (check for PEFT merge messages in output)
- Confirm generated answers reference the retrieved context, not hallucinated info
