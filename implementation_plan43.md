# SiteBot/WebBot — Full Project Setup Plan

## Background

You have **documentation files** and a **fine-tuned QLoRA adapter** (`gemma-2b-it`), but **no actual project code**. This plan creates the entire Django backend project from scratch, synthesizing requirements from all 4 reference documents.

### What We Have
| Asset | Status |
|-------|--------|
| `local_storage/finepuning/my_adapter/` (adapter weights, tokenizer, config) | ✅ Present (~78MB) |
| Django project (`manage.py`, `webbot/`, `core/`, etc.) | ❌ Missing |
| `requirements.txt` | ❌ Missing |
| `ai_engine/` package | ❌ Missing |
| `scripts/` (create_admin, verify, RAG test) | ❌ Missing |
| `.env` file | ❌ Missing |
| Database (`db.sqlite3`) | ❌ Missing |

---

## User Review Required

> [!IMPORTANT]
> **GPU Availability**: The QLoRA adapter requires a CUDA-capable NVIDIA GPU (~3-4GB VRAM). Do you have one? If not, we'll add CPU fallback mode (slower but functional) and optionally support the Google Colab remote inference endpoint (`COLAB_API_URL`) mentioned in one of the guides.

> [!IMPORTANT]
> **Scope Decision**: The guides describe two modes of operation:
> 1. **Local AI mode** — load the QLoRA model locally for inference
> 2. **Remote Colab mode** — offload LLM inference to a Google Colab Notebook via ngrok URL
>
> Should I implement both, or just local mode?

> [!WARNING]
> **Adapter path typo**: Your adapter is at `local_storage/finepuning/my_adapter/` (note: "finepuning" not "finetuning"). Some guides reference `./finetuning/my_adapter/`. I'll make the code point to the actual path and also create a symlink/alias for compatibility.

---

## Proposed Changes

### Phase 1: Django Project Scaffold

#### [NEW] `requirements.txt`
Core dependencies synthesized from all guides:
```
django>=4.2,<5.0
djangorestframework
django-cors-headers
python-dotenv
requests
beautifulsoup4
langchain
langchain-community
sentence-transformers
chromadb
transformers
torch
accelerate
peft
bitsandbytes
certifi
```

#### [NEW] `manage.py`
Standard Django management script pointing to `webbot.settings`.

#### [NEW] `webbot/` (Django project config)
- `__init__.py`
- `settings.py` — loads from `.env`, configures SQLite, REST framework, CORS, installed apps
- `urls.py` — root URL configuration, includes `core.urls` under `/api/`
- `wsgi.py` / `asgi.py`

---

### Phase 2: Core App (Models + API)

#### [NEW] `core/` (Django app)
- `__init__.py`
- `models.py` — `Bot` model (name, url, owner, created_at, status), `ChatMessage` model (bot FK, question, answer, timestamp)
- `serializers.py` — DRF serializers for Bot, ChatMessage
- `views.py` — API views:
  - `HealthCheckView` — GET `/api/health/` returns `{"status": "ok"}`
  - `BotListCreateView` — CRUD for bots
  - `ChatView` — POST `/api/chat/` accepts `{bot_id, question}`, runs RAG pipeline, returns answer
  - `ScanView` — POST `/api/scan/` triggers scraping + embedding for a bot URL
- `urls.py` — route definitions
- `admin.py` — register models

---

### Phase 3: AI Engine

#### [NEW] `ai_engine/__init__.py`

#### [NEW] `ai_engine/scraper.py`
- `scrape_url(url)` — uses `requests` + `BeautifulSoup` to extract text from a website
- Saves raw text to `local_storage/data/{bot_id}_scraped.txt`

#### [NEW] `ai_engine/embedder.py`
- `build_knowledge_base(bot_id, text)` — chunks text via LangChain `RecursiveCharacterTextSplitter`
- Embeds chunks using `all-MiniLM-L6-v2` via `sentence-transformers`
- Stores in ChromaDB at `./chroma_db/` with collection per bot (namespace: `bot_{id}`)

#### [NEW] `ai_engine/model_loader.py`
- `get_custom_pipeline()`:
  1. Configure `BitsAndBytesConfig` for 4-bit NF4 quantization
  2. Load base model `unsloth/gemma-2b-it-bnb-4bit`
  3. Load tokenizer from `./local_storage/finepuning/my_adapter/`
  4. Attach QLoRA adapter via `PeftModel`
  5. Wrap in `transformers.pipeline("text-generation")`
- CPU fallback if CUDA unavailable (loads in float32, slower)

#### [NEW] `ai_engine/rag_engine.py`
- `get_answer(bot_id, question)`:
  1. Embed user question with `all-MiniLM-L6-v2`
  2. Query ChromaDB collection `bot_{id}` for top 3 chunks
  3. Construct RAG prompt with system instruction + context + question
  4. Generate answer via `get_custom_pipeline()`
  5. Return answer text
- CLI mode: `python -m ai_engine.rag_engine` runs interactive chat loop

---

### Phase 4: Scripts

#### [NEW] `scripts/create_admin.py`
- Creates superuser `admin` / `password123` if not exists (uses `django.setup()`)

#### [NEW] `scripts/standalone_rag_test.py`
- Tests ChromaDB connection and vector search independently (no model loading)

#### [NEW] `scripts/verify_day5.py`
- Automated verification: checks imports, DB connection, ChromaDB, health endpoint

---

### Phase 5: Environment & Directory Setup

#### [NEW] `.env`
```env
SECRET_KEY=webgpt-secure-random-secret-key-123!
DEBUG=True
DB_NAME=db.sqlite3
USE_FINETUNED=False
```

#### Directories to create
- `local_storage/data/`
- `chroma_db/`
- (Already exists: `local_storage/finepuning/my_adapter/`)

---

### Phase 6: Database Init & Server Start

1. `python manage.py makemigrations core`
2. `python manage.py migrate`
3. `python scripts/create_admin.py`
4. `python manage.py runserver`
5. Verify `http://127.0.0.1:8000/api/health/` returns 200

---

## Open Questions

> [!IMPORTANT]
> 1. **Do you have an NVIDIA GPU?** This determines if we set `USE_FINETUNED=True` by default or stick with remote/CPU fallback.
> 2. **Do you have a Colab API URL?** If yes, I'll add remote inference support as a fallback.
> 3. **Is there a git repo to clone the actual project code from?** The guides mention `git clone <repository-url>` — if you have the repo URL, I can clone it instead of building from scratch.

---

## Verification Plan

### Automated Tests
```powershell
# 1. Health check
curl http://127.0.0.1:8000/api/health/

# 2. Import verification
python -c "from ai_engine.model_loader import get_custom_pipeline; print('Import OK')"

# 3. ChromaDB verification
python -c "import chromadb; c = chromadb.PersistentClient('./chroma_db'); print('ChromaDB OK')"

# 4. Full verification script
python scripts/verify_day5.py
```

### Manual Verification
- Browse to `http://127.0.0.1:8000/admin/` and login with `admin`/`password123`
- Test the RAG pipeline via CLI: `python -m ai_engine.rag_engine`
