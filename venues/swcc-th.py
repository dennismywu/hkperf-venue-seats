#!/usr/bin/env python3
"""Sheung Wan Civic Centre, Theatre: seat facts read from the LCSD seating plan.

The plan PDF carries a text layer for every seat number, W and row label. Centre blocks were read
from the tokens on each label's line; the side blocks slope slightly, so their seats were chained
box to box and matched to the row label at their aisle end. The solid black management boxes were
measured from the plan's filled rectangles and checked by eye (sha256 in source).
Writes data/swcc-th.json; fails if the count does not match the printed total.

Usage: python venues/swcc-th.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/swcc-th-lfe.pdf",
    "title": "Sheung Wan Civic Centre – Theatre, FULL Technical Information",
    "document_version": "V. 2026.03.09",
    "sha256": "ed56a6d2f6e7ec86d2f5c197c0d1fbaca84b4947122bd4d03f8b6bf1109a9f74",
    "retrieved": "2026-09-26",
}
REFERENCES = [
    {
        "what": "Seat total and orchestra pit",
        **TECH_SHEET,
        "quotes": ["Total Seating: 482", "35 seats will be lost from the Stall Row AA & BB for setting Orchestra pit"],
        "note": "Confirms the plan's total, and names the rows the pit removes.",
    },
    {
        "what": "An older total on the stage drawing",
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/tech/common/venue_drawing/swcc-th-dwg.pdf",
        "title": "Sheung Wan Civic Centre – Theatre, venue drawing (LCSD-PATSS-V.2023.3)",
        "sha256": "d2add50d5edd35553df7c65c1db8da8b41fa0b009016921b5277b41ba03a6820",
        "retrieved": "2026-09-26",
        "quotes": ["座位 Seats: 480"],
        "note": "The drawing predates the seat improvement project LCSD reports completed in August 2023; the plan, facility page and technical sheets all give 482.",
    },
]

# left block, centre block, right block (seat 1 at the left): last seat of each
ends = {
    "BB": (3, 15, 18), "A": (3, 16, 19), "B": (3, 15, 18),
    "C": (4, 17, 21), "D": (4, 16, 20), "E": (4, 17, 21),
    "F": (5, 17, 22), "H": (5, 17, 22),
    "J": (6, 19, 25), "K": (6, 18, 24), "L": (8, 21, 29),
    "M": (7, 19, 26), "N": (7, 20, 27), "P": (7, 19, 26), "Q": (7, 20, 27), "R": (7, 19, 26), "S": (7, 20, 27),
    "T": (6, 18, 24),
}


def plain(lab):
    a, b, c = ends[lab]
    return row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c))


rows = [row("AA", rng(1, 2), rng(3, 15), ["W1", "W2"], marks={"W1": "W", "W2": "W"},
            note="The right block is two wheelchair boxes, W with no number, after 15 (16-17 likely, not printed).")]
rows += [plain(lab) for lab in ["BB", "A", "B", "C", "D", "E", "F"]]
rows.append(row("G", rng(1, 5), rng(6, 16) + ["X1", "X2"], rng(19, 23), marks={"X1": "X", "X2": "X"},
                inferred={"X1": "17", "X2": "18"},
                note="Two solid black management boxes end the centre block after 16; the right block starts at 19, so they fill 17-18 exactly."))
rows += [plain(lab) for lab in ["H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T"]]
rows += [
    row("V", {"seats": rng(1, 6), "side": "left"}, {"seats": rng(7, 12), "side": "right"},
        note="No centre block: the plan prints a wheelchair platform (輪椅平台) there, in rows V-W. The right block continues the numbering at 7."),
    row("W", {"seats": rng(1, 4) + ["X1", "X2"], "side": "left"}, {"seats": ["W1", "W2"] + rng(9, 12), "side": "right"},
        marks={"X1": "X", "X2": "X", "W1": "W", "W2": "W"},
        inferred={"X1": "5", "X2": "6", "W1": "7", "W2": "8"},
        note="The left block ends with two solid black management boxes after 4; the right block opens with two wheelchair boxes before 9. "
             "The four boxes between 4 and 9 fill 5-8 exactly. No centre block (wheelchair platform)."),
]

finish({
    "venue": {"id": "swcc-th", "name_en": "Sheung Wan Civic Centre Theatre", "name_zh": "上環文娛中心 劇院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/swcc/attachments/theatre/swcc-theatre.pdf",
        "file": "swcc-theatre.pdf",
        "sha256": "30ab0cb39fcb261d7fe9709cbc28c114d1ef53ea9b8edabdecedbde48354a2a8",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": REFERENCES,
    "location": location(geo_id="87810042", geo_name="Sheung Wan Civic Centre (Theatre)", lat=22.28602, lon=114.14967,
                         address_en="345 Queen's Road Central, 4/F to 8/F of Sheung Wan Municipal Services Building, Hong Kong",
                         address_zh="香港皇后大道中345號上環市政大廈四樓至八樓", district="Central & Western",
                         address_name="Sheung Wan Civic Centre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side; numbering runs on from block to block. Rows AA and BB are in front of row A. No rows I, O, U. The side blocks slope slightly towards the stage. Rows V-W have a wheelchair platform in place of the centre block. The plan names no seating areas, only the space (劇院 THEATRE), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (solid black box, no number)",
    },
    "printed_totals": {"Theatre": 482, "Total": 482},
    "orchestra_pits": [{
        "name": "Orchestra pit (10 × 2 m)",
        "rows_removed": ["AA", "BB"],
        "rows_basis": "stated",
        "rows_reasoning": "The technical sheet names the rows. AA + BB = 17 + 18 = 35 boxes (AA's two wheelchair boxes included), matching the stated loss.",
        "stated": {"seats_removed": 35},
        "source": {**TECH_SHEET, "quote": "35 seats will be lost from the Stall Row AA & BB for setting Orchestra pit"},
    }],
    "zones": [
        {"name": "Theatre", "name_zh": "劇院", "rows": rows},
    ],
})
