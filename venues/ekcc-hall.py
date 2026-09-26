#!/usr/bin/env python3
"""East Kowloon Cultural Centre, The Hall: seat facts read from the published seating plan.

The plan PDF carries a text layer: every seat number and W is real text (1,200 tokens, one printed
as "3233" without a space). The tokens were chained into blocks by position; row labels, crossed
management boxes, grey limited-legroom fills and double outlines were then checked by eye against
zoomed renders (sha256 in source). Writes data/ekcc-hall.json; fails if the counts do not match.

Usage: python venues/ekcc-hall.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-hall/index/TechInfo/ekcc-ha-lfe.pdf",
    "title": "East Kowloon Cultural Centre – The Hall, FULL Technical Information",
    "document_version": "V. 2026.07.20",
    "sha256": "862d581404e7490840ebea89ccaf17c78cc681b0486b69b3d308a1b673c81d66",
    "retrieved": "2026-09-26",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}

front = [row(lab, rng(1, n)) for lab, n in dict(A=19, B=26, C=29, D=30, E=33).items()]

rear = [
    row("F", rng(12, 31)),
    row("G", ["W1", "W2", "W3", "W4"], rng(12, 30), rng(39, 44), marks=W("W1", "W2", "W3", "W4"),
        note="Four wheelchair boxes print W, no number, in place of the left block."),
    row("H", rng(1, 8), rng(12, 29), rng(39, 46)),
    row("J", rng(1, 9), rng(12, 28), rng(39, 47)),
    row("K", rng(1, 9), rng(12, 27), rng(39, 47)),
    row("L", rng(1, 10), rng(12, 28), rng(39, 48)),
    row("M", rng(1, 10), rng(12, 27), rng(39, 48)),
    row("N", rng(1, 9), rng(39, 47), note="No centre block: the plan prints 'Rear Stalls' there."),
    row("O", rng(1, 4) + ["X1", "X2"], rng(12, 29), rng(39, 44), marks=X("X1", "X2"),
        note="Two crossed management boxes, no number, follow seat 4 (5-6 likely, not printed)."),
    row("P", rng(12, 29)),
    row("Q", rng(12, 30)),
    row("R", rng(1, 10), rng(12, 31), rng(39, 48), marks={"10": "L", "39": "L"},
        note="The side blocks of rows R-W curve round the walls, labelled at their outer ends."),
    row("S", rng(1, 11), rng(12, 33), rng(39, 49)),
    row("T", rng(1, 11), rng(12, 34), rng(39, 49)),
    row("U", rng(1, 10), rng(12, 35), rng(39, 48)),
    row("V", rng(1, 7), rng(12, 36), rng(39, 45)),
    row("W", rng(1, 4), rng(12, 35) + ["X1", "X2"], rng(39, 42), marks=X("X1", "X2"),
        note="Two crossed management boxes, no number, follow seat 35 (36-37 likely, not printed)."),
    row("X", ["W1", "W2"] + rng(14, 36) + ["W3", "W4"], marks=W("W1", "W2", "W3", "W4"),
        note="Wheelchair boxes print W, no number: two before 14 (12-13 likely) and two after 36 (37-38 likely); not printed."),
]

balcony = [
    row("BA", rng(1, 4), rng(51, 54), marks={**{s: "R" for s in rng(1, 3) + rng(52, 54)}, "4": "RL", "51": "RL"},
        note="Side boxes on the walls. All four seats each side have the restricted-sightline outline; 4 and 51 are also grey (limited legroom)."),
    row("BB", rng(1, 3), rng(52, 54), marks={"3": "L", "52": "L"}, note="Side boxes on the walls."),
    row("BC", rng(1, 5), rng(50, 54), note="Side boxes on the walls."),
    row("BD", rng(1, 13), rng(14, 37), rng(42, 54)),
    row("BE", rng(1, 13), rng(14, 37), rng(42, 54)),
    row("BF", rng(1, 2), rng(6, 13), rng(14, 38), rng(42, 49), rng(53, 54),
        marks={s: "R" for s in ["1", "2", "53", "54"]},
        note="1-2 and 53-54 are small side boxes with the restricted-sightline outline."),
    row("BG", rng(6, 13), rng(14, 39), rng(42, 49)),
    row("BH", rng(6, 13), rng(14, 40), rng(42, 49)),
    row("BJ", ["X1", "X2"] + rng(16, 41), marks=X("X1", "X2"),
        note="Two crossed management boxes, no number, before seat 16 (14-15 likely, not printed)."),
    row("BK", rng(1, 22), rng(23, 44)),
    row("BL", rng(1, 22), rng(23, 44)),
    row("BM", rng(1, 21), rng(23, 43)),
    row("BN", rng(1, 20), rng(23, 42)),
    row("BO", rng(1, 17), rng(23, 39)),
]

doc = finish({
    "venue": {"id": "ekcc-hall", "name_en": "East Kowloon Cultural Centre, The Hall", "name_zh": "東九文化中心 劇院"},
    "source": {
        "publisher": LCSD + ", East Kowloon Cultural Centre",
        "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-hall/index/SeatsPlan-T1.pdf",
        "page": "https://www.ekcc.hk/en/hiring/the-hall/",
        "file": "SeatsPlan-T1.pdf",
        "sha256": "ba2eed03e7ee28610d9e0c427c0f40d14d7b9ca8552a22dfb77328ede616c59c",
        "plan_code": "ver. 202509",
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat totals and wheelchair seats",
        **TECH_SHEET,
        "quotes": ["Total Seating 1200", "Stalls 716", "Balcony 484", "Wheelchair Seats in Stalls 8"],
        "note": "Confirms the plan's totals and the 8 wheelchair boxes in rows G and X.",
    }],
    "location": location(geo_id="826817417", geo_name="East Kowloon Cultural Centre (The Hall)", lat=22.32427, lon=114.21494,
                         address_en="60 Ngau Tau Kok Road, Kowloon, Hong Kong", address_zh=None, district=None,
                         address_source={**TECH_SHEET, "quote": "East Kowloon Cultural Centre, 60 Ngau Tau Kok Road, Kowloon, HK",
                                         "note": "Not in LCSD's venue.json; address as printed on the technical sheet."}),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side. The stalls print two areas, Front Stalls (A-E) and Rear Stalls (F-X). Numbering skips where blocks are apart (e.g. 11 and 32-38 in rows R-W; 38-41 in BD-BE). No rows I, BI. Rows BA-BC are short runs of seats along the side walls, between the stalls and the balcony: 1-5 on the left wall, numbered from the front; 50-54 on the right wall, numbered towards the front.",
        "banks": [
            {"id": "stalls", "side": "front", "rows": [r["row"] for r in front + rear], "seat_1": "left"},
            {"id": "wall-left", "side": "left", "rows": [{"row": lab, "block": 1} for lab in ["BA", "BB", "BC"]],
             "in_line": True, "seat_1": "upstage", "after": "stalls"},
            {"id": "wall-right", "side": "right", "rows": [{"row": lab, "block": 2} for lab in ["BA", "BB", "BC"]],
             "in_line": True, "seat_1": "downstage", "after": "stalls"},
            {"id": "balcony", "side": "front", "rows": [r["row"] for r in balcony if r["row"] not in ("BA", "BB", "BC")], "seat_1": "left"},
        ],
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
        "R": "Seat with restricted sightline (double outline)",
        "L": "Limited legroom (grey box)",
    },
    "printed_totals": {"Stalls": 716, "Balcony": 484, "Total": 1200},
    "orchestra_pits": [
        {
            "name": "Small pit (60 m²)",
            "rows_removed": ["A", "B", "C"],
            "rows_basis": "inferred",
            "rows_reasoning": "The sheet gives the seats lost, not the rows. A + B + C = 19 + 26 + 29 = 74, and no other run of front rows gives 74 (A-B = 45, A-D = 104).",
            "stated": {"seats_removed": 74},
            "source": {**TECH_SHEET, "quote": "Small curved forestage/pit lift area (with a loss of 74 seats)"},
        },
        {
            "name": "Large pit (105 m²)",
            "rows_removed": ["A", "B", "C", "D", "E"],
            "rows_basis": "inferred",
            "rows_reasoning": "The sheet gives the seats lost, not the rows. A-E = 19 + 26 + 29 + 30 + 33 = 137, the whole Front Stalls; no other run of front rows gives 137 (A-D = 104, A-F = 157).",
            "stated": {"seats_removed": 137},
            "source": {**TECH_SHEET, "quote": "Big curved forestage/pit lift area (with a loss of 137 seats)"},
        },
    ],
    "zones": [
        {"name": "Stalls", "name_zh": "堂座", "rows": front + rear,
         "sections": [{"name": "Front Stalls", "name_zh": "大堂前座", "rows": ["A", "E"]},
                      {"name": "Rear Stalls", "name_zh": "大堂後座", "rows": ["F", "X"]}]},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})

# the technical sheet's wheelchair figure
stalls_w = sum(1 for r in doc["zones"][0]["rows"] for m in r.get("marks", {}).values() if "W" in m)
assert stalls_w == 8, stalls_w
