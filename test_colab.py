import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webbot.settings')
django.setup()

from django.conf import settings

COLAB_URL = settings.COLAB_API_URL
print(f"Testing Colab API at: {COLAB_URL}")

# Test 1 — health check
print("\n--- Test 1: Health Check ---")
try:
    r = requests.get(f"{COLAB_URL.replace('/generate', '')}/health", timeout=300)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Health check failed: {e}")

# Test 2 — generation
print("\n--- Test 2: Generation ---")
prompt = (
    "<start_of_turn>user\n"
    "Hello, this is a test from the backend terminal!\n"
    "<end_of_turn>\n"
    "<start_of_turn>model\n"
)

try:
    r = requests.post(
        COLAB_URL,
        json={"prompt": prompt},
        headers={"Content-Type": "application/json"},
        timeout=300,
    )
    print(f"HTTP Status: {r.status_code}")
    data = r.json()
    if "answer" in data:
        print(f"Answer: {data['answer']}")
    else:
        print(f"Error returned: {data}")
except requests.Timeout:
    print("Request timed out — model is still loading or Colab is slow")
except Exception as e:
    print(f"Request failed: {e}")