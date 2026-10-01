#!/usr/bin/env python3
"""Hong Kong Film Archive, Cinema: seat facts read from the LCSD seating plan.

The plan PDF carries only the labels and legend as text; the seating itself is one scanned image, so
every row end, seat number, W and management box below was read by eye from zoomed crops of it (sha256
in source). Writes data/hkfa-cinema.json; fails if the count does not match the printed total.

The plan prints two figures: "Total No. of Seats (excluding Wheelchair Seats): 125" and, adding the 3
management seats, 128. LCSD's facilities page states the same 125 seats and 4 wheelchair spaces. The
Cinema is counted here as every box on the plan less the four wheelchair spaces and the three
management seats = 125, as the plan's own "Total No. of Seats" gives it.

Usage: python venues/hkfa-cinema.py
"""
from common import CREDIT, LCSD, finish, location, rng, row

FACILITIES = {
    "publisher": LCSD,
    "url": "https://www.filmarchive.gov.hk/en/web/hkfa/facilities.html",
    "title": "Hong Kong Film Archive – Cinema and Exhibition Hall (facilities page)",
    "retrieved": "2026-10-01",
}
W = lambda *ids: {i: "W" for i in ids}
X = lambda *ids: {i: "X" for i in ids}

# Rows A-G hold the printed numbers; row A ends with one crossed management box, row H begins and ends
# with two wheelchair boxes and carries two crossed management boxes in its centre.
rows = [row("A", rng(1, 16) + ["X1"], marks=X("X1"),
            note="A crossed management box, no number, ends the row after 16; nothing follows it, so it "
                 "keeps no number.")]
for lab in "BCDEFG":
    rows.append(row(lab, rng(1, 17)))
rows.append(row("H", ["W1", "W2"] + rng(3, 9) + ["X1", "X2"] + ["W3", "W4"],
                marks={**W("W1", "W2", "W3", "W4"), **X("X1", "X2")},
                inferred={"W1": "1", "W2": "2"},
                note="Two wheelchair boxes print W, no number, at seat 1's end, between nothing and 3, so "
                     "they fill 1-2 exactly. Two crossed management boxes follow 9, then two more "
                     "wheelchair boxes end the row; none of these carries a number."))

finish({
    "venue": {"id": "hkfa-cinema", "name_en": "Hong Kong Film Archive Cinema",
              "name_zh": "香港電影資料館 電影院"},
    "source": {
        "publisher": LCSD,
        "url": "https://www.filmarchive.gov.hk/documents/Facilities/HKFA-Seating-Plan.pdf",
        "file": "HKFA-Seating-Plan.pdf",
        "sha256": "6699fcedd0c912a2ebf43353f7311eea4677bd137a5cafd34b3e42ab802763e4",
        "plan_code": None,
        "printed_date": None,
        "credit": CREDIT,
    },
    "references": [{
        "what": "Seating capacity",
        **FACILITIES,
        "quotes": ["Seating capacity: 125 seats and 4 wheelchair spaces"],
        "note": "Confirms the plan's 125 seats and four wheelchair boxes; the plan adds 3 management "
                "seats (128 with them), which LCSD's page does not count.",
    }],
    "location": location(geo_id="75010017", geo_name="Hong Kong Film Archive (Cinema)", lat=22.285056,
                         lon=114.222075, address_en="50 Lei King Road, Sai Wan Ho, Hong Kong",
                         address_zh="香港西灣河鯉景道50號", district="Eastern",
                         address_name="Hong Kong Film Archive"),
    "layout": {
        "seat_1_side": "left",
        "note": "Drawn with the screen at the top. Seat 1 is at the left-hand end of each row and blocks "
                "are listed from that side; the rows are drawn in arcs, so positions are not preserved. "
                "Rows A-H with no row I. The plan names no seating areas, only the space (電影院 CINEMA), "
                "so there is one zone.",
    },
    "marks": {
        "W": "Seat suitable for audience on wheelchairs (box prints W, no number)",
        "X": "Management seat (crossed grey box, no number)",
    },
    "printed_totals": {"Cinema": 125, "Total": 125},
    "zones": [{
        "name": "Cinema", "name_zh": "電影院", "rows": rows,
        "count_excludes": ["W"],
        "count_note": "The plan's \"Total No. of Seats (excluding Wheelchair Seats)\" is 125 and leaves "
                      "the four wheelchair boxes out; with the 3 management seats its other figure is 128. "
                      "Counted here as every box less the 3 management seats and the 4 wheelchair boxes "
                      "= 125, as the plan's own total gives it.",
    }],
})
