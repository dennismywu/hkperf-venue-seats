#!/usr/bin/env python3
"""Sha Tin Town Hall, Cultural Activities Hall: seat facts read from the LCSD seating plan.

The plan PDF has no text layer (every figure is outlined), so the rows were read by eye from zoomed
renders, with the seat boxes taken from the PDF's own rectangles (sha256 in source). Writes
data/stth-ca.json; fails if the count does not match the printed total.

Usage: python venues/stth-ca.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/stth-ca-lfe.pdf",
    "title": "Sha Tin Town Hall – Cultural Activities Hall, FULL Technical Information",
    "document_version": "V. 2026.07.02",
    "sha256": "83575aa51c87fdcba1f3837107feb49576be65db3ab7d6e6793dbb8071d1c97d",
    "retrieved": "2026-09-29",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}

rows = [row("A", ["W1", "W2"] + rng(3, 22) + ["W3", "W4"],
            marks=W("W1", "W2", "W3", "W4"), inferred={"W1": "1", "W2": "2", "W3": "23", "W4": "24"},
            note="A wheelchair box at each end of the row: two at seat 1's end (1-2) and two at the other (23-24).")]
rows += [row(lab, rng(1, n)) for lab, n in (("B", 28), ("C", 28))]
rows += [row(lab, rng(1, 24)) for lab in "DEFGHIJK"]
rows.append(row("L", rng(1, 26) + ["X1", "X2"], marks=X("X1", "X2"), inferred={"X1": "27", "X2": "28"},
                note="Two crossed management boxes, no number, end the row after 26, so they fill 27-28 exactly."))

finish({
    "venue": {"id": "stth-ca", "name_en": "Sha Tin Town Hall Cultural Activities Hall",
              "name_zh": "沙田大會堂 文娛廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/stth/common/files/stth_CA%20Hall%20Seating%20Plan%2020240730.pdf",
        "file": "stth_CA Hall Seating Plan 20240730.pdf",
        "sha256": "8e817f586fc7bb88d781c5a20edffd4572aa88a1d4453f03adec4f89ed6c5504",
        "plan_code": None,
        "printed_date": None,
        "applies": "Version as at Sep 2024",
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seat total",
        **TECH_SHEET,
        "quotes": ["Total Seating: 298", "Number of seating: 196 - 298"],
        "note": "Confirms the plan's printed total of 298, the room's maximum; the hall can also be set with fewer seats.",
    }],
    "location": location(geo_id="36310036", geo_name="Sha Tin Town Hall (Cultural Activities Hall)", lat=22.38136, lon=114.1899,
                         address_en="1 Yuen Wo Road, Sha Tin, New Territories, Hong Kong",
                         address_zh="香港新界沙田源禾路1號", district="Sha Tin", address_name="Sha Tin Town Hall"),
    "layout": {
        "seat_1_side": "right",
        "note": "Drawn with the stage at the top. Seat 1 is at the right-hand end of each row, and one block per row "
                "with no aisle. Rows A-L (row I included). The plan names no areas, only the space (文娛廳 CULTURAL "
                "ACTIVITIES HALL), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audiences on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Cultural Activities Hall": 298, "Total": 298},
    "zones": [
        {"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": rows},
    ],
})
