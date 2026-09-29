#!/usr/bin/env python3
"""Tai Po Civic Centre, Auditorium: seat facts read from the LCSD seating plan.

The plan PDF is vector but every figure is outlined, so it carries no text: the seat boxes were taken
from the PDF's own rectangles, their rows chained by position, and each number, block end and mark read
by eye from zoomed, upright strips of the page. Writes data/tpcc-aud.json; fails if the counts do not
match the printed total.

The plan is drawn with the stage at the top. Seat 1 is at the right-hand end of each row, so blocks are
listed from that side (right block, centre, left) and the numbers rise towards the left.

Usage: python venues/tpcc-aud.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/tpcc-au-lfe.pdf",
    "title": "Tai Po Civic Centre – Auditorium, FULL Technical Information",
    "document_version": "V. 2026.09.01",
    "sha256": "f17e2289cf95207975ca0a921bf35fee609e487f33b8989ea52fd90dc1841d26",
    "retrieved": "2026-09-29",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}

# ---- The house (rows A-V, no I, no O) is one fan of three angled blocks: to the right of the centre the
# numbers 1-8, the centre 9 upwards, the left block above the centre. Row A is centre only and the back row
# V tapers at both ends. Unnumbered wheelchair (W) and management (X) boxes are named and, where the gap
# between their printed neighbours fits exactly, given the number they must carry.
rows = [row("A", ["W1", "W2"] + rng(11, 25), marks=W("W1", "W2"), inferred={"W1": "9", "W2": "10"},
            note="Centre block only; the wall comes in either side. Two wheelchair boxes print W, no number, "
                 "at the right (low) end, between nothing and 11, so they fill 9-10 exactly.")]

# (right block, centre block, left block); the centre ends the three rows that carry boxes with no number
blocks = {
    "B": (rng(4, 8), rng(9, 26), ["W1", "W2"] + rng(29, 30)),
    "C": (rng(2, 8), rng(9, 27), rng(28, 34)), "D": (rng(1, 8), rng(9, 26), rng(27, 34)),
    "E": (rng(1, 8), rng(9, 27), rng(28, 35)), "F": (rng(2, 8), rng(9, 26), rng(27, 33)),
    "G": (rng(1, 8), rng(9, 25) + ["X1", "X2"], rng(28, 35)), "H": (rng(1, 8), rng(9, 26), rng(27, 34)),
    "J": (rng(2, 8), rng(9, 27), rng(28, 34)), "K": (rng(2, 8), rng(9, 26), rng(27, 33)),
    "L": (rng(1, 8), rng(9, 27), rng(28, 35)), "M": (rng(1, 8), rng(9, 26), rng(27, 34)),
    "N": (rng(2, 8), rng(9, 27), rng(28, 34)), "P": (rng(1, 8), rng(9, 26), rng(27, 34)),
    "Q": (rng(1, 8), rng(9, 27), rng(28, 35)), "R": (rng(2, 8), rng(9, 26), rng(27, 33)),
    "S": (rng(2, 8), rng(9, 27), rng(28, 34)), "T": (rng(1, 8), rng(9, 26), rng(27, 34)),
    "U": (rng(1, 8), rng(9, 27), rng(28, 35)),
    "V": (rng(2, 6) + ["X1", "X2"], rng(9, 23) + ["W1", "W2"], rng(26, 32)),
}
notes = {
    "B": "Right block starts at 4 and the left block ends with two wheelchair boxes (W, no number): the centre "
         "runs 9-26, so 27-28 fall exactly to the two boxes before 29.",
    "G": "Two crossed management boxes, no number, end the centre block after 25; the left block begins at 28, "
         "so they fill 26-27 exactly.",
    "V": "The back row tapers at both ends. Two crossed management boxes, no number, end the right block after "
         "6, between it and the centre's 9, so they fill 7-8 exactly; two wheelchair boxes print W, no number, "
         "end the centre after 23, before the left block's 26, so they fill 24-25 exactly.",
}
marks = {"B": W("W1", "W2"), "G": X("X1", "X2"), "V": {**X("X1", "X2"), **W("W1", "W2")}}
inferred = {"B": {"W1": "27", "W2": "28"}, "G": {"X1": "26", "X2": "27"},
            "V": {"X1": "7", "X2": "8", "W1": "24", "W2": "25"}}
for lab, (right, centre, left) in blocks.items():
    rows.append(row(lab, right, centre, left, marks=marks.get(lab), inferred=inferred.get(lab), note=notes.get(lab)))

finish({
    "venue": {"id": "tpcc-aud", "name_en": "Tai Po Civic Centre Auditorium", "name_zh": "大埔文娛中心 演藝廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/tpcc/common/doc/TPCC_Aud_a.pdf",
        "file": "TPCC_Aud_a.pdf",
        "sha256": "2697216597cdf8867c94bbbb143ace831f16e154fc58f6e4730312eb65e81b59",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total, wheelchair seats and orchestra pit",
        **TECH_SHEET,
        "quotes": ["Total Seating: 644", "Wheel chair seats: 6", "FORESTAGE . ORCHESTRA PIT Not available"],
        "note": "Confirms the plan's printed total of 644 and its six wheelchair boxes, and that there is no "
                "orchestra pit, so no configuration removes seats.",
    }],
    "location": location(geo_id="35510043", geo_name="Tai Po Civic Centre (Auditorium)", lat=22.45175, lon=114.16815,
                         address_en="12 On Pong Road, Tai Po, New Territories, Hong Kong",
                         address_zh="香港新界大埔安邦路12號", district="Tai Po", address_name="Tai Po Civic Centre"),
    "layout": {
        "seat_1_side": "right",
        "note": "Drawn with the stage at the top. Seat 1 is at the right-hand end of each row, and blocks are "
                "listed from that side: the right block, the centre, then the left. Numbers rise towards the "
                "left. Rows A-V with no row I and no row O. The two side blocks are angled towards the stage "
                "and step in at the front: row A is centre only, and row B's right block starts at seat 4. The "
                "plan names no seating areas, only the space (演藝廳 AUDITORIUM), so there is one zone.",
        "banks": [
            {"id": "centre", "side": "front", "seat_1": "right",
             "rows": [{"row": "A", "block": 1}] + [{"row": r["row"], "block": 2} for r in rows if r["row"] != "A"]},
            {"id": "right", "side": "right", "rows_run": "across", "seat_1": "right", "beside": "centre",
             "rows": [{"row": r["row"], "block": 1} for r in rows if r["row"] != "A"]},
            {"id": "left", "side": "left", "rows_run": "across", "seat_1": "right", "beside": "centre",
             "rows": [{"row": r["row"], "block": 3} for r in rows if r["row"] != "A"]},
        ],
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Auditorium": 644, "Total": 644},
    "zones": [
        {"name": "Auditorium", "name_zh": "演藝廳", "rows": rows},
    ],
})
