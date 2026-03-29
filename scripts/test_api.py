import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000/api"

print("--- Testing /api/token/ ---")
res = requests.post(f"{BASE_URL}/token/", json={"username": "admin", "password": "your-password"})
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")

token = res.json().get("token")
headers = {"Authorization": f"Token {token}"}

print("\n--- Testing /api/bots/ ---")
res2 = requests.post(f"{BASE_URL}/bots/", headers=headers, json={"name": "Wiki Python", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"})
print(f"Status: {res2.status_code}")
print(f"Response: {res2.text}")

bot_id = res2.json().get("bot_id")

print("\nWaiting 10 seconds for the background scraping to finish...")
time.sleep(10)

print("\n--- Testing /api/chat/ ---")
res3 = requests.post(f"{BASE_URL}/chat/", headers=headers, json={"bot_id": bot_id, "message": "What is Python mostly used for?"})
print(f"Status: {res3.status_code}")
try:
    print(f"Response: {json.dumps(res3.json(), indent=2)}")
except:
    print(f"Response: {res3.text}")

