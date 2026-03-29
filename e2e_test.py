import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

print("1. Getting Token...")
res = requests.post(f"{BASE_URL}/token/", json={"username": "admin", "password": "your-password"})
token = res.json().get("token")
headers = {"Authorization": f"Token {token}"}
print(f"Token received: {token[:10]}...")

print("\n2. Creating Bot & Triggering Scrape...")
res2 = requests.post(f"{BASE_URL}/bots/", headers=headers, json={
    "name": "Wiki Python II", 
    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"
})
bot_id = res2.json().get("bot_id")
print(f"Bot created! ID: {bot_id}")

print("\nWaiting 15 seconds for scraping & ChromaDB embedding to finish...")
for i in range(15):
    time.sleep(1)
    print(".", end="", flush=True)
print("\n")

print("3. Testing /api/chat/ Endpoint...")
res3 = requests.post(f"{BASE_URL}/chat/", headers=headers, json={
    "bot_id": bot_id, 
    "message": "What is Python mostly used for?"
})

print(f"Status Code: {res3.status_code}")
try:
    print(f"Response:\n{json.dumps(res3.json(), indent=2)}")
except Exception:
    print(f"Response:\n{res3.text}")
