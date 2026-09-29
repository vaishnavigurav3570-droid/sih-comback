import os
import requests
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("MOSDAC_USERNAME")
password = os.getenv("MOSDAC_PASSWORD")

print("User:", username)
print("Pass:", "*" * len(password) if password else "None")

try:
    res = requests.post("https://mosdac.gov.in/download_api/gettoken", json={
        "username": username,
        "password": password
    })
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
