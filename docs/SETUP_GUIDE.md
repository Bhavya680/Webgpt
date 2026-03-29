# WebBot AI — Project Setup Guide

This guide will help you set up and run the WebBot AI project on a new machine. It assumes you already have all the project files (including the scripts, requirements, and adapter weights).

---

## 1. Prerequisites

Before starting, ensure you have the following installed on your machine:
- **Python 3.10 or 3.11** (Check by opening a terminal and typing `python --version`)
- **NVIDIA GPU (Strongly Recommended)**: The model uses 4-bit `bitsandbytes` quantization, which is heavily optimized for NVIDIA graphics cards (GTX/RTX series). If you only have a CPU or an unsupported older GPU (like GT 710), the chatbot will run, but it will be **extremely slow** (it may take 10+ minutes to generate an answer).

---

## 2. Setting Up the Environment

It is best to use a virtual environment so you don't mess up your global Python installation. Open an Administrator PowerShell or Command Prompt in the project folder and follow these steps:

### Step A: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step B: Activate the Environment
```powershell
# For PowerShell:
.\venv\Scripts\Activate.ps1

# For Command Prompt:
.\venv\Scripts\activate.bat
```
*(You should see `(venv)` appear at the start of your terminal line).*

---

## 3. Install Dependencies

With the virtual environment active, install all the required libraries. The `requirements.txt` file already contains everything you need.

Run this command:
```powershell
pip install -r requirements.txt
```

<details>
<summary>Click to see what is being installed</summary>

- `requests`, `beautifulsoup4` (For Web Scraping)
- `langchain`, `sentence-transformers`, `chromadb` (For vector chunking and searching)
- `transformers`, `torch`, `accelerate`, `peft`, `bitsandbytes` (For loading the QLoRA AI model in 4-bit)

</details>

---

## 4. Running the Pipeline

If you were given the `chroma_db` folder and `data/scraped.txt`, you can skip to Step C. If you start from scratch, do everything in order:

### Step A: Scrape the Data
This gets the raw text from the target website.
```powershell
python scraper.py
```

### Step B: Build the Knowledge Base
This reads the scraped text, chops it into pieces, calculates vector embeddings, and stores them in ChromaDB.
```powershell
python embedder.py
```

### Step C: Run the CLI Chatbot
This connects everything together. It loads your custom fine-tuned Gemma-2B-IT SLM model, searches ChromaDB for your question, and strictly answers based on context.
```powershell
python -m ai_engine.rag_engine
```

**Note:** The first time you run this, it will download the base model (`gemma-2b-it-bnb-4bit`) from Hugging Face, which is about ~1.5 GB. Ensure you have at least 3-4 GB of free disk space.
PS C:\Users\Admin\Desktop\Webgpt> cd 'c:\Users\Admin\Desktop\Webgpt'
hon.exe -c "import torch; print('\n--- SYSTEM CHECK hon
---'); print('CUDA (NVIDIA GPU) Available:', torch.c');uda.is_available()); print('--- SYSTEM CHECK ---\n')_av"