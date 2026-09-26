#!/usr/bin/env python3
"""East Kowloon Cultural Centre, The Turns: seat facts for its two published seating layouts.

The Turns is a flexible room with one seating plan per stage layout; each becomes its own seat list:
  ekcc-turns-horizontal  horizontal stage (SeatsPlan-T4_Horizontal.pdf), 160 seats
  ekcc-turns-end         end stage (SeatsPlan-T4_End.pdf), 176 seats
Both PDFs carry a text layer: every seat number and W is real text. Rows were read from the tokens,
and crossed management boxes by eye from zoomed renders (sha256 in source).
Writes data/ekcc-turns-horizontal.json and data/ekcc-turns-end.json; fails if a count does not match.

Usage: python venues/ekcc-turns.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

PUBLISHER = LCSD + ", East Kowloon Cultural Centre"
PAGE = "https://www.ekcc.hk/en/hiring/the-turns/"
TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-turns/index/TechInfo/ekcc-tu-lfe.pdf",
    "title": "East Kowloon Cultural Centre – The Turns, FULL Technical Information",
    "document_version": "V. 2026.07.20",
    "sha256": "c0f97986adec049d368335b98b5b2597fb0c00151c48b317b911ed3f756225f8",
    "retrieved": "2026-09-26",
}
REFERENCES = [{
    "what": "Seat totals for each layout and wheelchair spaces",
    **TECH_SHEET,
    "quotes": ["Total Seating End Stage 176 Horizontal End Stage 160 Wheelchair Space 4",
               "Flat Floor (no seats) Width (seating retracted) 23.30m"],
    "note": "Confirms both plans' totals and the four W boxes in each. The room can also be used as a flat floor with the seating retracted. No orchestra pit is described.",
}]
WS = ["W1", "W2", "W3", "W4"]
XS = ["X1", "X2"]
MARKS = {
    "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
    "X": "Management seat (crossed box, no number)",
}


def loc():
    return location(geo_id="826817419", geo_name="East Kowloon Cultural Centre (The Turns)", lat=22.32427, lon=114.21494,
                    address_en="60 Ngau Tau Kok Road, Kowloon, Hong Kong", address_zh=None, district=None,
                    address_source=ADDRESS_SOURCE)


ADDRESS_SOURCE = {**TECH_SHEET, "quote": "East Kowloon Cultural Centre 60 Ngau Tau Kok Road, Kowloon, HK",
                  "note": "Not in LCSD's venue.json; address as printed on the technical sheet."}


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"East Kowloon Cultural Centre, The Turns ({layout_en})",
            "name_zh": f"東九文化中心 形館（{layout_zh}）"}


def source(file, sha):
    return {"publisher": PUBLISHER, "url": f"https://www.ekcc.hk/documents/venue_detail/hiring/the-turns/index/{file}",
            "page": PAGE, "file": file, "sha256": sha, "plan_code": None, "printed_date": None, "credit": CREDIT}


# ---- horizontal stage: the plan draws the stage on the left and rows A-E as columns behind it
horizontal = [
    row("A", rng(1, 6), WS + rng(14, 27), rng(28, 33), marks={w: "W" for w in WS},
        note="Four wheelchair boxes print W, no number, between 6 and 14. They are spaced apart, so their numbers cannot be read off."),
    row("B", rng(1, 6), rng(8, 27), rng(28, 33), note="No seat 7: the end block stops at 6 and the long block starts at 8."),
    row("C", rng(1, 6), rng(8, 27), rng(28, 33), note="No seat 7."),
    row("D", rng(1, 7), XS + rng(10, 27), rng(28, 34), marks={x: "X" for x in XS}, inferred={"X1": "8", "X2": "9"},
        note="Two crossed management boxes, no number, open the long block before 10; the end block stops at 7, so they fill 8-9 exactly."),
    row("E", rng(1, 7), rng(8, 27), rng(28, 34)),
]

# ---- end stage: stage at the top, nine straight rows
end = [row("A", WS + rng(14, 27), marks={w: "W" for w in WS},
           note="Four wheelchair boxes print W, no number, before 14. They are spaced apart, so their numbers cannot be read off.")]
for lab in "BCDEFGHJ":
    if lab == "D":
        end.append(row("D", XS + rng(10, 27), marks={x: "X" for x in XS},
                       note="Two crossed management boxes, no number, before 10; they stand under 8 and 9 of rows C and E (not printed)."))
    else:
        end.append(row(lab, rng(8, 27)))


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}
    finish({
        "venue": venue("ekcc-turns-horizontal", "horizontal stage", "橫向舞台"),
        "source": source("SeatsPlan-T4_Horizontal.pdf", "1fc7b671edd5ee58bb42195387ce24d0d585087590fb662965e0106ffd60961a"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "The plan draws the stage on the left, with rows A-E as columns one behind another; the map turns it so the stage is at the top. Seat 1 is at the bottom end of each row on the plan, the audience's left, so it is at the left here. Each row has a short block at each end, angled along the walls (1-6 or 1-7, 28-33 or 28-34), and a long straight block (8-27). This is one of The Turns' seating layouts; the end-stage layout is a separate seat list.",
        },
        "printed_totals": {"The Turns": 160, "Total": 160},
        "zones": [{"name": "The Turns", "name_zh": "形館", "rows": horizontal}],
    })
    finish({
        "venue": venue("ekcc-turns-end", "end stage", "單向舞台"),
        "source": source("SeatsPlan-T4_End.pdf", "7df546423484aa445a43e1f553c5577c4a0d420f89e892bc71a1a0fbeb664721"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Drawn with the stage at the top. Nine straight rows, A-J (no row I), numbered from 8 at the left to 27 at the right; no row has seats 1-7. This is one of The Turns' seating layouts; the horizontal-stage layout is a separate seat list.",
        },
        "printed_totals": {"The Turns": 176, "Total": 176},
        "zones": [{"name": "The Turns", "name_zh": "形館", "rows": end}],
    })


build()
