#!/usr/bin/env python3
"""East Kowloon Cultural Centre, The Lab: seat facts for its two published seating layouts.

The Lab is a flexible room with one seating plan per stage layout; each becomes its own seat list:
  ekcc-lab-end     end stage (SeatsPlan-T3_End.pdf), 243 seats
  ekcc-lab-thrust  long thrust stage (SeatsPlan-T3_LongThrust.pdf), 258 seats
Both PDFs carry a text layer for every seat number, W and row label. Straight rows were read from
the tokens on each label's line and the side rows (drawn upright along the stage and the walls) from
the tokens in each label's column; crossed management boxes were read by eye (sha256 in source).
The gallery (rows AN, AO and the wall rows BN, DN) is the same in both layouts.
Writes data/ekcc-lab-end.json and data/ekcc-lab-thrust.json; fails if a count does not match.

Usage: python venues/ekcc-lab.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

PUBLISHER = LCSD + ", East Kowloon Cultural Centre"
TECH_SHEET = {
    "publisher": LCSD,
    "url": "https://www.ekcc.hk/documents/venue_detail/hiring/the-lab/index/TechInfo/ekcc-la-lfe.pdf",
    "title": "East Kowloon Cultural Centre – The Lab, FULL Technical Information",
    "document_version": "V. 2026.07.20",
    "sha256": "aa4301585ecb15dac45093769282fd8f4a35d10ab2768f69238e45a4fc728835",
    "retrieved": "2026-09-26",
}
REFERENCES = [{
    "what": "Seat totals for each layout and wheelchair spaces",
    **TECH_SHEET,
    "quotes": ["Total Seating Long Thrust Stage 258 End Stage 243 Wheelchair Space 4"],
    "note": "Confirms both plans' totals and the four W boxes in each. No orchestra pit is described.",
}]
WS = ["W1", "W2"]
XS = ["X1", "X2"]
MARKS = {
    "W": "Seat suitable for audience on wheel chairs (box prints W, no number)",
    "X": "Management seat (crossed box, no number)",
}
SIDE_NOTE = "Drawn upright on the plan, numbered from the audience end (1) towards the stage."


def loc():
    loc = location(geo_id="826817417", geo_name="East Kowloon Cultural Centre (The Hall)", lat=22.32427, lon=114.21494,
                   address_en="60 Ngau Tau Kok Road, Kowloon, Hong Kong", address_zh=None, district=None,
                   address_source={**TECH_SHEET, "quote": "East Kowloon Cultural Centre 60 Ngau Tau Kok Road, Kowloon, HK",
                                   "note": "Not in LCSD's venue.json; address as printed on the technical sheet."})
    loc["coordinates_source"]["note"] = ("The Lab is not listed in venues.xml. This is the entry for The Hall; LCSD gives "
                                         "every East Kowloon Cultural Centre venue the same point for the building.")
    return loc


def venue(vid, layout_en, layout_zh):
    return {"id": vid, "name_en": f"East Kowloon Cultural Centre, The Lab ({layout_en})",
            "name_zh": f"東九文化中心 創館（{layout_zh}）"}


def source(file, sha):
    return {"publisher": PUBLISHER, "url": f"https://www.ekcc.hk/documents/venue_detail/hiring/the-lab/index/{file}",
            "page": "https://www.ekcc.hk/en/hiring/the-lab/", "file": file, "sha256": sha,
            "plan_code": "ver. 2025.08", "printed_date": None, "credit": CREDIT}


def gallery():
    return [
        row("AN", rng(1, 17) + XS, marks={x: "X" for x in XS},
            note="Two crossed management boxes, no number, after 17 (18-19 likely, not printed)."),
        row("AO", rng(1, 16) + WS, marks={w: "W" for w in WS},
            note="Two wheelchair boxes, W with no number, after 16, set apart from it and from each other; their numbers are not printed."),
        row("BN", rng(1, 18), note="Along the left wall, above the stalls. " + SIDE_NOTE),
        row("DN", rng(1, 18), note="Along the right wall, above the stalls. " + SIDE_NOTE),
    ]


# ---- end stage: straight rows facing the stage, and a short side row each side of it
end_stalls = [
    row("BA", rng(5, 8), note="Beside the stage on the left, upright on the plan; seats 5-8 only."),
    row("DA", WS, marks={w: "W" for w in WS},
        note="Beside the stage on the right: two wheelchair boxes, W with no number, upright on the plan."),
]
for lab in ["AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AJ", "AK", "AL", "AM"]:
    if lab == "AG":
        end_stalls.append(row("AG", rng(1, 12) + XS, marks={x: "X" for x in XS},
                              note="Two crossed management boxes, no number, after 12 (13-14 likely, not printed)."))
    else:
        end_stalls.append(row(lab, rng(1, 14)))

# ---- long thrust stage: four side rows each side of the stage, and straight rows at its end
thrust_stalls = [row(lab, rng(1, n), note=f"Left of the stage. {SIDE_NOTE}")
                 for lab, n in [("BD", 14), ("BC", 16), ("BB", 13), ("BA", 12)]]
thrust_stalls += [
    row("DA", rng(1, 12), note=f"Right of the stage. {SIDE_NOTE}"),
    row("DB", rng(1, 13), note=f"Right of the stage. {SIDE_NOTE}"),
    row("DC", WS + rng(4, 16), marks={w: "W" for w in WS},
        note=f"Right of the stage. Two wheelchair boxes, W with no number, at the audience end, set apart below 4; their numbers are not printed. {SIDE_NOTE}"),
    row("DD", rng(3, 14), note=f"Right of the stage; starts at 3. {SIDE_NOTE}"),
    row("AA", rng(2, 13), note="Starts at 2: the row is cut back at both ends where the side rows meet it."),
    row("AB", rng(1, 14)),
    row("AC", rng(1, 14)),
    row("AD", rng(1, 14)),
    row("AE", rng(1, 12) + XS, marks={x: "X" for x in XS},
        note="Two crossed management boxes, no number, after 12 (13-14 likely, not printed)."),
    row("AF", rng(1, 14)),
]


def build():
    common = {"references": REFERENCES, "location": loc(), "marks": MARKS}
    finish({
        "venue": venue("ekcc-lab-end", "end stage", "單向舞台"),
        "source": source("SeatsPlan-T3_End.pdf", "5effaee6ff82d39069b6c7c98ac2d18d6018e9370a2503629255b1128048cac9"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "Drawn with the stage at the top. Stalls rows AA-AM (no row AI) face the stage, seat 1 at the left; BA and DA are short rows beside the stage, drawn upright on the plan. The gallery is rows AN-AO at the back and rows BN and DN along the side walls, drawn upright. The map draws every row as one line. This is one of The Lab's seating layouts; the long-thrust layout is a separate seat list.",
        },
        "printed_totals": {"Stalls": 172, "Gallery": 71, "Total": 243},
        "zones": [
            {"name": "Stalls", "name_zh": "堂座", "rows": end_stalls},
            {"name": "Gallery", "name_zh": "樓座", "rows": gallery()},
        ],
    })
    finish({
        "venue": venue("ekcc-lab-thrust", "long thrust stage", "三向舞台（直向）"),
        "source": source("SeatsPlan-T3_LongThrust.pdf", "8a27d68a7f2c0679949983cd8eec9f3fa714ebcf6869d458f7812850463b04a6"),
        **common,
        "layout": {
            "seat_1_side": "left",
            "note": "The stage runs down the middle of the room with the audience on three sides: rows BA-BD to its left and DA-DD to its right, drawn upright on the plan and numbered from the audience end, and rows AA-AF facing its end, seat 1 at the left. The gallery is rows AN-AO at the back and rows BN and DN along the side walls. The map draws every row as one line. This is one of The Lab's seating layouts; the end-stage layout is a separate seat list.",
        },
        "printed_totals": {"Stalls": 187, "Gallery": 71, "Total": 258},
        "zones": [
            {"name": "Stalls", "name_zh": "堂座", "rows": thrust_stalls},
            {"name": "Gallery", "name_zh": "樓座", "rows": gallery()},
        ],
    })


build()
