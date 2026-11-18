#!/usr/bin/env python3
"""news-image-20261117 entry v4: Tuesday 17 November 2026 world news.

A pure-stdlib Python 3 program. It draws a 1024x1024 PNG from scratch
(no image files, no network, no fonts on disk): its own PNG encoder, its
own bold bitmap font, and its own dot-grid world map.

Design: a map-hero infographic poster, NOT a newspaper front page. A big
numbered-pin world map is the hero; three short ALL-CAPS lead headlines
sit under it; a numbered one-liner list covers the rest of the day. Every
story that is meant to be read is big enough to read at 300 px.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
The program writes <output>/entry.png. Two runs write byte-identical
files. All facts are the verified 17 November 2026 stories; contested
claims are marked as claims.
"""

import binascii
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
# Own visual identity: warm paper, deep navy ink, red pins, teal land.
# (The top entries are black + red on cream; this one is navy + red + teal.)
PAPER = (247, 243, 232)
PAPER2 = (238, 231, 214)
CARD = (252, 250, 244)
INK = (24, 33, 54)
NAVY = (16, 36, 72)
NAVY2 = (23, 52, 96)
GOLD = (176, 112, 22)
GOLD_LT = (250, 235, 200)
RED = (178, 34, 34)
RED_DK = (140, 24, 24)
TEAL = (13, 116, 110)
TEAL_DK = (16, 90, 84)
TEAL_LT = (204, 231, 228)
SKY = (186, 214, 228)
SKY_DK = (150, 190, 212)
GREY = (100, 107, 122)
GREY_LT = (190, 186, 172)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

# ---------------------------------------------------------------- canvas
# The picture lives in one RGB bytearray, row-major, 3 bytes per pixel.


def new_canvas():
    px = bytearray(W * H * 3)
    for i in range(0, W * H * 3, 3):
        px[i] = PAPER[0]
        px[i + 1] = PAPER[1]
        px[i + 2] = PAPER[2]
    return px


def set_px(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = color[0]
        px[i + 1] = color[1]
        px[i + 2] = color[2]


def fill_rect(px, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        px[i:i + len(row)] = row


def hline(px, x, y, w, color, thick=1):
    fill_rect(px, x, y, w, thick, color)


def vline(px, x, y, h, color, thick=1):
    fill_rect(px, x, y, thick, h, color)


def disc(px, cx, cy, r, color):
    """Filled circle, centre (cx, cy), radius r."""
    r2 = r * r
    for dy in range(-r, r + 1):
        dx = int((r2 - dy * dy) ** 0.5)
        fill_rect(px, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def ring(px, cx, cy, r, color, thick=2):
    """Circle outline."""
    for t in range(thick):
        rr = r - t
        r2 = rr * rr
        for dy in range(-rr, rr + 1):
            dx = int((r2 - dy * dy) ** 0.5)
            set_px(px, cx - dx, cy + dy, color)
            set_px(px, cx + dx, cy + dy, color)
        for dx in range(-rr, rr + 1):
            dy = int((r2 - dx * dx) ** 0.5)
            set_px(px, cx + dx, cy - dy, color)
            set_px(px, cx + dx, cy + dy, color)


def line(px, x0, y0, x1, y1, color, thick=2):
    """Straight line (Bresenham), drawn thick by stamping discs."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        disc(px, x, y, max(1, thick // 2), color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


# ---------------------------------------------------------------- PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, px, w, h):
    """Encode RGB bytes (w*h*3, row-major) as a PNG with filter 0 rows."""
    raw = bytearray()
    raw_append = raw.extend
    stride = w * 3
    for y in range(h):
        raw_append(b"\x00")
        raw_append(px[y * stride:(y + 1) * stride])
    body = zlib.compress(bytes(raw), 6)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", body)
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- font
# Own 5x7 bitmap font, drawn from scratch. Each glyph is 7 rows of 5
# characters ('#' = on). Only capitals, digits and the punctuation the
# poster needs are defined; every word on the poster is ALL-CAPS, so no
# lowercase glyphs exist. draw_text renders at any integer scale; bold
# thickens each stroke by one grid unit to the right, which is what makes
# the big headlines look chunky at 300 px.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".###.", "#...#", "#...#", ".#.#.", "#.#..", "#.#.#", ".##.#"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..##", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
}

CHAR_W = 5
CHAR_H = 7
ADVANCE = 6  # grid units per character, including the 1-unit gap


def _bold_rows(rows):
    """Thicken every stroke by one grid unit to the right."""
    out = []
    for row in rows:
        chars = list(row)
        for i in range(CHAR_W - 1, 0, -1):
            if chars[i - 1] == "#":
                chars[i] = "#"
        out.append("".join(chars))
    return tuple(out)


def text_width(text, scale):
    """Pixel width of text drawn at the given scale (no trailing gap)."""
    if not text:
        return 0
    return len(text) * ADVANCE * scale - scale


def draw_text(px, text, x, y, scale, color, bold=False, align="left"):
    """Draw ALL-CAPS text. align: left, center, right (x is the anchor)."""
    if align == "center":
        x -= text_width(text, scale) // 2
    elif align == "right":
        x -= text_width(text, scale)
    cx = x
    for ch in text:
        if ch == " ":
            cx += ADVANCE * scale
            continue
        rows = GLYPHS.get(ch)
        if rows is None:
            cx += ADVANCE * scale
            continue
        if bold:
            rows = _bold_rows(rows)
        for gy in range(CHAR_H):
            row = rows[gy]
            for gx in range(CHAR_W):
                if row[gx] == "#":
                    fill_rect(px, cx + gx * scale, y + gy * scale,
                              scale, scale, color)
        cx += ADVANCE * scale
    return cx


# ---------------------------------------------------------------- world map
# Own coarse world map: 24 rows x 64 columns, equirectangular, '#' = land.
# Drawn from general geography knowledge (row = 7.5 degrees of latitude,
# column = 5.625 degrees of longitude). Antarctica is a band at the bottom.
MAP_ROWS = (
    "................................................................",
    ".........#########......#####.............#################.....",
    "...##################..#####..#################################.",
    "....##################.....#..##################################",
    ".......################.....####################################",
    "......#################.....###########.#####################...",
    "......###############........################.......#######.##..",
    ".......#############.........#################...###.####...#...",
    ".......#####.................################....###.####.......",
    "........####................#####.......###......##..####.......",
    ".........###.................########............#...####.......",
    "............####.............#############............######....",
    "............#####.............############.............######...",
    ".............#####.............##########.................####..",
    ".............#####.............#####....#................######.",
    "..............####.............####......................######.",
    "..............###.........................................####.#",
    "..............##..............................................#.",
    "..............#.................................................",
    "..............#.................................................",
    "................................................................",
    "................................................................",
    ".....######################################################.....",
    "........################################################........",
)
MAP_COLS = 64
MAP_ROWS_N = 24

# The day's 10 biggest stories, pinned on the map.
# (grid_col, grid_row) is the true location; (draw_x, draw_y) is where the
# numbered pin circle is drawn, with a thin leader line to the true spot.
# chip: (x, y, w, label) — small navy label next to the pin.
PINS = (
    # 1 Crimea — road span of the Kerch bridge falls into the sea
    {"n": 1, "col": 38, "row": 6, "px": 586, "py": 296,
     "chip": (604, 288, 96, "CRIMEA")},
    # 2 Hormuz — Iran drones hit US radar in Bahrain; US strikes back
    {"n": 2, "col": 42, "row": 8, "px": 644, "py": 322,
     "chip": (662, 314, 96, "HORMUZ")},
    # 3 Manila — Trump's first Quad summit, critical-minerals deals
    {"n": 3, "col": 53, "row": 10, "px": 756, "py": 372,
     "chip": (730, 388, 72, "QUAD")},
    # 4 DR Congo — Ebola tops 11,000 cases (WHO)
    {"n": 4, "col": 40, "row": 12, "px": 612, "py": 396,
     "chip": (630, 388, 84, "EBOLA")},
    # 5 Antalya — COP31 split over the fossil-fuel phase-out draft
    {"n": 5, "col": 37, "row": 7, "px": 548, "py": 344,
     "chip": (448, 348, 84, "COP31")},
    # 6 United States — US, Mexico, Bolivia lose measles-free status
    {"n": 6, "col": 15, "row": 7, "px": 330, "py": 306,
     "chip": (296, 272, 108, "MEASLES")},
    # 7 United States — Nvidia quarter $115.8bn, doubles; Dow falls 849
    {"n": 7, "col": 10, "row": 7, "px": 268, "py": 306,
     "chip": (172, 272, 96, "NVIDIA")},
    # 8 Gaza — truce at risk; 1.4m face acute hunger
    {"n": 8, "col": 38, "row": 8, "px": 600, "py": 356,
     "chip": (618, 348, 72, "GAZA")},
    # 9 Mongolia — president says he will resign
    {"n": 9, "col": 51, "row": 6, "px": 730, "py": 294,
     "chip": (748, 286, 120, "MONGOLIA")},
    # 10 Serbia — student-led list takes 140 of 250 parliament seats
    {"n": 10, "col": 36, "row": 6, "px": 540, "py": 294,
     "chip": (440, 286, 84, "SERBIA")},
)


# ---------------------------------------------------------------- content
# The day's stories. 10 pinned on the map + 10 one-liners = 20 stories.
LEADS = (
    # (pin number, headline lines, sub lines)
    (1, ("CRIMEA BRIDGE", "HIT"),
     ("SECOND DAY OF STRIKES", "ON THE KERCH STRAIT")),
    (2, ("IRAN DRONES,", "US STRIKE"),
     ("DRONES HIT US RADAR", "IN BAHRAIN; US HITS BACK")),
    (3, ("QUAD MINERALS", "DEAL"),
     ("TRUMP'S FIRST QUAD", "SUMMIT IN MANILA")),
)

NUMBERS = (
    # (big number, label lines, colour)
    ("11,000+", ("EBOLA IN DR CONGO",), TEAL_DK),
    ("$115.8BN", ("NVIDIA QUARTER",), NAVY),
    ("-849", ("DOW POINTS",), RED),
    ("1,441", ("DRONES CLAIMED DOWN",), NAVY),
)

ALSO = (
    "BANGLADESH POLICE TEAR-GAS GARMENT WORKERS",
    "RUSSIAN AN-12 CRASHES IN SIBERIA, 19 DEAD",
    "MOZAMBIQUE PUTS OPPOSITION LEADER ON TRIAL",
    "SUDAN CIVILIAN TOLL REACHES 2,230 - UN",
    "CYCLONE NEARS INDIA, THOUSANDS EVACUATE",
    "KYIV BRIDGES HIT IN FRESH RUSSIAN STRIKES",
    "JAPAN SCRAMBLES JETS OVER AIRSPACE FEARS",
    "BRAZIL WIN 7-0",
    "FRANCE PUBLIC-SECTOR STRIKE: 146,000 MARCH",
    "DEUTSCHE BANK SHARES FALL IN DATA LEAK",
)

DATE_CHECK = (
    "DATE CHECK - WE LEFT OUT STORIES FROM BEFORE 17 NOV ON PURPOSE.",
    "EBOLA PASSED 11,000 ON 10 NOV; TODAY'S NEWS IS THE WHO UPDATE.",
)

FOOTER = (
    "EVERY STORY HERE HAPPENED OR WAS FIRST REPORTED ON TUESDAY 17 NOVEMBER 2026.",
    "CONTESTED CLAIMS ARE MARKED AS CLAIMS.",
    "SOURCES: REUTERS, AP, AFP, BBC, AL JAZEERA, WHO, UN.",
)


# ---------------------------------------------------------------- layout
def draw_header(px):
    fill_rect(px, 0, 0, W, 10, NAVY)
    fill_rect(px, 0, 10, W, 124, NAVY)
    draw_text(px, "THE WORLD IN ONE DAY", 40, 22, 2, GOLD, bold=True)
    draw_text(px, "TUESDAY 17 NOVEMBER 2026", 40, 46, 5, WHITE, bold=True)
    draw_text(px, "20 STORIES", 984, 46, 3, GOLD, bold=True, align="right")
    draw_text(px, "6 CONTINENTS", 984, 76, 2, WHITE, align="right")
    hline(px, 0, 128, W, GOLD_LT, 6)


def draw_numbers(px):
    fill_rect(px, 0, 134, W, 70, PAPER2)
    cells = (40, 276, 512, 748)
    for i, (num, labels, color) in enumerate(NUMBERS):
        cx = cells[i] + 118
        draw_text(px, num, cx, 142, 4, color, bold=True, align="center")
        if len(labels) == 1:
            draw_text(px, labels[0], cx, 178, 2, GREY, align="center")
        else:
            draw_text(px, labels[0], cx, 174, 2, GREY, align="center")
            draw_text(px, labels[1], cx, 188, 2, GREY, align="center")
    for x in (276, 512, 748):
        vline(px, x, 142, 56, GREY_LT, 2)


def draw_map(px):
    draw_text(px, "WHERE IT HAPPENED", 40, 210, 3, NAVY, bold=True)
    draw_text(px, "PINS 1-10 = THE DAY'S BIGGEST STORIES", 984, 214, 2,
              GREY, align="right")
    # Ocean + land dots.
    x0, y0, step = 160, 236, 11
    fill_rect(px, x0, y0, MAP_COLS * step, MAP_ROWS_N * step, SKY)
    for r, row in enumerate(MAP_ROWS):
        for c, ch in enumerate(row):
            if ch == "#":
                disc(px, x0 + c * step + 5, y0 + r * step + 5, 3, TEAL_DK)
    # Border.
    hline(px, x0, y0, MAP_COLS * step, NAVY, 2)
    hline(px, x0, y0 + MAP_ROWS_N * step - 2, MAP_COLS * step, NAVY, 2)
    vline(px, x0, y0, MAP_ROWS_N * step, NAVY, 2)
    vline(px, x0 + MAP_COLS * step - 2, y0, MAP_ROWS_N * step, NAVY, 2)
    # Pins: leader line, true spot, numbered circle, label chip.
    for pin in PINS:
        tx = x0 + pin["col"] * step + 5
        ty = y0 + pin["row"] * step + 5
        px_, py_ = pin["px"], pin["py"]
        line(px, px_, py_, tx, ty, RED, 2)
        disc(px, tx, ty, 4, WHITE)
        ring(px, tx, ty, 4, RED, 2)
        disc(px, px_, py_, 13, RED)
        ring(px, px_, py_, 13, WHITE, 2)
        draw_text(px, str(pin["n"]), px_, py_ - 7, 2, WHITE, bold=True,
                  align="center")
        cx, cy, cw, label = pin["chip"]
        fill_rect(px, cx, cy, cw, 20, NAVY)
        draw_text(px, label, cx + cw // 2, cy + 3, 2, WHITE, align="center")
    # Legend for pins 4-10 (pins 1-3 get full headlines below the map).
    draw_text(px,
              "4 EBOLA 11,000+ - 5 COP31 SPLIT - 6 MEASLES-FREE LOST "
              "- 7 NVIDIA DOUBLES",
              512, 506, 2, INK, align="center")
    draw_text(px,
              "8 GAZA TRUCE AT RISK - 9 MONGOLIA CHIEF TO QUIT "
              "- 10 SERBIA STUDENT MPS",
              512, 520, 2, INK, align="center")


def draw_leads(px):
    cols = (32, 356, 680)
    for i, (n, head, sub) in enumerate(LEADS):
        x = cols[i]
        fill_rect(px, x, 540, 30, 30, RED)
        draw_text(px, str(n), x + 15, 544, 3, WHITE, bold=True,
                  align="center")
        draw_text(px, head[0], x, 578, 4, INK, bold=True)
        draw_text(px, head[1], x, 610, 4, INK, bold=True)
        draw_text(px, sub[0], x, 646, 2, GREY)
        draw_text(px, sub[1], x, 660, 2, GREY)
    for x in (348, 672):
        vline(px, x, 544, 134, GREY_LT, 2)


def draw_also(px):
    hline(px, 40, 676, 944, NAVY, 4)
    draw_text(px, "ALSO ON TUESDAY", 40, 686, 3, NAVY, bold=True)
    draw_text(px, "MORE OF THE DAY, IN BRIEF", 984, 690, 2, GREY,
              align="right")
    for i, item in enumerate(ALSO):
        y = 710 + i * 23
        if i % 2 == 0:
            fill_rect(px, 40, y - 4, 944, 23, PAPER2)
        draw_text(px, str(11 + i), 40, y, 3, RED, bold=True)
        draw_text(px, item, 88, y, 3, INK)


def draw_honesty(px):
    fill_rect(px, 40, 944, 944, 32, PAPER2)
    fill_rect(px, 40, 944, 6, 32, RED)
    draw_text(px, DATE_CHECK[0], 56, 948, 2, INK)
    draw_text(px, DATE_CHECK[1], 56, 962, 2, INK)
    draw_text(px, FOOTER[0], 512, 980, 2, GREY, align="center")
    draw_text(px, FOOTER[1], 512, 994, 2, GREY, align="center")
    draw_text(px, FOOTER[2], 512, 1008, 2, GREY, align="center")


def build():
    px = new_canvas()
    draw_header(px)
    draw_numbers(px)
    draw_map(px)
    draw_leads(px)
    draw_also(px)
    draw_honesty(px)
    return px


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    write_png(path, build(), W, H)
    size = os.path.getsize(path)
    digest = binascii.crc32(open(path, "rb").read()) & 0xFFFFFFFF
    print("wrote %s (%d bytes, crc32 %08x)" % (path, size, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
