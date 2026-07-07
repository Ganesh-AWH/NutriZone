import requests

url = "http://127.0.0.1:8000/plan/day"

payload = {
    "age": 30,
    "gender": "female",
    "height": 162,
    "weight": 68,
    "activity_level": "light",
    "goal": "fat_loss",
    "digestive_issues": "ibs",
    "allergies": ["peanut"],
    "culture": "Indian",
    "region": "South",
    "state": "Karnataka"
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
