#!/usr/bin/env python3
"""Tuen Mun Town Hall, Cultural Activities Hall: seat facts read by hand from the LCSD seating plan.

The plan is a small JPEG (600x849, no text layer), so every row, block end and mark below was read
by eye from zoomed crops of it (sha256 in source). Writes data/tmth-ca.json; fails if the count does
not match the printed total.

Usage: python venues/tmth-ca.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

SHEET = {"publisher": LCSD, "retrieved": "2026-09-26", "document_version": "V. 2026.08.07"}
REFERENCES = [
    {
        "what": "Seat total",
        **SHEET,
        "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/tmth-ca-lfe.pdf",
        "title": "Tuen Mun Town Hall – Cultural Activities Hall, FULL Technical Information",
        "sha256": "eb99940d652c25d5f795d8bf943c176e675bdace91870a17e229b3993f3057c3",
        "quotes": ["Max. Total Seating: 290 The venue seats 290 on a fixed tier"],
        "note": "Confirms the plan's total. No wheelchair figure is given.",
    },
    {
        "what": "Orchestra pit",
        **SHEET,
        "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/tmth-ca-sfe.pdf",
        "title": "Tuen Mun Town Hall – Cultural Activities Hall, Basic Technical Information",
        "sha256": "b560acdf807067c4bcaa4d3868c9474e6cfb07caddbf174d777de5cca94bbcb8",
        "quotes": ["Orchestra pit None"],
        "note": "There is no orchestra pit.",
    },
]

rows = [
    row("A", ["X1", "W1", "W2"], rng(4, 16), ["W3", "W4", "X2"],
        marks={"X1": "X", "W1": "W", "W2": "W", "W3": "W", "W4": "W", "X2": "X"},
        inferred={"X1": "1", "W1": "2", "W2": "3"},
        note="The left block is a crossed management box and two wheelchair boxes (grey, W), under seats 1-3 of row B and "
             "before 4, so they are 1-3. The right block is two wheelchair boxes and a management box after 16 (17-19 "
             "likely, not printed)."),
    row("B", rng(1, 4), rng(5, 18), rng(19, 22)),
    row("C", rng(1, 4), rng(5, 17), rng(18, 21)),
]
rows += [row(lab, rng(1, 4), rng(5, 19), rng(20, 23)) for lab in "DEFGHJKLMN"]

finish({
    "venue": {"id": "tmth-ca", "name_en": "Tuen Mun Town Hall Cultural Activities Hall", "name_zh": "屯門大會堂 文娛廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/tmth/common/attachments/tc/cah/seatingplan2.jpg",
        "file": "seatingplan2.jpg",
        "sha256": "23e06286a613db49dea33a4de08d5384d7238f6dffb9d74549e3be850424b931",
        "plan_code": "revised Sept 2012",
        "printed_date": "2012-09",
        "credit": CREDIT,
    },
    "references": REFERENCES,
    "location": location(geo_id="76810049", geo_name="Tuen Mun Town Hall (Cultural Activities Hall)", lat=22.391810, lon=113.976771,
                         address_en="3 Tuen Hi Road, Tuen Mun, New Territories, Hong Kong",
                         address_zh="香港新界屯門屯喜路3號", district="Tuen Mun", address_name="Tuen Mun Town Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and numbering runs on through three blocks. The plan prints that rows A-C are on floor level and rows D-N on the platform. No row I. The plan names no seating areas with totals, only the space (文娛廳 CULTURAL ACTIVITIES HALL), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (grey box, W, no number)",
        "X": "Management seat (crossed box, no number)",
    },
    "printed_totals": {"Cultural Activities Hall": 290, "Total": 290},
    "zones": [
        {"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": rows,
         "sections": [{"name": "Floor level", "name_zh": "地面", "rows": ["A", "C"]},
                      {"name": "Platform", "name_zh": "級台", "rows": ["D", "N"]}]},
    ],
})
