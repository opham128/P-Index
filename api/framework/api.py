import os
import requests

# Primary and secondary API keys for Web of Science (WOS) access.
# The primary key is taken from the environment variable WOS_API_KEY.
# The secondary key can be set via WOS_API_KEY_SECOND or hard‑coded as needed.
PRIMARY_WOS_API_KEY = os.environ.get("WOS_API_KEY")
SECONDARY_WOS_API_KEY = os.environ.get("WOS_API_KEY_SECOND")
# Ordered list of keys to try. If the first hits a rate limit, we fall back to the next.
WOS_API_KEYS = [k for k in [PRIMARY_WOS_API_KEY, SECONDARY_WOS_API_KEY] if k]


BASE_URL = "https://api.clarivate.com/apis/wos-starter/v1"
DOCS_URL = f"{BASE_URL}/documents"

def _make_headers(api_key):
    return {
        "X-ApiKey": api_key,
        "Accept": "application/json"
    }

def wos_search(query, page=1, limit=50):
    params = {"q": query, "page": page, "limit": limit}
    for api_key in WOS_API_KEYS:
        headers = _make_headers(api_key)
        try:
            r = requests.get(DOCS_URL, headers=headers, params=params, timeout=30)
            if r.status_code == 429:
                # Rate limit hit – try the next key
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            # Network or HTTP error – if not a rate limit, re‑raise
            if r is not None and r.status_code == 429:
                continue
            raise e
    # If we exit the loop, all keys exhausted
    raise Exception("WOS_RATE_LIMIT_EXHAUSTED")


def get_records(data):
    return data.get("hits", [])