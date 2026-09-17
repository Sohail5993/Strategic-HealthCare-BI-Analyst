"""
brand_charts.py
-----------------
Adds a centered brand header (logo + title + tagline) to the top of every
chart PNG in outputs/charts/, matching the portfolio site's homepage brand
block. Writes branded versions to outputs/charts_branded/.
"""

from PIL import Image, ImageDraw, ImageFont
import glob
import os

CHART_DIR = "../outputs/charts"
OUT_DIR = "../outputs/charts_branded"
LOGO_PATH = "../assets/logo.png"

BRAND_TITLE = "Strategic HealthCare BI Analyst"
BRAND_TAGLINE = "Transforming HealthCare Complexities into Growth Blueprints"

os.makedirs(OUT_DIR, exist_ok=True)


def get_font(size, bold=False, italic=False):
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    candidates_italic = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    ]
    candidates_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    paths = candidates_bold if bold else (candidates_italic if italic else candidates_reg)
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def build_header(width, logo_h=64, pad_top=18, pad_bottom=14, gap=10):
    """Builds a centered header block: logo, title, tagline, hairline rule."""
    logo = Image.open(LOGO_PATH).convert("RGBA")
    scale = logo_h / logo.height
    logo = logo.resize((int(logo.width * scale), logo_h), Image.LANCZOS)

    title_font = get_font(22, bold=True)
    tagline_font = get_font(13, italic=True)

    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    title_bbox = d.textbbox((0, 0), BRAND_TITLE, font=title_font)
    tagline_bbox = d.textbbox((0, 0), BRAND_TAGLINE, font=tagline_font)
    title_w, title_h = title_bbox[2] - title_bbox[0], title_bbox[3] - title_bbox[1]
    tagline_w, tagline_h = tagline_bbox[2] - tagline_bbox[0], tagline_bbox[3] - tagline_bbox[1]

    text_block_w = max(title_w, tagline_w)
    content_w = logo.width + gap + text_block_w
    content_h = max(logo.height, title_h + 6 + tagline_h)

    header_h = pad_top + content_h + pad_bottom + 14  # +14 for rule spacing
    header = Image.new("RGB", (width, header_h), "white")
    d = ImageDraw.Draw(header)

    start_x = (width - content_w) // 2
    logo_y = pad_top + (content_h - logo.height) // 2
    header.paste(logo, (start_x, logo_y), logo)

    text_x = start_x + logo.width + gap
    text_block_h = title_h + 6 + tagline_h
    text_y = pad_top + (content_h - text_block_h) // 2

    d.text((text_x, text_y), BRAND_TITLE, font=title_font, fill=(27, 42, 74))  # navy
    d.text((text_x, text_y + title_h + 6), BRAND_TAGLINE, font=tagline_font, fill=(91, 100, 114))  # gray

    rule_y = pad_top + content_h + 8
    d.line([(width * 0.06, rule_y), (width * 0.94, rule_y)], fill=(200, 204, 210), width=2)

    return header


def brand_image(path, out_path):
    chart = Image.open(path).convert("RGB")
    header = build_header(chart.width)
    combined = Image.new("RGB", (chart.width, header.height + chart.height), "white")
    combined.paste(header, (0, 0))
    combined.paste(chart, (0, header.height))
    combined.save(out_path)
    print(f"Branded: {out_path}")


for path in sorted(glob.glob(f"{CHART_DIR}/*.png")):
    fname = os.path.basename(path)
    brand_image(path, f"{OUT_DIR}/{fname}")

print("Done.")
