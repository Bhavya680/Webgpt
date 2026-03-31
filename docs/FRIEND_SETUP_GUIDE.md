# 🚀 SiteBot Project Setup Guide

Welcome to the **SiteBot** repository! Follow these steps to get the project running on your local machine.

## 📋 Prerequisites
Ensure you have the following installed:
- **Python 3.10+**
- **Git**
- **Virtualenv** (optional but recommended)

---

## 🛠️ Step-by-Step Installation

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone <repository-url>
cd Webgpt
```

### 2. Create a Virtual Environment
It's best to keep dependencies isolated:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (copy from below or use the provided example):
```env
SECRET_KEY=your-random-secret-key
DEBUG=True

# Database (Uses SQLite by default, but ready for Postgres)
DB_NAME=webbot_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Remote LLM Inference (Google Colab via ngrok)
# Get the latest URL from the project owner if this one is expired
COLAB_API_URL=https://hadley-undeclarative-gratifiedly.ngrok-free.dev/generate

# HuggingFace Token (For vector embeddings)
HF_TOKEN=your-huggingface-token
```

### 5. Initialize the Database
Run migrations to set up the Django tables:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Demo User
You'll need a user to access the dashboard:
```bash
# Create a superuser for admin access
python manage.py createsuperuser

# OR use this shortcut for the demo user
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('demouser', 'demouser@example.com', 'DemoPass123!')"
```

### 7. Launch the Application
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

---

## 🤖 AI & RAG Configuration
This project uses **ChromaDB** for vector storage and **Sentence Transformers** for embeddings.
- **Inference**: The actual LLM logic is offloaded to a Google Colab notebook via the `COLAB_API_URL`.
- **Scanning**: When you add a new bot, it will scrape the URL and build a local vector index automatically.

---

## 🆘 Troubleshooting
- **Connection Refused**: Ensure the `COLAB_API_URL` is correct and the Colab instance is active.
- **Missing Dependencies**: Run `pip install -r requirements.txt` again if you see `ImportError`.
- **Database Errors**: If switching to Postgres, ensure your local Postgres server is running and the credentials in `.env` match.
