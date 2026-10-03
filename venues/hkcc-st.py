#!/usr/bin/env python3
"""Hong Kong Cultural Centre, Studio Theatre: seat facts for its four published seating layouts.

The Studio Theatre is a flexible room with one seating plan per stage layout; each becomes its own seat
list:
  hkcc-st-end      end stage (ST-End-New.gif), 321 seats
  hkcc-st-tv       transverse stage (ST-Tran-New.gif), 382 seats
  hkcc-st-thrust   thrust stage (ST-Thrust-New.gif), 303 seats
  hkcc-st-arena    arena stage (ST-Arena-New.gif), 496 seats
The plans are published as GIFs. The end, thrust and arena images are 2480x3508 and every box, number,
W and X was read by eye from zoomed crops; the transverse image is only 514x800, readable but small, so
its counts lean on LCSD's technical sheet (sha256 in source).

LCSD's technical sheet gives each layout's seating by tier, and every tier total matches the boxes the
plans draw minus the management seats. The plans themselves print only the grand total. Writes the four
data/*.json and .csv; fails if any tier or the total does not match.

Usage: python venues/hkcc-st.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/hkcc-st-lfe.pdf",
    "title": "Hong Kong Cultural Centre – Studio Theatre, FULL Technical Information",
    "document_version": "V. 2025.05.29",
    "sha256": "ee61856ee6ef71c1478e88467e81e562c36c172008006424466d7daf199db54d",
    "retrieved": "2026-10-03",
}
PAGE = "https://www.lcsd.gov.hk/en/hkcc/facilities/studiotheatre.html"
REFERENCES = [{
    "what": "Seat totals by tier for each layout, and the vomitory losses",
    **TECH_SHEET,
    "quotes": [
        "Max. Total Seating: Arena Stage: 496 seats Thrust Stage: 303 seats Transverse Stage: 382 seats End Stage: 321 seats",
        "West Tier 150 (West Vomitory 18) North Tier 45 (North Vomitory 9) East Tier 154 (East Vomitory 18) "
        "South Tier 45 (South Vomitory 9) Balcony West 21 Balcony North 30 Balcony East 21 Balcony Southarea 30 Total 496",
        "West Tier 150 (West Vomitory 18) North Tier 45 (North Vomitory 9) South Tier 45 (South Vomitory 9) "
        "Balcony West 21 Balcony North 21 Balcony South 21 Total 303",
        "West Tier 150 (West Vomitory 18) East Tier 154 (East Vomitory 18) Balcony West 21 Balcony East 21 "
        "Balcony North 18 Balcony South 18 Total 382",
        "Main Tier 270 Balcony West 21 Balcony North 15 Balcony South 15 Total 321",
        "Vomitory entries can be made available with a loss of 9 or 18 seats.",
    ],
    "note": "The plans print only the grand total; the tiers are the sheet's, and every tier equals the boxes the plan "
            "draws minus its management seats. The tiers are placed on the plan: West is the main house drawn at the "
            "bottom, East the house across an arena or transverse stage at the top, North the left side, South the "
            "right side. The sheet also gives vomitory losses (9 or 18 seats) but not the rows they take; no rows are "
            "removed here.",
}]
MARKS = {
    "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
    "X": "Management seat (crossed box, no number)",
}
WS = lambda n: [f"W{i}" for i in range(1, n + 1)]
W = lambda n: {f"W{i}": "W" for i in range(1, n + 1)}
X4 = ["X1", "X2", "X3", "X4"]
X_MARKS = {f"X{i}": "X" for i in range(1, 5)}
X_NOTE = ("Four crossed management boxes, no number: two open the row where 1-2 would be and two close it where "
          "20-21 would be, so each pair fills those numbers exactly.")


def loc():
    return location(geo_id="50110016", geo_name="Hong Kong Cultural Centre (Studio Theatre)",
                    lat=22.29386, lon=114.17053,
                    address_en="10 Salisbury Road, Tsim Sha Tsui, Kowloon, Hong Kong",
                    address_zh="香港九龍尖沙咀梳士巴利道十號", district="Yau Tsim Mong",
                    address_name="Hong Kong Cultural Centre")


def source(file, sha):
    return {"publisher": LCSD, "url": f"https://www.lcsd.gov.hk/en/hkcc/common/images/facilities/studiotheatre/{file}",
            "page": PAGE, "file": file, "sha256": sha, "plan_code": None, "printed_date": None, "credit": CREDIT}


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"Hong Kong Cultural Centre Studio Theatre ({layout_en})",
            "name_zh": f"香港文化中心 劇場（{layout_zh}）"}


def cp():
    return row("CP", X4[:2] + rng(3, 19) + X4[2:], marks=X_MARKS,
               inferred={"X1": "1", "X2": "2", "X3": "20", "X4": "21"}, note=X_NOTE)


def wrow(lab, n, note):
    return row(lab, WS(n), marks=W(n), note=note)


def wgroups(lab, groups, note):
    """A run of wheelchair boxes the plan draws as separate groups (spaced bays), e.g. 3+6+6."""
    blocks, i = [], 1
    for g in groups:
        blocks.append([f"W{j}" for j in range(i, i + g)])
        i += g
    return row(lab, *blocks, marks={f"W{j}": "W" for j in range(1, i)}, note=note)


# ---- the main house drawn at the bottom (West): rows C, nearest the stage first, seat 1 at the left.
# The end stage uses every letter; the other layouts use fewer rows on the same plan.
west = lambda: [row("CA", rng(5, 17)),
                row("CC", rng(4, 18))] + [row(lab, rng(1, 21)) for lab in ["CE", "CG", "CJ", "CL", "CN"]] + [cp()]

# ---- the house across an arena or transverse stage, drawn at the top (East): rows A, nearest the stage
# first (so AA is nearest), seat 1 at the right. Only the arena and transverse layouts use it.
east = lambda: [row("AA", rng(5, 17)),
                row("AC", rng(4, 18))] + [row(lab, rng(1, 21)) for lab in ["AE", "AG", "AJ", "AL", "AN", "AP"]]

SIDE_NOTE = "Drawn upright on the plan, numbered from the audience's end by the stage."
W_NOTE = "A row of wheelchair boxes printing W with no number; the numbers are not printed."
GROUPS_NOTE = "Drawn as separate groups of wheelchair bays, {}."

# ---- the side galleries, drawn upright: three numbered columns each side, numbered from the stage end,
# then an outer column of wheelchair boxes. Left = North, right = South.
left_cols = [row("DA", rng(5, 17), note=f"Left of the stage. {SIDE_NOTE}"),
             row("DC", rng(4, 18), note=f"Left of the stage. {SIDE_NOTE}"),
             row("DE", rng(3, 19), note=f"Left of the stage. {SIDE_NOTE}")]
right_cols = [row("BA", rng(5, 17), note=f"Right of the stage. {SIDE_NOTE}"),
              row("BC", rng(4, 18), note=f"Right of the stage. {SIDE_NOTE}"),
              row("BE", rng(3, 19), note=f"Right of the stage. {SIDE_NOTE}")]
DQ_END = lambda: wgroups("DQ", [3, 6, 6], "The outer column on the left. " + GROUPS_NOTE.format("3-6-6"))
BQ_END = lambda: wgroups("BQ", [3, 6, 6], "The outer column on the right. " + GROUPS_NOTE.format("3-6-6"))
DQ_TH = lambda: wgroups("DQ", [3, 6, 6, 6], "The outer column on the left. " + GROUPS_NOTE.format("3-6-6-6"))
BQ_TH = lambda: wgroups("BQ", [3, 6, 6, 6], "The outer column on the right. " + GROUPS_NOTE.format("3-6-6-6"))
DQ_AR = lambda: wgroups("DQ", [6, 6, 6, 6, 6], "The outer column on the left. " + GROUPS_NOTE.format("6-6-6-6-6"))
BQ_AR = lambda: wgroups("BQ", [6, 6, 6, 6, 6], "The outer column on the right. " + GROUPS_NOTE.format("6-6-6-6-6"))
CQ_W = lambda n: wrow("CQ", n, "The outer row of the west house, set apart from CP. " + W_NOTE)
AQ_W = lambda n: wrow("AQ", n, "The outer row of the east house, set apart from AP. " + W_NOTE)


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}

    # ---- end stage: every row of the main house, and one wheelchair column each side
    end_main = [row("CA", rng(5, 17)), row("CB", rng(4, 18)), row("CC", rng(4, 18))]
    end_main += [row(lab, rng(1, 21)) for lab in ["CD", "CE", "CF", "CG", "CH", "CJ", "CK", "CL", "CM", "CN"]]
    end_main += [cp()]
    finish({
        "venue": venue("hkcc-st-end", "end stage", "單向舞台"),
        "source": source("ST-End-New.gif", "0b98a893b457212870477422a7d5112028abf16ef636884a3ee6719e2b706797"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Drawn with the stage at the top. The main house (rows CA-CP) faces the stage; seat 1 is at the "
                    "left, numbering from 1 and skipping the letters I and O. CA and CB-CC are cut back at the sides. "
                    "CQ is a row of wheelchair boxes set apart below CP, and DQ and BQ are columns of wheelchair boxes "
                    "in groups along the left and right walls, drawn upright. This is one of the theatre's seating "
                    "layouts; the other three are separate seat lists.",
            "banks": [
                {"id": "west", "side": "front", "rows": [r["row"] for r in end_main], "seat_1": "left"},
                {"id": "balcony-west", "side": "front", "rows": ["CQ"], "seat_1": "left"},
                {"id": "north", "side": "left", "rows": ["DQ"], "seat_1": "upstage", "level_with": "CB"},
                {"id": "south", "side": "right", "rows": ["BQ"], "seat_1": "upstage", "level_with": "CB"},
            ],
        },
        "printed_totals": {"Main Tier": 270, "Balcony West": 21, "Balcony North": 15, "Balcony South": 15, "Total": 321},
        "totals_source": "The grand total is printed on the plan; the tiers are LCSD's technical sheet (V. 2025.05.29).",
        "zones": [
            {"name": "Main Tier", "name_zh": "主層", "rows": end_main},
            {"name": "Balcony West", "name_zh": "西樓座", "rows": [CQ_W(21)]},
            {"name": "Balcony North", "name_zh": "北樓座", "rows": [DQ_END()]},
            {"name": "Balcony South", "name_zh": "南樓座", "rows": [BQ_END()]},
        ],
    })

    # ---- transverse stage: house on opposite sides, plus a balcony column each side
    tv_west = west()
    tv_east = east()
    tv_dq = row("DQ", rng(1, 6), rng(7, 9), rng(22, 24), rng(25, 30),
                note="A balcony column along the left wall, split by the stage: seats 1-9 on the west side and 22-30 "
                     "on the east, in groups of 6 and 3. The numbers between are not drawn.")
    tv_bq = row("BQ", rng(1, 6), rng(7, 9), rng(22, 24), rng(25, 30),
                note="A balcony column along the right wall, split by the stage: seats 1-9 on the west side and 22-30 "
                     "on the east, in groups of 6 and 3. The numbers between are not drawn.")
    finish({
        "venue": venue("hkcc-st-tv", "transverse stage", "橫向舞台"),
        "source": source("ST-Tran-New.gif", "efc629652fae84873a4c751fa10f6a6ee5f4a6f8167e5ebdd090f21c9b9a773f"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Two houses face each other across the stage. The west house (rows CA-CP, drawn at the bottom) has "
                    "seat 1 at the left; the east house (rows AA-AP, drawn at the top and read upside down on the "
                    "plan) has seat 1 at the right. Numbering skips the letters I and O. CA-CC and AA-AC are cut back "
                    "at the sides, CQ is set apart below CP and AQ above AP, and rows DQ and BQ are balcony columns "
                    "along the walls, split by the stage. This is one of the theatre's seating layouts; the other "
                    "three are separate seat lists.",
            "banks": [
                {"id": "west", "side": "front", "rows": [r["row"] for r in tv_west], "seat_1": "left"},
                {"id": "balcony-west", "side": "front", "rows": ["CQ"], "seat_1": "left"},
                {"id": "east", "side": "back", "rows": [r["row"] for r in tv_east], "seat_1": "right"},
                {"id": "balcony-east", "side": "back", "rows": ["AQ"], "seat_1": "right"},
                {"id": "north-east", "side": "left", "rows": [{"row": "DQ", "block": [1, 2]}], "seat_1": "upstage",
                 "level_with": "AN"},
                {"id": "north-west", "side": "left", "rows": [{"row": "DQ", "block": [3, 4]}], "seat_1": "upstage",
                 "level_with": "CA"},
                {"id": "south-east", "side": "right", "rows": [{"row": "BQ", "block": [3, 4]}], "seat_1": "downstage",
                 "level_with": "AN"},
                {"id": "south-west", "side": "right", "rows": [{"row": "BQ", "block": [1, 2]}], "seat_1": "downstage",
                 "level_with": "CA"},
            ],
        },
        "printed_totals": {"West Tier": 150, "East Tier": 154, "Balcony West": 21, "Balcony East": 21,
                           "Balcony North": 18, "Balcony South": 18, "Total": 382},
        "totals_source": "The grand total is printed on the plan; the tiers are LCSD's technical sheet (V. 2025.05.29).",
        "zones": [
            {"name": "West Tier", "name_zh": "西翼", "rows": tv_west},
            {"name": "East Tier", "name_zh": "東翼", "rows": tv_east},
            {"name": "Balcony West", "name_zh": "西樓座", "rows": [row("CQ", rng(1, 21), note="The outer row of the west house, set apart from CP; seat 1 at the left.")]},
            {"name": "Balcony East", "name_zh": "東樓座", "rows": [row("AQ", rng(1, 21), note="The outer row of the east house, set apart from AP; seat 1 at the right.")]},
            {"name": "Balcony North", "name_zh": "北樓座", "rows": [tv_dq]},
            {"name": "Balcony South", "name_zh": "南樓座", "rows": [tv_bq]},
        ],
    })

    # ---- thrust stage: the west house, a numbered gallery each side, and a wheelchair column each side
    finish({
        "venue": venue("hkcc-st-thrust", "thrust stage", "三向舞台"),
        "source": source("ST-Thrust-New.gif", "544d3806d473794396d809ac97d21a2dd5798b858b99921d6d5407feb10e6484"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "The stage runs into the room with the audience on three sides. The west house (rows CA-CP, drawn "
                    "at the bottom) faces it, seat 1 at the left. Rows DA-DC-DE (left, North) and BA-BC-BE (right, "
                    "South) are galleries drawn upright, each numbered from the audience's end by the stage. CQ is a "
                    "row of wheelchair boxes set apart below CP, and DQ and BQ are outer columns of wheelchair boxes "
                    "in groups. Numbering skips the letters I and O. This is one of the theatre's seating layouts; the "
                    "other three are separate seat lists.",
            "banks": [
                {"id": "west", "side": "front", "rows": [r["row"] for r in west()], "seat_1": "left"},
                {"id": "balcony-west", "side": "front", "rows": ["CQ"], "seat_1": "left"},
                {"id": "north", "side": "left", "rows": [r["row"] for r in left_cols], "seat_1": "upstage", "align": "stage"},
                {"id": "south", "side": "right", "rows": [r["row"] for r in right_cols], "seat_1": "upstage", "align": "stage"},
                {"id": "balcony-north", "side": "left", "rows": ["DQ"], "seat_1": "upstage", "align": "room"},
                {"id": "balcony-south", "side": "right", "rows": ["BQ"], "seat_1": "upstage", "align": "room"},
            ],
        },
        "printed_totals": {"West Tier": 150, "North Tier": 45, "South Tier": 45, "Balcony West": 21,
                           "Balcony North": 21, "Balcony South": 21, "Total": 303},
        "totals_source": "The grand total is printed on the plan; the tiers are LCSD's technical sheet (V. 2025.05.29).",
        "zones": [
            {"name": "West Tier", "name_zh": "西翼", "rows": west()},
            {"name": "North Tier", "name_zh": "北翼", "rows": left_cols},
            {"name": "South Tier", "name_zh": "南翼", "rows": right_cols},
            {"name": "Balcony West", "name_zh": "西樓座", "rows": [CQ_W(21)]},
            {"name": "Balcony North", "name_zh": "北樓座", "rows": [DQ_TH()]},
            {"name": "Balcony South", "name_zh": "南樓座", "rows": [BQ_TH()]},
        ],
    })

    # ---- arena stage: houses on all four sides
    finish({
        "venue": venue("hkcc-st-arena", "arena stage", "中央舞台"),
        "source": source("ST-Arena-New.gif", "bb5d0a755ba82073def8562815dbbe1f91f7ed0142d7869010607217fbbb07c5"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "The stage sits in the middle with the audience on all four sides. The west house (rows CA-CP, "
                    "drawn at the bottom) faces it with seat 1 at the left; the east house (rows AA-AP, drawn at the "
                    "top and read upside down on the plan) faces it with seat 1 at the right. Rows DA-DC-DE (left, "
                    "North) and BA-BC-BE (right, South) are galleries drawn upright, numbered from the audience's end "
                    "by the stage. CQ and AQ are outer rows of wheelchair boxes set apart from CP and AP, and DQ and "
                    "BQ are outer columns of wheelchair boxes in groups. Numbering skips the letters I and O. This is "
                    "one of the theatre's seating layouts; the other three are separate seat lists.",
            "banks": [
                {"id": "west", "side": "front", "rows": [r["row"] for r in west()], "seat_1": "left"},
                {"id": "balcony-west", "side": "front", "rows": ["CQ"], "seat_1": "left"},
                {"id": "east", "side": "back", "rows": [r["row"] for r in east()], "seat_1": "right"},
                {"id": "balcony-east", "side": "back", "rows": ["AQ"], "seat_1": "right"},
                {"id": "north", "side": "left", "rows": [r["row"] for r in left_cols], "seat_1": "upstage", "align": "stage"},
                {"id": "south", "side": "right", "rows": [r["row"] for r in right_cols], "seat_1": "upstage", "align": "stage"},
                {"id": "balcony-north", "side": "left", "rows": ["DQ"], "seat_1": "upstage", "level_with": "AN"},
                {"id": "balcony-south", "side": "right", "rows": ["BQ"], "seat_1": "upstage", "level_with": "AN"},
            ],
        },
        "printed_totals": {"West Tier": 150, "East Tier": 154, "North Tier": 45, "South Tier": 45,
                           "Balcony West": 21, "Balcony East": 21, "Balcony North": 30, "Balcony South": 30,
                           "Total": 496},
        "totals_source": "The grand total is printed on the plan; the tiers are LCSD's technical sheet (V. 2025.05.29).",
        "zones": [
            {"name": "West Tier", "name_zh": "西翼", "rows": west()},
            {"name": "East Tier", "name_zh": "東翼", "rows": east()},
            {"name": "North Tier", "name_zh": "北翼", "rows": left_cols},
            {"name": "South Tier", "name_zh": "南翼", "rows": right_cols},
            {"name": "Balcony West", "name_zh": "西樓座", "rows": [CQ_W(21)]},
            {"name": "Balcony East", "name_zh": "東樓座", "rows": [AQ_W(21)]},
            {"name": "Balcony North", "name_zh": "北樓座", "rows": [DQ_AR()]},
            {"name": "Balcony South", "name_zh": "南樓座", "rows": [BQ_AR()]},
        ],
    })


build()
