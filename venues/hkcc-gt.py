#!/usr/bin/env python3
"""Hong Kong Cultural Centre, Grand Theatre: seat facts read from the LCSD seating plan.

The current plan is a one-page vector PDF (August 2025) whose seat numbers are drawn as outlines, not
text; the earlier 2018 plan (a 4961x5905 GIF) has the same seats. tools/seatplan.py found the boxes
on the GIF; every block end, row label and mark below was then read by eye from zoomed renders of both
(sha256 in source). Rows whose side blocks slope were matched to their labels by where each block's
aisle end sits, checked against rows whose assignment the row count fixes.

The plan prints no seat totals, so the figures checked are LCSD's technical sheet, which gives tiers
(Stalls 788, Circle 425, Upper Circle 495, Box 26) rather than the plan's area names; see the notes.
Writes data/hkcc-gt.json; fails if the counts do not match.

Usage: python venues/hkcc-gt.py
"""
from common import CREDIT, LCSD, aisle_banks, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/hkcc-gt-lfe.pdf",
    "title": "Hong Kong Cultural Centre – Grand Theatre, FULL Technical Information",
    "document_version": "V. 2025.05.29",
    "sha256": "e6f5added74b486058efcec542f418a12377509c5216ba43368fdc635c4be718",
    "retrieved": "2026-09-26",
}
X = lambda *ids: {i: "X" for i in ids}
W = lambda *ids: {i: "W" for i in ids}
L = lambda *ids: {i: "L" for i in ids}


def three(lab, a, b, c, left_from=1, centre_from=12, right_from=36, **kw):
    """Left, centre and right blocks, each with its own number range (seat 1 at the left)."""
    blocks = [rng(left_from, a)] if a else []
    blocks.append(rng(centre_from, b))
    if c:
        blocks.append(rng(right_from, c))
    return row(lab, *blocks, **kw)


# ---- Stalls 1 (the plan's 堂座1): left 1-, centre 12-, right 36-; rows K and V have only a centre block
stalls1 = [three(lab, a, b, c) for lab, a, b, c in [
    ("A", 3, 23, 38), ("B", 4, 24, 39), ("C", 4, 25, 39), ("D", 5, 26, 40), ("E", 5, 27, 40), ("F", 6, 28, 41),
    ("G", 6, 29, 41), ("H", 7, 30, 42), ("I", 7, 31, 42), ("J", 8, 32, 43),
]]
stalls1.append(row("K", rng(12, 33), note="Centre block only: the side blocks break for a cross-aisle."))
stalls1.append(row("L", rng(1, 8) + ["X1", "X2"], rng(12, 35), rng(36, 45), marks=X("X1", "X2"),
                   note="The left block ends with two crossed management boxes after 8 (9-10 likely, not printed)."))
stalls1 += [three(lab, a, 35, c) for lab, a, c in [
    ("M", 11, 46), ("N", 11, 46), ("O", 10, 45), ("P", 9, 44), ("Q", 8, 43), ("R", 7, 42), ("S", 6, 41), ("T", 5, 40), ("U", 3, 38),
]]
stalls1.append(row("V", rng(12, 35), note="Centre block only: the side blocks break for a cross-aisle."))
stalls1 += [row(lab, rng(12, 35)) for lab in "WX"]
stalls1.append(row("Y", rng(12, 32) + ["X1", "X2"], marks=X("X1", "X2"),
                   note="Two crossed management boxes end the row after 32 (33-34 likely, not printed)."))

# ---- Stalls 2 (the plan's 堂座2, Level 2; LCSD's sheet calls this tier Circle): rows A-D at the sides only
stalls2 = [
    row("A", rng(1, 2), rng(34, 35),
        note="34-35 are boxed and labelled 輪椅席 Wheel-Chaired Patrons Seats on the plan; they print numbers, not W."),
    row("B", rng(1, 4), rng(34, 36), marks=L("4")),
    row("C", rng(1, 5), rng(34, 37)),
    row("D", rng(1, 6), rng(34, 38)),
    row("E", rng(1, 11), rng(12, 33), ["X1", "X2"] + rng(36, 44), marks={**L("8", "37", "38"), **X("X1", "X2")},
        inferred={"X1": "34", "X2": "35"},
        note="Two crossed management boxes open the right block, between the centre block's 33 and 36, so they are 34-35."),
]
stalls2 += [three(lab, 11, 33, 44, right_from=34) for lab in "FGHIJK"]
stalls2 += [
    row("L", rng(1, 11), rng(12, 33), rng(34, 42) + ["W1", "W2"], marks=W("W1", "W2"),
        note="Two wheelchair boxes, W with no number, end the right block after 42 (43-44 likely, not printed)."),
    row("M", ["W1", "W2"] + rng(3, 11), rng(12, 33), rng(34, 42), marks=W("W1", "W2"), inferred={"W1": "1", "W2": "2"},
        note="Two wheelchair boxes, W with no number, open the row before 3, so they are 1-2. The right block ends at 42."),
]

# ---- Level 3 wall rows (the plan's 樓座 Circle) and Level 4 (高座 Upper Circle): one tier on LCSD's sheet
upper = [row(lab, rng(1, a), rng(48, c)) for lab, a, c in [("B", 4, 51), ("C", 3, 50), ("D", 3, 50), ("E", 3, 50)]]
for r in upper:
    r["note"] = "Short rows on the side walls at Level 3 (the plan's 樓座 Circle), numbered 1- on the left and 48- on the right."
upper += [
    row("F", ["W1", "W2", "3"], rng(4, 10), rng(12, 35), rng(41, 47), ["48", "W3", "W4"],
        marks=W("W1", "W2", "W3", "W4"), inferred={"W1": "1", "W2": "2"},
        note="Runs from the left wall (W W 3, the wheelchair boxes before 3 so 1-2) through the Upper Circle to the right "
             "wall (48 then two wheelchair boxes, 49-50 likely, not printed)."),
    three("G", 9, 36, 46, left_from=4, right_from=41),
    three("H", 9, 37, 46, left_from=4, right_from=41),
    row("I", rng(12, 34), note="Centre block only: the side blocks break for a cross-aisle."),
    three("J", 10, 35, 50, right_from=41),
    three("K", 10, 36, 50, right_from=41),
    row("L", ["X1"] + rng(2, 11), rng(12, 37), rng(41, 50) + ["X2"], marks=X("X1", "X2"), inferred={"X1": "1"},
        note="Crossed management boxes at both ends: before 2 on the left (so 1) and after 50 on the right (51 likely, not printed)."),
    three("M", 11, 38, 51, right_from=41),
    three("N", 10, 39, 50, right_from=41),
    three("O", 10, 40, 49, right_from=41),
    three("P", 9, 40, 49, right_from=41),
]

# ---- V.I.P. boxes (貴賓廂座)
boxes = [
    row("Box 1", rng(1, 4), note="V.I.P. Box 1, on the right wall at the back of Stalls 1."),
    row("Box 2", rng(1, 4), note="V.I.P. Box 2, on the left wall at the back of Stalls 1."),
    row("Box 3 A", rng(11, 14), rng(48, 52), note="V.I.P. Box 3, on the right wall at Level 3; the plan labels its row A. Two runs: 11-14 and 48-52."),
    row("Box 4 A", rng(1, 5), rng(11, 14), note="V.I.P. Box 4, on the left wall at Level 3; the plan labels its row A. Two runs: 1-5 and 11-14."),
]

# ---- banks: where each block sits around the stage (row letters restart per level, so refs name the zone)
UP, BOX = "Circle and Upper Circle", "V.I.P. Boxes"
u = lambda lab, blk: {"zone": UP, "row": lab, "block": blk}
three_rows = [r["row"] for r in upper if len(r["blocks"]) == 3]          # G, H, J-P
BANKS = aisle_banks(("stalls1", stalls1, "Stalls 1"), ("stalls2", stalls2, "Stalls 2")) + [
    # Level 4 (and row F): centre, with its side blocks across the aisles
    {"id": "upper-centre", "side": "front", "seat_1": "left",
     "rows": [u("F", 3)] + [u(lab, 1 if lab == "I" else 2) for lab in "GHIJKLMNOP"]},
    {"id": "upper-left", "side": "left", "rows_run": "across", "seat_1": "left", "beside": "upper-centre",
     "rows": [u("F", 2)] + [u(lab, 1) for lab in three_rows]},
    {"id": "upper-right", "side": "right", "rows_run": "across", "seat_1": "left", "beside": "upper-centre",
     "rows": [u("F", 4)] + [u(lab, 3) for lab in three_rows]},
    # Level 3: V.I.P. Boxes 3-4 and the wall rows B-E on the side walls, down to the wall seats of row F
    {"id": "wall-left", "side": "left", "rows_run": "across", "seat_1": "left", "after": "stalls2-centre",
     "rows": [{"zone": BOX, "row": "Box 4 A"}] + [u(lab, 1) for lab in "BCDEF"]},
    {"id": "wall-right", "side": "right", "rows_run": "across", "seat_1": "left", "after": "stalls2-centre",
     "rows": [{"zone": BOX, "row": "Box 3 A"}] + [u(lab, 2) for lab in "BCDE"] + [u("F", 5)]},
    # V.I.P. Boxes 1-2: upright on the side walls beside the back of Stalls 1
    {"id": "box-2", "side": "left", "rows": [{"zone": BOX, "row": "Box 2"}], "seat_1": "upstage",
     "level_with": {"zone": "Stalls 1", "row": "V"}},
    {"id": "box-1", "side": "right", "rows": [{"zone": BOX, "row": "Box 1"}], "seat_1": "downstage",
     "level_with": {"zone": "Stalls 1", "row": "V"}},
]

finish({
    "venue": {"id": "hkcc-gt", "name_en": "Hong Kong Cultural Centre Grand Theatre", "name_zh": "香港文化中心 大劇院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/hkcc/common/images/facilities/grandtheatre/HKCC_GT_Seating%20Plan_28082025.pdf",
        "page": "https://www.lcsd.gov.hk/en/hkcc/facilities/grandtheatre.html",
        "file": "HKCC_GT_Seating Plan_28082025.pdf",
        "sha256": "0a4172b5022c61307e7dd110863e9b3d1dca80b8dd7b12695742d33aced4a592",
        "plan_code": "HKCC_GT_Seating Plan_18082025",
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [
        {
            "what": "Seat totals by tier, and the orchestra pit",
            **TECH_SHEET,
            "quotes": ["Total Seating: 1734 Stalls: 788 Circle: 425 Upper Circle: 495 Box: 26",
                       "Small Pit Lift (seats): 53 Large Pit Lift (seats): 102"],
            "note": "The plan prints no totals, so these are the figures checked. The sheet's tiers match the plan's areas by count: "
                    "Stalls = Stalls 1; Circle = the plan's Stalls 2 (Level 2); Upper Circle = the Level 3 wall rows and Level 4; "
                    "Box = V.I.P. Boxes 1-4. The sheet gives the seats each pit removes but not the rows, and no run of front rows "
                    "gives 53 or 102, so no pit option is recorded.",
        },
        {
            "what": "The earlier plan",
            "publisher": LCSD,
            "url": "https://www.lcsd.gov.hk/en/hkcc/common/images/facilities/grandtheatre/grand_theatre_s.gif",
            "title": "Grand Theatre Seating Plan (applicable to events after 1 Nov 2018)",
            "sha256": "131666513a8ae4dcc66c222261147b28bcf5c8baceaf74a2af0f5ee5cf45768b",
            "retrieved": "2026-09-26",
            "note": "Same seats as the 2025 plan, which adds the limited-legroom marks (Stalls 2 B4, E8, E37, E38). No longer linked from the facility page.",
        },
    ],
    "location": location(geo_id="50110015", geo_name="Hong Kong Cultural Centre (Grand Theatre)", lat=22.29386, lon=114.17053,
                         address_en="10 Salisbury Road, Tsim Sha Tsui, Kowloon, Hong Kong",
                         address_zh="香港九龍尖沙咀梳士巴利道十號", district="Yau Tsim Mong", address_name="Hong Kong Cultural Centre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row. Blocks keep fixed number ranges, so numbers skip between them (Stalls 1: 1-, 12-, 36-; Stalls 2: 1-, 12-, 34-; Upper Circle: 1- or 4-, 12-, 41-, and 48- on the walls). Row letters restart on each level. Parts of house follow the plan's names; LCSD's technical sheet calls Stalls 2 the Circle, and counts the Level 3 wall rows (the plan's 樓座 Circle) with the Upper Circle. The plan prints the row labels in the aisles; Stalls 2 rows A-D are side blocks only, above row E.",
        "banks": BANKS,
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
        "L": "Limited legroom (grey box)",
    },
    "totals_source": "LCSD's technical sheet (V. 2025.05.29); the seating plan prints no totals",
    "printed_totals": {"Stalls 1": 788, "Stalls 2": 425, "Circle and Upper Circle": 495, "V.I.P. Boxes": 26, "Total": 1734},
    "zones": [
        {"name": "Stalls 1", "name_zh": "堂座1", "rows": stalls1},
        {"name": "Stalls 2", "name_zh": "堂座2", "rows": stalls2,
         "count_includes": ["X"],
         "count_note": "LCSD's figure for this tier (Circle 425) equals every box on the plan, including the two management "
                       "seats E34-E35; the other tiers leave their management seats out. Recorded as LCSD gives it."},
        {"name": "Circle and Upper Circle", "name_zh": "樓座及高座", "rows": upper,
         "sections": [{"name": "Circle (Level 3), wall rows", "name_zh": "樓座（三樓）", "rows": ["B", "E"]},
                      {"name": "Upper Circle (Level 4)", "name_zh": "高座（四樓）", "rows": ["F", "P"]}]},
        {"name": "V.I.P. Boxes", "name_zh": "貴賓廂座", "rows": boxes},
    ],
})
