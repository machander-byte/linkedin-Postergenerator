import os
from datetime import datetime
import re
import sys
from .config import MAX_POSTS, POSTER_FORMAT, DRY_RUN, HASHTAGS, ensure_posting_env_or_raise
from .fetch_news import pick_fresh_top
from .summarize import quick_bullets
from .poster import render_poster
from .linkedin_api import upload_image, create_post_with_image


def _ascii_sanitize(text: str) -> str:
    if not text:
        return ""
    # Normalize common Unicode punctuation to ASCII
    replacements = {
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\u2018": "'", "\u2019": "'",  # single quotes
        "\u201C": '"', "\u201D": '"',   # double quotes
        "\u2026": "...",               # ellipsis
        "\u00A0": " ",                 # nbsp
    }
    for k,v in replacements.items():
        text = text.replace(k, v)
    # collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def _shorten(text: str, max_len: int = 140) -> str:
    s = _ascii_sanitize(text)
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "\u2026"  # ASCII-like ellipsis


def run_once():
    try:
        ensure_posting_env_or_raise()
    except Exception as e:
        print("Configuration error:", e)
        sys.exit(1)
    picks = pick_fresh_top(n=MAX_POSTS)
    out_urns = []

    for idx, it in enumerate(picks, start=1):
        title = _shorten(it["title"]) if it.get("title") else ""
        url = it["url"]
        source = it["source"] or "Tech News"

        raw_bullets = quick_bullets(title, url, max_bullets=4)
        bullets = [_ascii_sanitize(b) for b in raw_bullets]
        caption = (
            f"{_ascii_sanitize(title)}\n\n"
            + "\n".join(f"- {b}" for b in bullets)
            + f"\n\nSource: {source}\n{url}\n{HASHTAGS}"
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(os.path.dirname(__file__), "..", "out")
        os.makedirs(out_dir, exist_ok=True)
        img_path = os.path.join(out_dir, f"poster_{POSTER_FORMAT}_{ts}_{idx}.png")
        render_poster(title, bullets, img_path)

        error_occurred = False
        if DRY_RUN:
            print("DRY_RUN=1 Would post:", title, "->", img_path)
            out_urns.append((img_path, None, None))
        else:
            try:
                image_urn = upload_image(img_path)
                post_urn = create_post_with_image(image_urn, caption, visibility="PUBLIC")
                print("Posted:", title, "->", post_urn)
                out_urns.append((img_path, image_urn, post_urn))
            except Exception as e:
                error_occurred = True
                print("Posting failed:", e)

        if (not DRY_RUN) and error_occurred:
            # Exit non-zero if any post fails
            sys.exit(1)

    return out_urns


if __name__ == "__main__":
    try:
        run_once()
    except SystemExit:
        raise
    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(1)
