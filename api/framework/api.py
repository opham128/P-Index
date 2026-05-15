import os
import requests

API_KEY = os.environ.get("WOS_API_KEY", "e79d99c5f006c46e7981921000444ea84e9e0316")   
BASE_URL = "https://api.clarivate.com/apis/wos-starter/v1"
DOCS_URL = f"{BASE_URL}/documents"

HEADERS = {
    "X-ApiKey": API_KEY,
    "Accept": "application/json"
}

def wos_search(query, page=1, limit=50):
    params = {"q": query, "page": page, "limit": limit}
    r = requests.get(DOCS_URL, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def get_records(data):
    return data.get("hits", [])