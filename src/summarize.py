import re, requests
from bs4 import BeautifulSoup

# Try to import trafilatura, but keep it optional (lxml may be missing)
try:
    import trafilatura as _trafi  # type: ignore
except Exception:
    _trafi = None

def _clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def scrape_text(url: str, timeout: int = 20) -> str:
    # Use trafilatura when available, otherwise fall back to BeautifulSoup
    try:
        text = ""
        downloaded = None
        if _trafi is not None:
            try:
                # Some versions of trafilatura.fetch_url don't accept timeout; keep call minimal
                downloaded = _trafi.fetch_url(url)
            except Exception:
                downloaded = None

        if downloaded:
            try:
                text = _trafi.extract(downloaded, favor_recall=True) or ""
            except Exception:
                text = ""

        if not text:
            html = requests.get(url, timeout=timeout).text
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

        return _clean(text)
    except Exception:
        return ""

def quick_bullets(title: str, url: str, max_bullets: int = 4, max_chars: int = 420):
    article = scrape_text(url)
    if not article:
        return [title]
    sentences = re.split(r'(?<=[.!?])\s+', article)[:12]
    bullets = []
    for s in sentences:
        s = _clean(s)
        if 30 < len(s) < 180 and not s.lower().startswith(("advertisement", "subscribe", "sign in")):
            bullets.append(s)
        if len(bullets) >= max_bullets:
            break
    if not bullets:
        bullets = [title]
    joined = []
    total = 0
    for b in bullets:
        if total + len(b) <= max_chars:
            joined.append(b)
            total += len(b)
        else:
            break
    return joined
