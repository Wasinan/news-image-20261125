#!/usr/bin/env python3
"""Build one 1024x1024 newspaper front page summing up 25 Nov 2026.

Renders the four verified stories of the day with PIL only: a masthead,
a full-width lead panel and three columns below it. Run it and it writes
news-image-20261125.png next to this script.
"""

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT_NAME = "news-image-20261125.png"

CANVAS = 1024
MARGIN = 36
PAPER = (245, 239, 224)
PANEL = (255, 253, 245)
INK = (26, 26, 26)
SOFT = (74, 74, 66)
RULE = (26, 26, 26)
RED = (178, 28, 28)
BLUE = (30, 58, 95)
GOLD = (176, 132, 30)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def pick(size, bold=False, serif=False):
    name = "DejaVuSerif-Bold.ttf" if serif else (
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    )
    return ImageFont.truetype(str(FONT_DIR / name), size)


def wrap(draw, text, font, width):
    """Greedy word wrap measured with the real font."""
    lines = []
    for chunk in text.split("\n"):
        words = chunk.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = cur + " " + word
            if draw.textlength(trial, font=font) <= width:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def block(draw, xy, text, font, width, fill=INK, gap=6):
    """Draw wrapped text, return the y just below the last line."""
    x, y = xy
    for line in wrap(draw, text, font, width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + gap
    return y


def fit_block(draw, xy, text, size, width, max_bottom, fill=SOFT, gap=4):
    """Draw body text shrunk until it fits above max_bottom.

    Drops the font size step by step; as a last resort trims the text
    with an ellipsis so nothing ever spills past the panel edge.
    """
    x, y = xy
    while size >= 13:
        font = pick(size)
        lines = wrap(draw, text, font, width)
        if y + len(lines) * (size + gap) <= max_bottom:
            for line in lines:
                draw.text((x, y), line, font=font, fill=fill)
                y += size + gap
            return y
        size -= 1
    font = pick(13)
    lines = wrap(draw, text, font, width)
    room = max(1, (max_bottom - y) // (13 + gap))
    for line in lines[:room]:
        draw.text((x, y), line, font=font, fill=fill)
        y += 13 + gap
    if len(lines) > room and room > 0:
        draw.text((x, y - 13 - gap), lines[room - 1].rstrip(". ") + "…",
                  font=font, fill=fill)
    return y


def headline_fit(draw, text, font_size, width, bold=True):
    """Largest bold font (<= font_size) that wraps the headline in 3 lines."""
    size = font_size
    while size > 18:
        font = pick(size, bold=bold)
        if len(wrap(draw, text, font, width)) <= 3:
            return font
        size -= 2
    return pick(18, bold=bold)


def refinery(draw, x, y, width, height):
    """Refinery silhouette with a flame above the stacks."""
    base = y + height
    # Stacks and tanks.
    draw.rectangle([x, base - 34, x + 26, base], fill=INK)
    draw.rectangle([x + 34, base - 52, x + 52, base], fill=INK)
    draw.rectangle([x + 60, base - 26, x + width - 8, base], fill=INK)
    draw.ellipse([x + 66, base - 40, x + 92, base - 26], fill=INK)
    draw.line([x, base, x + width, base], fill=INK, width=2)
    # Flame above the tallest stack.
    fx = x + 43
    flame = [
        (fx - 14, base - 52), (fx - 8, base - 74), (fx - 2, base - 62),
        (fx + 4, base - 82), (fx + 10, base - 64), (fx + 14, base - 52),
    ]
    draw.polygon(flame, fill=RED)
    inner = [
        (fx - 6, base - 54), (fx - 3, base - 66), (fx + 2, base - 58),
        (fx + 6, base - 54),
    ]
    draw.polygon(inner, fill=GOLD)


def gavel(draw, cx, cy, scale):
    s = scale
    # Head: horizontal bar at the top.
    draw.rounded_rectangle(
        [cx - 42 * s, cy - 48 * s, cx + 42 * s, cy - 22 * s],
        radius=int(6 * s), fill=INK,
    )
    # Handle: vertical, from head down to the block.
    draw.line([cx, cy - 22 * s, cx, cy + 20 * s], fill=INK,
              width=int(10 * s))
    # Sounding block.
    draw.rectangle(
        [cx - 32 * s, cy + 24 * s, cx + 32 * s, cy + 38 * s], fill=RED
    )
    draw.line([cx - 32 * s, cy + 24 * s, cx + 32 * s, cy + 24 * s],
              fill=INK, width=2)


def chart_down(draw, x, y, width, height):
    tops = [0.25, 0.5, 0.45, 0.75, 1.0]
    bw = width // 6
    for i, top in enumerate(tops):
        bx = x + i * (bw + 6)
        bh = int(height * top)
        draw.rectangle([bx, y + height - bh, bx + bw, y + height],
                       fill=BLUE if i < 4 else RED)
    draw.line([x, y + height, x + width, y + height], fill=INK, width=2)
    # Downward arrow across the bars.
    draw.line([x + 4, y + 6, x + width - 10, y + height - 8],
              fill=RED, width=4)
    draw.polygon([
        (x + width - 10, y + height - 8), (x + width - 26, y + height - 14),
        (x + width - 18, y + height + 2),
    ], fill=RED)


def rocket(draw, cx, cy, scale):
    s = scale
    body = [
        (cx, cy - 52 * s),
        (cx + 18 * s, cy - 10 * s),
        (cx + 18 * s, cy + 26 * s),
        (cx - 18 * s, cy + 26 * s),
        (cx - 18 * s, cy - 10 * s),
    ]
    draw.polygon(body, fill=INK)
    draw.polygon([
        (cx - 18 * s, cy + 10 * s), (cx - 34 * s, cy + 30 * s),
        (cx - 18 * s, cy + 26 * s),
    ], fill=INK)
    draw.polygon([
        (cx + 18 * s, cy + 10 * s), (cx + 34 * s, cy + 30 * s),
        (cx + 18 * s, cy + 26 * s),
    ], fill=INK)
    draw.ellipse([cx - 7 * s, cy - 34 * s, cx + 7 * s, cy - 20 * s],
                 fill=GOLD)
    flame = [
        (cx - 10 * s, cy + 26 * s), (cx, cy + 52 * s), (cx + 10 * s, cy + 26 * s),
    ]
    draw.polygon(flame, fill=RED)
    for sx, sy in ((-46, -40), (48, -30), (-52, 18)):
        draw.ellipse([cx + sx * s - 2, cy + sy * s - 2,
                      cx + sx * s + 2, cy + sy * s + 2], fill=BLUE)


LEAD = {
    "kicker": "LEAD  ·  GULF IN FLAMES",
    "title": "Houthis hit Saudi refinery and Riyadh towers",
    "body": (
        "Yemen's Houthis said on Wednesday they struck Saudi Arabia's Ras "
        "Tanura oil refinery — one of the world's largest — and Riyadh's "
        "financial district in three phases. Spokesman Yahya Saree claimed "
        "fires at the refinery; the Saudi-led coalition said air defences "
        "downed four drones over Ras Tanura. A day earlier, a strike on a "
        "tower in the King Abdullah Financial District wounded 11 people, "
        "including two Indians and three Nepalese. Saudi jets hit Yemen's "
        "Hodeidah port overnight in reply. Oil prices climbed on supply fears."
    ),
}

COLUMNS = [
    {
        "kicker": "CHINA  ·  PURGE",
        "title": "Politburo shrinks as Xi's graft net widens",
        "body": (
            "China's anti-graft watchdog opened an investigation into "
            "Shanghai party chief Chen Jining, a member of the Communist "
            "Party's Politburo — the fourth probe into the elite 24-member "
            "body since 2025. It follows the falls of He Weidong, Zhang "
            "Youxia and Ma Xingrui."
        ),
        "art": "gavel",
    },
    {
        "kicker": "MARKETS  ·  AI ROUT",
        "title": "Asian stocks tumble as tariff threat returns",
        "body": (
            "Asian shares slid on Wednesday as fresh US tariff threats hit "
            "sentiment and the AI rally fizzled. MSCI's Asia-Pacific index "
            "outside Japan fell 2.3%; South Korea dropped 5.3% and Taiwan "
            "5.1%, while Japan's Nikkei sank 2.9%. Nvidia gave back 5.9% "
            "after Jensen Huang's return as CEO. Brent slipped to $90.97."
        ),
        "art": "chart",
    },
    {
        "kicker": "SPACE  ·  TIANGONG",
        "title": "Shenzhou-24 carries first foreign astronaut",
        "body": (
            "China's Shenzhou-24 blasted off from Jiuquan at 08:18 Beijing "
            "time and docked with the Tiangong station at 11:56. Aboard: "
            "commander Tang Hongbo, flight engineer Wu Yi and Pakistani "
            "payload specialist Muhammad Zeeshan Ali — the first foreign "
            "astronaut ever to visit Tiangong."
        ),
        "art": "rocket",
    },
]


def paint():
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    draw = ImageDraw.Draw(img)

    # Double outer frame.
    draw.rectangle([10, 10, CANVAS - 11, CANVAS - 11], outline=RULE, width=3)
    draw.rectangle([20, 20, CANVAS - 21, CANVAS - 21], outline=RULE, width=1)

    # Masthead.
    title_font = pick(58, serif=True)
    title = "THE WORLD IN ONE PAGE"
    tw = draw.textlength(title, font=title_font)
    draw.text(((CANVAS - tw) / 2, 34), title, font=title_font, fill=INK)
    draw.line([MARGIN, 118, CANVAS - MARGIN, 118], fill=RULE, width=3)
    date_font = pick(20, bold=True)
    dateline = "WEDNESDAY, 25 NOVEMBER 2026  ·  FOUR STORIES THAT MATTER"
    dw = draw.textlength(dateline, font=date_font)
    draw.text(((CANVAS - dw) / 2, 130), dateline, font=date_font, fill=RED)
    draw.line([MARGIN, 164, CANVAS - MARGIN, 164], fill=RULE, width=1)

    # Lead panel.
    lead_top, lead_bottom = 180, 528
    draw.rectangle(
        [MARGIN, lead_top, CANVAS - MARGIN, lead_bottom], fill=PANEL,
        outline=RULE, width=2
    )
    kick_font = pick(20, bold=True)
    draw.text((MARGIN + 22, lead_top + 16), LEAD["kicker"], font=kick_font,
              fill=RED)
    head_font = headline_fit(draw, LEAD["title"], 46, 680)
    y = block(
        draw,
        (MARGIN + 22, lead_top + 48),
        LEAD["title"],
        head_font,
        680,
        gap=2,
    )
    fit_block(draw, (MARGIN + 22, y + 10), LEAD["body"], 20, 680,
              lead_bottom - 16, gap=5)
    refinery(draw, 782, 330, 150, 92)
    cap_font = pick(15)
    caption = "RAS TANURA, SAUDI ARABIA"
    cw = draw.textlength(caption, font=cap_font)
    draw.text((852 - cw / 2, 440), caption, font=cap_font, fill=SOFT)

    # Divider between lead and columns.
    draw.line([MARGIN, 548, CANVAS - MARGIN, 548], fill=RULE, width=2)

    # Three columns.
    col_w = 300
    gap_x = 26
    col_top = 566
    col_bottom = 946
    for i, col in enumerate(COLUMNS):
        x0 = MARGIN + i * (col_w + gap_x)
        draw.rectangle([x0, col_top, x0 + col_w, col_bottom], fill=PANEL,
                       outline=RULE, width=2)
        inner = x0 + 18
        width = col_w - 36
        if col["art"] == "gavel":
            gavel(draw, x0 + col_w // 2, col_top + 52, 0.85)
        elif col["art"] == "chart":
            chart_down(draw, inner + 30, col_top + 18, width - 60, 56)
        else:
            rocket(draw, x0 + col_w // 2, col_top + 52, 0.85)
        cy = col_top + 96
        draw.text((inner, cy), col["kicker"], font=pick(16, bold=True),
                  fill=RED)
        cy += 28
        hfont = headline_fit(draw, col["title"], 27, width)
        cy = block(draw, (inner, cy), col["title"], hfont, width, gap=2)
        fit_block(draw, (inner, cy + 10), col["body"], 18, width,
                  col_bottom - 14, gap=4)

    # Footer.
    foot_font = pick(15)
    foot = "Sources: Reuters · Xinhua · Yonhap  —  25 Nov 2026"
    fw = draw.textlength(foot, font=foot_font)
    draw.text(((CANVAS - fw) / 2, 964), foot, font=foot_font, fill=SOFT)

    out = HERE / OUT_NAME
    img.save(out, "PNG")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"wrote {out} ({img.size[0]}x{img.size[1]})")
    print(f"sha256 {digest}")
    return out


if __name__ == "__main__":
    paint()
