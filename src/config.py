import os
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

LI_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LI_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LI_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "")
LI_AUTHOR_URN = os.getenv("LINKEDIN_AUTHOR_URN", "")
LI_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LI_REFRESH_TOKEN = os.getenv("LINKEDIN_REFRESH_TOKEN", "")

BRAND_NAME = os.getenv("BRAND_NAME", "Tech Daily")
LOGO_PATH = os.getenv("LOGO_PATH", "assets/logo.png")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
POSTER_FORMAT = os.getenv("POSTER_FORMAT", "square")  # square | landscape
# Clamp MAX_POSTS to [1..5]
try:
    _max_posts = int(os.getenv("MAX_POSTS", "2"))
except Exception:
    _max_posts = 2
MAX_POSTS = min(5, max(1, _max_posts))

def _get_bool(name: str, default: str = "true") -> bool:
    v = str(os.getenv(name, default)).strip().lower()
    return v in {"1", "true", "yes", "on"}

# When true, do not call LinkedIn APIs; just print actions
DRY_RUN = _get_bool("DRY_RUN", "true")

# Caption/branding configuration
HASHTAGS = os.getenv("HASHTAGS", "#AI #Cloud #Security #Dev #TechNews")
FOOTER_TEXT = os.getenv("FOOTER_TEXT", "auto-generated poster - latest tech")

def ensure_posting_env_or_raise():
    if DRY_RUN:
        return
    missing = []
    if not LI_AUTHOR_URN:
        missing.append("LINKEDIN_AUTHOR_URN")
    if not (LI_ACCESS_TOKEN or LI_REFRESH_TOKEN):
        missing.append("LINKEDIN_ACCESS_TOKEN or LINKEDIN_REFRESH_TOKEN")
    if not LI_CLIENT_ID:
        missing.append("LINKEDIN_CLIENT_ID")
    if not LI_CLIENT_SECRET:
        missing.append("LINKEDIN_CLIENT_SECRET")
    if missing:
        raise ValueError(
            "DRY_RUN=false but required LinkedIn env vars are missing: "
            + ", ".join(missing)
        )
    if not (LI_AUTHOR_URN.startswith("urn:li:person:") or LI_AUTHOR_URN.startswith("urn:li:organization:")):
        raise ValueError(
            "LINKEDIN_AUTHOR_URN must start with 'urn:li:person:' or 'urn:li:organization:'"
        )

RSS_FEEDS = [
    "https://www.theverge.com/rss/index.xml",
    "http://feeds.arstechnica.com/arstechnica/index/",
    "https://www.wired.com/feed/rss",
]
