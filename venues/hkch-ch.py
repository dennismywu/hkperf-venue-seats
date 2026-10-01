#!/usr/bin/env python3
"""Hong Kong City Hall, Concert Hall: seat facts read by hand from the LCSD seating plan.

The plan PDF wraps a single scanned image (1653x2338, no text or vector data), so every block end, row
label and mark below was read by eye from zoomed crops of it (sha256 in source). Writes
data/hkch-ch.json; fails if a count does not match the printed total.

Usage: python venues/hkch-ch.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

BLACK = ("Solid black area about two seats wide; the numbering skips these numbers. The plan's legend "
         "does not explain it.")
TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/hkch-ch-lfe.pdf",
    "title": "Hong Kong City Hall – Concert Hall, FULL Technical Information",
    "document_version": "V. 2026.01.07",
    "sha256": "80ac1c5b4c239c4af322f1fde05e1d213bb53e204387e34c6a78c619de7980b9",
    "retrieved": "2026-10-01",
}
W = lambda *ids: {i: "W" for i in ids}


def blocked(seats, numbers):
    """A block followed (in number order) by a solid black area where `numbers` would be."""
    return {"seats": seats, "blocked": {"slots": len(numbers), "skipped_numbers": numbers, "note": BLACK}}


# left block, centre block, right block (seat 1 at the left), as row -> (end of left, end of centre,
# end of right); the centre starts at the left end + 1.
ends = {
    "A": (8, 22, 30), "B": (8, 21, 29), "C": (10, 25, 35), "D": (12, 26, 38),
    "E": (14, 29, 43), "F": (14, 28, 42), "G": (14, 29, 43), "H": (11, 25, 36),
    "J": (12, 27, 39), "K": (13, 27, 40), "L": (14, 29, 43), "M": (14, 28, 42),
    "N": (14, 29, 43), "O": (12, 26, 38), "P": (11, 26, 37),
}
front = [row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c)) for lab, (a, b, c) in ends.items()]

# rear stalls: rows Q, R, S carry a further outer block each side (and Q a black area); the rest are three
# blocks; row ZE carries the wheelchair boxes and its centre/right ends in the slots the black area takes.
rear = [
    row("Q", rng(1, 3), blocked(rng(4, 9), ["10", "11"]), rng(12, 25), rng(26, 33), rng(34, 36),
        note="An outer block 1-3 each side; the left-inner block ends at 9, then a solid black area where "
             "10-11 would be, and the right-inner block ends at 33."),
    row("R", rng(1, 3), rng(4, 11), rng(12, 26), rng(27, 34), rng(35, 37), note="An outer block 1-3 each side."),
    row("S", rng(1, 3), rng(4, 11), rng(12, 25), rng(26, 33), rng(34, 36), note="An outer block 1-3 each side."),
]
rear += [row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c)) for lab, (a, b, c) in {
    "T": (9, 24, 33), "V": (9, 23, 32), "W": (9, 24, 33), "X": (9, 23, 32), "Y": (9, 24, 33),
    "Z": (9, 23, 32), "ZA": (9, 24, 33), "ZB": (9, 23, 32), "ZC": (10, 25, 35), "ZD": (10, 24, 34),
}.items()]
rear.append(row("ZE", rng(1, 4) + ["W1", "W2", "W3", "W4"], rng(11, 23), ["W5", "W6", "W7", "W8"] + rng(28, 31),
                marks=W("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"),
                inferred={"W5": "24", "W6": "25", "W7": "26", "W8": "27"},
                note="Four wheelchair boxes print W, no number, after seat 4 (the numbers 9-10 are not "
                     "drawn); four more begin the right block after the centre's 23, between it and the "
                     "printed 28, so they fill 24-27 exactly."))

# balcony: three blocks per row (seat 1 at the left)
balcony = [row(lab, rng(1, a), rng(a + 1, b), rng(b + 1, c)) for lab, (a, b, c) in {
    "BA": (6, 21, 27), "BB": (6, 20, 26), "BC": (7, 22, 29), "BD": (9, 23, 32), "BE": (9, 24, 33),
    "BF": (9, 23, 32), "BG": (9, 24, 33), "BH": (9, 23, 32), "BJ": (9, 24, 33), "BK": (7, 21, 28),
    "BL": (7, 22, 29), "BM": (7, 19, 26), "BN": (7, 20, 27),
}.items()]

finish({
    "venue": {"id": "hkch-ch", "name_en": "Hong Kong City Hall Concert Hall",
              "name_zh": "香港大會堂 音樂廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/hkch/common/download/HKCH%20Seat%20plan%20(Revised).pdf",
        "file": "HKCH Seat plan (Revised).pdf",
        "sha256": "a87e85c714843dc98d185da3b666e604956cb02b3cd8008b7d910e4245183e6c",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total and orchestra pit / extension stage",
        **TECH_SHEET,
        "quotes": ["Total Seating: 1,430", "Front Stalls: 578", "Rear Stalls: 465", "Balcony: 387",
                   "Orchestra Pit. Formed by removing forestage traps Capacity of 10-15 musicians. Formed "
                   "by removal of Seats at Row A & B which will reduce 59 seats."],
        "note": "Confirms the plan's totals. The orchestra pit and the extension stage both remove Rows A "
                "and B, 59 seats.",
    }],
    "location": location(geo_id="87510008", geo_name="Hong Kong City Hall (Concert Hall)", lat=22.282279,
                         lon=114.161545, address_en="5 Edinburgh Place, Central, Hong Kong",
                         address_zh="香港中環愛丁堡廣場5號", district="Central & Western",
                         address_name="Hong Kong City Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks "
                "are listed from that side. Three blocks per row, save the first three rear-stall rows "
                "(Q-S), which carry a further short outer block each side. No rows I, O or U. The plan "
                "also draws side boxes (左廂座 / 右廂座) and numbered markers along the left and right "
                "promenades, and a large solid black area behind the rear stalls; LCSD's tier figures "
                "count none of these. The plan names only the space (音樂廳 CONCERT HALL), so there is one "
                "zone per part of house.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
    },
    "orchestra_pits": [{
        "name": "Orchestra pit / extension stage",
        "rows_removed": ["A", "B"],
        "rows_basis": "stated",
        "rows_reasoning": "The technical sheet names Rows A and B. A + B = 30 + 29 = 59, matching the "
                          "stated loss.",
        "stated": {"seats_removed": 59},
        "source": {**TECH_SHEET, "quote": "Formed by removal of Seats at Row A & B which will reduce 59 seats."},
    }],
    "printed_totals": {"Front Stalls": 578, "Rear Stalls": 465, "Balcony": 387, "Total": 1430},
    "standing": {
        "places": rng(1, 20),
        "note": "Printed as 'Standing' with 1-10 on the left and 11-20 on the right below row ZE, without "
                "boxes. Not part of the seat total.",
    },
    "zones": [
        {"name": "Front Stalls", "name_zh": "大堂前座", "rows": front},
        {"name": "Rear Stalls", "name_zh": "大堂後座", "rows": rear},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
