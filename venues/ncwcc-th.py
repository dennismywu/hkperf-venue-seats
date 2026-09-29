#!/usr/bin/env python3
"""Ngau Chi Wan Civic Centre, Theatre: seat facts read from the LCSD seating plan.

The plan's seat numbers and W are real text on a grid of boxes, so the rows were read from the tokens
on each row's line; the two crossed management boxes in row S were read by eye against a zoomed render
(sha256 in source). Writes data/ncwcc-th.json; fails if the count does not match the printed total.

Usage: python venues/ncwcc-th.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/ncwcc-th-lfe.pdf",
    "title": "Ngau Chi Wan Civic Centre – Theatre, FULL Technical Information",
    "document_version": "V. 2026.01.26",
    "sha256": "e75648ce2edb9ef5b9f6a4fde9770992a931a649020abe0f1c3648c4d546e828",
    "retrieved": "2026-09-29",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}

rows = [row("A", ["W1", "W2"] + rng(3, 14) + ["W3", "W4"],
            marks=W("W1", "W2", "W3", "W4"), inferred={"W1": "1", "W2": "2", "W3": "15", "W4": "16"},
            note="A wheelchair box at each end of the row: two before 3 (so 1-2) and two after 14 (so 15-16).")]
rows.append(row("B", rng(1, 20)))
rows += [row(lab, rng(1, 22)) for lab in "CDEFGHJKLMNPQ"]
rows.append(row("R", rng(1, 20)))
rows.append(row("S", rng(1, 12) + ["X1", "X2"], marks=X("X1", "X2"), inferred={"X1": "13", "X2": "14"},
                note="Two crossed management boxes, no number, end the row after 12, so they fill 13-14 exactly."))

finish({
    "venue": {"id": "ncwcc-th", "name_en": "Ngau Chi Wan Civic Centre Theatre", "name_zh": "牛池灣文娛中心 劇院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/ncwcc/common/form/ncwcc_seating_theatre.pdf",
        "file": "ncwcc_seating_theatre.pdf",
        "sha256": "5b6f7640fe6d055d08f0735949b8cf29f85f21937913687c673bfec5aa2031a5",
        "plan_code": None,
        "printed_date": None,
        "applies": "Applicable to events with ticket sales commencing after 1 December 2018",
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total and orchestra pit",
        **TECH_SHEET,
        "quotes": ["Seating Capacity: 354", "FORESTAGE / ORCHESTRA PIT Not available"],
        "note": "Confirms the plan's total and that there is no orchestra pit, so no configuration removes seats.",
    }],
    "location": location(geo_id="87410030", geo_name="Ngau Chi Wan Civic Centre (Theatre)", lat=22.334583, lon=114.208766,
                         address_en="2/F & 3/F, Ngau Chi Wan Municipal Services Building, 11 Clear Water Bay Road, Kowloon, Hong Kong",
                         address_zh="香港九龍清水灣道11號牛池灣市政大廈2樓及3樓", district="Wong Tai Sin",
                         address_name="Ngau Chi Wan Civic Centre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, one block per row with no "
                "aisle. Rows A-S, with no row I and no row O. The plan names no areas, only the space (劇院 THEATRE), so "
                "there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audiences on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Theatre": 354, "Total": 354},
    "zones": [
        {"name": "Theatre", "name_zh": "劇院", "rows": rows},
    ],
})
