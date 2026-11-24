"""frontpage3.py — the ALL-IN edition of the news-image-20261123 page.

Same verified dossier as the first edition (35 stories, Monday
23 November 2026, every figure two-sourced, the five AFP-wire
briefs flagged), rebuilt scene by scene for the final heat:

  * the world map's European pins are FANNED OUT on leader lines —
    London, Brussels (twice), Hamburg, Kyiv and Rostov each get a
    numbered disc in open water or open steppe, cased leader line
    running to a dot on the exact place, so no two discs touch;
  * the NATO hero is a drawn council chamber now — wall emblem,
    airspace screen, flags, a curved table of seated allies —
    not a diagram;
  * the briefs column is re-spaced (fewer, taller rows) so its
    type sits a full size larger, with six briefs reworded —
    facts untouched — until every line fits at that size;
  * the numbers strip carries two figures per cell wherever the
    dossier allows, and the Monday-updates band repeats each
    hero fact a second time.

frontpage.py holds the data; frontpage2.py is the first rich
edition; main.py copies whichever entry.png is committed. The
render is deterministic — same data, same PNG.

Usage:  python3 frontpage3.py [out.png]   (default: entry.png
        beside this file)
"""

import math
import os
import sys

from PIL import Image, ImageDraw

from frontpage import (
    BRIEFS, CARDS, DATE_CHECK, DEK, HEROES, PINS, REGION_TALLY,
    TAB_INK, TAB_ORDER, WORLD, SANS, SANS_BOLD, SERIF, SERIF_BOLD,
    SERIF_ITALIC, load_font,
)

# ------------------------------------------------------------------ ink

PAPER, FRAME = (248, 244, 231), (13, 30, 44)
INK, FAINT = (24, 23, 21), (96, 90, 76)
RED, DEEP_RED = (190, 30, 22), (148, 27, 18)
GOLD, ORANGE = (233, 165, 33), (243, 121, 33)
PIN_FILL, BADGE_BLUE = (204, 32, 24), (36, 84, 158)
SEA_TOP, SEA_BOT = (8, 34, 68), (10, 86, 106)
GRATICULE, LAND = (43, 102, 130), (240, 183, 92)
LAND_DEEP, RULE_SOFT = (224, 152, 58), (198, 190, 168)
WHITE = (255, 255, 255)

PILL_INK = dict([
    ("OFFICIAL", (0, 110, 110)),
    ("CONFIRMED", (26, 138, 60)),
    ("REPORTED", (192, 32, 24)),
    ("CLAIM", (110, 52, 140)),
    ("FORECAST", (176, 110, 10)),
])

PAGE = 1024
EDGE = 38
SPAN = PAGE - 2 * EDGE  # 948 px of content

DAY = "Monday 23 November 2026"
STORY_COUNT = len(HEROES) + len(CARDS) + len(BRIEFS)

# The Monday developments band: weekend events reached this page
# only through what Monday did to them — a toll that climbed, a
# condemnation that landed, a session that convened. Each slot
# repeats one hero or card fact in a second place on the page.
UPDATE_SLOTS = [
    ("TOLL CLIMBS", "Dymer toll reaches 11"),
    ("NO DEAL", "COP31 ends in Antalya"),
    ("32 ALLIES", "NATO emergency session"),
    ("24 CONFIRMED", "Banten fire toll set"),
    ("CONDEMNED", "Khartoum strikes hit UN"),
    ("BACK AT NVIDIA", "Huang reinstated, +30%"),
]

# The day in numbers: two dossier figures per cell where the
# dossier carries them (designations + tankers, dead + missing,
# toll + the hours the boy of 7 spent under the rubble).
NUMBERS2 = [
    ("7", "SEA DRONES", "MERKURY SUNK · ANGARA DISABLED"),
    ("92,000", "REGISTERED AT COP31", "190+ NATIONS ATTENDED"),
    ("+30%", "NVIDIA IN ONE DAY", "HUANG BACK · +$900BN VALUE"),
    ("$14.7bn", "SHADOW-BANK FLOWS", "30+ DESIGNATIONS · 12 TANKERS"),
    ("24", "DEAD IN BANTEN", "FIRE TOLL SET · ~30 MISSING"),
    ("11", "DEAD IN DYMER", "BOY OF 7 OUT AFTER ~14 HOURS"),
]

REGION_SHORT = {
    "Europe": "EUROPE", "Middle East": "MID EAST",
    "Asia-Pacific": "ASIA-PAC", "Americas": "AMERICAS",
    "Africa": "AFRICA", "World & Science": "WORLD & SCI",
}

HERO_PILL = {1: "CONFIRMED · AFP", 2: "CONFIRMED · AFP",
             3: "CONFIRMED · NATO"}

# Six briefs reworded for the larger brief type — every fact,
# figure and source carried over unchanged from the dossier;
# only the phrasing is tightened (and one figure the dossier
# states, Megaspeed's six affiliates, is now printed).
BRIEF_FIX = {
    21: "Singapore — Megaspeed, 6 affiliates on US Entity List (NY Post)",
    25: "Science — AI Riemann proof claim, unverified (Principia)",
    28: "S. Lebanon — Villagers back in wrecked homes (Principia)",
    31: "US — Democrats projected biggest majority since '92 (AFP wire)",
    32: "Antalya — COP31 backlash: Bowen faces quit calls (AFP)",
    34: "Kyiv — Ukraine braces for winter blackouts (Principia)",
}
BRIEFS2 = [(num, BRIEF_FIX.get(num, text), region)
           for num, text, region in BRIEFS]

# ------------------------------------------------------------------ helpers


def gradient(w, h, top, bottom):
    """A vertical blend: a one-pixel strip mixed row by row, then
    stretched to the full width — deterministic by construction."""
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for i in range(h):
        t = i / max(1, h - 1)
        px[0, i] = tuple(round(top[c] + (bottom[c] - top[c]) * t)
                         for c in range(3))
    return strip.resize((w, h))


def wrap(text, fnt, width, drw):
    """Greedy word wrap against an exact pixel width."""
    lines, current = [], ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if drw.textlength(trial, font=fnt) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def para(drw, x, y, text, fnt, fill, width, leading, cap=None):
    """Wrapped text from (x, y); returns the y just below it."""
    lines = wrap(text, fnt, width, drw)
    if cap is not None:
        lines = lines[:cap]
    for ln in lines:
        drw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def centre(drw, cx, y, text, fnt, fill):
    """One line centred on cx."""
    box = drw.textbbox((0, 0), text, font=fnt)
    drw.text((cx - (box[2] - box[0]) / 2 - box[0], y), text,
             font=fnt, fill=fill)


def fit(drw, x, y, text, path, size, width, fill, floor=9.0):
    """One line shrunk in half-point steps until it fits width;
    returns the size actually used."""
    s = float(size)
    fnt = load_font(path, s)
    while drw.textlength(text, font=fnt) > width and s > floor:
        s -= 0.5
        fnt = load_font(path, int(s) if s == int(s) else s)
    drw.text((x, y), text, font=fnt, fill=fill)
    return s


def pill(drw, right, y, text, colour, size=8.5, h=15):
    """A rounded certainty pill whose right edge sits at `right`."""
    fnt = load_font(SANS_BOLD, size)
    w = drw.textlength(text, font=fnt) + 11
    drw.rounded_rectangle([right - w, y, right, y + h], 3, fill=colour)
    drw.text((right - w + 5.5, y + (h - size) / 2 - 1), text,
             font=fnt, fill=WHITE)
    return w


def disc(drw, cx, cy, num, r=10):
    """The blue story-number disc with a white rim."""
    drw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BADGE_BLUE,
                outline=WHITE, width=2)
    label = str(num)
    fnt = load_font(SANS_BOLD, 12 if num < 10 else 11)
    box = drw.textbbox((0, 0), label, font=fnt)
    drw.text((cx - (box[2] - box[0]) / 2 - box[0], cy - 6.5), label,
             font=fnt, fill=WHITE)


def pin_disc(drw, cx, cy, num, r=6.5):
    """A numbered map disc: white halo, saturated red fill, dark
    edge — it pops on the deep sea and on the gold land alike."""
    drw.ellipse([cx - r - 1.5, cy - r - 1.5, cx + r + 1.5,
                 cy + r + 1.5], fill=WHITE)
    drw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PIN_FILL,
                outline=(10, 22, 34), width=1)
    label = str(num)
    fnt = load_font(SANS_BOLD, 9 if num < 10 else 8)
    box = drw.textbbox((0, 0), label, font=fnt)
    drw.text((cx - (box[2] - box[0]) / 2 - box[0], cy - 5), label,
             font=fnt, fill=WHITE)


def burst(drw, cx, cy, r, fill=ORANGE, core=GOLD):
    """A 24-point explosion star with a bright core."""
    pts = []
    for i in range(24):
        ang = math.tau * i / 24
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    drw.polygon(pts, fill=fill)
    inner = r * 0.3
    drw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner],
                fill=core)


def caption_tag(drw, x, y, text):
    """The red scene caption the winning pages carry, bottom-left."""
    fnt = load_font(SANS_BOLD, 10)
    tw = drw.textlength(text, font=fnt)
    drw.rectangle([x, y, x + tw + 12, y + 17], fill=RED)
    drw.text((x + 6, y + 3), text, font=fnt, fill=WHITE)


def grain(img):
    """Deterministic paper speckle: a fixed arithmetic lattice of
    slightly darkened pixels, no randomness anywhere."""
    px = img.load()
    w, h = img.size
    yy = 0
    while yy < h:
        xx = 0
        while xx < w:
            if (xx * 31 + yy * 17) % 89 in (0, 1):
                r, g, b = px[xx, yy]
                px[xx, yy] = (max(0, r - 6), max(0, g - 6),
                              max(0, b - 6))
            xx += 2
        yy += 2
    return img

# ------------------------------------------------------------------ hero scenes
# Each scene is drawn on its own canvas and pasted, so nothing spills.


def scene_corvette(w, h):
    """Pre-dawn off Benghazi: harbour cranes behind, the corvette at
    anchor mid-frame, sea-drone wakes converging on her, one burst
    already at the waterline; the Angara rides far astern."""
    img = gradient(w, h, (12, 28, 50), (54, 86, 112))
    g = ImageDraw.Draw(img)
    for fx, fy in [(0.06, 0.12), (0.24, 0.07), (0.44, 0.16),
                   (0.63, 0.08), (0.80, 0.18), (0.93, 0.10)]:
        g.ellipse([fx * w, fy * h, fx * w + 2, fy * h + 2],
                  fill=(214, 222, 238))
    shore = h * 0.74
    for fx in (0.06, 0.20, 0.86):
        gx = fx * w
        g.line([gx, shore, gx, shore - 26], fill=(16, 26, 40), width=3)
        g.line([gx, shore - 26, gx + 0.11 * w, shore - 26],
               fill=(16, 26, 40), width=3)
        g.line([gx + 0.09 * w, shore - 26, gx + 0.09 * w, shore - 16],
               fill=(16, 26, 40), width=2)
    g.rectangle([0, shore, w, shore + 2], fill=(12, 22, 36))
    # the arms carrier Angara, a low silhouette far astern, right
    ax, ay = 0.865 * w, h * 0.70
    g.polygon([(ax - 26, ay), (ax + 26, ay), (ax + 21, ay + 5),
               (ax - 21, ay + 5)], fill=(24, 36, 52))
    g.rectangle([ax - 4, ay - 6, ax + 6, ay], fill=(24, 36, 52))
    # the corvette, centre: long hull, superstructure, mast — drawn
    # a tone lighter than the night so she reads at a glance
    hull_tone = (66, 84, 106)
    hx0, hx1, hy = 0.28 * w, 0.76 * w, h * 0.64
    g.polygon([(hx0, hy), (hx1, hy), (hx1 - 8, hy + 10),
               (hx0 + 12, hy + 10)], fill=hull_tone)
    g.line([hx0 + 2, hy, hx1 - 2, hy], fill=(120, 140, 164), width=1)
    g.rectangle([0.44 * w, hy - 11, 0.60 * w, hy], fill=hull_tone)
    g.rectangle([0.485 * w, hy - 18, 0.545 * w, hy - 11],
                fill=hull_tone)
    g.line([0.515 * w, hy - 18, 0.515 * w, hy - 27], fill=hull_tone,
           width=2)
    g.ellipse([0.50 * w, hy - 31, 0.53 * w, hy - 26], fill=hull_tone)
    for k in range(6):  # lit portholes along her side
        px = (0.34 + 0.055 * k) * w
        g.ellipse([px, hy + 3, px + 2, hy + 5], fill=(240, 200, 110))
    ex, ey = 0.68 * w, hy - 7  # a helicopter silhouette on her deck
    g.ellipse([ex - 7, ey - 3, ex + 7, ey + 3], fill=(30, 40, 54))
    g.line([ex - 11, ey - 5, ex + 11, ey - 5], fill=(30, 40, 54),
           width=2)
    # sea-drone wakes converging from the dark, lower left and right
    for sx, sy in [(0.03, 0.94), (0.16, 0.99), (0.97, 0.92)]:
        tx, ty = 0.47 * w, hy + 8
        g.line([sx * w, sy * h, tx, ty], fill=(190, 220, 235), width=2)
        g.line([sx * w + 6, sy * h - 3, tx, ty], fill=(130, 175, 200),
               width=1)
    for dx, dy in [(0.20, 0.86), (0.86, 0.84)]:  # two drones, visible
        gx, gy = dx * w, dy * h
        g.polygon([(gx - 6, gy), (gx + 6, gy), (gx + 2, gy + 3),
                   (gx - 2, gy + 3)], fill=(16, 22, 32))
    # the hit: a burst at her waterline, forward, and smoke above it
    burst(g, 0.44 * w, hy + 4, 14)
    burst(g, 0.41 * w, hy + 8, 7)
    for k in range(3):
        r = 4 + k * 2.5
        gx, gy = 0.45 * w + k * 5, hy - 16 - k * 6
        g.ellipse([gx - r, gy - r * 0.7, gx + r, gy + r * 0.7],
                  fill=(104, 108, 116))
    caption_tag(g, 8, h - 25, "CORVETTE SUNK OFF BENGHAZI")
    return img


def scene_summit(w, h):
    """Antalya: the rejected final text under a red cross, flags at
    half-mast, a lone gavel at rest."""
    img = gradient(w, h, (15, 40, 36), (47, 76, 58))
    g = ImageDraw.Draw(img)
    for fx in (0.04, 0.96):  # hall panelling
        g.line([fx * w, 6, fx * w, h - 6], fill=(86, 116, 92), width=1)
    # the rejected document, centre-left, glowing cream
    px0, py0, px1, py1 = 0.30 * w, 7, 0.63 * w, h - 7
    g.rectangle([px0, py0, px1, py1], fill=(240, 236, 224))
    g.line([px0 + 5, py0 + 5, px1 - 5, py1 - 5], fill=RED, width=3)
    g.line([px0 + 5, py1 - 5, px1 - 5, py0 + 5], fill=RED, width=3)
    g.rectangle([px0 + 5, py0 + 4, px0 + 64, py0 + 17],
                fill=(240, 236, 224))
    g.text((px0 + 7, py0 + 5), "FINAL TEXT",
           font=load_font(SANS_BOLD, 9), fill=INK)
    ff = load_font(SERIF_ITALIC, 12)
    fy = py0 + h * 0.52
    tw = g.textlength("fossil fuels", font=ff)
    g.rectangle([px0 + 5, fy - 2, px0 + 13 + tw, fy + 14],
                fill=(240, 236, 224))
    g.text((px0 + 7, fy), "fossil fuels", font=ff, fill=INK)
    g.line([px0 + 5, fy + 7, px0 + 10 + tw, fy + 7], fill=RED, width=2)
    # four flags at half-mast, right
    flag_specs = [(0.70, (38, 62, 140)), (0.78, (30, 50, 110)),
                  (0.86, (235, 235, 230)), (0.94, (235, 130, 40))]
    for fx, col in flag_specs:
        gx = fx * w
        g.line([gx, 8, gx, h - 8], fill=(214, 212, 202), width=2)
        fy2 = h * 0.44
        g.rectangle([gx, fy2, gx + 0.055 * w, fy2 + 10], fill=col)
    for k in range(4):
        sx = 0.70 * w + 3 + (k % 2) * 5
        sy = h * 0.44 + 2 + (k // 2) * 5
        g.ellipse([sx, sy, sx + 2, sy + 2], fill=GOLD)
    gx, gy = 0.11 * w, h * 0.60  # a lone gavel at rest, left
    g.line([gx - 9, gy + 9, gx + 11, gy - 11], fill=(206, 160, 92),
           width=4)
    g.rectangle([gx + 3, gy - 15, gx + 15, gy - 5], fill=(160, 108, 56))
    g.line([0.04 * w, gy + 13, 0.24 * w, gy + 13], fill=(238, 234, 222),
           width=2)
    caption_tag(g, 8, h - 25, "NO DEAL ADOPTED")
    return img


def scene_alliance(w, h):
    """Brussels, Monday — the council chamber, drawn as a place:
    the alliance emblem on the wall, an airspace screen alive with
    the three missile tracks, flags behind a curved table where
    the allies sit."""
    img = gradient(w, h, (16, 30, 58), (38, 60, 98))
    g = ImageDraw.Draw(img)
    for fx in (0.36, 0.985):  # chamber panelling
        g.line([fx * w, 5, fx * w, h - 5], fill=(64, 88, 124), width=1)
    # the wall emblem, left: compass star ringed by 32 lights
    cx, cy = 0.115 * w, h * 0.34
    for k in range(32):
        ang = math.tau * k / 32
        lx, ly = cx + 17 * math.cos(ang), cy + 17 * math.sin(ang)
        g.ellipse([lx - 1.2, ly - 1.2, lx + 1.2, ly + 1.2], fill=GOLD)
    star = []
    for k in range(8):
        ang = math.tau * k / 8 - math.tau / 4
        rad = 12 if k % 2 == 0 else 3.2
        star.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    g.polygon(star, fill=(226, 232, 242))
    g.ellipse([cx - 1.8, cy - 1.8, cx + 1.8, cy + 1.8],
              fill=(16, 30, 58))
    # the airspace screen, upper right: a coastline, a radar sweep,
    # three missile tracks ending in bursts over the border
    sx0, sy0, sx1, sy1 = 0.44 * w, 8, 0.975 * w, h * 0.56
    g.rounded_rectangle([sx0, sy0, sx1, sy1], 4, fill=(9, 19, 36),
                        outline=(120, 150, 190), width=1)
    coast = [(sx0 + 8, sy1 - 8), (sx0 + 26, sy1 - 16),
             (sx0 + 40, sy1 - 12), (sx0 + 58, sy1 - 22),
             (sx0 + 84, sy1 - 18), (sx0 + 108, sy1 - 28),
             (sx0 + 132, sy1 - 24)]
    g.line(coast, fill=(74, 160, 170), width=2)
    ox, oy = sx0 + 18, sy1 - 10  # the radar's sweep, from its origin
    for rr in (12, 24, 36):
        g.arc([ox - rr, oy - rr, ox + rr, oy + rr], 270, 360,
              fill=(52, 110, 120), width=1)
    g.line([ox, oy, ox + 34, oy - 20], fill=(110, 200, 190), width=1)
    for jx, jy in [(0.86, 0.30), (0.80, 0.44), (0.90, 0.52)]:
        exx, eyy = jx * w, jy * h
        g.arc([exx - 44, eyy - 26, exx + 30, eyy + 14], 300, 55,
              fill=(240, 178, 105), width=2)
        burst(g, exx, eyy, 5, fill=(240, 150, 80), core=(255, 220, 160))
    g.text((sx0 + 7, sy0 + 4), "AIRSPACE — POLAND",
           font=load_font(SANS_BOLD, 8), fill=(150, 190, 220))
    # flags behind the table, right of the emblem
    flag_cols = [(0, 91, 172), (190, 30, 22), (240, 183, 92),
                 (26, 138, 60), (235, 235, 230)]
    for i, col in enumerate(flag_cols):
        fx = 0.245 + 0.036 * i
        gx = fx * w
        g.line([gx, h * 0.30, gx, h * 0.70], fill=(200, 204, 210),
               width=2)
        g.rectangle([gx, h * 0.30, gx + 13, h * 0.30 + 8], fill=col)
    # the curved council table: a warm arc band across the bottom,
    # six seated allies with name plates and two microphones
    ty = h * 0.70
    g.pieslice([0.02 * w, ty - 26, 1.06 * w, ty + 44], 180, 360,
               fill=(122, 84, 48))
    g.arc([0.02 * w, ty - 26, 1.06 * w, ty + 44], 180, 360,
          fill=(198, 168, 110), width=3)
    g.rectangle([0, ty + 17, w, h], fill=(96, 64, 36))
    heads = [(0.50, (214, 178, 150)), (0.585, (120, 84, 60)),
             (0.67, (226, 196, 168)), (0.755, (96, 66, 48)),
             (0.84, (204, 164, 132)), (0.925, (140, 100, 74))]
    for fx, tone in heads:
        hx, hyy = fx * w, ty - 1
        g.ellipse([hx - 4.5, hyy - 9, hx + 4.5, hyy], fill=tone)
        g.pieslice([hx - 7, hyy - 3, hx + 7, hyy + 9], 180, 360,
                   fill=(28, 32, 44))
        g.rectangle([hx - 6, ty + 8, hx + 6, ty + 12],
                    fill=(238, 234, 222))
    for fx in (0.585, 0.84):  # two microphone stems on the table
        gx = fx * w
        g.line([gx + 8, ty + 6, gx + 13, ty - 6], fill=(20, 22, 28),
               width=2)
        g.ellipse([gx + 12, ty - 9, gx + 15, ty - 5], fill=(20, 22, 28))
    caption_tag(g, 8, h - 25, "32 ALLIES IN EMERGENCY SESSION")
    return img


HERO_SCENES = {"merkury": scene_corvette, "cop": scene_summit,
               "nato": scene_alliance}

# ------------------------------------------------------------------ card scenes
# Compact full-colour illustrations, one per pictured card.


def icon_dymer(w, h):
    img = gradient(w, h, (58, 62, 74), (96, 100, 112))
    g = ImageDraw.Draw(img)
    base = h
    bx0, bx1 = 0.08 * w, 0.52 * w  # the five-storey block, corner torn
    g.rectangle([bx0, base - 30, bx1, base], fill=(38, 40, 48))
    for r in range(3):
        for c in range(4):
            if (r * 4 + c) % 3:
                g.rectangle([bx0 + 4 + c * 9, base - 27 + r * 9,
                             bx0 + 8 + c * 9, base - 23 + r * 9],
                            fill=(240, 200, 110))
    g.polygon([(bx1 - 10, base - 30), (bx1 + 6, base - 18),
               (bx1 - 2, base - 6), (bx1 - 12, base - 12)],
              fill=(24, 25, 30))
    for fx, fs in [(0.55, 5), (0.62, 4), (0.68, 6), (0.75, 3)]:
        gx = fx * w  # rubble spilling from the tear
        g.polygon([(gx, base), (gx + fs, base - fs), (gx + 2 * fs, base)],
                  fill=(30, 31, 37))
    cx0 = 0.97 * w  # a rescue crane leaning in, lamp lit
    g.line([cx0, base, cx0 - 4, 3], fill=(210, 214, 220), width=2)
    g.line([cx0 - 4, 3, 0.60 * w, 6], fill=(210, 214, 220), width=2)
    g.line([0.64 * w, 6, 0.64 * w, 13], fill=(210, 214, 220), width=1)
    g.ellipse([0.64 * w - 3, 12, 0.64 * w + 3, 17], fill=(255, 226, 150))
    return img


def icon_chip(w, h):
    img = gradient(w, h, (10, 26, 18), (16, 44, 28))
    g = ImageDraw.Draw(img)
    cx, cy = 0.36 * w, h / 2  # the die: dark, gold pins, green traces
    g.rectangle([cx - 13, cy - 11, cx + 13, cy + 11], fill=(18, 20, 22),
                outline=(120, 220, 150), width=1)
    for k in range(4):
        py = cy - 9 + k * 6
        g.line([cx - 18, py, cx - 13, py], fill=GOLD, width=2)
        g.line([cx + 13, py, cx + 18, py], fill=GOLD, width=2)
    g.text((cx - 8, cy - 5), "AI", font=load_font(SANS_BOLD, 10),
           fill=(160, 240, 180))
    for tx in (0.62, 0.74, 0.86):
        gx = tx * w
        g.line([gx, h - 4, gx + 6, h - 12], fill=(52, 199, 106),
               width=2)
    g.polygon([(0.90 * w, 4), (0.97 * w, 12), (0.86 * w, 12)],
              fill=(52, 199, 106))
    g.text((0.60 * w, 3), "+30%", font=load_font(SANS_BOLD, 11),
           fill=(160, 240, 180))
    return img


def icon_tanker(w, h):
    img = gradient(w, h, (24, 34, 54), (52, 66, 88))
    g = ImageDraw.Draw(img)
    keel = h * 0.70  # a shadow-fleet tanker riding dark and low
    g.polygon([(0.05 * w, keel), (0.93 * w, keel), (0.87 * w, keel + 8),
               (0.11 * w, keel + 8)], fill=(14, 16, 20))
    g.rectangle([0.10 * w, keel - 8, 0.20 * w, keel], fill=(14, 16, 20))
    for fx in (0.30, 0.48, 0.66):
        g.rectangle([fx * w, keel - 5, fx * w + 14, keel],
                    fill=(20, 22, 26))
    g.line([0.22 * w, keel - 2, 0.84 * w, keel - 2],
           fill=(214, 178, 90), width=1)
    sx, sy = 0.80 * w, h * 0.20  # and the sanction stamp across her
    g.rectangle([sx - 13, sy - 6, sx + 13, sy + 6], outline=RED, width=2)
    g.text((sx - 10, sy - 4), "OFAC", font=load_font(SANS_BOLD, 8),
           fill=RED)
    return img


def icon_arson(w, h):
    img = gradient(w, h, (30, 26, 40), (62, 48, 52))
    g = ImageDraw.Draw(img)
    base = h  # a row of village houses; the middle one is burning
    for i, fx in enumerate((0.06, 0.30, 0.56, 0.78)):
        hx = fx * w
        g.rectangle([hx, base - 13, hx + 16, base], fill=(22, 20, 24))
        g.polygon([(hx - 2, base - 13), (hx + 8, base - 19),
                   (hx + 18, base - 13)], fill=(16, 14, 18))
        if i == 1:
            g.polygon([(hx + 3, base - 15), (hx + 8, base - 27),
                       (hx + 13, base - 15)], fill=ORANGE)
            g.polygon([(hx + 6, base - 15), (hx + 8, base - 21),
                       (hx + 10, base - 15)], fill=GOLD)
            for k in range(3):
                r = 3 + k * 2
                gx = hx + 12 + k * 3
                g.ellipse([gx - r, 2 + k * 3, gx + r, 2 + k * 3 + r],
                          fill=(96, 90, 96))
    g.polygon([(0.60 * w, base - 3), (0.86 * w, base - 3),
               (0.82 * w, base - 7), (0.64 * w, base - 7)],
              fill=(10, 10, 12))  # a burnt-out car shell in front
    return img


def icon_factory(w, h):
    img = gradient(w, h, (56, 32, 26), (100, 54, 38))
    g = ImageDraw.Draw(img)
    floor_y = h
    g.rectangle([0.06 * w, floor_y - 14, 0.60 * w, floor_y],
                fill=(24, 18, 16))
    g.polygon([(0.06 * w, floor_y - 14), (0.22 * w, floor_y - 20),
               (0.33 * w, floor_y - 15), (0.44 * w, floor_y - 21),
               (0.60 * w, floor_y - 14)], fill=(24, 18, 16))
    for fx, fh in [(0.26, 0.30), (0.37, 0.44), (0.49, 0.26)]:
        cx = fx * w
        g.polygon([(cx - 5, floor_y - 15), (cx, floor_y - 15 - fh * h),
                   (cx + 5, floor_y - 15)], fill=ORANGE)
        g.polygon([(cx - 2, floor_y - 15),
                   (cx, floor_y - 15 - fh * h * 0.55),
                   (cx + 2, floor_y - 15)], fill=GOLD)
    for fx, fh in ((0.63, 18), (0.73, 15)):
        g.rectangle([fx * w, floor_y - fh, fx * w + 6, floor_y],
                    fill=(24, 18, 16))
    ex = 0.64 * w  # an ambulance waiting at the gate
    g.rectangle([ex, floor_y - 7, ex + 22, floor_y - 1],
                fill=(158, 42, 30))
    g.rectangle([ex + 15, floor_y - 11, ex + 22, floor_y - 7],
                fill=(158, 42, 30))
    for fx in (0.70, 0.86):
        cx = fx * w
        g.ellipse([cx - 3, floor_y - 4, cx + 3, floor_y + 1],
                  fill=(10, 10, 10))
    return img


def icon_khartoum(w, h):
    img = gradient(w, h, (12, 18, 38), (34, 44, 66))
    g = ImageDraw.Draw(img)
    base = h - 8  # rooftops across the capital
    for fx, fw, fh in [(0.02, 0.20, 0.30), (0.26, 0.16, 0.44),
                       (0.46, 0.22, 0.26), (0.72, 0.26, 0.38)]:
        bx = fx * w
        g.rectangle([bx, base - fh * h, bx + fw * w, base],
                    fill=(10, 12, 18))
    burst(g, 0.56 * w, base - 0.30 * h, 7)
    for fx, fy in [(0.30, 0.22), (0.68, 0.14)]:  # two drones crossing
        dx, dy = fx * w, fy * h
        g.line([dx - 7, dy - 5, dx + 7, dy + 5], fill=(228, 230, 238),
               width=2)
        g.line([dx - 7, dy + 5, dx + 7, dy - 5], fill=(228, 230, 238),
               width=2)
        g.ellipse([dx - 1.5, dy - 1.5, dx + 1.5, dy + 1.5], fill=RED)
    g.rectangle([0, h - 8, w, h], fill=(38, 92, 168))  # the UN band
    g.text((6, h - 8), "UN", font=load_font(SANS_BOLD, 8), fill=WHITE)
    return img


def icon_chart(w, h):
    img = gradient(w, h, (26, 14, 16), (48, 22, 24))
    g = ImageDraw.Draw(img)
    for gy in (0.28, 0.55, 0.82):  # gridlines, then the fall
        g.line([4, gy * h, w - 4, gy * h], fill=(92, 52, 54), width=1)
    pts = [(0.04 * w, 0.24 * h), (0.24 * w, 0.30 * h),
           (0.42 * w, 0.26 * h), (0.60 * w, 0.48 * h),
           (0.78 * w, 0.62 * h), (0.96 * w, 0.80 * h)]
    g.line(pts, fill=(232, 64, 52), width=2)
    for px, py in pts[::2]:
        g.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(232, 64, 52))
    g.text((0.06 * w, 0.60 * h), "KOSPI −3.3%",
           font=load_font(SANS_BOLD, 10), fill=(255, 190, 180))
    return img


def icon_eustars(w, h):
    img = gradient(w, h, (24, 48, 110), (34, 66, 140))
    g = ImageDraw.Draw(img)
    cx, cy = 0.30 * w, h / 2  # the circle of twelve stars
    for k in range(12):
        ang = math.tau * k / 12 - math.tau / 2
        sx, sy = cx + 11 * math.cos(ang), cy + 11 * math.sin(ang)
        g.polygon([(sx, sy - 3), (sx + 2.4, sy + 2), (sx - 2.4, sy + 2)],
                  fill=GOLD)
    g.text((0.52 * w, cy - 8), "22nd", font=load_font(SERIF_BOLD, 15),
           fill=(255, 240, 200))
    g.text((0.52 * w, cy + 7), "PACKAGE", font=load_font(SANS_BOLD, 8),
           fill=(255, 240, 200))
    return img


def icon_oil(w, h):
    img = gradient(w, h, (40, 30, 34), (74, 54, 44))
    g = ImageDraw.Draw(img)
    base = h  # two derricks on a dark plain; the far one is burning
    for fx, s in [(0.16, 1.0), (0.62, 0.8)]:
        gx = fx * w
        top = base - 24 * s
        g.line([gx - 8 * s, base, gx, top], fill=(16, 14, 16), width=2)
        g.line([gx + 8 * s, base, gx, top], fill=(16, 14, 16), width=2)
        g.line([gx - 5 * s, base - 8 * s, gx + 5 * s, base - 8 * s],
               fill=(16, 14, 16), width=1)
    burst(g, 0.62 * w, base - 22, 8)
    g.polygon([(0.62 * w - 3, base - 12), (0.62 * w, base - 24),
               (0.62 * w + 3, base - 12)], fill=GOLD)
    g.line([0.30 * w, base - 3, 0.97 * w, base - 3], fill=(16, 14, 16),
           width=2)  # a pipeline running off into the distance
    return img


def icon_strike(w, h):
    img = gradient(w, h, (66, 76, 94), (112, 122, 140))
    g = ImageDraw.Draw(img)
    base = h  # the factory gate, shut; a line of pickets before it
    g.rectangle([0.06 * w, base - 20, 0.52 * w, base], fill=(40, 46, 56))
    g.polygon([(0.06 * w, base - 20), (0.29 * w, base - 27),
               (0.52 * w, base - 20)], fill=(30, 35, 44))
    for i in range(4):
        px = (0.60 + 0.075 * i) * w
        g.ellipse([px - 2.5, base - 13, px + 2.5, base - 8],
                  fill=(24, 26, 30))
        g.line([px, base - 8, px, base], fill=(24, 26, 30), width=2)
    sx = 0.88 * w
    g.line([sx, base - 13, sx, base], fill=(120, 84, 44), width=2)
    g.rectangle([sx - 10, base - 21, sx + 10, base - 13],
                fill=(247, 245, 238))
    g.text((sx - 8, base - 20), "STOP", font=load_font(SANS_BOLD, 7),
           fill=RED)
    return img


def icon_gta(w, h):
    img = gradient(w, h, (122, 28, 110), (16, 128, 140))
    g = ImageDraw.Draw(img)
    sx, sy = 0.70 * w, h * 0.52  # a neon sun behind a palm silhouette
    g.ellipse([sx - 10, sy - 10, sx + 10, sy + 10], fill=(255, 196, 64))
    for gy in (0.40, 0.52, 0.64):
        g.line([sx - 11, gy * h, sx + 11, gy * h], fill=(16, 128, 140),
               width=2)
    px = 0.16 * w
    g.line([px, h, px + 2, h * 0.30], fill=(14, 20, 24), width=3)
    for k in range(5):
        ang = math.pi * (0.08 + 0.21 * k)
        ex = px + 2 + 13 * math.cos(ang)
        ey = h * 0.30 - 9 * math.sin(ang)
        g.line([px + 2, h * 0.30, ex, ey], fill=(14, 20, 24), width=2)
    g.text((0.26 * w, h * 0.58), "$3.79bn",
           font=load_font(SANS_BOLD, 14), fill=(255, 240, 200))
    return img


def icon_nhs(w, h):
    img = gradient(w, h, (240, 244, 238), (212, 230, 218))
    g = ImageDraw.Draw(img)
    cy = h / 2
    cx = 0.20 * w  # the red cross, then a heartbeat going steady
    g.rectangle([cx - 4, cy - 12, cx + 4, cy + 12], fill=RED)
    g.rectangle([cx - 12, cy - 4, cx + 12, cy + 4], fill=RED)
    pts = [(0.42 * w, cy), (0.55 * w, cy), (0.59 * w, cy - 8),
           (0.64 * w, cy + 6), (0.68 * w, cy), (0.97 * w, cy)]
    g.line(pts, fill=(26, 138, 72), width=2)
    return img


CARD_SCENES = {
    "dymer": icon_dymer, "chip": icon_chip, "tanker": icon_tanker,
    "arson": icon_arson, "factory": icon_factory,
    "khartoum": icon_khartoum, "chart": icon_chart,
    "eustars": icon_eustars, "oil": icon_oil, "strike": icon_strike,
    "gta": icon_gta, "nhs": icon_nhs,
}

# ------------------------------------------------------------------ the map
# Pins sit at each place's real longitude/latitude. Seven of them
# crowd into Europe and the Levant, where a disc at the true point
# would bury its neighbours — so those seven are FANNED: the disc
# moves out to open water or open steppe and a cased leader line
# runs from it to a dot on the exact spot. Nothing is hidden and
# nothing is moved silently: the line is the position.

CALLOUTS = {
    15: (0.378, 0.190),  # London -> North Atlantic
    13: (0.438, 0.120),  # Hamburg -> Denmark Strait
    3: (0.408, 0.300),   # Brussels (NATO) -> Atlantic
    11: (0.462, 0.352),  # Brussels (EU) -> off Iberia
    4: (0.672, 0.148),   # Dymer / Kyiv -> the steppe
    12: (0.715, 0.255),  # Rostov -> east of the Caspian gap
    7: (0.680, 0.445),   # West Bank -> Arabia
}


def draw_map(img, g, map_x, map_y):
    """The block world on its navy-to-teal sea, pins fanned."""
    pitch_x, pitch_y = 4.0, 3.6
    map_w = len(WORLD[0]) * pitch_x
    map_h = len(WORLD) * pitch_y
    sea_w, sea_h = int(map_w) + 10, int(map_h) + 10
    sea = gradient(sea_w, sea_h, SEA_TOP, SEA_BOT)
    sd = ImageDraw.Draw(sea)
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
    img.paste(sea, (map_x - 5, map_y - 5))

    def spot(fx, fy):
        return map_x + fx * map_w, map_y + fy * map_h

    for num, (fx, fy) in CALLOUTS.items():  # leader lines first
        ax, ay = spot(*PINS[num])
        dx, dy = spot(fx, fy)
        g.line([dx, dy, ax, ay], fill=(10, 22, 34), width=4)
        g.line([dx, dy, ax, ay], fill=WHITE, width=2)
    for num in CALLOUTS:  # a dot on the exact place
        ax, ay = spot(*PINS[num])
        g.ellipse([ax - 3.0, ay - 3.0, ax + 3.0, ay + 3.0], fill=WHITE)
        g.ellipse([ax - 1.9, ay - 1.9, ax + 1.9, ay + 1.9],
                  fill=PIN_FILL)
    for num, (fx, fy) in PINS.items():
        if num not in CALLOUTS:
            px, py = spot(fx, fy)
            pin_disc(g, px, py, num, r=6.0)
    for num, (fx, fy) in CALLOUTS.items():
        px, py = spot(fx, fy)
        pin_disc(g, px, py, num, r=6.5)
    return map_w, map_h

# ------------------------------------------------------------------ page


def render_page():
    img = Image.new("RGB", (PAGE, PAGE), FRAME)
    g = ImageDraw.Draw(img)
    g.rectangle([8, 8, PAGE - 8, PAGE - 8], fill=PAPER)

    # ---- masthead
    g.rectangle([EDGE, 22, EDGE + 9, 31], fill=RED)
    g.text((EDGE + 14, 19), "ONE DAY OF WORLD NEWS, ONE PICTURE",
           font=load_font(SANS_BOLD, 15), fill=RED)
    total = (f"{STORY_COUNT} STORIES · 6 REGIONS · "
             f"EVERY ONE FROM THIS MONDAY")
    rf = load_font(SANS, 10)
    g.text((PAGE - EDGE - g.textlength(total, font=rf), 23), total,
           font=rf, fill=INK)
    g.line([EDGE, 42, PAGE - EDGE, 42], fill=INK, width=1)
    g.line([EDGE, 45, PAGE - EDGE, 45], fill=INK, width=3)

    # ---- date and dek: the day named, in full, before anything else
    centre(g, PAGE / 2, 52, DAY, load_font(SERIF_BOLD, 56), INK)
    centre(g, PAGE / 2, 118, DEK, load_font(SERIF_ITALIC, 16), RED)
    g.line([EDGE, 140, PAGE - EDGE, 140], fill=INK, width=1)

    # ---- Monday updates: red label, six slots
    g.rectangle([EDGE, 146, EDGE + 66, 182], fill=RED)
    centre(g, EDGE + 33, 152, "MONDAY", load_font(SANS_BOLD, 10), WHITE)
    centre(g, EDGE + 33, 165, "UPDATES", load_font(SANS_BOLD, 10), WHITE)
    slot_x = EDGE + 74
    slot_w = (PAGE - EDGE - slot_x) / 6
    for i, (tm, what) in enumerate(UPDATE_SLOTS):
        sx = slot_x + i * slot_w
        fit(g, sx + 6, 149, tm, SANS_BOLD, 12, slot_w - 10, RED,
            floor=8)
        fit(g, sx + 6, 166, what, SANS, 9, slot_w - 10, INK, floor=7)
        if i:
            g.line([sx, 150, sx, 178], fill=RULE_SOFT, width=1)
    g.line([EDGE, 186, PAGE - EDGE, 186], fill=INK, width=1)

    # ---- the day in numbers
    g.text((EDGE, 192), "THE DAY IN NUMBERS",
           font=load_font(SANS_BOLD, 10), fill=RED)
    cell = SPAN / 6
    for i, (fig, cap1, cap2) in enumerate(NUMBERS2):
        cx = EDGE + cell * i + cell / 2
        centre(g, cx, 206, fig, load_font(SERIF_BOLD, 27), INK)
        centre(g, cx, 240, cap1, load_font(SANS, 9), FAINT)
        centre(g, cx, 251, cap2, load_font(SANS, 9), FAINT)
        if i:
            g.line([EDGE + cell * i, 208, EDGE + cell * i, 258],
                   fill=RULE_SOFT, width=1)
    g.line([EDGE, 264, PAGE - EDGE, 264], fill=INK, width=1)

    # ---- region tabs, counts computed from the story list
    tf = load_font(SANS_BOLD, 12)
    labels = [(r, f"{r.upper()} {REGION_TALLY[r]}") for r in TAB_ORDER]
    widths = [g.textlength(t, font=tf) + 20 for _r, t in labels]
    gap = (SPAN - sum(widths)) / (len(labels) - 1)
    tx = float(EDGE)
    for (r, t), tw in zip(labels, widths):
        g.rectangle([tx, 270, tx + tw, 292], fill=TAB_INK[r])
        centre(g, tx + tw / 2, 275, t, tf, WHITE)
        tx += tw + gap

    # ---- heroes: rich scenes, badge, tag, pill, headline, summary
    hero_w = 309
    for i, hero in enumerate(HEROES):
        hx = EDGE + i * (hero_w + 10)
        img.paste(HERO_SCENES[hero["scene"]](hero_w, 100), (hx, 300))
        disc(g, hx + 10, 414, hero["num"], r=10)
        pill(g, hx + hero_w, 406, HERO_PILL[hero["num"]],
             PILL_INK[hero["cert"]], size=9, h=15)
        pw = g.textlength(HERO_PILL[hero["num"]],
                          font=load_font(SANS_BOLD, 9))
        fit(g, hx + 26, 407, hero["tag"], SANS_BOLD, 10,
            hero_w - 26 - pw - 20, RED, floor=8)
        para(g, hx, 428, hero["head"], load_font(SERIF_BOLD, 24), INK,
             hero_w, 26, cap=2)
        para(g, hx, 484, hero["summ"], load_font(SERIF, 12), INK,
             hero_w, 15, cap=3)
    g.line([EDGE, 534, PAGE - EDGE, 534], fill=INK, width=1)

    # ---- pictured cards, two rows of six
    card_w = 151
    for i, card in enumerate(CARDS):
        cx0 = EDGE + (i % 6) * (card_w + 8)
        cy0 = 540 + (i // 6) * 116
        img.paste(CARD_SCENES[card["scene"]](card_w, 38), (cx0, cy0))
        pill(g, cx0 + card_w - 3, cy0 + 3, card["cert"],
             PILL_INK[card["cert"]], size=8, h=13)
        g.rectangle([cx0, cy0 + 43, cx0 + 7, cy0 + 50],
                    fill=TAB_INK[card["region"]])
        fit(g, cx0 + 11, cy0 + 42, card["place"], SANS_BOLD, 9,
            card_w - 11, RED, floor=7)
        para(g, cx0, cy0 + 55, card["head"],
             load_font(SERIF_BOLD, 14), INK, card_w, 16, cap=2)
        para(g, cx0, cy0 + 88, card["summ"], load_font(SERIF, 11),
             INK, card_w, 13, cap=2)

    # ---- bottom band: the map left, the briefs right
    g.line([EDGE, 774, PAGE - EDGE, 774], fill=INK, width=1)
    by = 780
    g.text((EDGE, by), "WHERE IT HAPPENED",
           font=load_font(SANS_BOLD, 12), fill=INK)
    g.text((EDGE, by + 15),
           "Europe's pins are fanned out — the lines mark the "
           "exact places.", font=load_font(SANS, 8.5), fill=FAINT)
    map_x, map_y = EDGE, by + 24
    map_w, map_h = draw_map(img, g, map_x, map_y)
    lf = load_font(SANS, 9)
    for li, group in enumerate((TAB_ORDER[:3], TAB_ORDER[3:])):
        lx = float(EDGE)
        ly = map_y + map_h + 7 + li * 11
        for r in group:
            g.rectangle([lx, ly + 1, lx + 7, ly + 8], fill=TAB_INK[r])
            t = f"{REGION_SHORT[r]} {REGION_TALLY[r]}"
            g.text((lx + 10, ly), t, font=lf, fill=INK)
            lx += 10 + g.textlength(t, font=lf) + 13

    bx = 404
    g.text((bx, by), f"ALSO ON MONDAY — {len(BRIEFS2)} MORE STORIES",
           font=load_font(SANS_BOLD, 12), fill=INK)
    bf = load_font(SANS_BOLD, 8)
    col_w = 284
    for i, (num, text, _region) in enumerate(BRIEFS2):
        col, row_i = divmod(i, 10)
        x0 = bx + col * (col_w + 12)
        y0 = by + 24 + row_i * 15.6
        g.rectangle([x0, y0 + 1, x0 + 15, y0 + 13], fill=RED)
        label = str(num)
        box = g.textbbox((0, 0), label, font=bf)
        g.text((x0 + 7.5 - (box[2] - box[0]) / 2 - box[0], y0 + 3),
               label, font=bf, fill=WHITE)
        fit(g, x0 + 18, y0 + 2, text, SANS, 11, col_w - 18, INK,
            floor=9)

    # ---- footer: dating line left, certainty key right
    g.text((EDGE, 964),
           "Every story happened, or was first reported, on Monday "
           "23 November 2026.", font=load_font(SANS, 9), fill=FAINT)
    key = ("OFFICIAL govt · CONFIRMED multi-source · REPORTED "
           "attributed · CLAIM one side")
    kf = load_font(SANS_BOLD, 9)
    g.text((PAGE - EDGE - g.textlength(key, font=kf), 964), key,
           font=kf, fill=INK)

    # ---- date-check box
    box_y = 977
    g.rectangle([EDGE, box_y, PAGE - EDGE, box_y + 32],
                fill=(250, 238, 231), outline=RED, width=2)
    para(g, EDGE + 16, box_y + 6, DATE_CHECK, load_font(SERIF, 11),
         DEEP_RED, SPAN - 32, 12, cap=2)

    return grain(img)


def save_page(out_path):
    render_page().save(out_path, format="PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "entry.png")
    out = sys.argv[1] if len(sys.argv) > 1 else default
    print(save_page(out), os.path.getsize(out))
