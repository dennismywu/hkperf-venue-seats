#!/usr/bin/env python3
"""Ko Shan Theatre, Theatre: seat facts read from the LCSD seating plan.

The plan PDF carries a text layer: every seat number, W and row label is real text on a grid of
cells, so the rows were read by grouping the tokens on each row's line. Management boxes (grey, no
number) and sightline restrictions (yellow) come from the plan's filled rectangles, checked by eye
against zoomed renders (sha256 in source). Writes data/kst-th.json; fails if the counts do not match
the printed totals.

The plan is drawn with the stage at the bottom; rows and blocks below are as seen with the stage at
the top, so seat 1 is at the left.

Usage: python venues/kst-th.py
"""
from common import CREDIT, LCSD, aisle_banks, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/kst-th-lfe.pdf",
    "title": "Ko Shan Theatre – Theatre, FULL Technical Information",
    "document_version": "V. 2026.05.27",
    "sha256": "d27c5b1e6c9e02ba9894b8818e4d08f5bbf01356ac6201990729d85758a7192d",
    "retrieved": "2026-09-27",
}
X = lambda *ids: {i: "X" for i in ids}
W = lambda *ids: {i: "W" for i in ids}
R = lambda *ids: {i: "R" for i in ids}

# ---- Stalls (堂座): blocks keep fixed number ranges (1-12, 13-41, 42-53), so rows start or end part-way
stalls = [row(lab, rng(a, 12), rng(b, c), rng(42, e)) for lab, a, b, c, e in [
    ("A", 5, 23, 31, 49), ("B", 4, 22, 31, 50), ("C", 3, 21, 32, 51), ("D", 3, 21, 33, 51), ("E", 2, 20, 33, 52),
    ("F", 2, 20, 34, 52), ("G", 2, 19, 34, 52),
]]
stalls.append(row("H", rng(2, 12), rng(19, 35), ["X1", "X2"] + rng(44, 52), marks=X("X1", "X2"),
                  note="Two grey management boxes, no number, open the third block before 44 (42-43 likely, as every "
                       "full row's third block starts at 42; not printed)."))
stalls += [row(lab, rng(1, 12), rng(b, c), rng(42, 53)) for lab, b, c in [("J", 18, 35), ("K", 18, 36), ("L", 17, 36)]]
stalls.append(row("M", rng(1, 12), ["X1", "X2"] + rng(19, 37), rng(42, 53), marks=X("X1", "X2"),
                  note="Two grey management boxes, no number, open the centre block before 19 (17-18 likely, as in row L; not printed)."))
stalls += [row(lab, rng(1, 12), rng(b, c), rng(42, 53)) for lab, b, c in [
    ("N", 16, 37), ("P", 16, 38), ("Q", 15, 38), ("R", 15, 39), ("S", 14, 39), ("T", 14, 40), ("U", 13, 40),
    ("V", 13, 40), ("W", 13, 41),
]]
stalls.append(row(
    "X", rng(1, 6) + ["X1", "11", "12"], rng(13, 15) + ["W1", "W2"] + rng(23, 30) + ["W3", "W4", "W5", "W6"] + rng(39, 41),
    ["42", "43", "X2"] + rng(48, 53), marks={**X("X1", "X2"), **W("W1", "W2", "W3", "W4", "W5", "W6")},
    note="The back row is broken by gaps. First block: 1-6, a gap, a grey management box, 11-12. Centre: 13-15, two "
         "wheelchair boxes (W), a gap, 23-30, W W, a gap, W W, 39-41. Third block: 42-43, a management box, a gap, 48-53. "
         "No box has a number that fits exactly; by the columns of row W they stand where 10, 16-17, 31-32, 37-38 and 44 are."))

# ---- Balcony (樓座): row AA is marked for restricted sightlines throughout
balcony = [
    row("AA", rng(1, 10) + ["X1"], rng(12, 24), ["X2"] + rng(26, 35), marks={**R(*rng(1, 10), *rng(12, 24), *rng(26, 35)), **X("X1", "X2")},
        inferred={"X1": "11", "X2": "25"},
        note="Every numbered seat is yellow (restricted sightline). A grey management box ends the first block after 10 "
             "and another opens the third before 26; the numbers either side (12, 24) make them 11 and 25 exactly."),
    row("BB", rng(1, 8), rng(12, 23), rng(28, 35)),
    row("CC", rng(1, 8), rng(12, 23), rng(28, 35)),
    row("DD", rng(3, 9), ["X1"] + rng(12, 23) + ["X2"], rng(27, 33), marks=X("X1", "X2"),
        note="Grey management boxes, no number, at both ends of the centre block: before 12 (after 9, so 10 or 11) and "
             "after 23 (before 27, so 24-26). Neither fits exactly."),
]

finish({
    "venue": {"id": "kst-th", "name_en": "Ko Shan Theatre (Theatre)", "name_zh": "高山劇場 劇院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/kst/common/forms/KST%20Theatre%20seating%20plan.pdf",
        "file": "KST Theatre seating plan.pdf",
        "sha256": "4146b62e71a20bd7f4960b11c5f73cd8dbd0021350420abf4cb5a384d8afe4c4",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat totals and orchestra pit",
        **TECH_SHEET,
        "quotes": ["Total Seating: 1031 Stalls: 916 Balcony: 115",
                   "Formed by removing trap and lowering centre lift, maximum for 12 persons"],
        "note": "Confirms the plan's totals, which leave out the six wheelchair spaces (the plan adds them separately). "
                "The pit is formed from a trap and the centre lift, so no seats are lost to it.",
    }],
    "location": location(geo_id="87610118", geo_name="Ko Shan Theatre (Theatre)", lat=22.31368, lon=114.18556,
                         address_en="77 Ko Shan Road, Hung Hom, Kowloon, Hong Kong",
                         address_zh="香港九龍紅磡高山道77號", district="Kowloon City", address_name="Ko Shan Theatre"),
    "layout": {
        "seat_1_side": "left",
        "note": "The plan is drawn with the stage at the bottom and seat 1 at the right-hand end of each row as drawn, "
                "which is the left-hand end with the stage at the top. Blocks keep fixed number ranges (stalls 1-12, "
                "13-41, 42-53; balcony about 1-10, 12-24, 26-35), so rows start or end part-way and numbers skip "
                "between blocks. No rows I and O. The plan prints no date.",
        "banks": aisle_banks(("stalls", stalls), ("balcony", balcony)),
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (grey box, no number)",
        "R": "Seat with sightline restrictions (yellow box)",
    },
    "printed_totals": {"Stalls": 916, "Balcony": 115, "Total": 1031},
    "zones": [
        {"name": "Stalls", "name_zh": "堂座", "rows": stalls,
         "count_excludes": ["W"],
         "count_note": "The plan's figures leave out the six wheelchair spaces: beside the total it prints \"(另加 輪椅座位數目 "
                       "add Number of wheel-chair seats: 6)\". LCSD's technical sheet gives the same 916 and 1031."},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
