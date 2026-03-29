# 🚀 WebBot Project: Universal Setup Guide

This guide provides a professional, step-by-step walkthrough to set up the **WebBot AI Backend** on any Windows machine. Follow these steps exactly to ensure the AI models and Django server run smoothly.

---

## 📋 1. Prerequisites

Before starting, ensure you have the following installed:
*   **Python 3.10 or 3.11**: [Download from Python.org](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
*   **Git**: [Download from git-scm.com](https://git-scm.com/).
*   **Disk Space**: You need at least **12GB of free space** on your C: drive for model weights and environment.
*   **Hardware (Recommended)**: NVIDIA GPU with 8GB+ VRAM for Gemma-2B fine-tuning. If you don't have a GPU, the system will run on CPU (slower).

---

## 🛠 2. Initial Setup

### Step A: Clone and Navigate
Open terminal (PowerShell or CMD) and run:
```powershell
# Navigate to where you want the project
cd Desktop
git clone <repository-url>  # or copy the folder
cd Webgpt
```

### Step B: Create Virtual Environment
Isolate your libraries to avoid conflicts:
```powershell
python -m venv venv
.\venv\Scripts\activate
```
*You should now see `(venv)` at the start of your terminal command line.*

### Step C: Install Dependencies
Install all required AI and Web libraries:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ 3. Configuration

### Step A: Environment Variables
Create a file named `.env` in the root folder and paste this template:
```env
SECRET_KEY=generate-a-random-string-here
DEBUG=True
USE_FINETUNED=False

# Database (Using SQLite by default)
DB_NAME=db.sqlite3
```

### Step B: Database Migration
Prepare the local SQLite database:
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Step C: Create Admin User
Run our custom script to quickly create an admin account:
```powershell
python scripts/create_admin.py
```
*Default login: username: `admin` | password: `password123`*

---

## 🚀 4. Running the Project

### Start the Django Server
```powershell
python manage.py runserver
```
The API is now live at `http://127.0.0.1:8000/`.

---

## 🧪 5. Testing & Verification

We have provided built-in scripts in the `scripts/` folder to verify your setup:

1.  **Health Check**: Visit `http://127.0.0.1:8000/api/health/` in your browser.
2.  **Full Verification**: Run the automated test suite:
    ```powershell
    python scripts/verify_day5.py
    ```
3.  **RAG Sandbox**: Test the retrieval and answer engine without starting the whole server:
    ```powershell
    python scripts/standalone_rag_test.py
    ```

---

## 📁 Project Structure Overview
*   `webbot/` - Core Django configuration files.
*   `core/` - Database models and API views.
*   `ai_engine/` - Logic for Scraping, Embedding (ChromaDB), and LLM loading.
*   `scripts/` - All testing and utility scripts.
*   `local_storage/` - Where AI models and scraped data are stored.
*   `docs/` - Documentation and planning files.

---

## ⚠️ Troubleshooting
*   **SSL Errors**: If the scraper fails, ensure you are using the latest `certifi` package (`pip install --upgrade certifi`).
*   **CUDA/GPU Not Found**: If AI is slow, ensure you have torch installed with CUDA support (`pip install torch --index-url https://download.pytorch.org/whl/cu121`).
*   **Model Crash**: Ensure you have enough disk space and RAM (8GB+ minimum).
