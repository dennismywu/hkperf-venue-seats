#!/usr/bin/env python3
"""East Kowloon Cultural Centre, The Beats: seat facts read from the published seating plan.

The plan's seat numbers and W are a text layer on a grid of boxes, so the rows were read from the tokens
on each row's line; the two crossed management boxes in row D were read by eye against a zoomed render
(sha256 in source). Writes data/ekcc-beats.json; fails if the count does not match the printed total.

Usage: python venues/ekcc-beats.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

PUBLISHER = LCSD + ", East Kowloon Cultural Centre"
TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-beats/index/TechInfo/ekcc-be-lfe.pdf",
    "title": "East Kowloon Cultural Centre – The Beats, FULL Technical Information",
    "document_version": "V. 2026.07.20",
    "sha256": "dc7bccab8927f01703e57946b6a6744a9b94ec46aafc296c7c3752f112790667",
    "retrieved": "2026-09-29",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}

rows = [
    row("A", ["W1", "W2"] + rng(3, 9) + ["W3", "W4"],
        marks=W("W1", "W2", "W3", "W4"), inferred={"W1": "1", "W2": "2", "W3": "10", "W4": "11"},
        note="A wheelchair box at each end: two before 3 (so 1-2) and two after 9 (so 10-11)."),
    row("B", rng(1, 16)),
    row("C", rng(1, 15)),
    row("D", ["X1", "X2"] + rng(3, 16), marks=X("X1", "X2"), inferred={"X1": "1", "X2": "2"},
        note="Two crossed management boxes, no number, open the row before 3, so they fill 1-2 exactly."),
    row("E", rng(1, 15)),
    row("F", rng(1, 16)),
    row("G", rng(1, 15)),
    row("H", rng(1, 18)),
]

finish({
    "venue": {"id": "ekcc-beats", "name_en": "East Kowloon Cultural Centre, The Beats",
              "name_zh": "東九文化中心 樂館"},
    "source": {
        "publisher": PUBLISHER,
        "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-beats/index/SeatsPlan-T5.pdf",
        "page": "https://www.ekcc.hk/en/hiring/the-beats/",
        "file": "SeatsPlan-T5.pdf",
        "sha256": "1f0c0b002ddf994bf37241b2f3c52fda799f13b35e330a14b163dcf29438e5ec",
        "plan_code": "T5-v4",
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total, wheelchair spaces and orchestra pit",
        **TECH_SHEET,
        "quotes": ["Total Seating 120", "Wheelchair Space 4", "END STAGE (120 seats)", "FLAT FLOOR (no seats)"],
        "note": "Confirms the plan's total and its four wheelchair boxes. The room has an end-stage layout (120 seats) "
                "and a flat-floor, no-seat layout; on the plan the four W print no number.",
    }],
    "location": location(geo_id="826817420", geo_name="East Kowloon Cultural Centre (The Beats)", lat=22.32427, lon=114.21494,
                         address_en="60 Ngau Tau Kok Road, Kowloon, Hong Kong", address_zh=None, district=None,
                         address_source={**TECH_SHEET, "quote": "East Kowloon Cultural Centre 60 Ngau Tau Kok Road, Kowloon, HK",
                                         "note": "Not in LCSD's venue.json; address as printed on the technical sheet."}),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, one block per row with no "
                "aisle. Rows A-H. The plan names no areas, only the space (樂館 THE BEATS), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"The Beats": 120, "Total": 120},
    "zones": [
        {"name": "The Beats", "name_zh": "樂館", "rows": rows},
    ],
})
