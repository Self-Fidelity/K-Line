
import requests
import json

try:
    response = requests.get("http://127.0.0.1:8000/api/strategy/Bollinger%20Strategy/info")
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
