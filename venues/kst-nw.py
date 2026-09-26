#!/usr/bin/env python3
"""Ko Shan Theatre New Wing, Auditorium: seat facts read from the LCSD seating plan.

The plan PDF carries a text layer: every seat number and W is real text, so the rows were read by
grouping the tokens on each row's line. Management boxes (solid black, no number) and sightline
restrictions (yellow boxes) come from the plan's filled rectangles, checked by eye against zoomed
renders (sha256 in source). Writes data/kst-nw.json; fails if the counts do not match.

Usage: python venues/kst-nw.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/kst-nw-lfe.pdf",
    "title": "Ko Shan Theatre New Wing – Auditorium, FULL Technical Information",
    "document_version": "V. 2026.05.27",
    "sha256": "4e3ac86d3d73017a7acc90d609190707b8496e06007c8e758dcf735ff745b399",
    "retrieved": "2026-09-26",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}
R = lambda *ids: {i: "R" for i in ids}

# left block, centre block, right block (seat 1 at the left)
stalls = [row(lab, rng(a, 12), rng(13, c), rng(27, e)) for lab, a, c, e in [
    ("A", 8, 26, 31), ("B", 7, 26, 32), ("C", 6, 26, 33), ("D", 5, 25, 34), ("E", 4, 26, 35), ("F", 3, 25, 36),
]]
stalls += [
    row("G", ["W1", "W2", "X1"] + rng(5, 12), rng(13, 26), rng(27, 35) + ["X2", "W3", "W4"],
        marks={**W("W1", "W2", "W3", "W4"), **X("X1", "X2")},
        note="The left block opens with two wheelchair boxes and a management box, no numbers, before seat 5; "
             "the right block ends with a management box and two wheelchair boxes after 35. Not numbered on the plan."),
    row("H", rng(1, 12), rng(13, 26), rng(27, 38)),
    row("J", rng(1, 12), rng(13, 24) + ["X1", "X2"], rng(27, 38), marks=X("X1", "X2"),
        inferred={"X1": "25", "X2": "26"},
        note="Two management boxes, no number, end the centre block after 24; the right block starts at 27, so they fill 25-26 exactly."),
    row("K", rng(1, 12), rng(13, 26), rng(27, 38)),
    row("L", rng(1, 12), rng(13, 26), rng(27, 38)),
    row("M", rng(2, 12), rng(13, 26), rng(27, 37)),
    row("N", rng(4, 12), rng(13, 26), rng(27, 35)),
    row("P", rng(5, 12), rng(13, 26), rng(27, 34)),
    row("Q", rng(7, 12), rng(13, 25), rng(27, 32)),
    row("R", rng(11, 12), rng(13, 23), rng(27, 28)),
]

balcony = [
    row("AA", rng(3, 9), rng(10, 23), rng(24, 31), marks=R(*rng(3, 31)),
        note="Every seat in the front balcony row is marked as having a restricted sightline."),
    row("BB", rng(1, 9), rng(10, 23), rng(24, 31), marks=R("1", "2", "8", "9", "10", "23", "24", "25", "30", "31")),
    row("CC", rng(4, 9), rng(10, 23), rng(24, 29), marks=R("7", "8", "9", "10", "23", "24", "25", "26")),
    row("DD", rng(10, 24), marks=R("10", "24")),
]

finish({
    "venue": {"id": "kst-nw", "name_en": "Ko Shan Theatre New Wing Auditorium", "name_zh": "高山劇場新翼 演藝廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/kst/common/forms/KST%20New%20Wing%20Auditorium%20seating%20plan.pdf",
        "file": "KST New Wing Auditorium seating plan.pdf",
        "sha256": "759d3ec58cd42661fb988433d77f816e7c8381f997e239ba081e01dda3ac1015",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [
        {
            "what": "Seat totals and orchestra pit",
            **TECH_SHEET,
            "quotes": ["Total Seating: 596 Stalls: 495 Balcony: 101",
                       "Curved forestage/pit lift area, suitable for 15 persons", "Orchestra pit area 30.00m2 approx."],
            "note": "Confirms the plan's totals. The sheet describes the pit lift but gives no seats lost and no capacity with the pit in use, so no pit option is recorded here.",
        },
        {
            "what": "Wheelchair spaces",
            "publisher": LCSD,
            "url": "https://www.lcsd.gov.hk/en/kst/services/disabilities.html",
            "title": "Ko Shan Theatre: facilities for persons with disabilities",
            "retrieved": "2026-09-26",
            "quotes": ["Designated spaces convenient for wheelchair users (6 in Theatre and 4 in Auditorium)"],
            "note": "Matches the four W boxes in row G.",
        },
        {
            "what": "A different total on the booking form",
            "publisher": LCSD,
            "url": "https://www.lcsd.gov.hk/en/kst/common/doc/2025/Application%20form_KST_major_facilities_en__.pdf",
            "title": "Application for Booking of Major Facilities, Ko Shan Theatre (LCS 226c, Dec 2025)",
            "sha256": "b06ee23589e5310a0ca699c793ce21afd516625b6150d9df039e9a622c146c2f",
            "retrieved": "2026-09-26",
            "quotes": ["New Wing Auditorium (592 seats)"],
            "note": "The booking form gives 592, four fewer than the plan and technical sheets (596). No LCSD document found explains the difference; this file follows the plan.",
        },
    ],
    "location": location(geo_id="87616551", geo_name="Ko Shan Theatre (New Wing Auditorium)", lat=22.31368, lon=114.18556,
                         address_en="77 Ko Shan Road, Hung Hom, Kowloon, Hong Kong",
                         address_zh="香港九龍紅磡高山道77號", district="Kowloon City", address_name="Ko Shan Theatre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side. Three blocks per row in the stalls and balcony; each block keeps its own number range (1-12, 13-26, 27-38 in the stalls; 1-9, 10-23, 24-31 in the balcony), so short rows start or end part-way. No rows I, O.",
        "banks": [
            {"id": "stalls-centre", "side": "front", "rows": [{"row": r["row"], "block": 2} for r in stalls], "seat_1": "left"},
            {"id": "stalls-left", "side": "left", "rows": [{"row": r["row"], "block": 1} for r in stalls], "rows_run": "across",
             "seat_1": "left", "beside": "stalls-centre"},
            {"id": "stalls-right", "side": "right", "rows": [{"row": r["row"], "block": 3} for r in stalls], "rows_run": "across",
             "seat_1": "left", "beside": "stalls-centre"},
            {"id": "balcony-centre", "side": "front", "rows": [{"row": r["row"], "block": 2 if len(r["blocks"]) == 3 else 1} for r in balcony],
             "seat_1": "left"},
            {"id": "balcony-left", "side": "left", "rows": [{"row": r["row"], "block": 1} for r in balcony if len(r["blocks"]) == 3],
             "rows_run": "across", "seat_1": "left", "beside": "balcony-centre"},
            {"id": "balcony-right", "side": "right", "rows": [{"row": r["row"], "block": 3} for r in balcony if len(r["blocks"]) == 3],
             "rows_run": "across", "seat_1": "left", "beside": "balcony-centre"},
        ],
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (solid black box, no number)",
        "R": "Seat with sightline restrictions (yellow box)",
    },
    "printed_totals": {"Stalls": 495, "Balcony": 101, "Total": 596},
    "zones": [
        {"name": "Stalls", "name_zh": "堂座", "rows": stalls},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
