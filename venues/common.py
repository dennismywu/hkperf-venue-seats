"""Shared helpers for the venue scripts: build rows, check counts, write data/<id>.json.

A venue script holds only facts read from LCSD sources. finish() checks them and fails loudly:
  - each zone: boxes on the plan minus management seats (X) = the printed zone total (zones with counted_in:
    together, against the one figure the operator gives for them)
  - each orchestra pit: seats in its rows or blocks (minus X) = the stated loss, and the total follows
"""
import csv
import json
from pathlib import Path

SCHEMA = "hkperf-venue-seats/seatlist@0.5"
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


BANK_SIDES = {"front", "back", "left", "right"}
LEVEL_SIDES = ("front", "back")          # banks drawn level, facing the stage
BANK_ALIGN = {"downstage", "upstage", "stage", "house", "room"}


def find_row(doc, ref):
    """A bank's row reference -> (zone name, row). ref: "AA", or {row, zone?, block?}; zone is needed when the
    letter repeats across parts of house."""
    label = ref if isinstance(ref, str) else ref["row"]
    zone = None if isinstance(ref, str) else ref.get("zone")
    hits = [(z["name"], r) for z in doc["zones"] if zone in (None, z["name"]) for r in z["rows"] if r["row"] == label]
    assert hits, f"no row {zone + ' ' if zone else ''}{label}"
    assert len(hits) == 1, f"row {label} is in {', '.join(h[0] for h in hits)}: name its zone"
    return hits[0]


def ref_blocks(ref, row):
    """Block indexes a reference covers: all of them, or the one it names."""
    if isinstance(ref, str) or "block" not in ref:
        return range(len(row["blocks"]))
    return [b - 1 for b in (ref["block"] if isinstance(ref["block"], list) else [ref["block"]])]


def ref_text(ref):
    """"A", or "Stalls 1 C block 2"."""
    if isinstance(ref, str):
        return ref
    return " ".join(filter(None, [ref.get("zone"), ref["row"], f"block {'-'.join(map(str, ref['block'])) if isinstance(ref['block'], list) else ref['block']}" if "block" in ref else ""]))


def pit_seats(doc, pit):
    """The seats an orchestra pit removes, as (zone, row, seat). rows_removed takes the same references as
    a bank: a row label, or {row, zone?, block?} when the label repeats or the pit takes one block of a row."""
    out = []
    for ref in pit["rows_removed"]:
        zone, r = find_row(doc, ref)
        out += [(zone, r["row"], s) for i in ref_blocks(ref, r) for s in r["blocks"][i]["seats"]]
    assert len(set(out)) == len(out), f"{pit['name']}: a seat is listed twice"
    return out


def bank_of(doc):
    """(zone, row, block index) -> the id of the bank it is in; empty when the layout has no banks."""
    out = {}
    for b in doc.get("layout", {}).get("banks") or []:
        for ref in b["rows"]:
            zone, r = find_row(doc, ref)
            out.update({(zone, r["row"], i): b["id"] for i in ref_blocks(ref, r)})
    return out


def aisle_banks(*parts):
    """Banks for halls whose rows run left block · centre block · right block (seat 1 at the left), with
    the row labels in the aisles. parts: (id prefix, rows) or (id prefix, rows, zone name) per part of
    house; give the zone when row letters repeat across parts. A row with one block is centre only; a
    row with two blocks has side blocks only, level with the rows either side of it; a row with four
    has a centre in two runs (blocks 2-3)."""
    banks = []
    for prefix, rows, *zone in parts:
        ref = (lambda r, blk: {"zone": zone[0], "row": r["row"], "block": blk}) if zone else (lambda r, blk: {"row": r["row"], "block": blk})
        centre = f"{prefix}-centre"
        mid = {3: 2, 1: 1, 4: [2, 3]}
        banks += [
            {"id": centre, "side": "front", "rows": [ref(r, mid[len(r["blocks"])]) for r in rows if len(r["blocks"]) in mid],
             "seat_1": "left"},
            {"id": f"{prefix}-left", "side": "left", "rows": [ref(r, 1) for r in rows if len(r["blocks"]) > 1],
             "rows_run": "across", "seat_1": "left", "beside": centre},
            {"id": f"{prefix}-right", "side": "right", "rows": [ref(r, len(r["blocks"])) for r in rows if len(r["blocks"]) > 1],
             "rows_run": "across", "seat_1": "left", "beside": centre},
        ]
    return banks


def check_banks(doc):
    """layout.banks, when given, must place every block of every row exactly once."""
    banks = doc.get("layout", {}).get("banks")
    if not banks:
        return
    fronts = {b["id"] for b in banks if b["side"] in LEVEL_SIDES}
    front_rows = {(find_row(doc, r)[0], find_row(doc, r)[1]["row"]) for f in banks if f["side"] in LEVEL_SIDES for r in f["rows"]}
    placed = {}
    for b in banks:
        assert b["side"] in BANK_SIDES, f"bank {b['id']}: side {b['side']!r}"
        run = b.get("rows_run", "along")
        assert b["side"] in LEVEL_SIDES or run in ("along", "across"), f"bank {b['id']}: rows_run {run!r}"
        level = b["side"] in LEVEL_SIDES or run == "across"       # rows drawn level, numbered left/right
        assert b.get("seat_1", "left" if level else "downstage") in ({"left", "right"} if level else {"downstage", "upstage"}), \
            f"bank {b['id']}: seat_1 {b.get('seat_1')!r}"
        assert not b.get("in_line") or (b["side"] not in LEVEL_SIDES and run == "along"), f"bank {b['id']}: in_line needs upright side rows"
        assert "after" not in b or (b["side"] not in LEVEL_SIDES and b["after"] in fronts), f"bank {b['id']}: after {b.get('after')!r}"
        assert "beside" not in b or (b["side"] not in LEVEL_SIDES and run == "across" and b["beside"] in fronts and "after" not in b), \
            f"bank {b['id']}: beside {b.get('beside')!r} needs a front bank and rows running across"
        if "level_with" in b:
            zone, r = find_row(doc, b["level_with"])
            assert b["side"] not in LEVEL_SIDES and (zone, r["row"]) in front_rows and not {"after", "beside"} & set(b), \
                f"bank {b['id']}: level_with {b['level_with']!r} must be a row of a front or back bank"
        assert b["side"] in LEVEL_SIDES or {"after", "beside", "level_with"} & set(b) or b.get("align", "downstage") in BANK_ALIGN, f"bank {b['id']}: align"
        for ref in b["rows"]:
            zone, r = find_row(doc, ref)
            for i in ref_blocks(ref, r):
                key = (zone, r["row"], i)
                assert 0 <= i < len(r["blocks"]), f"bank {b['id']}: {zone} row {r['row']} has no block {i + 1}"
                assert key not in placed, f"{zone} row {r['row']} block {i + 1} is in banks {placed[key]} and {b['id']}"
                placed[key] = b["id"]
    missing = [f"{z['name']} {r['row']} block {i + 1}" for z in doc["zones"] for r in z["rows"]
               for i in range(len(r["blocks"])) if (z["name"], r["row"], i) not in placed]
    assert not missing, f"not in any bank: {', '.join(missing)}"


def _seats(rows):
    return sum(len(b["seats"]) for r in rows for b in r["blocks"])


def _marked(rows, mark):
    # a seat's mark is one or more letters, e.g. "R" or "RL" (restricted sightline and limited legroom)
    return sum(1 for r in rows for m in r.get("marks", {}).values() if mark in m)


def finish(doc):
    """Check doc against its printed and stated figures, then write data/<venue id>.json."""
    doc = {"schema": SCHEMA, **doc}
    printed = doc["printed_totals"]
    rows_by = {(z["name"], r["row"]): r for z in doc["zones"] for r in z["rows"]}

    check = {}
    for z in doc["zones"]:
        boxes, x = _seats(z["rows"]), _marked(z["rows"], "X")
        # A part of house whose official figure also counts its management seats (count_includes X), or leaves
        # out a kind of seat it has (count_excludes, e.g. W, or "*" for a zone the operator gives no figure
        # for at all), says so, and why.
        with_x = "X" in z.get("count_includes", [])
        without = z.get("count_excludes", [])
        assert set(z.get("count_includes", [])) <= {"X"}, f"{z['name']}: count_includes takes only X"
        assert "X" not in without, f"{z['name']}: X is left out already"
        assert not (with_x or without) or z.get("count_note"), f"{z['name']}: count_includes/count_excludes needs a count_note"
        left_out = boxes if "*" in without else sum(_marked(z["rows"], m) for m in without)
        counted = (boxes if with_x else boxes - x) - left_out
        check[z["name"]] = {"boxes": boxes, "management_X": x, "wheelchair_W": _marked(z["rows"], "W"),
                            "restricted_R": _marked(z["rows"], "R"), "limited_legroom_L": _marked(z["rows"], "L"),
                            "boxes_minus_X": boxes - x,
                            **({"counted_with_X": boxes, "exception": z["count_note"]} if with_x else {}),
                            **({f"counted_without_{''.join(without)}": counted, "exception": z["count_note"]} if without else {})}
        if "counted_in" in z:
            # parts of house the operator totals together (counted_in names the shared figure): checked below
            assert not (with_x or without), f"{z['name']}: count_includes/count_excludes is not supported with counted_in"
            assert z["counted_in"] not in {y["name"] for y in doc["zones"]}, f"{z['name']}: counted_in names a zone"
            check[z["name"]]["counted_in"] = z["counted_in"]
            continue
        check[z["name"]]["printed"] = printed[z["name"]]
        assert counted == printed[z["name"]], f"{z['name']}: {boxes} boxes - {x} X{f' - {left_out} {without}' if without else ''} != {printed[z['name']]}"
    groups = {}
    for z in doc["zones"]:
        if "counted_in" in z:
            groups.setdefault(z["counted_in"], []).append(z)
    for name, zs in groups.items():
        assert len(zs) > 1, f"{name}: counted_in needs two or more zones"
        boxes, x = sum(check[z["name"]]["boxes"] for z in zs), sum(check[z["name"]]["management_X"] for z in zs)
        check[name] = {"zones": [z["name"] for z in zs], "boxes": boxes, "management_X": x, "boxes_minus_X": boxes - x,
                       "printed": printed[name]}
        assert boxes - x == printed[name], f"{name} ({', '.join(check[name]['zones'])}): {boxes} boxes - {x} X != {printed[name]}"
    totals = [z["name"] for z in doc["zones"] if "counted_in" not in z] + list(groups)
    assert sum(printed[n] for n in totals) == printed["Total"], "zone totals do not add up"

    for pit in doc.get("orchestra_pits", []):
        seats = pit_seats(doc, pit)
        removed = sum(1 for zone, lab, s in seats if "X" not in rows_by[zone, lab].get("marks", {}).get(s, ""))
        stated = pit.pop("stated")
        if "seats_removed" in stated:
            assert removed == stated["seats_removed"], f"{pit['name']}: rows give {removed}, stated {stated}"
        if "total_with_pit" in stated:
            assert printed["Total"] - removed == stated["total_with_pit"], f"{pit['name']}: {removed} vs {stated}"
        pit["seats_removed"] = removed
        pit["total_with_pit"] = printed["Total"] - removed
        pit["stated"] = list(stated)

    check_banks(doc)
    doc["count_check"] = {"rule": COUNT_RULE, **check}
    out = DATA / f"{doc['venue']['id']}.json"
    with open(out, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"wrote {out.relative_to(DATA.parent)}")
    write_csv(doc, out.with_suffix(".csv"))
    print(f"wrote {out.with_suffix('.csv').relative_to(DATA.parent)}")
    print(json.dumps(check, indent=1))
    for pit in doc.get("orchestra_pits", []):
        print(f"{pit['name']}: rows {', '.join(map(ref_text, pit['rows_removed']))} -> -{pit['seats_removed']} = {pit['total_with_pit']}")
    return doc


CSV_COLUMNS = ["venue_id", "part_of_house", "part_of_house_zh", "row", "block", "block_area", "bank", "seat",
               "seat_number", "number_basis", "marks", "wheelchair", "management", "restricted_sightline",
               "limited_legroom", "orchestra_pits"]


def csv_rows(doc):
    """One record per seat box, in the order of the JSON (the viewer builds its CSV the same way)."""
    pits = [(p["name"], set(pit_seats(doc, p))) for p in doc.get("orchestra_pits", [])]
    bank = bank_of(doc)
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
                        "row": r["row"], "block": bi, "block_area": b.get("area") or b.get("side") or "", "bank": bank.get((z["name"], r["row"], bi - 1), ""), "seat": s,
                        "seat_number": number, "number_basis": basis, "marks": m,
                        "wheelchair": int("W" in m), "management": int("X" in m),
                        "restricted_sightline": int("R" in m), "limited_legroom": int("L" in m),
                        "orchestra_pits": "; ".join(name for name, seats in pits if (z["name"], r["row"], s) in seats),
                    }


def write_csv(doc, path):
    # utf-8 with a byte-order mark, so spreadsheet apps read the Chinese names correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(csv_rows(doc))
