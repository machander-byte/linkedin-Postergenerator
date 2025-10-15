import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.fetch_news import pick_fresh_top
from src.summarize import quick_bullets
from src.poster import render_poster


def main():
    items = pick_fresh_top(n=1)
    print('Fetched items:', len(items))
    if items:
        it = items[0]
        title = it['title']
        url = it['url']
        bullets = quick_bullets(title, url, max_bullets=3)
    else:
        title = 'Tech Daily - Sample Poster'
        bullets = [
            'No network or feeds available; using sample content.',
            'Customize .env and requirements, then rerun.',
            'This verifies poster rendering offline.'
        ]

    out_dir = os.path.join(os.path.dirname(__file__), 'out')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'test_poster.png')
    render_poster(title, bullets, out_path)
    print('Poster saved to', out_path)


if __name__ == '__main__':
    main()

