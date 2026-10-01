#!/usr/bin/env python3
"""Tai Po Civic Centre, Black Box Theatre: seat facts for its three published seating layouts.

The Black Box Theatre is a flexible room with one seating plan per stage layout; each becomes its own
seat list:
  tpcc-bb-end     end stage (bbt1.pdf), 130 seats
  tpcc-bb-tv      transverse stage (bbt2.pdf), 123 seats
  tpcc-bb-thrust  thrust stage (bbt3.pdf), 123 seats
The plans have no text layer (every figure is outlined), so the rows, seat numbers, W and X boxes were
read by eye from zoomed, upright renders, with the seat boxes taken from the PDF's own rectangles by
tools/draft_rows.py (sha256 in source). Writes the three data/*.json and .csv; fails if a count does not
match.

Usage: python venues/tpcc-bb.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/tpcc-bbt-lfe.pdf",
    "title": "Tai Po Civic Centre – Black Box Theatre, FULL Technical Information",
    "document_version": "V. 2026.09.01",
    "sha256": "a175c54c5ab5e5641847c982314e302686704b53e9491faed8b0ba0403cc83c4",
    "retrieved": "2026-10-01",
}
REFERENCES = [{
    "what": "Seat totals for each layout",
    **TECH_SHEET,
    "quotes": ["End Stage: 130 seats", "Transverse Stage :123 seats", "Thrust Stage: 123 seats"],
    "note": "Confirms all three plans' printed totals. No orchestra pit is described.",
}]
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}
MARKS = {
    "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
    "X": "Management seat (crossed box, no number)",
}


def loc():
    return location(geo_id="35510044", geo_name="Tai Po Civic Centre (Black Box Theatre)", lat=22.45175,
                    lon=114.16815, address_en="12 On Pong Road, Tai Po, New Territories, Hong Kong",
                    address_zh="香港新界大埔安邦路12號", district="Tai Po", address_name="Tai Po Civic Centre")


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"Tai Po Civic Centre Black Box Theatre ({layout_en})",
            "name_zh": f"大埔文娛中心 黑盒劇場（{layout_zh}）"}


def source(file, sha):
    return {"publisher": LCSD, "url": f"https://www.lcsd.gov.hk/en/tpcc/common/doc/{file}", "file": file,
            "sha256": sha, "plan_code": None, "printed_date": None, "credit": CREDIT}


def blocks(rows, block=1):
    return [{"row": r["row"], "block": block} for r in rows]


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}

    # ---- the house that faces the stage from the front (end and near sides), seat 1 at the left
    w_note = ("Two wheelchair boxes print W, no number, at each end of the row: 1-2 before the printed 3, "
              "and 11-12 after the printed 10.")
    x_note = ("Two crossed management boxes, no number, at seat 1's end, between nothing and 3, so they "
              "fill 1-2 exactly.")
    end_rows = [
        row("A", ["W1", "W2"] + rng(3, 10) + ["W3", "W4"], marks=W("W1", "W2", "W3", "W4"),
            inferred={"W1": "1", "W2": "2", "W3": "11", "W4": "12"}, note=w_note),
        row("B", rng(1, 15)), row("C", rng(1, 14)), row("D", rng(1, 15)), row("E", rng(1, 14)),
        row("F", rng(1, 15)), row("G", rng(1, 14)), row("H", rng(1, 15)),
        row("J", ["X1", "X2"] + rng(3, 18), marks=X("X1", "X2"), inferred={"X1": "1", "X2": "2"},
            note=x_note),
    ]
    near = [
        row("A", ["W1", "W2"] + rng(3, 10) + ["W3", "W4"], marks=W("W1", "W2", "W3", "W4"),
            inferred={"W1": "1", "W2": "2", "W3": "11", "W4": "12"}, note=w_note),
        row("B", rng(1, 15)), row("C", rng(1, 14)), row("D", rng(1, 15)), row("E", rng(1, 14)),
        row("F", ["X1", "X2"] + rng(3, 15), marks=X("X1", "X2"), inferred={"X1": "1", "X2": "2"},
            note=x_note),
    ]
    # rows on the far side of a transverse stage, seat 1 at the right (numbers fall to the left)
    far = [row("AA", rng(1, 12)), row("AB", rng(1, 12)), row("AC", rng(1, 16))]
    # side rows of a thrust stage: the plan uses one letter a side, its two columns numbered on end, the
    # right column from seat 1 at the downstage end, the left column carrying the numbers the right
    # column leaves (block 1 is the right column, block 2 the left)
    side = [row("AA", rng(1, 6), rng(7, 12)), row("AB", rng(1, 6), rng(7, 12)),
            row("AC", rng(1, 8), rng(9, 16))]

    finish({
        "venue": venue("tpcc-bb-end", "end stage", "單向舞台"),
        "source": source("bbt1.pdf", "f1d7d74ca6eab5e03020a619795feed3779896ab292f3eba9c13641e031d73f1"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Drawn with the stage at the top. One bank of rows faces it, seat 1 at the left-hand "
                    "end of each row and numbering rising to the right. Rows A-J with no row I; the two "
                    "side walls step in at the front (the empty cells beside the number boxes are not "
                    "seats). This is one of the room's seating layouts; the transverse- and thrust-stage "
                    "layouts are separate seat lists.",
        },
        "printed_totals": {"Black Box Theatre": 130, "Total": 130},
        "zones": [{"name": "Black Box Theatre", "name_zh": "黑盒劇場", "rows": end_rows}],
    })

    finish({
        "venue": venue("tpcc-bb-tv", "transverse stage", "橫向舞台"),
        "source": source("bbt2.pdf", "5ccfe726b243e68c9a54257768b1e1439c030e1ed0b31c14154bab5cd8a668e9"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Seating on two opposite sides of the stage. Rows A-F face the stage from the near "
                    "side (seat 1 at the left) and rows AA, AB, AC from the far side (seat 1 at the "
                    "right, AA nearest the stage), each split by an aisle. This is one of the room's "
                    "seating layouts; the end- and thrust-stage layouts are separate seat lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "left", "rows": blocks(near)},
                {"id": "back", "side": "back", "seat_1": "right", "rows": blocks(far)},
            ],
        },
        "printed_totals": {"Black Box Theatre": 123, "Total": 123},
        "zones": [{"name": "Black Box Theatre", "name_zh": "黑盒劇場", "rows": far + near}],
    })

    finish({
        "venue": venue("tpcc-bb-thrust", "thrust stage", "三向舞台"),
        "source": source("bbt3.pdf", "1966dc2635e519104478204f9354f11106b02d4ab7835b86be568e7712ab9d94"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Seating on three sides. Rows A-F face the stage from the front (seat 1 at the left); "
                    "upright columns stand along each side, named AA, AB, AC on both, nearest the stage "
                    "first. On the right the numbers run from seat 1 at the downstage (bottom) end; on "
                    "the left they carry on (AA, AB: 7-12; AC: 9-16), so each side row is one row in two "
                    "columns, block 1 on the right and block 2 on the left. This is one of the room's "
                    "seating layouts; the end- and transverse-stage layouts are separate seat lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "left", "rows": blocks(near)},
                {"id": "left", "side": "left", "seat_1": "upstage", "align": "upstage",
                 "rows": blocks(side, block=2)},
                {"id": "right", "side": "right", "seat_1": "downstage", "align": "upstage",
                 "rows": blocks(side, block=1)},
            ],
        },
        "printed_totals": {"Black Box Theatre": 123, "Total": 123},
        "zones": [{"name": "Black Box Theatre", "name_zh": "黑盒劇場", "rows": near + side}],
    })


build()
