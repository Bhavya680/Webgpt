import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

print("--- Testing /api/chat/ ---")
headers = {"Authorization": f"Token 43b79daba734ab5101ab0801f482f6168a41c8c9"}
bot_id = "e1863fc2-83a3-431a-b112-a13bd6319315"

res3 = requests.post(f"{BASE_URL}/chat/", headers=headers, json={"bot_id": bot_id, "message": "What is Python mostly used for?"})
print(f"Status: {res3.status_code}")
try:
    print(f"Response: {json.dumps(res3.json(), indent=2)}")
except:
    print(f"Response: {res3.text}")

