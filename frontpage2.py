"""frontpage2.py — the RICH edition of the news-image-20261123 page.

The verified dossier of frontpage.py (35 stories, Monday 23 November
2026, every figure two-sourced, the five AFP-wire briefs flagged),
rendered in the full-colour illustrated style of the winning daily
pages: gradient skies and seas in the hero scenes, a coloured
mini-illustration on every card, coloured certainty pills, a bold
landmass world map on a deep navy-to-teal sea, and a dense,
grid-disciplined page — rich ink everywhere, nothing clipped,
nothing spilled. Monday is a follow-up day, so the page carries a
"Monday updates" band of the day's developments and a date-check
box stating the rule the page applied.

frontpage.py holds the data and the compact fallback edition;
main.py copies whichever entry.png is committed. The render is
deterministic — same data, same PNG.

Usage:  python3 frontpage2.py [out.png]   (default: entry.png
        beside this file)
"""

import os
import sys

from PIL import Image, ImageDraw

from frontpage import (
    BRIEFS, CARDS, DATE_CHECK, DEK, HEROES, PINS, REGION_TALLY,
    SANS, SANS_BOLD, SERIF, SERIF_BOLD, SERIF_ITALIC, STORY_COUNT,
    TAB_INK, TAB_ORDER, WORLD, block, fit, font, grain, middle, wrap_to,
)

# ------------------------------------------------------------------ ink

PAPER = (248, 244, 231)
FRAME = (13, 30, 44)
INK = (24, 23, 21)
FAINT = (96, 90, 76)
RED = (190, 30, 22)
DEEP_RED = (148, 27, 18)
GOLD = (233, 165, 33)
ORANGE = (243, 121, 33)
PIN_FILL = (204, 32, 24)
BADGE_BLUE = (36, 84, 158)
SEA_TOP = (8, 34, 68)
SEA_BOT = (10, 86, 106)
GRATICULE = (43, 102, 130)
LAND = (240, 183, 92)
LAND_DEEP = (224, 152, 58)
RULE_SOFT = (198, 190, 168)

PILL_INK = {
    "OFFICIAL": (0, 110, 110),
    "CONFIRMED": (26, 138, 60),
    "REPORTED": (192, 32, 24),
    "CLAIM": (110, 52, 140),
    "FORECAST": (176, 110, 10),
}

PAGE = 1024
EDGE = 38
SPAN = PAGE - 2 * EDGE  # 948 px of content

DAY = "Monday 23 November 2026"

# The Monday developments band: weekend events reached this page
# only through what Monday did to them — a toll that climbed, a
# condemnation that landed, a session that convened.
UPDATE_SLOTS = [
    ("TOLL CLIMBS", "Dymer toll reaches 11"),
    ("NO DEAL", "COP31 ends in Antalya"),
    ("32 ALLIES", "NATO emergency session"),
    ("24 CONFIRMED", "Banten fire toll set"),
    ("CONDEMNED", "Khartoum strikes hit UN"),
    ("BACK AT NVIDIA", "Huang reinstated, +30%"),
]

NUMBERS2 = [
    ("7", "SEA DRONES", "SANK THE MERKURY OFF LIBYA"),
    ("92,000", "REGISTERED AT COP31", "PROVISIONALLY THE LARGEST COP"),
    ("+30%", "NVIDIA IN ONE DAY", "HUANG BACK · +$900BN VALUE"),
    ("$14.7bn", "SHADOW-BANK FLOWS", "TRACED BY THE US TREASURY"),
    ("24", "DEAD IN BANTEN", "FACTORY FIRE TOLL CONFIRMED"),
    ("11", "DEAD IN DYMER", "A BOY OF 7 PULLED OUT ALIVE"),
]

REGION_SHORT = {
    "Europe": "EUROPE", "Middle East": "MID EAST",
    "Asia-Pacific": "ASIA-PAC", "Americas": "AMERICAS",
    "Africa": "AFRICA", "World & Science": "WORLD & SCI",
}

HERO_PILL = {1: "CONFIRMED · AFP", 2: "CONFIRMED · AFP",
             3: "CONFIRMED · NATO"}

# ------------------------------------------------------------------ helpers


def vgrad(w, h, top, bot):
    """A deterministic vertical gradient as an image of size (w, h)."""
    strip = Image.new("RGB", (1, h))
    for i in range(h):
        t = i / max(1, h - 1)
        strip.putpixel((0, i), tuple(
            round(top[c] + (bot[c] - top[c]) * t) for c in range(3)))
    return strip.resize((w, h))


def pill(d, x_right, y, text, color, size=8.5, h=15):
    fnt = font(SANS_BOLD, size)
    tw = d.textlength(text, font=fnt)
    w = tw + 11
    d.rounded_rectangle([x_right - w, y, x_right, y + h], 3, fill=color)
    d.text((x_right - w + 5.5, y + (h - size) / 2 - 1), text, font=fnt,
           fill=(255, 255, 255))
    return w


def badge(d, cx, cy, num, r=10):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BADGE_BLUE,
              outline=(255, 255, 255), width=2)
    label = str(num)
    fnt = font(SANS_BOLD, 12 if num < 10 else 11)
    box = d.textbbox((0, 0), label, font=fnt)
    d.text((cx - (box[2] - box[0]) / 2 - box[0], cy - 6.5), label,
           font=fnt, fill=(255, 255, 255))


def pin2(d, cx, cy, num, r=6.5):
    # a white halo ring and a saturated red fill, so the pin pops on
    # the deep sea and on the gold land alike
    d.ellipse([cx - r - 1.5, cy - r - 1.5, cx + r + 1.5,
               cy + r + 1.5], fill=(255, 255, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PIN_FILL,
              outline=(10, 22, 34), width=1)
    label = str(num)
    fnt = font(SANS_BOLD, 9 if num < 10 else 8)
    box = d.textbbox((0, 0), label, font=fnt)
    d.text((cx - (box[2] - box[0]) / 2 - box[0], cy - 5), label,
           font=fnt, fill=(255, 255, 255))


def burst2(d, cx, cy, r, fill=ORANGE, core=GOLD):
    import math
    spikes = []
    for i in range(24):
        ang = math.tau * i / 24
        rad = r if i % 2 == 0 else r * 0.45
        spikes.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(spikes, fill=fill)
    inner = r * 0.3
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=core)


def scene_tag(d, x, y, text):
    """The red scene tag the winning pages carry, bottom-left."""
    fnt = font(SANS_BOLD, 10)
    tw = d.textlength(text, font=fnt)
    d.rectangle([x, y, x + tw + 12, y + 17], fill=RED)
    d.text((x + 6, y + 3), text, font=fnt, fill=(255, 255, 255))

# ------------------------------------------------------------------ hero scenes
# Each scene is drawn on its own canvas and pasted, so nothing spills.


def hero_merkury(w, h):
    """Pre-dawn off Benghazi: harbour cranes behind, the corvette at
    anchor mid-frame, sea-drone wakes converging on her, one burst
    already at the waterline."""
    img = vgrad(w, h, (12, 28, 50), (54, 86, 112))
    d = ImageDraw.Draw(img)
    # stars fading toward dawn
    for fx, fy in [(0.06, 0.12), (0.24, 0.07), (0.44, 0.16), (0.63, 0.08),
                   (0.80, 0.18), (0.93, 0.10)]:
        d.ellipse([fx * w, fy * h, fx * w + 2, fy * h + 2],
                  fill=(214, 222, 238))
    # harbour cranes along the back shore
    base = h * 0.74
    for fx in (0.06, 0.20, 0.86):
        gx = fx * w
        d.line([gx, base, gx, base - 26], fill=(16, 26, 40), width=3)
        d.line([gx, base - 26, gx + 0.11 * w, base - 26],
               fill=(16, 26, 40), width=3)
        d.line([gx + 0.09 * w, base - 26, gx + 0.09 * w, base - 16],
               fill=(16, 26, 40), width=2)
    d.rectangle([0, base, w, base + 2], fill=(12, 22, 36))
    # the corvette, centre: long hull, superstructure, mast — drawn
    # a tone lighter than the night so she reads at a glance
    hull = (52, 68, 88)
    hx0, hx1, hy = 0.28 * w, 0.76 * w, h * 0.64
    d.polygon([(hx0, hy), (hx1, hy), (hx1 - 8, hy + 10), (hx0 + 12, hy + 10)],
              fill=hull)
    d.line([hx0 + 2, hy, hx1 - 2, hy], fill=(120, 140, 164), width=1)
    d.rectangle([0.44 * w, hy - 11, 0.60 * w, hy], fill=hull)
    d.rectangle([0.485 * w, hy - 18, 0.545 * w, hy - 11], fill=hull)
    d.line([0.515 * w, hy - 18, 0.515 * w, hy - 27], fill=hull,
           width=2)
    d.ellipse([0.50 * w, hy - 31, 0.53 * w, hy - 26], fill=hull)
    # lit portholes along her side
    for k in range(6):
        px = (0.34 + 0.055 * k) * w
        d.ellipse([px, hy + 3, px + 2, hy + 5], fill=(240, 200, 110))
    # a helicopter silhouette on her deck, aft
    ex, ey = 0.68 * w, hy - 7
    d.ellipse([ex - 7, ey - 3, ex + 7, ey + 3], fill=(30, 40, 54))
    d.line([ex - 11, ey - 5, ex + 11, ey - 5], fill=(30, 40, 54), width=2)
    # sea-drone wakes converging from the dark, lower left and right
    for sx, sy in [(0.03, 0.94), (0.16, 0.99), (0.97, 0.92)]:
        tx, ty = 0.47 * w, hy + 8
        d.line([sx * w, sy * h, tx, ty], fill=(190, 220, 235), width=2)
        d.line([sx * w + 6, sy * h - 3, tx, ty], fill=(130, 175, 200),
               width=1)
    # the drones themselves, two of them close enough to see
    for dx, dy in [(0.20, 0.86), (0.86, 0.84)]:
        gx, gy = dx * w, dy * h
        d.polygon([(gx - 6, gy), (gx + 6, gy), (gx + 2, gy + 3),
                   (gx - 2, gy + 3)], fill=(16, 22, 32))
    # the hit: a burst at her waterline, forward, and smoke above it
    burst2(d, 0.44 * w, hy + 4, 14)
    burst2(d, 0.41 * w, hy + 8, 7)
    for k in range(3):
        r = 4 + k * 2.5
        gx, gy = 0.45 * w + k * 5, hy - 16 - k * 6
        d.ellipse([gx - r, gy - r * 0.7, gx + r, gy + r * 0.7],
                  fill=(104, 108, 116))
    scene_tag(d, 8, h - 25, "CORVETTE SUNK OFF BENGHAZI")
    return img


def hero_cop(w, h):
    img = vgrad(w, h, (15, 40, 36), (47, 76, 58))
    d = ImageDraw.Draw(img)
    # hall panelling
    for fx in (0.04, 0.96):
        d.line([fx * w, 6, fx * w, h - 6], fill=(86, 116, 92), width=1)
    # the rejected document, centre-left, glowing cream
    px0, py0, px1, py1 = 0.30 * w, 7, 0.63 * w, h - 7
    d.rectangle([px0, py0, px1, py1], fill=(240, 236, 224))
    d.line([px0 + 5, py0 + 5, px1 - 5, py1 - 5], fill=RED, width=3)
    d.line([px0 + 5, py1 - 5, px1 - 5, py0 + 5], fill=RED, width=3)
    d.rectangle([px0 + 5, py0 + 4, px0 + 64, py0 + 17],
                fill=(240, 236, 224))
    d.text((px0 + 7, py0 + 5), "FINAL TEXT", font=font(SANS_BOLD, 9),
           fill=INK)
    ff = font(SERIF_ITALIC, 12)
    fy = py0 + h * 0.52
    tw = d.textlength("fossil fuels", font=ff)
    d.rectangle([px0 + 5, fy - 2, px0 + 13 + tw, fy + 14],
                fill=(240, 236, 224))
    d.text((px0 + 7, fy), "fossil fuels", font=ff, fill=INK)
    d.line([px0 + 5, fy + 7, px0 + 10 + tw, fy + 7], fill=RED, width=2)
    # four flags at half-mast, right
    flags = [(0.70, (38, 62, 140)), (0.78, (30, 50, 110)),
             (0.86, (235, 235, 230)), (0.94, (235, 130, 40))]
    for fx, col in flags:
        gx = fx * w
        d.line([gx, 8, gx, h - 8], fill=(214, 212, 202), width=2)
        fy2 = h * 0.44
        d.rectangle([gx, fy2, gx + 0.055 * w, fy2 + 10], fill=col)
    for k in range(4):
        sx = 0.70 * w + 3 + (k % 2) * 5
        sy = h * 0.44 + 2 + (k // 2) * 5
        d.ellipse([sx, sy, sx + 2, sy + 2], fill=GOLD)
    # a lone gavel at rest, left
    gx, gy = 0.11 * w, h * 0.60
    d.line([gx - 9, gy + 9, gx + 11, gy - 11], fill=(206, 160, 92), width=4)
    d.rectangle([gx + 3, gy - 15, gx + 15, gy - 5], fill=(160, 108, 56))
    d.line([0.04 * w, gy + 13, 0.24 * w, gy + 13], fill=(238, 234, 222),
           width=2)
    scene_tag(d, 8, h - 25, "NO DEAL ADOPTED")
    return img


def hero_nato(w, h):
    """Brussels, Monday: the alliance's compass star ringed by the
    32 allies' lights, three missile trails still fading above the
    council table."""
    import math
    img = vgrad(w, h, (14, 26, 54), (32, 52, 88))
    d = ImageDraw.Draw(img)
    cx, cy = 0.30 * w, h * 0.46
    # the ring of 32 allied lights
    for k in range(32):
        ang = math.tau * k / 32
        lx, ly = cx + 30 * math.cos(ang), cy + 30 * math.sin(ang)
        d.ellipse([lx - 1.6, ly - 1.6, lx + 1.6, ly + 1.6], fill=GOLD)
    # the four-point compass star
    r1, r2 = 21, 5.5
    star = []
    for k in range(8):
        ang = math.tau * k / 8 - math.tau / 4
        rad = r1 if k % 2 == 0 else r2
        star.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(star, fill=(226, 232, 242))
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(14, 26, 54))
    # three missile trails arcing in from the east, fading
    for jx, jy, tx in [(0.97, 0.10, 0.80), (0.99, 0.24, 0.86),
                       (0.95, 0.36, 0.78)]:
        d.arc([jx * w - 90, jy * h - 18, tx * w + 26, jy * h + 30],
              300, 60, fill=(240, 178, 105), width=2)
        d.ellipse([tx * w - 2, jy * h + 12, tx * w + 2, jy * h + 16],
                  fill=(246, 200, 130))
    # the council table: a long arc of seats along the bottom
    ty = h * 0.86
    d.arc([0.52 * w, ty - 16, 0.98 * w, ty + 14], 180, 360,
          fill=(198, 168, 110), width=3)
    for k in range(9):
        sx = (0.56 + 0.045 * k) * w
        d.ellipse([sx - 2, ty - 4, sx + 2, ty], fill=(226, 232, 242))
    scene_tag(d, 8, h - 25, "32 ALLIES IN EMERGENCY SESSION")
    return img


HERO_SCENES = {"merkury": hero_merkury, "cop": hero_cop, "nato": hero_nato}

# ------------------------------------------------------------------ card scenes
# Compact full-colour illustrations, one per pictured card.


def card_dymer(w, h):
    img = vgrad(w, h, (58, 62, 74), (96, 100, 112))
    d = ImageDraw.Draw(img)
    base = h
    # the five-storey block, its near corner torn away
    bx0, bx1 = 0.08 * w, 0.52 * w
    d.rectangle([bx0, base - 30, bx1, base], fill=(38, 40, 48))
    for r in range(3):
        for c in range(4):
            if (r * 4 + c) % 3:
                d.rectangle([bx0 + 4 + c * 9, base - 27 + r * 9,
                             bx0 + 8 + c * 9, base - 23 + r * 9],
                            fill=(240, 200, 110))
    d.polygon([(bx1 - 10, base - 30), (bx1 + 6, base - 18),
               (bx1 - 2, base - 6), (bx1 - 12, base - 12)],
              fill=(24, 25, 30))
    # rubble spilling from the tear
    for fx, fs in [(0.55, 5), (0.62, 4), (0.68, 6), (0.75, 3)]:
        gx = fx * w
        d.polygon([(gx, base), (gx + fs, base - fs), (gx + 2 * fs, base)],
                  fill=(30, 31, 37))
    # a rescue crane leaning in, lamp lit
    cx0 = 0.97 * w
    d.line([cx0, base, cx0 - 4, 3], fill=(210, 214, 220), width=2)
    d.line([cx0 - 4, 3, 0.60 * w, 6], fill=(210, 214, 220), width=2)
    d.line([0.64 * w, 6, 0.64 * w, 13], fill=(210, 214, 220), width=1)
    d.ellipse([0.64 * w - 3, 12, 0.64 * w + 3, 17], fill=(255, 226, 150))
    return img


def card_chip(w, h):
    img = vgrad(w, h, (10, 26, 18), (16, 44, 28))
    d = ImageDraw.Draw(img)
    cx, cy = 0.36 * w, h / 2
    # the chip: dark die, gold pins, green traces running off it
    d.rectangle([cx - 13, cy - 11, cx + 13, cy + 11], fill=(18, 20, 22),
                outline=(120, 220, 150), width=1)
    for k in range(4):
        py = cy - 9 + k * 6
        d.line([cx - 18, py, cx - 13, py], fill=GOLD, width=2)
        d.line([cx + 13, py, cx + 18, py], fill=GOLD, width=2)
    d.text((cx - 8, cy - 5), "AI", font=font(SANS_BOLD, 10),
           fill=(160, 240, 180))
    for tx in (0.62, 0.74, 0.86):
        gx = tx * w
        d.line([gx, h - 4, gx + 6, h - 12], fill=(52, 199, 106), width=2)
    d.polygon([(0.90 * w, 4), (0.97 * w, 12), (0.86 * w, 12)],
              fill=(52, 199, 106))
    d.text((0.60 * w, 3), "+30%", font=font(SANS_BOLD, 11),
           fill=(160, 240, 180))
    return img


def card_tanker(w, h):
    img = vgrad(w, h, (24, 34, 54), (52, 66, 88))
    d = ImageDraw.Draw(img)
    keel = h * 0.70
    # a shadow-fleet tanker riding dark and low
    d.polygon([(0.05 * w, keel), (0.93 * w, keel), (0.87 * w, keel + 8),
               (0.11 * w, keel + 8)], fill=(14, 16, 20))
    d.rectangle([0.10 * w, keel - 8, 0.20 * w, keel], fill=(14, 16, 20))
    for i, fx in enumerate((0.30, 0.48, 0.66)):
        d.rectangle([fx * w, keel - 5, fx * w + 14, keel],
                    fill=(20, 22, 26))
    # one thin line of light along her deck — and a sanction stamp
    d.line([0.22 * w, keel - 2, 0.84 * w, keel - 2],
           fill=(214, 178, 90), width=1)
    sx, sy = 0.80 * w, h * 0.20
    d.rectangle([sx - 13, sy - 6, sx + 13, sy + 6], outline=RED, width=2)
    d.text((sx - 10, sy - 4), "OFAC", font=font(SANS_BOLD, 8), fill=RED)
    return img


def card_arson(w, h):
    img = vgrad(w, h, (30, 26, 40), (62, 48, 52))
    d = ImageDraw.Draw(img)
    base = h
    # a row of village houses; the middle one is burning
    for i, fx in enumerate((0.06, 0.30, 0.56, 0.78)):
        hx = fx * w
        d.rectangle([hx, base - 13, hx + 16, base], fill=(22, 20, 24))
        d.polygon([(hx - 2, base - 13), (hx + 8, base - 19),
                   (hx + 18, base - 13)], fill=(16, 14, 18))
        if i == 1:
            d.polygon([(hx + 3, base - 15), (hx + 8, base - 27),
                       (hx + 13, base - 15)], fill=ORANGE)
            d.polygon([(hx + 6, base - 15), (hx + 8, base - 21),
                       (hx + 10, base - 15)], fill=GOLD)
            for k in range(3):
                r = 3 + k * 2
                gx = hx + 12 + k * 3
                d.ellipse([gx - r, 2 + k * 3, gx + r, 2 + k * 3 + r],
                          fill=(96, 90, 96))
    # a burnt-out car shell in front
    d.polygon([(0.60 * w, base - 3), (0.86 * w, base - 3),
               (0.82 * w, base - 7), (0.64 * w, base - 7)],
              fill=(10, 10, 12))
    return img


def card_factory(w, h):
    img = vgrad(w, h, (56, 32, 26), (100, 54, 38))
    d = ImageDraw.Draw(img)
    floor_y = h
    d.rectangle([0.06 * w, floor_y - 14, 0.60 * w, floor_y],
                fill=(24, 18, 16))
    d.polygon([(0.06 * w, floor_y - 14), (0.22 * w, floor_y - 20),
               (0.33 * w, floor_y - 15), (0.44 * w, floor_y - 21),
               (0.60 * w, floor_y - 14)], fill=(24, 18, 16))
    for fx, fh in [(0.26, 0.30), (0.37, 0.44), (0.49, 0.26)]:
        cx = fx * w
        d.polygon([(cx - 5, floor_y - 15), (cx, floor_y - 15 - fh * h),
                   (cx + 5, floor_y - 15)], fill=ORANGE)
        d.polygon([(cx - 2, floor_y - 15),
                   (cx, floor_y - 15 - fh * h * 0.55),
                   (cx + 2, floor_y - 15)], fill=GOLD)
    for fx, fh in ((0.63, 18), (0.73, 15)):
        d.rectangle([fx * w, floor_y - fh, fx * w + 6, floor_y],
                    fill=(24, 18, 16))
    ex = 0.64 * w
    d.rectangle([ex, floor_y - 7, ex + 22, floor_y - 1], fill=(158, 42, 30))
    d.rectangle([ex + 15, floor_y - 11, ex + 22, floor_y - 7],
                fill=(158, 42, 30))
    for fx in (0.70, 0.86):
        cx = fx * w
        d.ellipse([cx - 3, floor_y - 4, cx + 3, floor_y + 1],
                  fill=(10, 10, 10))
    return img


def card_khartoum(w, h):
    img = vgrad(w, h, (12, 18, 38), (34, 44, 66))
    d = ImageDraw.Draw(img)
    base = h - 8
    # rooftops across the capital
    for fx, fw, fh in [(0.02, 0.20, 0.30), (0.26, 0.16, 0.44),
                       (0.46, 0.22, 0.26), (0.72, 0.26, 0.38)]:
        bx = fx * w
        d.rectangle([bx, base - fh * h, bx + fw * w, base],
                    fill=(10, 12, 18))
    burst2(d, 0.56 * w, base - 0.30 * h, 7)
    # two drone silhouettes crossing the night
    for fx, fy in [(0.30, 0.22), (0.68, 0.14)]:
        dx, dy = fx * w, fy * h
        d.line([dx - 7, dy - 5, dx + 7, dy + 5], fill=(228, 230, 238),
               width=2)
        d.line([dx - 7, dy + 5, dx + 7, dy - 5], fill=(228, 230, 238),
               width=2)
        d.ellipse([dx - 1.5, dy - 1.5, dx + 1.5, dy + 1.5], fill=RED)
    # the UN band along the bottom
    d.rectangle([0, h - 8, w, h], fill=(38, 92, 168))
    d.text((6, h - 8), "UN", font=font(SANS_BOLD, 8),
           fill=(255, 255, 255))
    return img


def card_chart(w, h):
    img = vgrad(w, h, (26, 14, 16), (48, 22, 24))
    d = ImageDraw.Draw(img)
    # gridlines, then the index falling away to the right
    for gy in (0.28, 0.55, 0.82):
        d.line([4, gy * h, w - 4, gy * h], fill=(92, 52, 54), width=1)
    pts = [(0.04 * w, 0.24 * h), (0.24 * w, 0.30 * h),
           (0.42 * w, 0.26 * h), (0.60 * w, 0.48 * h),
           (0.78 * w, 0.62 * h), (0.96 * w, 0.80 * h)]
    d.line(pts, fill=(232, 64, 52), width=2)
    for px, py in pts[::2]:
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(232, 64, 52))
    d.text((0.06 * w, 0.60 * h), "KOSPI −3.3%", font=font(SANS_BOLD, 10),
           fill=(255, 190, 180))
    return img


def card_eustars(w, h):
    import math
    img = vgrad(w, h, (24, 48, 110), (34, 66, 140))
    d = ImageDraw.Draw(img)
    cx, cy = 0.30 * w, h / 2
    for k in range(12):
        ang = math.tau * k / 12 - math.tau / 2
        sx, sy = cx + 11 * math.cos(ang), cy + 11 * math.sin(ang)
        d.polygon([(sx, sy - 3), (sx + 2.4, sy + 2), (sx - 2.4, sy + 2)],
                  fill=GOLD)
    d.text((0.52 * w, cy - 8), "22nd", font=font(SERIF_BOLD, 15),
           fill=(255, 240, 200))
    d.text((0.52 * w, cy + 7), "PACKAGE", font=font(SANS_BOLD, 8),
           fill=(255, 240, 200))
    return img


def card_oil(w, h):
    img = vgrad(w, h, (40, 30, 34), (74, 54, 44))
    d = ImageDraw.Draw(img)
    base = h
    # two derricks on a dark plain; the far one is hit and burning
    for fx, s in [(0.16, 1.0), (0.62, 0.8)]:
        gx = fx * w
        top = base - 24 * s
        d.line([gx - 8 * s, base, gx, top], fill=(16, 14, 16), width=2)
        d.line([gx + 8 * s, base, gx, top], fill=(16, 14, 16), width=2)
        d.line([gx - 5 * s, base - 8 * s, gx + 5 * s, base - 8 * s],
               fill=(16, 14, 16), width=1)
    burst2(d, 0.62 * w, base - 22, 8)
    d.polygon([(0.62 * w - 3, base - 12), (0.62 * w, base - 24),
               (0.62 * w + 3, base - 12)], fill=GOLD)
    # a pipeline running off into the distance
    d.line([0.30 * w, base - 3, 0.97 * w, base - 3], fill=(16, 14, 16),
           width=2)
    return img


def card_strike(w, h):
    img = vgrad(w, h, (66, 76, 94), (112, 122, 140))
    d = ImageDraw.Draw(img)
    base = h
    # the factory gate, shut; a line of pickets before it
    d.rectangle([0.06 * w, base - 20, 0.52 * w, base], fill=(40, 46, 56))
    d.polygon([(0.06 * w, base - 20), (0.29 * w, base - 27),
               (0.52 * w, base - 20)], fill=(30, 35, 44))
    for i in range(4):
        px = (0.60 + 0.075 * i) * w
        d.ellipse([px - 2.5, base - 13, px + 2.5, base - 8],
                  fill=(24, 26, 30))
        d.line([px, base - 8, px, base], fill=(24, 26, 30), width=2)
    sx = 0.88 * w
    d.line([sx, base - 13, sx, base], fill=(120, 84, 44), width=2)
    d.rectangle([sx - 10, base - 21, sx + 10, base - 13],
                fill=(247, 245, 238))
    d.text((sx - 8, base - 20), "STOP", font=font(SANS_BOLD, 7), fill=RED)
    return img


def card_gta(w, h):
    img = vgrad(w, h, (122, 28, 110), (16, 128, 140))
    d = ImageDraw.Draw(img)
    # a neon sun going down behind a palm
    sx, sy = 0.70 * w, h * 0.52
    d.ellipse([sx - 10, sy - 10, sx + 10, sy + 10], fill=(255, 196, 64))
    for gy in (0.40, 0.52, 0.64):
        d.line([sx - 11, gy * h, sx + 11, gy * h], fill=(16, 128, 140),
               width=2)
    px = 0.16 * w
    d.line([px, h, px + 2, h * 0.30], fill=(14, 20, 24), width=3)
    import math
    for k in range(5):
        ang = math.pi * (0.08 + 0.21 * k)
        ex = px + 2 + 13 * math.cos(ang)
        ey = h * 0.30 - 9 * math.sin(ang)
        d.line([px + 2, h * 0.30, ex, ey], fill=(14, 20, 24), width=2)
    d.text((0.34 * w, h * 0.16), "$3.79bn", font=font(SANS_BOLD, 14),
           fill=(255, 240, 200))
    return img


def card_nhs(w, h):
    img = vgrad(w, h, (240, 244, 238), (212, 230, 218))
    d = ImageDraw.Draw(img)
    cy = h / 2
    cx = 0.20 * w
    d.rectangle([cx - 4, cy - 12, cx + 4, cy + 12], fill=RED)
    d.rectangle([cx - 12, cy - 4, cx + 12, cy + 4], fill=RED)
    pts = [(0.42 * w, cy), (0.55 * w, cy), (0.59 * w, cy - 8),
           (0.64 * w, cy + 6), (0.68 * w, cy), (0.97 * w, cy)]
    d.line(pts, fill=(26, 138, 72), width=2)
    return img


CARD_SCENES = {
    "dymer": card_dymer, "chip": card_chip, "tanker": card_tanker,
    "arson": card_arson, "factory": card_factory,
    "khartoum": card_khartoum, "chart": card_chart,
    "eustars": card_eustars, "oil": card_oil, "strike": card_strike,
    "gta": card_gta, "nhs": card_nhs,
}

# ------------------------------------------------------------------ page


def render():
    img = Image.new("RGB", (PAGE, PAGE), FRAME)
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, PAGE - 8, PAGE - 8], fill=PAPER)

    # ---- masthead
    d.rectangle([EDGE, 22, EDGE + 9, 31], fill=RED)
    d.text((EDGE + 14, 19), "ONE DAY OF WORLD NEWS, ONE PICTURE",
           font=font(SANS_BOLD, 15), fill=RED)
    total = (f"{STORY_COUNT} STORIES · 6 REGIONS · "
             f"EVERY ONE FROM THIS MONDAY")
    rf = font(SANS, 10)
    d.text((PAGE - EDGE - d.textlength(total, font=rf), 23), total,
           font=rf, fill=INK)
    d.line([EDGE, 42, PAGE - EDGE, 42], fill=INK, width=1)
    d.line([EDGE, 45, PAGE - EDGE, 45], fill=INK, width=3)

    # ---- date and dek
    middle(d, PAGE / 2, 52, DAY, font(SERIF_BOLD, 56), INK)
    middle(d, PAGE / 2, 118, DEK, font(SERIF_ITALIC, 16), RED)
    d.line([EDGE, 140, PAGE - EDGE, 140], fill=INK, width=1)

    # ---- Monday updates: red label, six slots
    d.rectangle([EDGE, 146, EDGE + 66, 182], fill=RED)
    middle(d, EDGE + 33, 152, "MONDAY", font(SANS_BOLD, 10),
           (255, 255, 255))
    middle(d, EDGE + 33, 165, "UPDATES", font(SANS_BOLD, 10),
           (255, 255, 255))
    slot_x = EDGE + 74
    slot_w = (PAGE - EDGE - slot_x) / 6
    for i, (tm, what) in enumerate(UPDATE_SLOTS):
        sx = slot_x + i * slot_w
        fit(d, sx + 6, 149, tm, SANS_BOLD, 12, slot_w - 10, RED, floor=8)
        fit(d, sx + 6, 166, what, SANS, 9, slot_w - 10, INK, floor=7)
        if i:
            d.line([sx, 150, sx, 178], fill=RULE_SOFT, width=1)
    d.line([EDGE, 186, PAGE - EDGE, 186], fill=INK, width=1)

    # ---- the day in numbers
    d.text((EDGE, 192), "THE DAY IN NUMBERS", font=font(SANS_BOLD, 10),
           fill=RED)
    cell = SPAN / 6
    for i, (fig, cap1, cap2) in enumerate(NUMBERS2):
        cx = EDGE + cell * i + cell / 2
        middle(d, cx, 206, fig, font(SERIF_BOLD, 27), INK)
        middle(d, cx, 240, cap1, font(SANS, 9), FAINT)
        middle(d, cx, 251, cap2, font(SANS, 9), FAINT)
        if i:
            d.line([EDGE + cell * i, 208, EDGE + cell * i, 258],
                   fill=RULE_SOFT, width=1)
    d.line([EDGE, 264, PAGE - EDGE, 264], fill=INK, width=1)

    # ---- region tabs, counts computed from the story list
    tf = font(SANS_BOLD, 12)
    labels = [(r, f"{r.upper()} {REGION_TALLY[r]}") for r in TAB_ORDER]
    widths = [d.textlength(t, font=tf) + 20 for _r, t in labels]
    gap = (SPAN - sum(widths)) / (len(labels) - 1)
    tx = float(EDGE)
    for (r, t), tw in zip(labels, widths):
        d.rectangle([tx, 270, tx + tw, 292], fill=TAB_INK[r])
        middle(d, tx + tw / 2, 275, t, tf, (255, 255, 255))
        tx += tw + gap

    # ---- heroes: rich scenes, badge, tag, pill, headline, summary
    hero_w = 309
    for i, hero in enumerate(HEROES):
        hx = EDGE + i * (hero_w + 10)
        img.paste(HERO_SCENES[hero["scene"]](hero_w, 100), (hx, 300))
        badge(d, hx + 10, 414, hero["num"], r=10)
        pill(d, hx + hero_w, 406, HERO_PILL[hero["num"]],
             PILL_INK[hero["cert"]], size=9, h=15)
        pw = d.textlength(HERO_PILL[hero["num"]], font=font(SANS_BOLD, 9))
        fit(d, hx + 26, 407, hero["tag"], SANS_BOLD, 10,
            hero_w - 26 - pw - 20, RED, floor=8)
        block(d, hx, 428, hero["head"], font(SERIF_BOLD, 24), INK,
              hero_w, 26, cap=2)
        block(d, hx, 484, hero["summ"], font(SERIF, 12), INK,
              hero_w, 15, cap=3)
    d.line([EDGE, 534, PAGE - EDGE, 534], fill=INK, width=1)

    # ---- pictured cards, two rows of six
    card_w = 151
    for i, card in enumerate(CARDS):
        cx0 = EDGE + (i % 6) * (card_w + 8)
        cy0 = 542 + (i // 6) * 121
        img.paste(CARD_SCENES[card["scene"]](card_w, 38), (cx0, cy0))
        pill(d, cx0 + card_w - 3, cy0 + 3, card["cert"],
             PILL_INK[card["cert"]], size=8, h=13)
        d.rectangle([cx0, cy0 + 43, cx0 + 7, cy0 + 50],
                    fill=TAB_INK[card["region"]])
        fit(d, cx0 + 11, cy0 + 42, card["place"], SANS_BOLD, 9,
            card_w - 11, RED, floor=7)
        block(d, cx0, cy0 + 55, card["head"], font(SERIF_BOLD, 14), INK,
              card_w, 16, cap=2)
        block(d, cx0, cy0 + 88, card["summ"], font(SERIF, 11), INK,
              card_w, 13, cap=2)

    # ---- bottom band: coloured map left, briefs right
    by = 786
    d.text((EDGE, by), "WHERE IT HAPPENED", font=font(SANS_BOLD, 12),
           fill=INK)
    map_x, map_y = EDGE, by + 18
    pitch_x, pitch_y = 4.0, 3.6
    map_w = len(WORLD[0]) * pitch_x
    map_h = len(WORLD) * pitch_y
    # the map is drawn on its own canvas — a deep navy-to-teal sea
    # with a faint graticule under saturated gold land — pasted whole
    sea_w, sea_h = int(map_w) + 10, int(map_h) + 10
    sea_img = vgrad(sea_w, sea_h, SEA_TOP, SEA_BOT)
    sd = ImageDraw.Draw(sea_img)
    for gi in range(8, len(WORLD[0]), 8):
        gx = 5 + gi * pitch_x
        sd.line([gx, 3, gx, sea_h - 3], fill=GRATICULE, width=1)
    for gj in range(6, len(WORLD), 6):
        gy = 5 + gj * pitch_y
        sd.line([3, gy, sea_w - 3, gy], fill=GRATICULE, width=1)
    for ri, row in enumerate(WORLD):
        for ci, ch in enumerate(row):
            if ch == "#":
                cxp = 5 + ci * pitch_x + pitch_x / 2
                cyp = 5 + ri * pitch_y + pitch_y / 2
                tone = LAND_DEEP if (ri + ci) % 7 == 0 else LAND
                sd.rectangle([cxp - pitch_x / 2 + 0.4,
                              cyp - pitch_y / 2 + 0.4,
                              cxp + pitch_x / 2 - 0.4,
                              cyp + pitch_y / 2 - 0.4], fill=tone)
    img.paste(sea_img, (map_x - 5, map_y - 5))
    for num, (fx, fy) in PINS.items():
        pin2(d, map_x + fx * map_w, map_y + fy * map_h, num, r=6.5)
    # region legend under the map, coloured squares + computed counts
    lf = font(SANS, 9)
    for li, group in enumerate((TAB_ORDER[:3], TAB_ORDER[3:])):
        lx = float(EDGE)
        ly = map_y + map_h + 7 + li * 11
        for r in group:
            d.rectangle([lx, ly + 1, lx + 7, ly + 8], fill=TAB_INK[r])
            t = f"{REGION_SHORT[r]} {REGION_TALLY[r]}"
            d.text((lx + 10, ly), t, font=lf, fill=INK)
            lx += 10 + d.textlength(t, font=lf) + 13

    bx = 404
    d.text((bx, by), f"ALSO ON MONDAY — {len(BRIEFS)} MORE STORIES",
           font=font(SANS_BOLD, 12), fill=INK)
    bf = font(SANS_BOLD, 8)
    col_w = 284
    for i, (num, text, _region) in enumerate(BRIEFS):
        col, row_i = divmod(i, 10)
        x0 = bx + col * (col_w + 12)
        y0 = by + 18 + row_i * 14.0
        d.rectangle([x0, y0 + 1, x0 + 15, y0 + 13], fill=RED)
        label = str(num)
        box = d.textbbox((0, 0), label, font=bf)
        d.text((x0 + 7.5 - (box[2] - box[0]) / 2 - box[0], y0 + 3),
               label, font=bf, fill=(255, 255, 255))
        fit(d, x0 + 19, y0 + 2, text, SANS, 10, col_w - 19, INK, floor=8)

    # ---- footer: dating line left, certainty key right
    d.text((EDGE, 964),
           "Every story happened, or was first reported, on Monday "
           "23 November 2026.", font=font(SANS, 9), fill=FAINT)
    key = ("OFFICIAL govt · CONFIRMED multi-source · REPORTED "
           "attributed · CLAIM one side")
    kf = font(SANS_BOLD, 9)
    d.text((PAGE - EDGE - d.textlength(key, font=kf), 964), key,
           font=kf, fill=INK)

    # ---- date-check box
    box_y = 977
    d.rectangle([EDGE, box_y, PAGE - EDGE, box_y + 32],
                fill=(250, 238, 231), outline=RED, width=2)
    block(d, EDGE + 16, box_y + 6, DATE_CHECK, font(SERIF, 11), DEEP_RED,
          SPAN - 32, 12, cap=2)

    return grain(img)


def build(out_path):
    render().save(out_path, format="PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "entry.png")
    out = sys.argv[1] if len(sys.argv) > 1 else default
    print(build(out), os.path.getsize(out))
