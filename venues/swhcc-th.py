#!/usr/bin/env python3
"""Sai Wan Ho Civic Centre, Theatre: seat facts read from the LCSD seating plan.

The plan PDF carries a text layer for every seat number and W; the row labels are drawn as outlines,
not text. The centre block of each row was read from the tokens on its line. The side blocks are
drawn at an angle, so their seats were chained by position (n to n+1, nearest box) and each chain
matched to the row whose centre block its aisle end meets. Crossed management boxes were read by eye
from zoomed renders (sha256 in source). Writes data/swhcc-th.json; fails if the count does not match.

Usage: python venues/swhcc-th.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

# left block, centre block, right block (seat 1 at the left); None where the plan has no block
ends = {
    "B": (4, 18, 22), "C": (5, 19, 24), "D": (5, 19, 24), "E": (6, 20, 26),
    "F": (7, 21, 28), "G": (7, 21, 28), "H": (7, 21, 28),
    "J": (8, 22, 30), "K": (8, 22, 30), "L": (8, 22, 30), "M": (8, 22, 30),
    "O": (7, 21, 28), "P": (6, 20, 26),
}
rows = [row("A", rng(1, 2), ["W1", "W2"] + rng(5, 10) + ["W3", "W4"], rng(13, 14),
            marks={w: "W" for w in ["W1", "W2", "W3", "W4"]},
            inferred={"W1": "3", "W2": "4", "W3": "11", "W4": "12"},
            note="Four wheelchair boxes print W, no number: two between 2 and 5, two between 10 and 13, so they fill 3-4 and 11-12 exactly, as the technical sheet lists them.")]
for lab in "BCDEFGHJKLM":
    a, b, c = ends[lab]
    rows.append(row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c)))
rows.append(row("N", rng(1, 8), rng(9, 20) + ["X1", "X2"], rng(23, 30), marks={"X1": "X", "X2": "X"},
                inferred={"X1": "21", "X2": "22"},
                note="Two crossed management boxes, no number, end the centre block after 20; the right block starts at 23, so they fill 21-22 exactly."))
for lab in "OP":
    a, b, c = ends[lab]
    rows.append(row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c)))
rows += [
    row("Q", rng(1, 7), rng(8, 21), note="No right block: the wall comes in behind row P."),
    row("R", rng(1, 7), rng(8, 21), note="No right block."),
    row("S", rng(1, 5) + ["X1", "X2"], ["W1", "W2"] + rng(10, 15) + ["W3", "W4"],
        marks={"X1": "X", "X2": "X", "W1": "W", "W2": "W", "W3": "W", "W4": "W"},
        inferred={"X1": "6", "X2": "7", "W1": "8", "W2": "9", "W3": "16", "W4": "17"},
        note="The left block ends with two crossed management boxes after 5, and the centre block has two wheelchair boxes "
             "each side of 10-15, all without numbers. 6-9 fall exactly to the four boxes between 5 and 10; the technical "
             "sheet names the wheelchair seats S8, S9, S16 and S17. No right block."),
]

finish({
    "venue": {"id": "swhcc-th", "name_en": "Sai Wan Ho Civic Centre Theatre", "name_zh": "西灣河文娛中心 劇院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/swhcc/common/doc/seating-plan.pdf",
        "file": "seating-plan.pdf",
        "sha256": "d949e65c0fdb7cda2d1ee34276fc7bb25083460f31701c40803d2e1b1f6f1222",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total, wheelchair seats and orchestra pit",
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/swhcc-th-lfe.pdf",
        "title": "Sai Wan Ho Civic Centre – Theatre, FULL Technical Information",
        "document_version": "V. 2026.07.09",
        "sha256": "e0bfc213bd00ef93770adc7ba39943b169632e2c073f90e5c1c017981a493a0b",
        "retrieved": "2026-09-26",
        "quotes": ["Total Seating: 453", "Wheelchair Seat Row A: A3, A4, A11 & A12 Row S: S8, S9, S16 & S17",
                   "FORESTAGE / ORCHESTRA PIT Not available"],
        "note": "Confirms the plan's total and the numbers of the eight wheelchair boxes. There is no orchestra pit.",
    }],
    "location": location(geo_id="87710034", geo_name="Sai Wan Ho Civic Centre (Theatre)", lat=22.2818, lon=114.222501,
                         address_en="111 Shau Kei Wan Road, Hong Kong", address_zh="香港筲箕灣道111號",
                         district="Eastern", address_name="Sai Wan Ho Civic Centre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side. The side blocks are angled towards the stage; rows Q-S have no right block, where the wall steps in. No row I. The plan names no seating areas, only the space (劇院 THEATRE), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Theatre": 453, "Total": 453},
    "zones": [
        {"name": "Theatre", "name_zh": "劇院", "rows": rows},
    ],
})
