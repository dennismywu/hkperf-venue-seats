#!/usr/bin/env python3
"""Tsuen Wan Town Hall, Cultural Activities Hall: seat facts read from the LCSD seating plan.

The plan PDF carries a text layer for every seat number, W, X and row label; each row was read from
the tokens on its label's line and checked by eye (sha256 in source).
Writes data/twth-ca.json; fails if the count does not match the printed total.

Usage: python venues/twth-ca.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/twth-ca-lfe.pdf",
    "title": "Tsuen Wan Town Hall – Cultural Activities Hall, FULL Technical Information",
    "document_version": "V. 2026.07.20",
    "sha256": "4bc97b373dba8905831aed3888f8f05fef93b5371166c2c5ad5edbdb1d3b6a43",
    "retrieved": "2026-09-26",
}
REFERENCES = [{
    "what": "Seat total, floor and platform, wheelchair seats",
    **TECH_SHEET,
    "quotes": ["Total Seating: 260 - 49 on flat floor (including 4 wheelchair seats) - 211 on retractable seating platform"],
    "note": "Confirms the plan's total. Rows A-C hold 45 numbered seats and the 4 wheelchair boxes (49, the flat floor); rows D-N hold 211 (the platform). No orchestra pit is described.",
}]

rows = [row("A", rng(1, 16) + ["W1", "W2", "W3", "W4"], marks={f"W{i}": "W" for i in range(1, 5)},
            note="Four wheelchair boxes, W with no number, end the row after 16 (17-20 likely, not printed).")]
rows += [row(lab, rng(1, n)) for lab, n in dict(B=13, C=16, D=18, E=19, F=20, G=21, H=22, J=21, K=22, L=22, M=22).items()]
rows.append(row("N", ["X1", "X2"] + rng(3, 26), marks={"X1": "X", "X2": "X"}, inferred={"X1": "1", "X2": "2"},
                note="Two management boxes, X with no number, open the row before 3, so they are 1-2."))

finish({
    "venue": {"id": "twth-ca", "name_en": "Tsuen Wan Town Hall Cultural Activities Hall", "name_zh": "荃灣大會堂 文娛廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/tc/twth/attachments/culturalactivitieshall/twth-cultural-act-hall2012.pdf",
        "file": "twth-cultural-act-hall2012.pdf",
        "sha256": "ac0364d4349e6a80dda2827fdc32ae69d023a310c2466dd16d034786c39902b7",
        "plan_code": "Version as at 10 Nov 2011",
        "printed_date": "2011-11-10",
        "credit": CREDIT,
    },
    "references": REFERENCES,
    "location": location(geo_id="87210046", geo_name="Tsuen Wan Town Hall (Cultural Activities Hall)", lat=22.37109, lon=114.11277,
                         address_en="72 Tai Ho Road, Tsuen Wan, New Territories, Hong Kong",
                         address_zh="香港新界荃灣大河道72號", district="Tsuen Wan", address_name="Tsuen Wan Town Hall"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. One straight block per row, seat 1 at the left; rows are centred, so their ends step in and out. Per the technical sheet, rows A-C are on the flat floor and rows D-N on a retractable seating platform. No row I. The plan names no seating areas, only the space (文娛廳 CULTURAL ACTIVITIES HALL), so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
        "X": "Management seat (box prints X, no number)",
    },
    "printed_totals": {"Cultural Activities Hall": 260, "Total": 260},
    "zones": [
        {"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": rows,
         "sections": [{"name": "Flat floor", "name_zh": "水平面", "rows": ["A", "C"]},
                      {"name": "Retractable seating platform", "name_zh": "電動折合式單向觀眾席", "rows": ["D", "N"]}]},
    ],
})
