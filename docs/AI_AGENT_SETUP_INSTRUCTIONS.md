# INSTRUCTIONS FOR AI AGENT (Copy & Paste this entire file into the chat on your friend's laptop)

**Hello AI Agent!** Please act as a Senior Full Stack Engineer. I need your help to configure and start a highly specific Django WebBot Backend project on my machine. 

Please execute the following **Setup Plan** step-by-step. Do not skip any steps. After each major phase, summarize your success before moving on.

---

## 🛠 PHASE 1: Environment & Dependencies
1. Check the current directory structure to ensure you are in the `Webgpt` root folder.
2. If it does not exist, create a new Python Virtual Environment named `venv` in this root directory using `python -m venv venv`.
3. Activate the virtual environment. 
4. Upgrade `pip` to the latest version.
5. Install all libraries by running `pip install -r requirements.txt`. 

## ⚙️ PHASE 2: Environment Variables
1. At the root of the project, create a file named `.env`.
2. Write the following identical text into `.env`:
   ```env
   SECRET_KEY=webgpt-secure-random-secret-key-123!
   DEBUG=True
   DB_NAME=db.sqlite3
   USE_FINETUNED=False
   ```

## 🗄️ PHASE 3: Database & Auth Setup
1. Run Django migrations to initialize the SQLite database:
   * Execute: `python manage.py makemigrations`
   * Execute: `python manage.py migrate`
2. Create the default admin account by running our custom script:
   * Execute: `python scripts/create_admin.py`
   *(Note: This creates a superuser with username `admin` and password `password123`)*

## 📂 PHASE 4: Directory Structure Validation
1. Ensure the following directories exist in the root (create them if missing):
   * `local_storage/finetuning/`
   * `local_storage/data/`
   * `chroma_db/`
2. The `ai_engine` modules strictly rely on `local_storage/` being present to load local AI model data, so verify its existence.

## 🚀 PHASE 5: Server Startup & Verification
1. Start the Django development server using: `python manage.py runserver`
2. If the server starts successfully, use a background command or HTTP test script to ping `http://127.0.0.1:8000/api/health/` to confirm it returns HTTP 200 OK.
3. **IMPORTANT WARNING for Windows Users:** When hitting the AI routes (like `/api/chat/`), the `bitsandbytes` C++ library may occasionally cause a silent Exit Code 0 crash if the physical disk space is extremely full or if natively loading `unsloth` 4-bit weights fails. 
   * If this hardware limitation occurs, run the offline verification script: `python scripts/standalone_rag_test.py` to independently prove that our vector matching and database integration works perfectly.

**Please begin with PHASE 1 and let me know when the server is fully operational!**
