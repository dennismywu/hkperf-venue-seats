#!/usr/bin/env python3
"""Hong Kong Cultural Centre, Concert Hall: seat facts read from the LCSD seating plan.

The plan is a two-page vector PDF with no text layer: every number and letter is drawn as an outline.
Page 1 is for events before 1 Sep 2020; page 2, used here, is for events on or after it. An extraction
script read every seat box and decoded its number from the digit outlines; every block end, row label
and mark below was then checked by eye against zoomed renders of page 2 (sha256 in source).

The hall wraps the platform: the Stalls in front (Stalls 1 rows A-M, Stalls 2 rows AA-MM), and the
Balcony all round it, from the choir rows behind the platform (rows A-F) down both sides to the rear
(rows up to R). Row letters restart in the Balcony. The plan prints no totals, so the figures checked
are LCSD's technical sheet: Stalls 1044 (Stalls 1 and 2 together), Balcony 913, Box Seat 14.
Writes data/hkcc-ch.json; fails if the counts do not match. Then run tools/derive_glyph_runs.py hkcc-ch
to add each block's position from the plan.

Usage: python venues/hkcc-ch.py && python tools/derive_glyph_runs.py hkcc-ch
"""
from common import CREDIT, LCSD, finish, location, rng, row

TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.lcsd.gov.hk/en/tech/common/pdf/en/hkcc-ch-lfe.pdf",
    "title": "Hong Kong Cultural Centre – Concert Hall, FULL Technical Information",
    "document_version": "V. 2025.04.10",
    "sha256": "5d7f9c1730b44081d1f98f494db1b3b86d347f81c1d5725781b68e17310c73d2",
    "retrieved": "2026-10-03",
}
X = lambda *ids: {i: "X" for i in ids}
W = lambda *ids: {i: "W" for i in ids}
WC = "Wheel Chair Box"

# ---- Stalls 1 (堂座1): rows A-M. A left block numbered from 1, a centre block from 18 and a right block
# from 46; row D has no centre block, rows K-M only the centre.
stalls1 = [row(lab, rng(1, a), rng(18, b), rng(46, c)) for lab, (a, b, c) in {
    "A": (12, 35, 57), "B": (15, 36, 60), "C": (17, 37, 62),
}.items()]
stalls1.append(row("D", rng(1, 14) + ["X1", "X2"], rng(46, 61), marks=X("X1", "X2"),
                   note="No centre block: the plan prints the row letter on both sides of an empty centre. The "
                        "left block ends with two crossed management boxes after 14 (15-16 likely, not printed)."))
stalls1 += [row(lab, rng(1, a), rng(18, b), rng(46, c)) for lab, (a, b, c) in {
    "E": (13, 39, 58), "F": (8, 40, 53), "G": (9, 41, 54), "H": (8, 42, 53), "I": (6, 43, 51), "J": (3, 44, 48),
}.items()]
stalls1 += [
    row("K", rng(18, 43) + ["X1", "X2"], marks=X("X1", "X2"),
        note="Centre block only. It ends with two crossed management boxes after 43 (44-45 likely, not printed)."),
    row("L", rng(18, 40), note="Centre block only."),
    row("M", rng(18, 33), note="Centre block only."),
]

# ---- Stalls 2 (堂座2): rows AA-MM, behind and beside Stalls 1. Blocks keep fixed number ranges round the
# hall: 1- and 14- on the far left, 27-, 39- (centre), 60-, 76- and 89- on the right.
stalls2 = [
    row("AA", rng(1, 12), rng(89, 100), note="Two upright side blocks only, one each side of Stalls 1."),
    row("BB", rng(1, 13), rng(89, 101), ["X1", "X2"], marks=X("X1", "X2"),
        note="Two upright side blocks only. Two crossed management boxes stand in a column of their own beside "
             "the end of the left block (after 13); the plan prints no row letter or number for them."),
    row("CC", rng(14, 26), rng(27, 36), rng(39, 53), rng(60, 69), rng(76, 88), rng(89, 90),
        note="89-90 stand at the foot of the right side block, under rows AA-BB's 89-."),
    row("DD", rng(14, 23), rng(27, 37), rng(39, 54), rng(60, 70), rng(76, 88)),
    row("EE", rng(14, 23), rng(27, 38), rng(39, 55), rng(60, 71), rng(76, 86)),
    row("FF", rng(14, 25), rng(27, 35), rng(39, 56), rng(60, 71), rng(76, 86)),
    row("GG", rng(27, 35), rng(39, 57), rng(60, 72), rng(76, 88)),
    row("HH", rng(27, 38), rng(39, 57), rng(60, 73), rng(76, 84)),
    row("II", rng(39, 58), rng(60, 74)),
    row("JJ", rng(39, 59), rng(60, 75)),
    row("KK", rng(39, 52), rng(60, 69)),
    row("LL", rng(39, 45), rng(46, 52), rng(60, 68), note="The centre block breaks in two, between 45 and 46."),
    row("MM", rng(39, 46), rng(47, 55), rng(60, 74), note="The centre block breaks in two, between 46 and 47."),
    row(WC, rng(1, 6), marks=W(*rng(1, 6)),
        note="Six numbered places in a box labelled 輪椅席 Wheel Chair Box, on the left behind rows GG-HH; the plan "
             "prints no row letter. The boxes print numbers, not W; marked W as the plan names them wheelchair "
             "seats. Places 7-10 are the Balcony's wheelchair box."),
]

# ---- Balcony (樓座): rows A-F behind the platform (the choir seats: right section 1-, centre 14-, left 30-),
# continuing as rows C-I down both sides, and rows G-R across the rear. Blocks keep fixed number ranges.
balcony = [
    row("A", rng(1, 8), rng(14, 25), rng(30, 37)),
    row("B", rng(1, 9), rng(14, 25), rng(30, 38)),
    row("C", rng(1, 10), rng(14, 27), rng(30, 39), rng(43, 51), rng(54, 62), rng(142, 150), rng(154, 162)),
    row("D", rng(1, 11), rng(14, 29), rng(30, 40), rng(43, 51), rng(54, 63), rng(142, 151), rng(154, 162)),
    row("E", rng(1, 12), rng(14, 15), rng(28, 29), rng(30, 41), rng(43, 52), rng(54, 64), rng(67, 76),
        rng(142, 152), rng(154, 163),
        note="Behind the platform only the ends of the centre section are seated: 14-15 and 28-29."),
    row("F", rng(1, 13), rng(30, 42), rng(43, 53), rng(54, 64), rng(67, 77), rng(129, 138), rng(142, 152),
        rng(154, 164), note="Behind the platform the row has no centre section."),
    row("G", rng(43, 53), rng(54, 65), rng(67, 77), rng(80, 87), rng(129, 139), rng(142, 153), rng(154, 164)),
    row("H", rng(54, 65), rng(67, 78), rng(80, 87), rng(129, 140), rng(142, 153)),
    row("I", rng(54, 66), rng(67, 78), rng(80, 88), rng(92, 105), rng(113, 121), rng(142, 153)),
    row("J", rng(67, 79), rng(80, 89), rng(92, 106), rng(113, 122)),
    row("K", rng(67, 79) + ["X1"], rng(80, 90), rng(92, 107), rng(113, 123), marks=X("X1"),
        note="The left side block ends with a crossed management box after 79; the next block starts at 80, so "
             "the box carries no number."),
    row("L", rng(80, 91), rng(92, 108), rng(113, 124)),
    row("M", rng(80, 91) + ["X1"], rng(92, 108), rng(113, 125), marks=X("X1"),
        note="The left rear block ends with a crossed management box after 91; the next block starts at 92, so "
             "the box carries no number."),
    row("N", rng(92, 109), rng(113, 125)),
    row("O", rng(92, 110), rng(113, 126)),
    row("P", rng(92, 111), rng(113, 127)),
    row("Q", rng(92, 112), rng(113, 128)),
    row("R", rng(113, 127), note="Right rear block only."),
    row(WC, rng(7, 10), marks=W(*rng(7, 10)),
        note="Four numbered places in a box labelled 輪椅席 Wheel Chair Box, on the right beside Balcony rows F-H; "
             "the plan prints no row letter. The boxes print numbers, not W, and follow on from the Stalls' "
             "wheelchair box (1-6); marked W as the plan names them wheelchair seats."),
]

# ---- V.I.P. boxes (貴賓廂座)
boxes = [
    row("Box 1", rng(1, 10), note="V.I.P. Box 1 (貴賓廂座1), at the rear of the hall behind Balcony row Q."),
    row("Box 2", rng(1, 4), note="V.I.P. Box 2 (貴賓廂座2), on the left behind Balcony row K."),
]

finish({
    "venue": {"id": "hkcc-ch", "name_en": "Hong Kong Cultural Centre Concert Hall", "name_zh": "香港文化中心 音樂廳"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.lcsd.gov.hk/en/hkcc/common/images/facilities/concerthall/concert_hall_seating%20plan_web_ch_2pages.pdf",
        "page": "https://www.lcsd.gov.hk/en/hkcc/facilities/concerthall.html",
        "file": "concert_hall_seating plan_web_ch_2pages.pdf",
        "sha256": "59b8fd692fff23045f958fab0175135232dfa0c589b34e1151528f0665dd7a9c",
        "pdf_page": 2,
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
        "note": "Two pages. Page 2 (Applicable to the events taking place on or after 1 Sep 2020) is the one read. "
                "Page 1 (before 1 Sep 2020) differs only at the wheelchair boxes and the V.I.P. boxes.",
    },
    "references": [{
        "what": "Seat totals by tier",
        **TECH_SHEET,
        "quotes": ["Max. Total Seating: 1971 Stalls: 1044 Balcony: 913 Box Seat: 14",
                   "Choir stalls on balcony behind with 186 seats in 3 sections, or used as additional audience seating."],
        "note": "The plan prints no totals, so these are the figures checked. The sheet's Stalls are the plan's Stalls 1 "
                "and Stalls 2 together; its Balcony includes the choir rows behind the platform; its Box Seat is V.I.P. "
                "Boxes 1 and 2. The choir rows (Balcony rows A-F behind the platform) hold 184 boxes on the plan, not the "
                "sheet's 186; the plan is recorded as drawn.",
    }],
    "location": location(geo_id="50110014", geo_name="Hong Kong Cultural Centre (Concert Hall)", lat=22.29386, lon=114.17053,
                         address_en="10 Salisbury Road, Tsim Sha Tsui, Kowloon, Hong Kong",
                         address_zh="香港九龍尖沙咀梳士巴利道十號", district="Yau Tsim Mong", address_name="Hong Kong Cultural Centre"),
    "layout": {
        "seat_1_side": "left",
        "arrangement": "arc",
        # the plan's seat pitch is 9.6-13.6 units and the viewer's seats are 15 wide, so the plan is drawn
        # 1.75x larger to leave a gap between seats (geometry from tools/derive_glyph_runs.py)
        # the stage is drawn as a circle about the centre (the plan's 舞台 Stage label), clear of the nearest
        # seats (183 units out)
        "arc": {"stage_span": 70, "rotate_seats": True, "ring_gap": 1.6, "scale": 1.75, "centre": [596, 360],
                "row_labels": "along", "stage": {"shape": "circle", "radius": 150}},
        "stage_label": "STAGE 舞台",
        "note": "A surround hall: the stage sits in the middle with seats all round it. Every block is drawn where "
                "the plan draws it, as straight runs. Blocks keep fixed number ranges, so numbers skip between them. Row "
                "letters restart in the Balcony; Stalls 2 doubles the letters (AA-MM). The plan prints no row letters "
                "for the wheelchair boxes or the V.I.P. boxes.",
    },
    "marks": {
        "W": "Wheelchair seat (in a box the plan labels 輪椅席 Wheel Chair Box; the boxes print numbers, not W)",
        "X": "Management seat (crossed box, no number; the plan's 場館留座 Management Seats)",
    },
    "totals_source": "LCSD's technical sheet (V. 2025.04.10); the seating plan prints no totals",
    "printed_totals": {"Stalls": 1044, "Balcony": 913, "V.I.P. Boxes": 14, "Total": 1971},
    # label_at: where the plan prints each part of house's name, from the centre (plan units): 堂座1 Stalls 1 in
    # row D's empty centre, 堂座2 Stalls 2 between rows M and CC, 樓座 Balcony at the foot of the plan. The plan
    # names each V.I.P. box under its own seats; the heading sits under Box 1, above the Balcony's.
    "zones": [
        {"name": "Stalls 1", "name_zh": "堂座1", "rows": stalls1, "counted_in": "Stalls", "arc": {"label_at": [13, 246]}},
        {"name": "Stalls 2", "name_zh": "堂座2", "rows": stalls2, "counted_in": "Stalls", "arc": {"label_at": [-3, 388]}},
        {"name": "Balcony", "name_zh": "樓座", "rows": balcony, "arc": {"label_at": [10, 891]}},
        {"name": "V.I.P. Boxes", "name_zh": "貴賓廂座", "rows": boxes, "arc": {"label_at": [10, 866]}},
    ],
})
