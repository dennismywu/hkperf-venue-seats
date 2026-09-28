#!/usr/bin/env python3
"""Sha Tin Town Hall Auditorium: seat facts read from the LCSD seating plan.

The plan is vector with outlined text. An extraction script found every seat box (1,376) and read the
block ends; each row's blocks, the marks and the row labels were then checked by eye against zoomed
renders (sha256 in source). Writes data/stth-aud.json; fails if the counts do not match.

Usage: python venues/stth-aud.py
"""
from common import CREDIT, LCSD, aisle_banks, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/stth-au-sfe.pdf",
    "title": "Sha Tin Town Hall Auditorium, Basic Technical Information",
    "document_version": "V. 2026.07.02",
    "sha256": "05b21b55fbd819545e1e22494c7d2062301c1baca3a0742594bb3868bb1999b8",
    "retrieved": "2026-09-26",
}


def three(label, a, b, c, **kw):
    """Left block 1-a, centre a+1-b, right b+1-c (seat 1 at the left)."""
    return row(label, rng(1, a), rng(a + 1, b), rng(b + 1, c), **kw)


stalls = [three(lab, *ends) for lab, ends in {
    "A": (11, 25, 36), "B": (11, 26, 37), "C": (12, 26, 38), "D": (13, 28, 41), "E": (13, 27, 40),
    "F": (13, 28, 41), "G": (13, 27, 40), "H": (13, 28, 41), "I": (11, 25, 36), "J": (13, 28, 41),
    "K": (13, 27, 40), "L": (13, 28, 41), "M": (13, 27, 40), "N": (13, 28, 41), "O": (11, 25, 36),
}.items()]

upper = [row("P", rng(1, 6) + ["X1", "X2"], rng(9, 22), rng(23, 30),
             marks={"X1": "X", "X2": "X"}, inferred={"X1": "7", "X2": "8"},
             note="Two management boxes print X, no number. They sit between seat 6 and the centre block's 9, so they fill 7-8 exactly.")]
upper += [three(lab, *ends) for lab, ends in {
    "Q": (8, 23, 31), "R": (8, 22, 30), "S": (8, 23, 31), "T": (9, 23, 32), "U": (9, 24, 33),
    "V": (9, 23, 32), "W": (9, 24, 33), "X": (9, 23, 32), "Y": (9, 24, 33), "Z": (9, 23, 32),
    "ZA": (9, 24, 33), "ZB": (9, 23, 32),
}.items()]
upper.append(row("ZC", ["W1", "W2"] + rng(3, 7) + ["X1", "X2"], rng(10, 24),
                 ["W3", "W4", "W5", "W6"] + rng(29, 31) + ["W7", "W8"],
                 marks={**{f"W{i}": "W" for i in range(1, 9)}, "X1": "X", "X2": "X"},
                 inferred={"W1": "1", "W2": "2", "X1": "8", "X2": "9", "W3": "25", "W4": "26", "W5": "27", "W6": "28"},
                 note="Wheelchair and management boxes print W or X, no number. W1-W2 fill 1-2 (before 3); X1-X2 fill 8-9 (between 7 and the centre block's 10); W3-W6 fill 25-28 (between 24 and 29). W7-W8 follow 31 at the row end; 32-33 is likely but not printed."))

balcony = [three(lab, *ends) for lab, ends in {
    "BB": (5, 20, 25), "BC": (6, 21, 27), "BD": (9, 24, 33), "BE": (9, 24, 33), "BF": (9, 24, 33),
    "BG": (9, 24, 33), "BH": (9, 24, 33), "BI": (9, 24, 33), "BJ": (6, 21, 27), "BK": (6, 21, 27),
    "BL": (6, 18, 24),
}.items()]
balcony.append(row("BM", rng(1, 6), rng(19, 24), note="No centre block: the numbering runs 1-6, then 19-24."))

finish({
    "venue": {"id": "stth-aud", "name_en": "Sha Tin Town Hall Auditorium", "name_zh": "沙田大會堂 演奏廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/stth/common/files/stth-auditorium%20v5_0604.pdf",
        "file": "stth-auditorium v5_0604.pdf",
        "sha256": "2c312c25c8262d3950ff732366862f0da9841e03a4fdee96c7cf03489c9b16d7",
        "plan_code": "v5_0604",
        "printed_date": None,
        "applies": "Applicable to events with advance booking and counter booking after 1 Sep 2024",
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat totals",
        **TECH_SHEET,
        "quotes": ["1372 - stalls 589, upper stalls 443, balcony 340"],
        "note": "Confirms the plan's totals.",
    }],
    "location": location(geo_id="36310035", geo_name="Sha Tin Town Hall (Auditorium)", lat=22.38136, lon=114.1899,
                         address_en="1 Yuen Wo Road, Sha Tin, New Territories, Hong Kong",
                         address_zh="香港新界沙田源禾路1號", district="Sha Tin", address_name="Sha Tin Town Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side. Three straight blocks per row. The stalls include a row I; the upper stalls run P-Z then ZA-ZC; the balcony starts at BB and includes BI. The plan prints the row labels in the aisles.",
        "banks": aisle_banks(("stalls", stalls), ("upper", upper), ("balcony", balcony)),
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (grey box printed W, no number)",
        "X": "Management seat (grey box printed X, no number)",
    },
    "printed_totals": {"Stalls": 589, "Upper Stalls": 443, "Balcony": 340, "Total": 1372},
    "orchestra_pits": [{
        "name": "Orchestra pit (91.5 m²)",
        "rows_removed": ["A", "B"],
        "rows_basis": "inferred",
        "rows_reasoning": "The sheet gives the seats lost, not the rows. A + B = 36 + 37 = 73, and no other run of front rows gives 73 (A = 36, A-C = 111).",
        "stated": {"seats_removed": 73},
        "source": {**TECH_SHEET, "quote": "Pit 91.5 m2 with a loss of 73 seats"},
    }],
    "zones": [
        {"name": "Stalls", "name_zh": "大堂前座", "rows": stalls},
        {"name": "Upper Stalls", "name_zh": "大堂後座", "rows": upper},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
