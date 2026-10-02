#!/usr/bin/env python3
"""East Kowloon Cultural Centre, The Theatre: seat facts read from the LCSD seating plan (PROVISIONAL).

The plan is a round hall: the stage sits in an opening at the top and the seats wrap it in concentric
rings (rows A-L, no I). The plan is vector but every figure is an outline and the seat boxes are rotated,
so tools/draft_rows.py cannot group them; this first pass assigns each seat rectangle to a ring
geometrically and reads its number from the text layer. It totals the printed 536, but the per-row
assignment still needs checking by eye. Writes data/ekcc-th.json.

Usage: python venues/ekcc-th.py
"""
from common import CREDIT, LCSD, finish, location, row, rng

W = lambda *ids: {i: "W" for i in ids}

rows = [
    row("A", rng(1, 5), rng(6, 8), rng(19, 21), rng(28, 30), rng(43, 45), rng(50, 54)),
    row("B", rng(1, 4), rng(6, 11), rng(16, 21), rng(28, 33), rng(40, 45), rng(50, 53)),
    row("C", rng(1, 3), rng(6, 12), rng(16, 22), rng(28, 34), rng(40, 46), rng(50, 52)),
    row("D", rng(1, 3), rng(6, 9), ["10"], rng(11, 13), rng(16, 23), rng(28, 35), rng(40, 47), rng(50, 52)),
    row("E", rng(1, 3), rng(6, 15), rng(16, 25), rng(28, 37), rng(40, 52)),
    row("F", rng(1, 12), rng(16, 27), rng(28, 39), rng(40, 51)),
    row("G", rng(1, 29), rng(30, 50), marks={"1": "X", "2": "X"}),
    row("H", rng(1, 10), rng(11, 26), rng(30, 43), rng(49, 64), rng(68, 77)),
    row("J", rng(1, 10), rng(11, 28), rng(30, 45), rng(49, 66), rng(68, 77)),
    row("K", rng(1, 10), rng(11, 29), rng(30, 46), rng(49, 67), rng(68, 77)),
    row("L", rng(11, 29), rng(30, 48), rng(49, 67), marks={"26": "W", "27": "W", "28": "W", "29": "W", "47": "X", "48": "X"}),
]

finish({
    "venue": {"id": "ekcc-th", "name_en": "East Kowloon Cultural Centre, The Theatre",
              "name_zh": "\u6771\u4e5d\u6587\u5316\u4e2d\u5fc3 \u5287\u5834"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-theatre/index/SeatsPlan-T2.pdf",
        "file": "SeatsPlan-T2.pdf",
        "sha256": "a46d05c5614fe0a9e8d37c3fca0724d57ffcdbb2c528e6dc1f6c849e32f2e48f",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [],
    "location": location(geo_id="826817392", geo_name="East Kowloon Cultural Centre (The Theatre)",
                         lat=22.32427, lon=114.21494,
                         address_en="60 Ngau Tau Kok Road, Kowloon, Hong Kong",
                         address_zh="\u4e5d\u9f8d\u725b\u982d\u89d2\u725b\u982d\u89d2\u905360\u865f",
                         district="Kwun Tong", address_name="East Kowloon Cultural Centre"),
    "layout": {
        "seat_1_side": "left",
        "arrangement": "arc",
        # scale: the plan's seat pitch is 13.5 units and the viewer's seats are 15 wide, so the plan is
        # drawn 1.25x larger to leave a gap between seats (geometry from tools/derive_runs.py)
        "arc": {"stage_span": 100, "rotate_seats": True, "ring_gap": 1.6, "scale": 1.25, "centre": [420, 440]},
        "note": "A round hall: the stage sits in an opening at the top and the seats wrap it in "
                "rings of straight runs. Rows A-L with no row I; each row runs anticlockwise from seat 1 near "
                "true bearing 310 around the front to the last seat near bearing 50.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Theatre": 536, "Total": 536},
    "zones": [{
        "name": "Theatre", "name_zh": "\u5287\u5834",
        "arc": {"start": 310, "span": 260, "dir": "ccw"},
        "rows": rows,
        # bearings and radii are recut by tools/derive_runs.py to the clear gap between the seats
        "vomitoria": [
            {"rows": list("ABCDEF"), "from": 230, "to": 222, "inner": 0, "outer": 0,
             "note": "Entrance (vomitorium) between seats 11 and 16; rows G-L continue across it."},
            {"rows": list("ABCDEF"), "from": 138, "to": 130, "inner": 0, "outer": 0,
             "note": "Entrance (vomitorium) between seats 33 and 40; rows G-L continue across it."},
        ],
    }],
})
