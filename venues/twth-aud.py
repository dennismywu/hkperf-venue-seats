#!/usr/bin/env python3
"""Tsuen Wan Town Hall, Auditorium: seat facts read from the LCSD seating plan.

The plan PDF wraps a single scanned image (2061x2568, stored upside down and flipped upright by the
page), with text only in the totals box. tools/seatplan.py found the seat boxes on a render of the
page and read their numbers; every block end, row label and mark below was then checked by eye against
zoomed crops (sha256 in source). Writes data/twth-aud.json; fails if the counts do not match the
printed totals.

Usage: python venues/twth-aud.py
"""
from common import CREDIT, LCSD, aisle_banks, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/twth-aud-lfe.pdf",
    "title": "Tsuen Wan Town Hall – Auditorium, FULL Technical Information",
    "document_version": "V. 2026.09.08",
    "sha256": "ddbe4325e279dba15438841240f1d722526ddcc6471512d03154902c5710efb3",
    "retrieved": "2026-09-27",
}
X = lambda *ids: {i: "X" for i in ids}
W = lambda *ids: {i: "W" for i in ids}
R = lambda *ids: {i: "R" for i in ids}


def three(lab, a, b, c, **kw):
    """Left block 1-a, centre a+1-b, right b+1-c (seat 1 at the left)."""
    return row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c), **kw)


# ---- Stalls (大堂前座): three blocks, numbered on from seat 1 at the left; no row I
stalls = [three(lab, *ends) for lab, ends in [
    ("A", (10, 24, 34)), ("B", (10, 23, 33)), ("C", (12, 27, 39)), ("D", (13, 27, 40)), ("E", (13, 28, 41)),
    ("F", (13, 27, 40)), ("G", (13, 28, 41)), ("H", (11, 25, 36)), ("J", (12, 27, 39)), ("K", (13, 27, 40)),
    ("L", (13, 28, 41)), ("M", (13, 27, 40)), ("N", (13, 28, 41)), ("O", (12, 26, 38)), ("P", (11, 26, 37)),
]]

# ---- Upper Stalls (大堂後座): rows Q-S also have three seats in each side corridor (左邊走廊 / 右邊走廊),
# numbered on from the row; no row U
LEFT_CORRIDOR = "left corridor (左邊走廊)"
RIGHT_CORRIDOR = "right corridor (右邊走廊)"
upper = [
    row("Q", {"seats": rng(1, 3), "area": LEFT_CORRIDOR}, rng(4, 9) + ["X1", "X2"], rng(12, 25), rng(26, 33),
        {"seats": rng(34, 36), "area": RIGHT_CORRIDOR}, marks=X("X1", "X2"), inferred={"X1": "10", "X2": "11"},
        note="Two crossed management boxes end the left block after 9; the centre block starts at 12, so they fill 10-11 exactly. "
             "Seats 1-3 and 34-36 are in the side corridors."),
    row("R", {"seats": rng(1, 3), "area": LEFT_CORRIDOR}, rng(4, 11), rng(12, 26), rng(27, 34),
        {"seats": rng(35, 37), "area": RIGHT_CORRIDOR}, note="Seats 1-3 and 35-37 are in the side corridors."),
    row("S", {"seats": rng(1, 3), "area": LEFT_CORRIDOR}, rng(4, 11), rng(12, 25), rng(26, 33),
        {"seats": rng(34, 36), "area": RIGHT_CORRIDOR}, note="Seats 1-3 and 34-36 are in the side corridors."),
]
upper += [three(lab, *ends) for lab, ends in [
    ("T", (9, 24, 33)), ("V", (9, 23, 32)), ("W", (9, 24, 33)), ("X", (9, 23, 32)), ("Y", (9, 24, 33)),
    ("Z", (9, 23, 32)), ("ZA", (9, 24, 33)), ("ZB", (9, 23, 32)), ("ZC", (10, 25, 35)), ("ZD", (10, 24, 34)),
]]
upper.append(row(
    "ZE", ["W1", "W2"] + rng(3, 8) + ["X1", "X2"], ["W3", "W4"] + rng(13, 23) + ["W5", "W6"], ["W7", "W8"] + rng(28, 33) + ["W9", "W10"],
    marks={**W(*[f"W{i}" for i in range(1, 11)]), **X("X1", "X2")},
    inferred={"W1": "1", "W2": "2", "X1": "9", "X2": "10", "W3": "11", "W4": "12", "W5": "24", "W6": "25", "W7": "26", "W8": "27"},
    note="Ten wheelchair boxes (W, no number) and two crossed management boxes. W W open the row before 3 (1-2); after 8, "
         "X X then the centre block's W W fill 9-12 before 13; after 23, the centre's W W and the right block's W W fill "
         "24-27 before 28. The last two W, after 33, are likely 34-35 (not printed)."))

# ---- Balcony (樓座): rows BA-BC have a centre in two runs; bold boxes are restricted sightlines
balcony = [
    row("BA", rng(1, 6), rng(7, 11), rng(12, 16), rng(17, 22)),
    row("BB", rng(1, 6), rng(7, 11), rng(12, 16), rng(17, 22), marks=R("6", "17")),
    row("BC", rng(1, 7), rng(8, 12), rng(13, 17), rng(18, 24), marks=R("7", "18")),
]
balcony += [three(lab, *ends) for lab, ends in [
    ("BD", (9, 23, 32)), ("BE", (9, 24, 33)), ("BF", (9, 23, 32)), ("BG", (9, 24, 33)), ("BH", (9, 23, 32)),
    ("BJ", (9, 24, 33)), ("BK", (7, 21, 28)), ("BL", (7, 22, 29)), ("BM", (7, 19, 26)), ("BN", (7, 18, 25)),
]]

# ---- banks: the side corridors' seats against the walls, level with row Q
UP = "Upper Stalls"
BANKS = aisle_banks(("stalls", stalls), ("upper", [r for r in upper if len(r["blocks"]) == 3], UP), ("balcony", balcony))
for b in BANKS:
    if b["id"].startswith("upper-"):
        k = {"upper-centre": 3, "upper-left": 2, "upper-right": 4}[b["id"]]
        b["rows"] = [{"zone": UP, "row": lab, "block": k} for lab in "QRS"] + b["rows"]
BANKS += [
    {"id": "corridor-left", "side": "left", "rows_run": "across", "seat_1": "left", "level_with": {"zone": UP, "row": "Q"},
     "rows": [{"zone": UP, "row": lab, "block": 1} for lab in "QRS"], "label": "Left corridor"},
    {"id": "corridor-right", "side": "right", "rows_run": "across", "seat_1": "left", "level_with": {"zone": UP, "row": "Q"},
     "rows": [{"zone": UP, "row": lab, "block": 5} for lab in "QRS"], "label": "Right corridor"},
]

finish({
    "venue": {"id": "twth-aud", "name_en": "Tsuen Wan Town Hall Auditorium", "name_zh": "荃灣大會堂 演奏廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/twth/attachments/auditorium/aud_seating_plan.pdf",
        "file": "aud_seating_plan.pdf",
        "sha256": "43a11c41d12518eda1824a1fcb3f5ee1cb018718564ee9c1efc14959134a0b1d",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat totals, wheelchair seats and orchestra pit",
        **TECH_SHEET,
        "quotes": ["Total Seating: 1420 Stalls: 1049 (including 10 wheelchair seats) Balcony: 371",
                   "67 seats will be lost from Stalls Level Row A & Row B for setting orchestra pit."],
        "note": "Confirms the plan's totals: the sheet's Stalls (1049) is the plan's Stalls (580) and Upper Stalls (469) together, "
                "and its 10 wheelchair seats are the ten W boxes of row ZE. Names the rows the pit removes.",
    }],
    "location": location(geo_id="87210045", geo_name="Tsuen Wan Town Hall (Auditorium)", lat=22.37109, lon=114.11277,
                         address_en="72 Tai Ho Road, Tsuen Wan, New Territories, Hong Kong",
                         address_zh="香港新界荃灣大河道72號", district="Tsuen Wan", address_name="Tsuen Wan Town Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and numbering runs on through "
                "the blocks. No row I in the stalls; no row U in the upper stalls. Rows Q-S of the upper stalls also have "
                "three seats in each side corridor (左邊走廊, 右邊走廊). Balcony rows BA-BC have a centre in two runs. "
                "The plan also marks a left and right box (左包廂, 右包廂) and promenade boxes on the stalls' side walls, "
                "with no seats drawn in them; circles along the side walls are not seats. The plan prints no date.",
        "banks": BANKS,
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
        "R": "Seat with restricted sightline (heavy outline)",
    },
    "printed_totals": {"Stalls": 580, "Upper Stalls": 469, "Balcony": 371, "Total": 1420},
    "orchestra_pits": [{
        "name": "Orchestra pit (62 m²)",
        "rows_removed": ["A", "B"],
        "rows_basis": "stated",
        "rows_reasoning": "The technical sheet names the rows. A + B = 34 + 33 = 67, matching the stated loss.",
        "stated": {"seats_removed": 67},
        "source": {**TECH_SHEET, "quote": "67 seats will be lost from Stalls Level Row A & Row B for setting orchestra pit."},
    }],
    "zones": [
        {"name": "Stalls", "name_zh": "大堂前座", "rows": stalls},
        {"name": "Upper Stalls", "name_zh": "大堂後座", "rows": upper},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
