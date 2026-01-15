
import requests
import json

base_url = "http://127.0.0.1:8000/api"

def login():
    try:
        resp = requests.post(f"{base_url}/auth/login", data={"username": "admin", "password": "admin"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return None
        return resp.json()["access_token"]
    except Exception as e:
        print("Login error:", e)
        return None

def check_strategy(token, name):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{base_url}/strategy/{name}/info", headers=headers)
        print(f"--- Strategy: {name} ---")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
            print("-" * 30)
        else:
            print("Error:", resp.status_code, resp.text)
    except Exception as e:
        print(f"Check {name} error:", e)

token = login()
if token:
    check_strategy(token, "Bollinger Strategy")
    check_strategy(token, "Morning Star")
