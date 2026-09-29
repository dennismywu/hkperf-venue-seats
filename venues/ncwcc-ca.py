#!/usr/bin/env python3
"""Ngau Chi Wan Civic Centre, Cultural Activities Hall: seat facts for its four published seating layouts.

The hall is a flexible room with one seating plan per stage layout, printed on the four pages of one
PDF; each becomes its own seat list:
  ncwcc-ca-end         end stage (p. 1), 93 seats
  ncwcc-ca-transverse  transverse stage (p. 2), 120 seats
  ncwcc-ca-thrust      thrust stage (p. 3), 119 seats
  ncwcc-ca-arena       arena stage (p. 4), 146 seats
Every seat number, W and row label is real text on the plans. Straight rows were read from the tokens on
each row's line and the upright side columns from the tokens in each label's column; the two crossed
management boxes in row AG and the four W in row AA were read by eye from zoomed renders (sha256 in
source). Writes the four data/*.json and .csv; fails if a count does not match.

Usage: python venues/ncwcc-ca.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/ncwcc-ca-lfe.pdf",
    "title": "Ngau Chi Wan Civic Centre – Cultural Activities Hall, FULL Technical Information",
    "document_version": "V. 2026.03.12",
    "sha256": "d48d030790c738143ef06c2b1a172f77e8e84fcaa283e8c01f83cd58c6be33fb",
    "retrieved": "2026-09-29",
}
REFERENCES = [{
    "what": "Seat totals for each layout",
    **TECH_SHEET,
    "quotes": ["End stage 93 seats", "Transverse stage 120 seats", "Thrust stage 119 seats", "Arena stage 146 seats"],
    "note": "Confirms all four plans' totals. No orchestra pit is described.",
}]
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}
MARKS = {
    "W": "Seat suitable for audiences on wheelchairs (box prints W, no number)",
    "X": "Management seat (crossed box, no number)",
}
WS = ["W1", "W2", "W3", "W4"]
XS = ["X1", "X2"]


def loc():
    return location(geo_id="87410028", geo_name="Ngau Chi Wan Civic Centre (Cultural Activities Hall)",
                    lat=22.334583, lon=114.208766,
                    address_en="2/F & 3/F, Ngau Chi Wan Municipal Services Building, 11 Clear Water Bay Road, Kowloon, Hong Kong",
                    address_zh="香港九龍清水灣道11號牛池灣市政大廈2樓及3樓", district="Wong Tai Sin",
                    address_name="Ngau Chi Wan Civic Centre")


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"Ngau Chi Wan Civic Centre Cultural Activities Hall ({layout_en})",
            "name_zh": f"牛池灣文娛中心 文娛廳（{layout_zh}）"}


def source():
    return {"publisher": LCSD, "url": "https://www.lcsd.gov.hk/en/ncwcc/common/form/ncwcc_seating_ca.pdf",
            "file": "ncwcc_seating_ca.pdf", "sha256": "ef36e8273af99232984a94a5c048409f5abb38ade46edeb9744873472be47912",
            "plan_code": None, "printed_date": None, "credit": CREDIT}


# ---- the house that faces the stage from the front (rows AA-AG), the same on every page; seat 1 at the right
near = [
    row("AA", WS + rng(5, 9), marks=W(*WS), inferred={"W1": "1", "W2": "2", "W3": "3", "W4": "4"},
        note="Four wheelchair boxes print W, no number, at seat 1's end, between nothing and 5, so they fill 1-4 exactly."),
    row("AB", rng(1, 12)),
    row("AC", rng(1, 14)),
    row("AD", rng(1, 13)),
    row("AE", rng(1, 16)),
    row("AF", rng(1, 15)),
    row("AG", XS + rng(3, 16), marks=X(*XS), inferred={"X1": "1", "X2": "2"},
        note="Two crossed management boxes, no number, at seat 1's end, between nothing and 3, so they fill 1-2 exactly."),
]

# ---- the house on the far side of a transverse or arena stage (rows CA-CC), seat 1 at the left
far = [row(lab, rng(1, n)) for lab, n in (("CA", 8), ("CB", 10), ("CC", 9))]

# ---- the upright columns along each side of a thrust or arena stage; seat 1 at the bottom (downstage)
left_cols = [row(lab, rng(1, n)) for lab, n in (("BA", 4), ("BB", 3), ("BC", 6))]
right_cols = [row(lab, rng(1, n)) for lab, n in (("DA", 4), ("DB", 3), ("DC", 6))]


def blocks(rows, block=1):
    return [{"row": r["row"], "block": block} for r in rows]


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}

    finish({
        "venue": venue("ncwcc-ca-end", "end stage", "單向舞台"),
        "source": source(),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "Drawn with the stage at the top. On page 1 of the plan (end stage): seven straight rows, AA-AG, one block each, seat 1 at the right-hand "
                    "end and numbering rising to the left. This is one of the hall's seating layouts; the other three are "
                    "separate seat lists.",
        },
        "printed_totals": {"Cultural Activities Hall": 93, "Total": 93},
        "zones": [{"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": near}],
    })

    finish({
        "venue": venue("ncwcc-ca-transverse", "transverse stage", "橫向舞台"),
        "source": source(),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "On page 2 of the plan (transverse stage): seating on opposite sides of the stage, rows CA-CC face the stage from the far side (seat 1 at the "
                    "left), and rows AA-AG from the near side (seat 1 at the right). Row CA is nearest the stage. This is "
                    "one of the hall's seating layouts; the other three are separate seat lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "right", "rows": blocks(near)},
                {"id": "back", "side": "back", "seat_1": "left", "rows": blocks(far)},
            ],
        },
        "printed_totals": {"Cultural Activities Hall": 120, "Total": 120},
        "zones": [{"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": far + near}],
    })

    finish({
        "venue": venue("ncwcc-ca-thrust", "thrust stage", "三向舞台"),
        "source": source(),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "On page 3 of the plan (thrust stage): seating on three sides. Rows AA-AG face the stage from the front (seat 1 at the right); upright "
                    "columns stand along each side of the stage, numbered from the bottom (downstage): BA, BB, BC on the "
                    "left, DA, DB, DC on the right, each nearest the stage first. This is one of the hall's seating "
                    "layouts; the other three are separate seat lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "right", "rows": blocks(near)},
                {"id": "left", "side": "left", "rows": blocks(left_cols), "seat_1": "downstage",
                 "align": "downstage"},
                {"id": "right", "side": "right", "rows": blocks(right_cols), "seat_1": "downstage",
                 "align": "downstage"},
            ],
        },
        "printed_totals": {"Cultural Activities Hall": 119, "Total": 119},
        "zones": [{"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": near + left_cols + right_cols}],
    })

    finish({
        "venue": venue("ncwcc-ca-arena", "arena stage", "中央舞台"),
        "source": source(),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "On page 4 of the plan (arena stage): seating on all four sides. Rows AA-AG face the stage from the front (seat 1 at the right) and rows "
                    "CA-CC from the far side (seat 1 at the left, row CA nearest the stage); upright columns stand along "
                    "each side, numbered from the bottom (downstage): BA, BB, BC on the left, DA, DB, DC on the right, each "
                    "nearest the stage first. This is one of the hall's seating layouts; the other three are separate seat "
                    "lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "right", "rows": blocks(near)},
                {"id": "back", "side": "back", "seat_1": "left", "rows": blocks(far)},
                {"id": "left", "side": "left", "rows": blocks(left_cols), "seat_1": "downstage",
                 "align": "downstage"},
                {"id": "right", "side": "right", "rows": blocks(right_cols), "seat_1": "downstage",
                 "align": "downstage"},
            ],
        },
        "printed_totals": {"Cultural Activities Hall": 146, "Total": 146},
        "zones": [{"name": "Cultural Activities Hall", "name_zh": "文娛廳", "rows": far + near + left_cols + right_cols}],
    })


build()
