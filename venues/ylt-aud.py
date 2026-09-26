#!/usr/bin/env python3
"""Yuen Long Theatre Auditorium: seat facts read by hand from the LCSD seating plan.

The plan is a 150 dpi JPEG (no vector data, and too coarse for tools/seatplan.py), so every row end,
row label and mark below was read by eye from zoomed crops of it (sha256 in source).
Writes data/ylt-aud.json; fails if the counts do not match the printed or stated totals.

Usage: python venues/ylt-aud.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/ylt-aud-sfe.pdf",
    "title": "Yuen Long Theatre Auditorium, Basic Information",
    "document_version": "V. 2026.08.07",
    "sha256": "2e2afb6b23cf02881e1bf71b4b2dcbfd648b2d165702dadd786be74483e05325",
    "retrieved": "2026-09-26",
}

stalls = []
for lab, n in dict(A=15, B=20, C=23, D=26, E=31, F=34, G=37, H=36, J=35, K=36, L=35, M=34).items():
    stalls.append(row(lab, rng(1, n)))
stalls.append(row("N", ["X1", "X2"] + rng(3, 33), marks={"X1": "X", "X2": "X"},
                  inferred={"X1": "1", "X2": "2"},
                  note="Two management boxes print no number. They sit before seat 3, so they fill 1-2 exactly."))
for lab, n in dict(O=32, P=33, Q=34, R=35, S=34, T=35, U=34, V=33, W=34).items():
    stalls.append(row(lab, rng(1, n)))
stalls.append(row("X", rng(1, 33) + ["X1", "X2"], marks={"X1": "X", "X2": "X"},
                  note="Two management boxes print no number. They follow seat 33 at the row end; 34-35 is likely (wheelchair seats Y34-Y35 sit below them) but not printed."))
stalls.append(row("Y", ["1", "2"], ["34", "35"], marks={s: "W" for s in ["1", "2", "34", "35"]},
                  note="Wheelchair spaces only, at both ends of the row. The boxes print W; the legend prints their numbers (Y1, Y2, Y34, Y35)."))

balcony = []
for lab, k in dict(BA=3, BB=2, BC=3, BD=2).items():
    seats = rng(1, 2 * k)
    balcony.append(row(lab, {"side": "left", "area": "Left Box 左廂座", "seats": seats[:k]},
                       {"side": "right", "area": "Right Box 右廂座", "seats": seats[k:]},
                       marks={s: "R" for s in seats},
                       note="Side boxes printed as Left Box and Right Box; numbering runs on from the left box to the right box."))
balcony.append(row("BE", rng(1, 35), marks={s: "R" for s in rng(1, 35)},
                   note="The whole front balcony row is drawn with the restricted-sightline outline."))
for lab, n in dict(BF=36, BG=37).items():
    balcony.append(row(lab, rng(1, n)))
balcony.append(row("BH", rng(1, 34), marks={"33": "W", "34": "W"},
                   note="Seats 33-34 are wheelchair spaces. The boxes print W; the legend prints their numbers (BH33, BH34)."))
balcony.append(row("BJ", rng(1, 27)))

finish({
    "venue": {"id": "ylt-aud", "name_en": "Yuen Long Theatre Auditorium", "name_zh": "元朗劇院 演藝廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/ylt/common/images/floorplan/aud-seatplan.jpg",
        "page": "https://www.lcsd.gov.hk/tc/ylt/facilities/auditorium/floorplan.html",
        "page_revised": "2021-06-17",
        "file": "aud-seatplan.jpg",
        "sha256": "8cf354ea8d654a2e1e6dc8cf2181a37de69fc7f521d444269525ac1eba31d71e",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "location": location(geo_id="87310051", geo_name="Yuen Long Theatre (Auditorium)", lat=22.44152, lon=114.02289,
                         address_en="9 Yuen Long Tai Yuk Road, Yuen Long, New Territories, Hong Kong",
                         address_zh="香港新界元朗體育路9號", district="Yuen Long", address_name="Yuen Long Theatre"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the stage at the top. Seat 1 is at the left-hand end of each row, and blocks are listed from that side. No row I in the stalls; no row BI in the balcony. Row Y holds only the four wheelchair spaces, under the two ends of row X.",
    },
    "marks": {
        "W": "Wheelchair seat (box prints W; numbers given in the legend where printed)",
        "X": "Management seat (box prints a bold X, no number)",
        "R": "Seat with restricted sightline (heavy outline)",
    },
    "printed_totals": {"Stalls": 734, "Balcony": 189, "Total": 923},
    "orchestra_pits": [
        {
            "name": "Small pit (60 m²)",
            "rows_removed": ["A", "B"],
            "rows_basis": "inferred",
            "rows_reasoning": "The sheet gives the seats lost, not the rows. A + B = 15 + 20 = 35, and no other run of front rows gives 35 (A = 15, A-C = 58).",
            "stated": {"seats_removed": 35},
            "source": {**TECH_SHEET, "quote": "Small pit 60 m2 with a loss of 35 seats"},
        },
        {
            "name": "Large pit (95 m²)",
            "rows_removed": ["A", "B", "C", "D"],
            "rows_basis": "inferred",
            "rows_reasoning": "The sheet gives the seats lost, not the rows. A-D = 15 + 20 + 23 + 26 = 84, and no other run of front rows gives 84 (A-C = 58, A-E = 115).",
            "stated": {"seats_removed": 84},
            "source": {**TECH_SHEET, "quote": "Large pit 95 m2 with a loss of 84 seats"},
        },
    ],
    "zones": [
        {"name": "Stalls", "name_zh": "堂座", "rows": stalls},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
