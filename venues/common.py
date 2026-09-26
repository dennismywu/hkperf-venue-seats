"""Shared helpers for the venue scripts: build rows, check counts, write data/<id>.json.

A venue script holds only facts read from LCSD sources. finish() checks them and fails loudly:
  - each zone: boxes on the plan minus management seats (X) = the printed zone total
  - each orchestra pit: seats in its rows (minus X) = the stated loss, and the total follows
"""
import csv
import json
from pathlib import Path

SCHEMA = "hkperf-venue-seats/seatlist@0.2"
DATA = Path(__file__).resolve().parent.parent / "data"

LCSD = "Leisure and Cultural Services Department (LCSD)"
CREDIT = ("Seat facts compiled from the seating plan published by the Leisure and Cultural Services "
          "Department, HKSAR Government.")
COUNT_RULE = ("Printed total = boxes on the plan minus management seats (X). Wheelchair boxes (W) are "
              "counted. This rule matches every zone exactly; it is our reading, not printed on the plan.")


# Where each building is: LCSD's own open data, published through DATA.GOV.HK.
# tools/check_locations.py re-reads both files and confirms the values below.
LCSD_GEO = {
    "publisher": LCSD,
    "title": "Cultural Programmes (DATA.GOV.HK): venue list with coordinates",
    "dataset": "https://data.gov.hk/en-data/dataset/hk-lcsd-event-event-cultural",
    "url": "https://www.lcsd.gov.hk/datagovhk/event/venues.xml",
    "retrieved": "2026-09-26",
}
LCSD_ADDRESSES = {
    "publisher": LCSD,
    "title": "LCSD venue list for DATA.GOV.HK: names, addresses and districts",
    "url": "https://www.lcsd.gov.hk/datagovhk/venue/venue.json",
    "retrieved": "2026-09-26",
}


def location(*, geo_id, geo_name, lat, lon, address_en, address_zh=None, district=None, address_name=None,
             address_source=None):
    """The building's address and LCSD's published point for it (not surveyed by this project)."""
    return {
        "address_en": address_en,
        "address_zh": address_zh,
        "district": district,
        "latitude": lat,
        "longitude": lon,
        "coordinates_source": {**LCSD_GEO, "venue_id": geo_id, "name_in_source": geo_name},
        "address_source": address_source or {**LCSD_ADDRESSES, "name_in_source": address_name},
        "note": "Coordinates are LCSD's published point for the building, reproduced as given.",
    }


def rng(a, b):
    return [str(i) for i in range(a, b + 1)]


def row(label, *blocks, marks=None, inferred=None, note=None):
    """blocks: lists of seat ids, or dicts {"seats": [...], "side": "left"|"right"}."""
    r = {"row": label, "blocks": [b if isinstance(b, dict) else {"seats": b} for b in blocks]}
    if marks: r["marks"] = marks
    if inferred: r["inferred_numbers"] = inferred
    if note: r["note"] = note
    return r


def _seats(rows):
    return sum(len(b["seats"]) for r in rows for b in r["blocks"])


def _marked(rows, mark):
    # a seat's mark is one or more letters, e.g. "R" or "RL" (restricted sightline and limited legroom)
    return sum(1 for r in rows for m in r.get("marks", {}).values() if mark in m)


def finish(doc):
    """Check doc against its printed and stated figures, then write data/<venue id>.json."""
    doc = {"schema": SCHEMA, **doc}
    printed = doc["printed_totals"]
    all_rows = [r for z in doc["zones"] for r in z["rows"]]

    check = {}
    for z in doc["zones"]:
        boxes, x = _seats(z["rows"]), _marked(z["rows"], "X")
        check[z["name"]] = {"boxes": boxes, "management_X": x, "wheelchair_W": _marked(z["rows"], "W"),
                            "restricted_R": _marked(z["rows"], "R"), "limited_legroom_L": _marked(z["rows"], "L"),
                            "boxes_minus_X": boxes - x,
                            "printed": printed[z["name"]]}
        assert boxes - x == printed[z["name"]], f"{z['name']}: {boxes} boxes - {x} X != {printed[z['name']]}"
    assert sum(printed[z["name"]] for z in doc["zones"]) == printed["Total"], "zone totals do not add up"

    for pit in doc.get("orchestra_pits", []):
        rows = [r for r in all_rows if r["row"] in pit["rows_removed"]]
        assert len(rows) == len(pit["rows_removed"]), f"{pit['name']}: unknown rows {pit['rows_removed']}"
        removed = _seats(rows) - _marked(rows, "X")
        stated = pit.pop("stated")
        if "seats_removed" in stated:
            assert removed == stated["seats_removed"], f"{pit['name']}: rows give {removed}, stated {stated}"
        if "total_with_pit" in stated:
            assert printed["Total"] - removed == stated["total_with_pit"], f"{pit['name']}: {removed} vs {stated}"
        pit["seats_removed"] = removed
        pit["total_with_pit"] = printed["Total"] - removed
        pit["stated"] = list(stated)

    doc["count_check"] = {"rule": COUNT_RULE, **check}
    out = DATA / f"{doc['venue']['id']}.json"
    with open(out, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"wrote {out.relative_to(DATA.parent)}")
    write_csv(doc, out.with_suffix(".csv"))
    print(f"wrote {out.with_suffix('.csv').relative_to(DATA.parent)}")
    print(json.dumps(check, indent=1))
    for pit in doc.get("orchestra_pits", []):
        print(f"{pit['name']}: rows {', '.join(pit['rows_removed'])} -> -{pit['seats_removed']} = {pit['total_with_pit']}")
    return doc


CSV_COLUMNS = ["venue_id", "part_of_house", "part_of_house_zh", "row", "block", "block_area", "seat",
               "seat_number", "number_basis", "marks", "wheelchair", "management", "restricted_sightline",
               "limited_legroom", "orchestra_pits"]


def csv_rows(doc):
    """One record per seat box, in the order of the JSON (the viewer builds its CSV the same way)."""
    pits = doc.get("orchestra_pits", [])
    for z in doc["zones"]:
        for r in z["rows"]:
            marks = r.get("marks", {})
            for bi, b in enumerate(r["blocks"], 1):
                for s in b["seats"]:
                    m = marks.get(s, "")
                    inferred = r.get("inferred_numbers", {}).get(s)
                    number, basis = (s, "printed") if s.isdigit() else (inferred, "inferred") if inferred else ("", "none")
                    yield {
                        "venue_id": doc["venue"]["id"], "part_of_house": z["name"], "part_of_house_zh": z.get("name_zh", ""),
                        "row": r["row"], "block": bi, "block_area": b.get("area") or b.get("side") or "", "seat": s,
                        "seat_number": number, "number_basis": basis, "marks": m,
                        "wheelchair": int("W" in m), "management": int("X" in m),
                        "restricted_sightline": int("R" in m), "limited_legroom": int("L" in m),
                        "orchestra_pits": "; ".join(p["name"] for p in pits if r["row"] in p["rows_removed"]),
                    }


def write_csv(doc, path):
    # utf-8 with a byte-order mark, so spreadsheet apps read the Chinese names correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(csv_rows(doc))
