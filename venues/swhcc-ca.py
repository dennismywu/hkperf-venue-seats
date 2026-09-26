#!/usr/bin/env python3
"""Sai Wan Ho Civic Centre, Cultural Activities Hall: seat facts for its two published seating layouts.

The hall is a flexible room with one seating plan per stage layout; each becomes its own seat list:
  swhcc-ca-end     end stage (plan_end.pdf), 110 seats
  swhcc-ca-thrust  thrust stage (plan_thrust.pdf), 100 seats
Both PDFs carry a text layer for every seat number and row label, on rotated pages. Seats were
chained box to box (n to n+1, nearest box) and each chain matched to the row label beside its first
seat; crossed management boxes were read by eye from zoomed renders (sha256 in source).
Writes data/swhcc-ca-end.json and data/swhcc-ca-thrust.json; fails if a count does not match.

Usage: python venues/swhcc-ca.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

REFERENCES = [{
    "what": "Seat totals for each layout",
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/swhcc-ca-lfe.pdf",
    "title": "Sai Wan Ho Civic Centre – Cultural Activities Hall, FULL Technical Information",
    "document_version": "V. 2026.05.28",
    "sha256": "c76908b02ac915f40685196714a77743f0adf1f0b0041bec73b8fcfb03f6ba7f",
    "retrieved": "2026-09-26",
    "quotes": ["Total Seating: End Stage: 110 seats Thrust Stage: 100 seats normally set-up within the booking period"],
    "note": "Confirms both plans' totals. Neither plan marks wheelchair seats, and no orchestra pit is described.",
}]
XS = ["X1", "X2"]
MARKS = {"X": "Management seat (crossed box, no number)"}


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"Sai Wan Ho Civic Centre Cultural Activities Hall ({layout_en})",
            "name_zh": f"西灣河文娛中心 文娛廳（{layout_zh}）"}


def source(file, sha):
    return {"publisher": LCSD, "url": f"https://www.lcsd.gov.hk/en/swhcc/common/forms/{file}", "file": file,
            "sha256": sha, "plan_code": None, "printed_date": None, "credit": CREDIT}


def loc():
    return location(geo_id="87710033", geo_name="Sai Wan Ho Civic Centre (Cultural Activities Hall)", lat=22.2818,
                    lon=114.222501, address_en="111 Shau Kei Wan Road, Hong Kong", address_zh="香港筲箕灣道111號",
                    district="Eastern", address_name="Sai Wan Ho Civic Centre")


# ---- end stage: one straight block per row
end = [row(lab, rng(1, n)) for lab, n in dict(A=8, B=8, C=7, D=9, E=9, F=9, G=8, H=8, J=7, K=7, L=8, M=8, N=8).items()]
end.append(row("O", rng(1, 6) + XS, marks={x: "X" for x in XS},
               note="Two crossed management boxes, no number, after 6 (7-8 likely, not printed)."))

# ---- thrust stage: a block on each side of the stage, angled towards it, and a centre block facing it
thrust = [
    row("A", rng(1, 7), rng(8, 16), rng(17, 24)),
    row("B", rng(1, 7), rng(8, 14), rng(15, 21)),
    row("C", rng(1, 7), rng(8, 13), rng(14, 19)),
    row("D", rng(1, 8), rng(9, 14), rng(15, 18)),
    row("E", rng(1, 6), rng(7, 13), rng(14, 16)),
    row("F", {"seats": rng(1, 2) + XS, "side": "left"}, marks={x: "X" for x in XS},
        note="Left side only: 1-2, then two crossed management boxes, no number (3-4 likely, not printed)."),
]


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}
    finish({
        "venue": venue("swhcc-ca-end", "end stage", "單向舞台"),
        "source": source("plan_end.pdf", "37a36f43b1c60cea0997607f72526fa962f22d19e9a55520441707ff7577ee11"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Drawn with the stage at the top. One straight block per row, rows A-O (no row I), seat 1 at the left; the rows are staggered by half a seat. This is one of the hall's seating layouts; the thrust-stage layout is a separate seat list.",
        },
        "printed_totals": {"Cultural Activities Hall": 110, "Total": 110},
        "zones": [{"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": end}],
    })
    finish({
        "venue": venue("swhcc-ca-thrust", "thrust stage", "三向舞台"),
        "source": source("plan_thrust.pdf", "18aad6614983e3fdf781c1e86037c524bb31ec46ebf4c2379c9b34455d8773a1"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "The audience sits on three sides of the stage: a block to the left, angled towards it, a block facing it, and a block to the right, angled towards it. Each row runs through all three: seat 1 is at the upstage end of the left block, numbering runs on through the centre block and back up the right block. Row F is on the left side only. This is one of the hall's seating layouts; the end-stage layout is a separate seat list.",
            "banks": [
                {"id": "left", "side": "left", "rows": [{"row": r, "block": 1} for r in "ABCDEF"], "seat_1": "upstage", "align": "downstage"},
                {"id": "centre", "side": "front", "rows": [{"row": r, "block": 2} for r in "ABCDE"], "seat_1": "left"},
                {"id": "right", "side": "right", "rows": [{"row": r, "block": 3} for r in "ABCDE"], "seat_1": "downstage", "align": "downstage"},
            ],
        },
        "printed_totals": {"Cultural Activities Hall": 100, "Total": 100},
        "zones": [{"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": thrust}],
    })


build()
