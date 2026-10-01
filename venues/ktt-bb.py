#!/usr/bin/env python3
"""Kwai Tsing Theatre, Black Box Theatre: seat facts for its three published seating layouts.

The Black Box Theatre is a flexible room with one seating plan per stage layout; each becomes its own
seat list:
  ktt-bb-tv      transverse stage (BBT_TransverseStage.pdf), 130 seats
  ktt-bb-thrust  thrust stage (BBT_ThrustStage.pdf), 150 seats
  ktt-bb-arena   arena stage (BBT_SeatingPlan-ALL.pdf), 160 seats
The plans have no text layer (every figure is outlined), so the rows and columns were read by eye from
zoomed renders, with the seat boxes taken from the PDF's own rectangles and each column's cross-aisle
found from the gap in its boxes (sha256 in source). On the two side banks the rows run upright and are
split into two blocks by that aisle: the left columns (DA, DC, DE, DG) number from the top, the right
columns (BA, BC, BE, BG) from the bottom. Writes the three data/*.json and .csv; fails if a count does
not match.

Usage: python venues/ktt-bb.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/ktt-bb-lfe.pdf",
    "title": "Kwai Tsing Theatre – Black Box Theatre, FULL Technical Information",
    "document_version": "V. 2026.07.20",
    "sha256": "7168ae28c93465e1d0f4d9fb5c722ea654d58d09b79db36382e0d028ffd813fb",
    "retrieved": "2026-09-29",
}
REFERENCES = [{
    "what": "Seat totals for each layout",
    **TECH_SHEET,
    "quotes": ["Transverse Stage: 130 seats", "Thrust Stage: 150 seats", "Arena Stage: 160 seats"],
    "note": "Confirms all three plans' totals. No orchestra pit is described.",
}]
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}
MARKS = {
    "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
    "X": "Management seat (crossed box, no number)",
}


def loc():
    return location(geo_id="87112562", geo_name="Kwai Tsing Theatre (Black Box Theatre)", lat=22.35665, lon=114.12623,
                    address_en="12 Hing Ning Road, Kwai Chung, New Territories, Hong Kong",
                    address_zh="香港新界葵涌興寧路12號", district="Kwai Tsing", address_name="Kwai Tsing Theatre")


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"Kwai Tsing Theatre Black Box Theatre ({layout_en})",
            "name_zh": f"葵青劇院 黑盒劇場（{layout_zh}）"}


def source(file, sha):
    return {"publisher": LCSD, "url": f"https://www.lcsd.gov.hk/en/ktt/common/files/{file}", "file": file,
            "sha256": sha, "plan_code": None, "printed_date": None, "credit": CREDIT}


def whole(rows):
    """One bank row reference per hall row; the viewer draws all of the row's blocks together."""
    return [{"row": r["row"]} for r in rows]


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}

    # ---- transverse stage: seating on two opposite sides, no straight rows
    tv_left = [
        row("DA", rng(1, 6), rng(7, 14) + ["W1", "W2"], marks=W("W1", "W2"), inferred={"W1": "15", "W2": "16"},
            note="Two wheelchair boxes, no number, end the column after 14; a cross-aisle divides the column after 6."),
        row("DC", rng(1, 6), rng(7, 15), note="A cross-aisle divides the column after 6."),
        row("DE", rng(1, 6), rng(7, 16), note="A cross-aisle divides the column after 6."),
        row("DG", rng(1, 7), rng(8, 17) + ["X1", "X2"], marks=X("X1", "X2"), inferred={"X1": "18", "X2": "19"},
            note="Two crossed management boxes, no number, end the column after 17; a cross-aisle divides it after 7."),
    ]
    tv_right = [
        row("BA", ["W1", "W2"] + rng(3, 10), rng(11, 16), marks=W("W1", "W2"), inferred={"W1": "1", "W2": "2"},
            note="Two wheelchair boxes, no number, at seat 1's end; a cross-aisle divides the column after 10."),
        row("BC", rng(1, 9), rng(10, 15), note="A cross-aisle divides the column after 9."),
        row("BE", rng(1, 10), rng(11, 16), note="A cross-aisle divides the column after 10."),
        row("BG", rng(1, 12), rng(13, 19), note="A cross-aisle divides the column after 12."),
    ]
    finish({
        "venue": venue("ktt-bb-tv", "transverse stage", "橫向舞台"),
        "source": source("BBT_TransverseStage.pdf", "39df8391dbae774a530b760cdb550c48a54a2cf78188f47f29c99da39d84815b"),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "Seating on two opposite sides of the stage. Upright columns: DA, DC, DE, DG on the left (DA "
                    "nearest the stage) with seat 1 at the top, and BA, BC, BE, BG on the right (BA nearest the "
                    "stage) with seat 1 at the bottom. A cross-aisle cuts each column into two blocks. This is one "
                    "of the room's seating layouts; the thrust- and arena-stage layouts are separate seat lists.",
            "banks": [
                {"id": "left", "side": "left", "seat_1": "upstage", "rows": whole(tv_left)},
                {"id": "right", "side": "right", "seat_1": "downstage", "rows": whole(tv_right)},
            ],
        },
        "printed_totals": {"Black Box Theatre": 130, "Total": 130},
        "zones": [{"name": "Black Box Theatre", "name_zh": "黑盒劇場", "rows": tv_left + tv_right}],
    })

    # ---- thrust stage: three sides, plus four straight front rows
    th_front = [
        row("CA", rng(1, 6), rng(7, 12), note="One row with an aisle after 6."),
        row("CC", ["X1", "X2"] + rng(3, 8), rng(9, 16), marks=X("X1", "X2"), inferred={"X1": "1", "X2": "2"},
            note="Two crossed management boxes, no number, at seat 1's end; an aisle after 8."),
        row("CE", rng(1, 7), rng(8, 14), note="One row with an aisle after 7."),
        row("CG", rng(1, 8), rng(9, 16), note="One row with an aisle after 8."),
    ]
    th_left = [
        row("DA", rng(1, 6), rng(7, 10) + ["W1", "W2"], marks=W("W1", "W2"), inferred={"W1": "11", "W2": "12"},
            note="Two wheelchair boxes, no number, end the column after 10; a cross-aisle divides the column after 6."),
        row("DC", rng(1, 5), rng(6, 11), note="A cross-aisle divides the column after 5."),
        row("DE", rng(1, 6), rng(7, 12), note="A cross-aisle divides the column after 6."),
        row("DG", rng(1, 6), rng(7, 12), note="A cross-aisle divides the column after 6."),
    ]
    th_right = [
        row("BA", ["W1", "W2"] + rng(3, 6), rng(7, 12), marks=W("W1", "W2"), inferred={"W1": "1", "W2": "2"},
            note="Two wheelchair boxes, no number, at seat 1's end; a cross-aisle divides the column after 6."),
        row("BC", rng(1, 6), rng(7, 11), note="A cross-aisle divides the column after 6."),
        row("BE", rng(1, 6), rng(7, 12), note="A cross-aisle divides the column after 6."),
        row("BG", rng(1, 6), rng(7, 12), note="A cross-aisle divides the column after 6."),
    ]
    finish({
        "venue": venue("ktt-bb-thrust", "thrust stage", "三向舞台"),
        "source": source("BBT_ThrustStage.pdf", "f4b284d0aa93152488d2e43ba0d8a6afb36547b651bc10dfc9a7f0d82ab5911c"),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "Seating on three sides. Rows CA, CC, CE, CG face the stage from the front (seat 1 at the left, "
                    "each split by an aisle); upright columns stand along each side: DA, DC, DE, DG on the left (DA "
                    "nearest the stage) with seat 1 at the top, and BA, BC, BE, BG on the right (BA nearest the "
                    "stage) with seat 1 at the bottom, each cut by a cross-aisle into two blocks. This is one of the "
                    "room's seating layouts; the transverse- and arena-stage layouts are separate seat lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "left", "rows": whole(th_front)},
                {"id": "left", "side": "left", "seat_1": "upstage", "rows": whole(th_left)},
                {"id": "right", "side": "right", "seat_1": "downstage", "rows": whole(th_right)},
            ],
        },
        "printed_totals": {"Black Box Theatre": 150, "Total": 150},
        "zones": [{"name": "Black Box Theatre", "name_zh": "黑盒劇場", "rows": th_front + th_left + th_right}],
    })

    # ---- arena stage: all four sides
    ar_front = [
        row("CA", rng(1, 5), rng(6, 10), note="One row with an aisle after 5."),
        row("CC", ["X1", "X2"] + rng(3, 6), rng(7, 12), marks=X("X1", "X2"), inferred={"X1": "1", "X2": "2"},
            note="Two crossed management boxes, no number, at seat 1's end; an aisle after 6."),
        row("CE", rng(1, 6), rng(7, 12), note="One row with an aisle after 6."),
        row("CG", rng(1, 7), rng(8, 14), note="One row with an aisle after 7."),
    ]
    ar_back = [
        row("AA", rng(1, 6), rng(7, 12), note="One row with an aisle after 6; seat 1 at the right."),
        row("AC", rng(1, 6), rng(7, 12), note="One row with an aisle after 6; seat 1 at the right."),
        row("AE", rng(1, 7), rng(8, 14), note="One row with an aisle after 7; seat 1 at the right."),
    ]
    ar_left = [
        row("DG", rng(1, 5), rng(6, 10), note="A cross-aisle divides the column after 5."),
        row("DE", rng(1, 5), rng(6, 10), note="A cross-aisle divides the column after 5."),
        row("DC", rng(1, 4), rng(5, 8), note="A cross-aisle divides the column after 4."),
        row("DA", rng(1, 5), rng(6, 8) + ["W1", "W2"], marks=W("W1", "W2"), inferred={"W1": "9", "W2": "10"},
            note="Two wheelchair boxes, no number, end the column after 8; a cross-aisle divides it after 5."),
    ]
    ar_right = [
        row("BA", ["W1", "W2"] + rng(3, 5), rng(6, 10), marks=W("W1", "W2"), inferred={"W1": "1", "W2": "2"},
            note="Two wheelchair boxes, no number, at seat 1's end; a cross-aisle divides the column after 5."),
        row("BC", rng(1, 4), rng(5, 8), note="A cross-aisle divides the column after 4."),
        row("BE", rng(1, 5), rng(6, 10), note="A cross-aisle divides the column after 5."),
        row("BG", rng(1, 5), rng(6, 10), note="A cross-aisle divides the column after 5."),
    ]
    finish({
        "venue": venue("ktt-bb-arena", "arena stage", "四向舞台"),
        "source": source("BBT_SeatingPlan-ALL.pdf", "2efe6f5c69b6d251b4556a424ab233d032577362c46bd052056065ac9782d0c1"),
        **common,
        "layout": {
            "seat_1_side": "right",
            "note": "Seating on all four sides. Rows CA, CC, CE, CG face the stage from the front (seat 1 at the "
                    "left) and AA, AC, AE from the far side (seat 1 at the right, AA nearest the stage), each split "
                    "by an aisle; upright columns stand along each side: DA, DC, DE, DG on the left (DA nearest the "
                    "stage) with seat 1 at the top, and BA, BC, BE, BG on the right (BA nearest the stage) with seat "
                    "1 at the bottom, each cut by a cross-aisle into two blocks. This is one of the room's seating "
                    "layouts; the transverse- and thrust-stage layouts are separate seat lists.",
            "banks": [
                {"id": "front", "side": "front", "seat_1": "left", "rows": whole(ar_front)},
                {"id": "back", "side": "back", "seat_1": "right", "rows": whole(ar_back)},
                {"id": "left", "side": "left", "seat_1": "upstage", "rows": whole(ar_left)},
                {"id": "right", "side": "right", "seat_1": "downstage", "rows": whole(ar_right)},
            ],
        },
        "printed_totals": {"Black Box Theatre": 160, "Total": 160},
        "zones": [{"name": "Black Box Theatre", "name_zh": "黑盒劇場",
                   "rows": ar_back + ar_front + ar_left + ar_right}],
    })


build()
