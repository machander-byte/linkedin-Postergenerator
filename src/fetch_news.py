import feedparser, time, requests, sqlite3, os
from datetime import datetime, timedelta, timezone
from dateutil import parser as dtp
from .config import RSS_FEEDS, NEWS_API_KEY

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seen.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS seen (
            url TEXT PRIMARY KEY,
            first_seen INTEGER
        )""")

def _is_seen(url:str)->bool:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT 1 FROM seen WHERE url=?", (url,))
        return cur.fetchone() is not None

def _mark_seen(url:str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR IGNORE INTO seen(url, first_seen) VALUES(?,?)",
                    (url, int(time.time())))

def _parse_ts(ts):
    try:
        return dtp.parse(ts).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def fetch_from_rss(max_items=10, lookback_hours=24):
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed)
        for e in parsed.entries[:max_items]:
            url = e.get("link")
            title = e.get("title", "").strip()
            published = _parse_ts(e.get("published", e.get("updated","")))
            if url and title and published >= cutoff:
                items.append({
                    "source": parsed.feed.get("title",""),
                    "title": title,
                    "url": url,
                    "published_at": published,
                })
    uniq = {}
    for it in items:
        key = it["url"] or it["title"]
        uniq[key] = it
    items = list(uniq.values())
    items.sort(key=lambda x: x["published_at"], reverse=True)
    return items

def fetch_from_newsapi(max_items=10):
    if not NEWS_API_KEY:
        return []
    url = ("https://newsapi.org/v2/top-headlines"
           "?category=technology&pageSize={}&language=en").format(max_items)
    r = requests.get(url, headers={"X-Api-Key": NEWS_API_KEY}, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    for a in data.get("articles", []):
        if a.get("url") and a.get("title"):
            ts = _parse_ts(a.get("publishedAt"))
            out.append({
                "source": a.get("source",{}).get("name",""),
                "title": a["title"].strip(),
                "url": a["url"],
                "published_at": ts
            })
    out.sort(key=lambda x: x["published_at"], reverse=True)
    return out

def pick_fresh_top(n=2):
    _init_db()
    candidates = fetch_from_rss(max_items=15) + fetch_from_newsapi(max_items=10)
    picks = []
    for it in candidates:
        if len(picks) >= n:
            break
        if not _is_seen(it["url"]):
            picks.append(it)
            _mark_seen(it["url"])
    return picks

