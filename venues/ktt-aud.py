#!/usr/bin/env python3
"""Kwai Tsing Theatre Auditorium: seat facts read by hand from the LCSD seating plan.

Every row end, row label and mark below was checked by eye against zoomed renders of the plan
(sha256 in source). Writes data/ktt-aud.json; fails if the counts do not match the printed totals.

Usage: python venues/ktt-aud.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

stalls_ends = dict(A=15, B=24, C=27, D=28, E=33, F=34, G=37, H=40, J=41, K=42, L=41, M=44, N=45, O=46, P=47)
stalls = []
for lab, n in stalls_ends.items():
    if lab == "H":
        stalls.append(row("H", rng(1, n), marks={"1": "X", "2": "X"}))
    else:
        stalls.append(row(lab, rng(1, n)))
stalls.append(row("Q", ["W1", "W2"] + rng(3, 44) + ["W3", "W4"],
                  marks={w: "W" for w in ["W1", "W2", "W3", "W4"]},
                  inferred={"W1": "1", "W2": "2"},
                  note="Four wheelchair boxes print no number. W1-W2 sit before seat 3, so they fill 1-2 exactly. W3-W4 follow seat 44 at the row end; 45-46 is likely but not printed."))
stalls.append(row("R", rng(1, 13), rng(14, 26), rng(27, 39), marks={"1": "X", "2": "X"},
                  note="Three blocks: 1-13 right, 14-26 centre, 27-39 left."))

side = dict(BA=2, BB=2, BC=3, BD=3)
balcony = []
for lab, k in side.items():
    seats = rng(1, 2 * k)
    balcony.append(row(lab, {"side": "right", "seats": seats[:k]}, {"side": "left", "seats": seats[k:]},
                       marks={s: "R" for s in seats},
                       note="Side box pair on the side walls, drawn between the stalls and the balcony."))
for lab, n in dict(BE=49, BF=50, BG=51, BH=52).items():
    balcony.append(row(lab, rng(1, n)))
balcony.append(row("BJ", ["W1", "W2"] + rng(3, 52), marks={"W1": "W", "W2": "W"},
                   inferred={"W1": "1", "W2": "2"},
                   note="Two wheelchair boxes print no number; they sit before seat 3, so they fill 1-2 exactly."))

finish({
    "venue": {"id": "ktt-aud", "name_en": "Kwai Tsing Theatre Auditorium", "name_zh": "葵青劇院 演藝廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/ktt/common/files/ktt-aud.pdf",
        "file": "ktt-aud.pdf",
        "sha256": "7fbe41129683cfb2a703d7851cec5e5d83617a1c9e35278bd34e2d31ad1b0a2d",
        "plan_code": "Auditorium.7a",
        "printed_date": None,
        "credit": CREDIT,
    },
    "location": location(geo_id="87110023", geo_name="Kwai Tsing Theatre (Auditorium)", lat=22.35665, lon=114.12623,
                         address_en="12 Hing Ning Road, Kwai Chung, New Territories, Hong Kong",
                         address_zh="香港新界葵涌興寧路12號", district="Kwai Tsing", address_name="Kwai Tsing Theatre"),
    "layout": {
        "seat_1_side": "right",
        "note": "Drawn with the stage at the top. Seat 1 is at the right-hand end of each row, and blocks are listed from that side. No row I in the stalls; no row BI in the balcony.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchair (box prints W, no number)",
        "X": "Management seat (number printed under a cross)",
        "R": "Seat with restricted sightline (double outline)",
    },
    "printed_totals": {"Stalls": 625, "Balcony": 274, "Total": 899},
    "orchestra_pits": [{
        "name": "Orchestra pit",
        "rows_removed": ["A", "B", "C"],
        "rows_basis": "inferred",
        "rows_reasoning": "The source gives only the reduced total, not the rows. 899 - 833 = 66, and A + B + C = 15 + 24 + 27 = 66; no other run of front rows gives 66 (A = 15, A-B = 39, A-D = 94). None of these seats is a management seat.",
        "stated": {"total_with_pit": 833},
        "source": {
            "publisher": LCSD,
            "url": "https://www.lcsd.gov.hk/en/ktt/facilities/auditorium.html",
            "quote": "833 seats if the orchestra pit is in use",
            "page_revised": "2022-09-16",
            "retrieved": "2026-09-26",
        },
    }],
    "zones": [
        {"name": "Stalls", "name_zh": "堂座", "rows": stalls},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony},
    ],
})
