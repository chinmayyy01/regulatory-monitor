import os
import requests
from dotenv import load_dotenv

load_dotenv()

response = requests.post(
    os.getenv("SLACK_WEBHOOK_URL"),
    json={
        "text": "RegIntel AI test message"
    },
    timeout=10
)

print("Status:", response.status_code)
print("Response:", response.text)