#!/usr/bin/env python3
"""Tuen Mun Town Hall, Auditorium: seat facts read from the LCSD seating plan.

The plan PDF wraps a single scanned image (1240x1754, no text or vector data). An extraction script
found the seat boxes and read their numbers; every block end, row label and mark below was then checked by
eye against zoomed crops of the scan (sha256 in source). Writes data/tmth-aud.json; fails if the
counts do not match the printed totals.

Usage: python venues/tmth-aud.py
"""
from common import CREDIT, LCSD, aisle_banks, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/tmth-aud-lfe.pdf",
    "title": "Tuen Mun Town Hall – Auditorium, FULL Technical Information",
    "document_version": "V. 2026.08.07",
    "sha256": "5263856e6fe678ad8e3bb5036c4edc3e4d20ce1b1b568e19a743adb960d6a53b",
    "retrieved": "2026-09-26",
}
REFERENCES = [{
    "what": "Seat totals and orchestra pit",
    **TECH_SHEET,
    "quotes": ["Total Seating: 1,368 Stalls: 1,028 Stall: 589 Upper Stall: 439 Balcony: 340",
               "73 seats will be lost from Stall Level Row A & Row B for setting orchestra pit"],
    "note": "Confirms the plan's totals (the sheet's 'Stalls: 1,028' is stall and upper stall together), and names the rows the pit removes. No wheelchair figure is given.",
}]
X = lambda *ids: {i: "X" for i in ids}
W = lambda *ids: {i: "W" for i in ids}


def three(lab, a, b, c, **kw):
    """Left block 1-a, centre a+1-b, right b+1-c (seat 1 at the left)."""
    return row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c), **kw)


# the stalls alternate between three row lengths
S36, S37, S38, S40, S41 = (11, 25, 36), (11, 26, 37), (12, 26, 38), (13, 27, 40), (13, 28, 41)
stalls = [three(lab, *ends) for lab, ends in [
    ("A", S36), ("B", S37), ("C", S38), ("D", S41), ("E", S40), ("F", S41), ("G", S40), ("H", S41),
    ("I", S36), ("J", S41), ("K", S40), ("L", S41), ("M", S40), ("N", S41), ("O", S36),
]]

U30, U31, U32, U33 = (8, 22, 30), (8, 23, 31), (9, 23, 32), (9, 24, 33)
upper = [row("P", rng(1, 6) + ["X1", "X2"], rng(9, 22), rng(23, 30), marks=X("X1", "X2"), inferred={"X1": "7", "X2": "8"},
             note="Two crossed management boxes end the left block after 6; the centre block starts at 9, so they fill 7-8 exactly.")]
upper += [three(lab, *ends) for lab, ends in [
    ("Q", U31), ("R", U30), ("S", U31), ("T", U32), ("U", U33), ("V", U32), ("W", U33), ("X", U32),
    ("Y", U33), ("Z", U32), ("ZA", U33), ("ZB", U32),
]]
upper.append(row("ZC", ["W1", "W2"] + rng(4, 7) + ["X1", "X2"], rng(10, 24), ["W3", "W4", "W5", "W6", "W7", "W8"],
                 marks={**W("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"), **X("X1", "X2")},
                 inferred={"X1": "8", "X2": "9"},
                 note="The left block is two wheelchair boxes, 4-7, then two crossed management boxes; the centre block starts "
                      "at 10, so the management boxes fill 8-9 exactly. The left wheelchair boxes are likely 2-3 and the six "
                      "on the right 25-30; neither is printed."))

B25, B27, B33 = (5, 20, 25), (6, 21, 27), (9, 24, 33)
balcony = [three(lab, *ends) for lab, ends in [
    ("BB", B25), ("BC", B27), ("BD", B33), ("BE", B33), ("BF", B33), ("BG", B33), ("BH", B33), ("BI", B33),
    ("BJ", B27), ("BK", B27),
]]
balcony += [
    row("BL", rng(1, 6), rng(7, 18), rng(19, 24)),
    row("BM", rng(1, 6), rng(19, 24), note="No centre block; the right block continues the numbering at 19, as in row BL."),
]

finish({
    "venue": {"id": "tmth-aud", "name_en": "Tuen Mun Town Hall Auditorium", "name_zh": "屯門大會堂 演奏廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/tmth/common/attachments/tc/aud/tmth-aud.pdf",
        "file": "tmth-aud.pdf",
        "sha256": "c7ae870cf859a5d8b8b5b20b4ed86f2a8937e43b7fa052b9b53b465779e6a9ed",
        "plan_code": "revised Sept 2012",
        "printed_date": "2012-09",
        "credit": CREDIT,
    },
    "references": REFERENCES,
    "location": location(geo_id="76810048", geo_name="Tuen Mun Town Hall (Auditorium)", lat=22.391810, lon=113.976771,
                         address_en="3 Tuen Hi Road, Tuen Mun, New Territories, Hong Kong",
                         address_zh="香港新界屯門屯喜路3號", district="Tuen Mun", address_name="Tuen Mun Town Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and numbering runs on through three blocks. The stalls include a row I; the upper stalls run P-Z then ZA-ZC; the balcony runs BB-BM (no BA). Row BM has no centre block. The plan prints the row labels in the aisles.",
        "banks": aisle_banks(("stalls", stalls), ("upper", upper), ("balcony", balcony)),
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Stalls": 589, "Upper Stalls": 439, "Balcony": 340, "Total": 1368},
    "orchestra_pits": [{
        "name": "Orchestra pit (91.5 m²)",
        "rows_removed": ["A", "B"],
        "rows_basis": "stated",
        "rows_reasoning": "The technical sheet names the rows. A + B = 36 + 37 = 73, matching the stated loss.",
        "stated": {"seats_removed": 73},
        "source": {**TECH_SHEET, "quote": "73 seats will be lost from Stall Level Row A & Row B for setting orchestra pit"},
    }],
    "zones": [
        {"name": "Stalls", "name_zh": "大堂前座", "rows": stalls},
        {"name": "Upper Stalls", "name_zh": "大堂後座", "rows": upper},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
