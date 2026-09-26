#!/usr/bin/env python3
"""Hong Kong City Hall Theatre: seat facts read by hand from the LCSD seating plan.

The plan PDF wraps a single scanned image (1018x1422, no text or vector data), so every block end,
row label and mark below was read by eye from zoomed crops of it (sha256 in source).
Writes data/hkch-th.json; fails if the count does not match the printed total.

Usage: python venues/hkch-th.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

BLACK = "Solid black area about two seats wide; the numbering skips these numbers. The plan's legend does not explain it."


def blocked(seats, numbers):
    """A block followed (in number order) by a solid black area where `numbers` would be."""
    return {"seats": seats, "blocked": {"slots": len(numbers), "skipped_numbers": numbers, "note": BLACK}}


# left block, centre block, right block (seat 1 at the left)
ends = {
    "B": (5, 15, 20), "C": (5, 15, 20), "D": (5, 15, 20),
    "E": (5, 16, 21), "F": (5, 16, 21),
    "G": (6, 17, 23), "H": (6, 17, 23),
    "J": (6, 18, 24), "K": (6, 18, 24), "L": (6, 18, 24), "M": (6, 18, 24),
    "N": (6, 19, 25), "P": (6, 19, 25), "R": (6, 19, 25),
    "S": (6, 20, 26), "T": (6, 20, 26), "V": (6, 20, 26),
}

rows = [row("A", ["W1", "W2", "W3", "W4", "W5"], rng(6, 14), rng(15, 19),
            marks={f"W{i}": "W" for i in range(1, 6)},
            inferred={f"W{i}": str(i) for i in range(1, 6)},
            note="Five wheelchair boxes print no number. They sit before seat 6, so they fill 1-5 exactly.")]
for lab in "BCDEFGHJKLMNPQRSTVW":
    if lab == "Q":
        rows.append(row("Q", rng(1, 6), blocked(rng(7, 17), ["18", "19"]), rng(20, 25),
                        note="Centre block ends at 17, then a solid black area where 18-19 would be."))
    elif lab == "W":
        rows.append(row("W", blocked(rng(1, 4), ["5", "6"]), rng(7, 20), rng(21, 26),
                        note="Left block ends at 4, then a solid black area where 5-6 would be."))
    else:
        a, b, c = ends[lab]
        rows.append(row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c)))

finish({
    "venue": {"id": "hkch-th", "name_en": "Hong Kong City Hall Theatre", "name_zh": "香港大會堂 劇院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/hkch/common/download/hkch-theatre.pdf",
        "file": "hkch-theatre.pdf",
        "sha256": "b50a5082c09e56df1fe554ab06fc182a158ac45d487a810702bf7fcee5fa734b",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total and orchestra pit",
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/hkch-th-sfe.pdf",
        "title": "Hong Kong City Hall – Theatre, Basic Technical Information",
        "document_version": "V. 2026.01.07",
        "sha256": "8b63eb497116012c18dc177d652e6d6b3240b93f256ac44a01149c9af0a8f1df",
        "retrieved": "2026-09-26",
        "quotes": ["Seats 463", "Orchestra Pit: Formed by removing forestage traps. Capacity for 8-15"],
        "note": "Confirms the plan's total. The pit is formed from forestage traps, so no seats are lost to it.",
    }],
    "location": location(geo_id="87510010", geo_name="Hong Kong City Hall (Theatre)", lat=22.282279, lon=114.161545,
                         address_en="5 Edinburgh Place, Central, Hong Kong",
                         address_zh="香港中環愛丁堡廣場5號", district="Central & Western", address_name="Hong Kong City Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side. Three blocks per row. No rows I, O or U. The plan names no seating areas, only the space (劇院 THEATRE), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
    },
    "printed_totals": {"Theatre": 463, "Total": 463},
    "standing": {
        "places": rng(1, 10),
        "note": "Printed as 'STANDING' with the numbers 1-10 below row W, without boxes. Not part of the seat total.",
    },
    "zones": [
        {"name": "Theatre", "name_zh": "劇院", "rows": rows},
    ],
})
