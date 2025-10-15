from PIL import Image, ImageDraw, ImageFont
import textwrap, os
from .config import BRAND_NAME, LOGO_PATH, POSTER_FORMAT, FOOTER_TEXT

SIZES = {
    "square":    (1080, 1080),
    "landscape": (1200, 627)
}

def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, path)

def _font(path, size):
    try:
        return ImageFont.truetype(_resolve_path(path), size=size)
    except:
        return ImageFont.load_default()

def render_poster(title: str, bullets: list, out_path: str):
    W, H = SIZES.get(POSTER_FORMAT, SIZES["square"])
    img = Image.new("RGB", (W, H), "#0B1020")
    draw = ImageDraw.Draw(img)

    title_font = _font("assets/fonts/Poppins-SemiBold.ttf", 56 if W >= 1080 else 46)
    body_font = _font("assets/fonts/Inter-Regular.ttf", 36 if W >= 1080 else 30)
    meta_font = _font("assets/fonts/Inter-Regular.ttf", 28)

    padding = 64
    x = padding
    y = padding

    logo_path = _resolve_path(LOGO_PATH)
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        scale = 120 / max(logo.size)
        logo = logo.resize((int(logo.size[0] * scale), int(logo.size[1] * scale)))
        img.paste(logo, (W - padding - logo.width, padding), logo)
    draw.text((x, y), BRAND_NAME, font=meta_font, fill="#9EA7C3")
    y += 70

    wrapped = textwrap.fill(title, width=28 if W >= 1080 else 24)
    draw.text((x, y), wrapped, font=title_font, fill="white")
    y += draw.multiline_textbbox((x, y), wrapped, font=title_font)[3] - y + 32

    for b in bullets:
        bullet = "- " + b
        wrap = textwrap.fill(bullet, width=38 if W >= 1080 else 34)
        draw.text((x, y), wrap, font=body_font, fill="#DCE3FF")
        y += draw.multiline_textbbox((x, y), wrap, font=body_font)[3] - y + 18
        if y > H - 180:
            break

    draw.line([(padding, H - 120), (W - padding, H - 120)], fill="#223", width=2)
    draw.text((padding, H - 100), FOOTER_TEXT, font=meta_font, fill="#9EA7C3")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return out_path
