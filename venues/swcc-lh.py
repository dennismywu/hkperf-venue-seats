#!/usr/bin/env python3
"""Sheung Wan Civic Centre, Lecture Hall: seat facts read by hand from the LCSD seating plan.

The plan PDF wraps a single scanned image (2480x3508, no text or vector data), so every row, block
end and mark below was read by eye from zoomed crops of it (sha256 in source).
Writes data/swcc-lh.json; fails if the count does not match the printed total.

Usage: python venues/swcc-lh.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

REFERENCES = [{
    "what": "Seat total and orchestra pit",
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/swcc-lh-lfe.pdf",
    "title": "Sheung Wan Civic Centre – Lecture Hall, FULL Technical Information",
    "document_version": "V. 2026.03.09",
    "sha256": "c1c538483e6fe86ffb44656a9f7d7d7a856cbfd222efe02cec04ad81dbf04b79",
    "retrieved": "2026-09-26",
    "quotes": ["Max. Total Seating: 150", "FORESTAGE / ORCHESTRA PIT None"],
    "note": "Confirms the plan's total. There is no orchestra pit.",
}]
WS = ["W1", "W2", "W3", "W4"]

rows = [row(lab, rng(1, 12)) for lab in "ABCDEFGHJKLM"]
rows += [
    row("N", {"seats": ["X1", "X2"], "side": "left"}, {"seats": rng(3, 4), "side": "right"}, marks={"X1": "X", "X2": "X"}, inferred={"X1": "1", "X2": "2"},
        note="A solid black management area two boxes wide, under seats 1-2 of row M, then seats 3-4 at the right. "
             "The two boxes before 3 fill 1-2 exactly. A wheelchair platform (輪椅平台) takes the middle of rows N-P."),
    row("P", {"seats": WS[:2], "side": "left"}, {"seats": WS[2:], "side": "right"}, marks={w: "W" for w in WS},
        note="Two wheelchair boxes at each end, W with no number, either side of the wheelchair platform."),
]

finish({
    "venue": {"id": "swcc-lh", "name_en": "Sheung Wan Civic Centre Lecture Hall", "name_zh": "上環文娛中心 演講廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/swcc/attachments/lecturehall/swcc-lecture-hall.pdf",
        "file": "swcc-lecture-hall.pdf",
        "sha256": "f39742b50142527e21d26311fd78f9aa5c89d05fb0ddbddaf03f6266dc11d36f",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": REFERENCES,
    "location": location(geo_id="87810041", geo_name="Sheung Wan Civic Centre (Lecture Hall)", lat=22.28602, lon=114.14967,
                         address_en="345 Queen's Road Central, 4/F to 8/F of Sheung Wan Municipal Services Building, Hong Kong",
                         address_zh="香港皇后大道中345號上環市政大廈四樓至八樓", district="Central & Western",
                         address_name="Sheung Wan Civic Centre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row. Rows A-M are single blocks of 1-12 (no row I). Rows N-P have a wheelchair platform in the middle, with seats only at the ends. The plan names no seating areas, only the space (演講廳 LECTURE HALL), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (solid black box, no number)",
    },
    "printed_totals": {"Lecture Hall": 150, "Total": 150},
    "zones": [
        {"name": "Lecture Hall", "name_zh": "演講廳", "rows": rows},
    ],
})
