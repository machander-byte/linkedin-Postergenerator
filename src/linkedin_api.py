import os, time, json, requests
from .config import (
    LI_ACCESS_TOKEN, LI_REFRESH_TOKEN, LI_CLIENT_ID, LI_CLIENT_SECRET,
    LI_REDIRECT_URI, LI_AUTHOR_URN
)

BASE = "https://api.linkedin.com"
HEADERS_BASE = {
    "X-Restli-Protocol-Version": "2.0.0",
    "LinkedIn-Version": "202506",  # YYYYMM
}

TOKENS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "li_tokens.json")
os.makedirs(os.path.dirname(TOKENS_PATH), exist_ok=True)


def _should_retry_status(code: int) -> bool:
    return code == 429 or 500 <= code < 600


def _request_with_retry(method: str, url: str, *, headers=None, json=None, data=None, timeout=30, max_retries=3):
    last_exc = None
    for attempt in range(max_retries):
        try:
            r = requests.request(method, url, headers=headers, json=json, data=data, timeout=timeout)
        except requests.RequestException as e:
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"Network error contacting {url}: {e}") from e
        if _should_retry_status(r.status_code):
            if attempt < max_retries - 1:
                retry_after = r.headers.get("Retry-After")
                wait = int(retry_after) if (retry_after and retry_after.isdigit()) else (2 ** attempt)
                time.sleep(wait)
                continue
        return r
    if last_exc:
        raise last_exc
    raise RuntimeError("Request retry loop ended unexpectedly")

def _get_token():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN") or ""
    if token:
        return token
    if os.path.exists(TOKENS_PATH):
        return json.load(open(TOKENS_PATH)).get("access_token","")
    return ""

def _save_token(tok:str):
    json.dump({"access_token": tok, "saved_at": int(time.time())}, open(TOKENS_PATH,"w"))

def maybe_refresh():
    if not LI_REFRESH_TOKEN:
        return _get_token()
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": LI_REFRESH_TOKEN,
        "client_id": LI_CLIENT_ID,
        "client_secret": LI_CLIENT_SECRET,
    }
    r = _request_with_retry("POST", url, data=data, timeout=20)
    if r.ok:
        token = r.json().get("access_token")
        if token:
            _save_token(token)
            return token
    return _get_token()

def upload_image(image_path:str)->str:
    token = maybe_refresh()
    init_url = f"{BASE}/rest/images?action=initializeUpload"
    r = _request_with_retry(
        "POST",
        init_url,
        headers={**HEADERS_BASE, "Authorization": f"Bearer {token}"},
        json={"initializeUploadRequest": {"owner": LI_AUTHOR_URN}},
        timeout=30,
    )
    r.raise_for_status()
    value = r.json()["value"]
    upload_url = value["uploadUrl"]
    image_urn = value["image"]

    try:
        with open(image_path, "rb") as f:
            up = _request_with_retry("PUT", upload_url, data=f, timeout=60)
        up.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            raise RuntimeError("Image upload forbidden. Check token scopes and upload URL validity.") from e
        raise
    return image_urn

def create_post_with_image(image_urn:str, commentary:str, visibility="PUBLIC")->str:
    token = maybe_refresh()
    url = f"{BASE}/rest/posts"
    payload = {
        "author": LI_AUTHOR_URN,
        "commentary": commentary,
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": { "id": image_urn }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    r = _request_with_retry(
        "POST",
        url,
        headers={**HEADERS_BASE,
                 "Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=30,
        max_retries=3,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        if r.status_code == 400:
            raise RuntimeError("Invalid request. Check author URN and payload format.") from e
        if r.status_code == 401:
            raise RuntimeError("Unauthorized. Access token expired or invalid; check refresh flow.") from e
        if r.status_code == 403:
            raise RuntimeError("Forbidden. Token missing required scopes (w_member_social / w_organization_social).") from e
        if r.status_code == 404:
            raise RuntimeError("Resource not found. Verify author URN and image URN.") from e
        raise
    return r.headers.get("x-restli-id","")
