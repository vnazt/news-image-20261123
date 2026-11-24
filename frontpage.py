"""frontpage.py — the data and shared drawing helpers for the
news-image-20261123 front page, plus a compact fallback edition.

The page is a classic illustrated broadsheet for one day — Monday
23 November 2026 — drawn entirely in code with Pillow and the
Liberation family. frontpage2.py renders the rich edition from the
data held here: masthead, giant serif date naming the Monday, a
six-figure numbers strip, region tabs counted from the story list
itself, three hero panels with drawn scenes, twelve pictured story
cards with certainty pills, a filled-block world map carrying a
numbered pin for every pictured story, twenty one-line briefs, and
a red date-check box.

All 35 stories come from a verified research dossier: every figure
was confirmed by two independent sources before it was allowed on
the page (five briefs rest on the AFP wire, the originating source,
and are flagged as such), one-sided claims are labelled CLAIM, and
Monday is a follow-up day — weekend events appear only through
their Monday developments: the toll that climbed, the condemnation
that landed, the session that convened. The render is
deterministic: same data, same PNG, every run.

Usage:  python3 frontpage.py   ->   fallback.png (compact edition)
        python3 frontpage2.py  ->   the rich edition (entry.png)
"""

import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ fonts

FONT_ROOT = "/usr/share/fonts/truetype/liberation"
SERIF = os.path.join(FONT_ROOT, "LiberationSerif-Regular.ttf")
SERIF_BOLD = os.path.join(FONT_ROOT, "LiberationSerif-Bold.ttf")
SERIF_ITALIC = os.path.join(FONT_ROOT, "LiberationSerif-Italic.ttf")
SANS = os.path.join(FONT_ROOT, "LiberationSans-Regular.ttf")
SANS_BOLD = os.path.join(FONT_ROOT, "LiberationSans-Bold.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


# ------------------------------------------------------------------ ink

PAPER = (247, 242, 227)
INK = (26, 25, 23)
FAINT = (99, 94, 81)
RED = (178, 34, 24)
DEEP_RED = (148, 27, 18)
GOLD = (233, 165, 33)
ORANGE = (243, 121, 33)
RULE_SOFT = (192, 184, 161)

TAB_INK = {
    "Europe": (43, 90, 166),
    "Middle East": (125, 60, 152),
    "Africa": (30, 132, 73),
    "Asia-Pacific": (178, 62, 32),
    "Americas": (183, 149, 11),
    "World & Science": (93, 109, 126),
}
TAB_ORDER = ["Europe", "Middle East", "Africa", "Asia-Pacific",
             "Americas", "World & Science"]

PAGE = 1024
EDGE = 28
SPAN = PAGE - 2 * EDGE  # 968 px of content

DAY = "Monday 23 November 2026"
DEK = ("A Russian corvette sunk off Libya · COP31 collapses, no deal "
       "· NATO's 32 allies reckon with missiles in Poland")

# ------------------------------------------------------------------ heroes
# num, place tag, headline, summary, region, scene key, certainty

HEROES = [
    dict(num=1, region="Africa", scene="merkury", cert="CONFIRMED",
         tag="BENGHAZI · LIBYA — WAR AT SEA",
         head="Ukraine Sinks a Russian Corvette off Libya",
         summ="Zelensky confirmed it Monday: seven sea drones sank the "
              "corvette Merkury as it refuelled in Benghazi, and "
              "disabled the arms carrier Angara. (CNN / AFP)"),
    dict(num=2, region="World & Science", scene="cop", cert="CONFIRMED",
         tag="ANTALYA · TÜRKİYE — CLIMATE",
         head="COP31 Collapses: No Deal in Antalya",
         summ="The summit ended Monday, two days into overtime, "
              "adopting nothing — 130+ nations refused a text silent "
              "on fossil fuels. First failed COP since 2009. (AFP)"),
    dict(num=3, region="Europe", scene="nato", cert="CONFIRMED",
         tag="BRUSSELS · BELGIUM — NATO",
         head="NATO in Emergency Session over Poland Missiles",
         summ="All 32 allies met Monday over the three Russian "
              "Kh-101s that fell in Poland on Friday. NATO: Russia "
              "bears full responsibility. (Wires)"),
]

# ------------------------------------------------------------------ cards
# num, place, certainty, headline, summary, region, scene key

CARDS = [
    dict(num=4, region="Europe", scene="dymer",
         place="DYMER · UKRAINE", cert="CONFIRMED",
         head="Dymer Toll Climbs to 11",
         summ="Boy of 7 out alive after 14 hours; region mourns. (BBC)"),
    dict(num=5, region="Americas", scene="chip",
         place="SANTA CLARA · US", cert="CONFIRMED",
         head="Nvidia Brings Back Huang; Shares Leap 30%",
         summ="Reinstated after 11 days; +$900bn in a day. (CNN)"),
    dict(num=6, region="Middle East", scene="tanker",
         place="WASHINGTON · US", cert="OFFICIAL",
         head="US Sanctions Iran's Shadow Fleet",
         summ="30+ targets, 12 tankers; $14.7bn traced — Treasury."),
    dict(num=7, region="Middle East", scene="arson",
         place="WEST BANK", cert="CONFIRMED",
         head="Eisenkot: Arson Is ‘Jewish Terrorism’",
         summ="12 vehicles torched across five villages. (Reuters)"),
    dict(num=8, region="Asia-Pacific", scene="factory",
         place="CIKANDE · INDONESIA", cert="CONFIRMED",
         head="Indonesia Confirms 24 Dead in Fire",
         summ="Candy-plant fire; 30 missing; DNA tests begin. (Reuters)"),
    dict(num=9, region="Africa", scene="khartoum",
         place="KHARTOUM · SUDAN", cert="CONFIRMED",
         head="UN and US Condemn Khartoum Strikes",
         summ="UN site hit, four dead; UN and US condemn. (AFP)"),
    dict(num=10, region="Asia-Pacific", scene="chart",
         place="SEOUL · KOREA", cert="CONFIRMED",
         head="Asia's AI Sell-Off Deepens",
         summ="Kospi −3.3% at 4,708.5 — a 10-month low. (CNBC)"),
    dict(num=11, region="Europe", scene="eustars",
         place="BRUSSELS · EU", cert="CONFIRMED",
         head="EU Unveils 22nd Russia Package",
         summ="Wider finance, travel curbs presented Monday. (h.ua)"),
    dict(num=12, region="Europe", scene="oil",
         place="KYIV · UKRAINE", cert="REPORTED",
         head="Ukraine Confirms Deep Oil Strikes",
         summ="Oil sites hit 1,200–1,500 km inside Russia. (h.ua)"),
    dict(num=13, region="Europe", scene="strike",
         place="NORTHERN GERMANY", cert="CONFIRMED",
         head="23,000 Metalworkers Walk Out",
         summ="IG Metall's 24-hour wave hits 19 firms. (EcoPulse24)"),
    dict(num=14, region="World & Science", scene="gta",
         place="NEW YORK · US", cert="REPORTED",
         head="GTA VI Takes $3.79bn on Day One",
         summ="Entertainment's biggest day-one tally ever. (Reports)"),
    dict(num=15, region="Europe", scene="nhs",
         place="LONDON · UK", cert="CONFIRMED",
         head="NHS Puts AI in Cancer Screening",
         summ="EDITH trial invites nearly 700,000 women. (BBC)"),
]

# ------------------------------------------------------------------ briefs
# num, one-line text (place first, source last), region.
# The five AFP-wire briefs (17, 23, 29, 30, 31) rest on the wire as
# originating source and keep the "(AFP wire)" flag.

BRIEFS = [
    (16, "New York — UNSC briefed on Ukraine energy, food (h.ua)",
     "World & Science"),
    (17, "Berlin — Zelensky: four-way talks with Russia (AFP wire)",
     "World & Science"),
    (18, "Moscow — Kremlin warns of Baltic escalation (AFP · CNN)",
     "World & Science"),
    (19, "Tripoli — Libya: Benghazi ‘no arena for scores’ (CNN)",
     "Africa"),
    (20, "Atlanta — Delta backlog: 155 delays, 44 cancelled (AP)",
     "Americas"),
    (21, "Singapore — Megaspeed put on US Entity List (NY Post)",
     "Americas"),
    (22, "Wall Street — Nasdaq +6.5%, S&P +4.73% (Le Monde)",
     "Americas"),
    (23, "Tehran — Iran vows to counter US blockade (AFP wire)",
     "Middle East"),
    (24, "London — UK named host of 2035 Women's World Cup (BBC)",
     "World & Science"),
    (25, "Science — AI Riemann proof claimed, unverified (Principia)",
     "World & Science"),
    (26, "New Delhi — India gives flood-hit Nepal $1.62bn (AFP)",
     "Asia-Pacific"),
    (27, "Mexico — More arrests follow kingpin's capture (AFP)",
     "Americas"),
    (28, "S. Lebanon — Villagers return to wrecked homes (Principia)",
     "Middle East"),
    (29, "Sydney — Solomons security treaty near (AFP wire)",
     "Asia-Pacific"),
    (30, "Hodeidah — Houthi claim: Saudi strike kills 10 (AFP wire)",
     "World & Science"),
    (31, "US — Democrats projected biggest majority since 1992 (AFP wire)",
     "Americas"),
    (32, "Antalya — COP31 backlash; Bowen faces calls to quit (AFP)",
     "World & Science"),
    (33, "Warsaw — Russian ambassador to be summoned (h.ua)", "Europe"),
    (34, "Kyiv — Ukraine braces for a winter of blackouts (Principia)",
     "Europe"),
    (35, "Taipei — Taiex +2.16% as short-sale curbs begin (TechBag)",
     "Asia-Pacific"),
]

# ------------------------------------------------------------------ numbers

NUMBERS = [
    ("7", "SEA DRONES SANK THE CORVETTE MERKURY"),
    ("92,000", "REGISTERED AT COP31, PROVISIONALLY THE LARGEST"),
    ("+30%", "NVIDIA IN ONE DAY, A RECORD $900BN ADDED"),
    ("$14.7bn", "TRACED TO IRAN'S SHADOW BANKS BY TREASURY"),
    ("24", "DEAD IN THE BANTEN FACTORY FIRE, CONFIRMED"),
    ("11", "DEAD IN DYMER; A BOY OF 7 CAME OUT ALIVE"),
]

DATE_CHECK = (
    "DATE CHECK — Weekend events appear only as their Monday "
    "developments. Left out as other days' news: the missiles' fall "
    "in Poland itself (Fri 20 Nov) · the Nigeria funeral boat (Fri) "
    "· October's euro inflation figure (18 Nov) · the FBI database "
    "hack (Fri) · Kerch Bridge damage (16–19 Nov) · GTA VI's "
    "launch (19 Nov)."
)

STORY_COUNT = len(HEROES) + len(CARDS) + len(BRIEFS)
REGION_TALLY = Counter(
    [h["region"] for h in HEROES]
    + [c["region"] for c in CARDS]
    + [region for _n, _t, region in BRIEFS]
)

# ------------------------------------------------------------------ map
# A block world at 88 x 36 cells on a plain equirectangular grid:
# each column is ~4.1 degrees of longitude, each row ~4 degrees of
# latitude (84N down to 56S), so the shapes keep their real
# proportions — the Americas waist, Africa's bulge and horn, India's
# triangle, the Indonesian scatter, Australia and New Zealand.
# '#' is land. Pins below are fractions of the map box, computed
# from each place's real longitude and latitude, so they stay put
# whatever the grid's resolution.

WORLD = [
    "            ######    #####       #####       ##       #####       ###                  ",
    "             ####   ######       #######      ###      #######     ####     ###         ",
    "          ###################    #######          ######################################",
    "   ###########################    #####      ###########################################",
    "   ###################    #####    ###  #   ############################################",
    "    ###################    #####            ############################################",
    "            ############   #####          ##############################################",
    "            ###################          ###############################################",
    "            ##################            #######################################       ",
    "            ##################           #############    ########################      ",
    "            ##################           ########## ############################        ",
    "            #################            ######## #############################         ",
    "             ###############             #######################################        ",
    "             ########## ##              #####################################           ",
    "             ######                     #################################               ",
    "              #####                     ################ ################ ##            ",
    "                ####                   ################       ##########  #             ",
    "                 ####                  #################      ##  #####                 ",
    "                         ########        ###############      #     ## ###              ",
    "                         #########         ##########             ### ####### #####     ",
    "                         ##########           ########            ### ###### ######     ",
    "                         ###########          #######               ######   ######     ",
    "                         ############          #######              ######   ######     ",
    "                          ###########          #######                  ###   ###       ",
    "                          ###########          ####### ##              ###########      ",
    "                          ##########           ######  #               ###########      ",
    "                          #########           #######  #               ###########      ",
    "                          ########            ######                    #########       ",
    "                          #######             #####                     #########       ",
    "                          ######              ####                       #######     #  ",
    "                          #####                                           #####      ###",
    "                          ####                                                      ### ",
    "                          ###                                                      ###  ",
    "                          ###                                                           ",
    "                          ##                                                            ",
    "                                                                                        ",
]

# Pin for every pictured story, as a fraction of the map box:
# fx = (lon + 180) / 360, fy = (84 - lat) / 144.
PINS = {
    1: (0.556, 0.360),   # Benghazi, Libya (20.1E, 32.1N)
    2: (0.585, 0.327),   # Antalya (30.7E, 36.9N)
    3: (0.512, 0.230),   # Brussels — NATO (4.35E, 50.85N)
    4: (0.584, 0.231),   # Dymer, Kyiv region (30.3E, 50.8N)
    5: (0.161, 0.324),   # Santa Clara (122.0W, 37.4N)
    6: (0.643, 0.336),   # Tehran (51.4E, 35.7N)
    7: (0.598, 0.362),   # West Bank (35.2E, 31.9N)
    8: (0.795, 0.626),   # Cikande, Java (106.4E, 6.2S)
    9: (0.590, 0.475),   # Khartoum (32.5E, 15.6N)
    10: (0.853, 0.322),  # Seoul (127.0E, 37.6N)
    11: (0.526, 0.248),  # Brussels — EU (4.35E, 50.85N)
    12: (0.610, 0.256),  # Rostov (39.7E, 47.2N)
    13: (0.528, 0.211),  # Hamburg (10.0E, 53.6N)
    14: (0.294, 0.301),  # New York (74.0W, 40.7N)
    15: (0.500, 0.226),  # London (0.1W, 51.5N)
}

# ------------------------------------------------------------------ helpers


def wrap_to(draw, text, fnt, width):
    """Greedy word wrap; returns the list of lines that fit width."""
    words = text.split()
    lines, current = [], words[0] if words else ""
    for word in words[1:]:
        trial = current + " " + word
        if draw.textlength(trial, font=fnt) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def block(draw, x, y, text, fnt, fill, width, leading, cap=None):
    """Draw wrapped text; returns the y just below the last line."""
    lines = wrap_to(draw, text, fnt, width)
    shown = lines if cap is None else lines[:cap]
    yy = y
    for ln in shown:
        draw.text((x, yy), ln, font=fnt, fill=fill)
        yy += leading
    return yy


def middle(draw, cx, y, text, fnt, fill):
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((cx - (box[2] - box[0]) / 2 - box[0], y), text,
              font=fnt, fill=fill)


def fit(draw, x, y, text, path, size, width, fill, floor=8):
    """Draw one line, shrinking the font until it fits the width."""
    s = size
    while True:
        fnt = font(path, s)
        if draw.textlength(text, font=fnt) <= width or s <= floor:
            break
        s -= 1
    draw.text((x, y), text, font=fnt, fill=fill)


def grain(img):
    """Deterministic paper speckle: a fixed arithmetic lattice of
    slightly darkened pixels, no randomness anywhere."""
    px = img.load()
    w, h = img.size
    for yy in range(0, h, 2):
        for xx in range(0, w, 2):
            if (xx * 41 + yy * 23) % 97 < 2:
                r, g, b = px[xx, yy]
                px[xx, yy] = (max(0, r - 7), max(0, g - 7), max(0, b - 7))
    return img


def masthead(d, total_line):
    d.rectangle([EDGE, 15, EDGE + 9, 24], fill=RED)
    d.text((EDGE + 14, 11), "THE WORLD IN ONE DAY",
           font=font(SANS_BOLD, 17), fill=RED)
    rf = font(SANS, 11)
    tw = d.textlength(total_line, font=rf)
    d.text((PAGE - EDGE - tw, 16), total_line, font=rf, fill=INK)
    d.line([EDGE, 39, PAGE - EDGE, 39], fill=INK, width=1)
    d.line([EDGE, 42, PAGE - EDGE, 42], fill=INK, width=3)


def render_fallback():
    """A compact edition of the same page, kept as the safety copy."""
    img = Image.new("RGB", (PAGE, PAGE), PAPER)
    d = ImageDraw.Draw(img)
    masthead(d, f"{STORY_COUNT} STORIES · MONDAY 23 NOVEMBER 2026")
    middle(d, PAGE / 2, 60, DAY, font(SERIF_BOLD, 58), INK)
    block(d, EDGE, 150, DEK, font(SERIF_ITALIC, 17), RED, SPAN, 22)
    d.line([EDGE, 190, PAGE - EDGE, 190], fill=INK, width=1)
    y = 210
    for hero in HEROES:
        d.text((EDGE, y), f"{hero['num']}  {hero['tag']}",
               font=font(SANS_BOLD, 12), fill=RED)
        y = block(d, EDGE, y + 20, hero["head"], font(SERIF_BOLD, 30),
                  INK, SPAN, 34, cap=1)
        y = block(d, EDGE, y + 4, hero["summ"], font(SERIF, 15), INK,
                  SPAN, 20, cap=2)
        y += 26
    d.line([EDGE, y, PAGE - EDGE, y], fill=INK, width=1)
    cell = SPAN / 6
    for i, (fig, cap) in enumerate(NUMBERS):
        cx = EDGE + cell * i + cell / 2
        middle(d, cx, y + 14, fig, font(SERIF_BOLD, 28), INK)
        for j, ln in enumerate(wrap_to(d, cap, font(SANS, 10),
                                       cell - 14)):
            middle(d, cx, y + 48 + j * 11, ln, font(SANS, 10), FAINT)
    d.text((EDGE, PAGE - 40),
           "Compact edition — the full front page is entry.png.",
           font=font(SANS, 10), fill=FAINT)
    return grain(img)


def build():
    here = os.path.dirname(os.path.abspath(__file__))
    fallback = os.path.join(here, "fallback.png")
    render_fallback().save(fallback, format="PNG", optimize=True)
    return fallback


if __name__ == "__main__":
    path = build()
    print(path, os.path.getsize(path))
