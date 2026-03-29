import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import json
import time
import sys

BASE_URL="http://127.0.0.1:8000/api"

print("=============================")
# Step 2: Health
try:
    r = requests.get(f"{BASE_URL}/health/")
    print("STEP 2:", r.status_code, r.text)
    if r.status_code != 200:
        sys.exit(1)
except Exception as e:
    print("STEP 2 FAILED:", e)
    sys.exit(1)

print("=============================")
# Step 3: Token
try:
    r = requests.post(f"{BASE_URL}/token/", data={"username":"admin", "password":"your-password"})
    print("STEP 3:", r.status_code, r.text)
    if r.status_code != 200:
        sys.exit(1)
    token = r.json()["token"]
except Exception as e:
    print("STEP 3 FAILED:", e)
    sys.exit(1)

headers = {"Authorization": f"Token {token}"}

print("=============================")
# Step 4: Create Bot
try:
    r = requests.post(f"{BASE_URL}/bots/", headers=headers, json={"name": "Test Bot", "url": "https://example.com"})
    print("STEP 4:", r.status_code, r.text)
    if r.status_code != 201:
        sys.exit(1)
    bot_id = r.json()["bot_id"]
except Exception as e:
    print("STEP 4 FAILED:", e)
    sys.exit(1)

print("=============================")
# Step 5: Wait
try:
    for i in range(30):
        r = requests.get(f"{BASE_URL}/bots/{bot_id}/", headers=headers)
        data = r.json()
        status = data["pages"][0]["status"]
        print(f"STEP 5 (attempt {i}): status={status}")
        if status == "success":
            break
        elif status == "failed":
            print("STEP 5 FAILED: scraper failed")
            sys.exit(1)
        time.sleep(5)
    else:
        print("STEP 5 FAILED: timeout")
        sys.exit(1)
except Exception as e:
    print("STEP 5 FAILED:", e)
    sys.exit(1)

print("=============================")
# Step 6: Ask question
try:
    r = requests.post(f"{BASE_URL}/chat/", headers=headers, json={"message": "What domain is this?", "bot_id": bot_id})
    print("STEP 6:", r.status_code)
    print("Answer JSON:", json.dumps(r.json(), indent=2))
    if r.status_code != 200:
        sys.exit(1)
except Exception as e:
    print("STEP 6 FAILED:", e)
    sys.exit(1)

print("=============================")
# Step 7: Error handling
try:
    r = requests.post(f"{BASE_URL}/chat/", headers=headers, json={"message": "hello", "bot_id": "00000000-0000-0000-0000-000000000000"})
    print("STEP 7:", r.status_code, r.text)
    if r.status_code != 404:
        sys.exit(1)
except Exception as e:
    print("STEP 7 FAILED:", e)
    sys.exit(1)

print("ALL STEPS PASSED")

