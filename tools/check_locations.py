#!/usr/bin/env python3
"""Check each seat list's location against LCSD's open data on DATA.GOV.HK.

Downloads venues.xml (coordinates) and venue.json (addresses) and compares them with the
"location" block of every data/<venue>.json. Also checks the region given in data/index.json
against the venue's district (or, where LCSD gives none, its address). Prints one line per venue;
exits 1 on any mismatch.

Usage: python tools/check_locations.py
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# Hong Kong's 18 districts by region
REGIONS = {
    "Hong Kong Island": ["Central & Western", "Wan Chai", "Eastern", "Southern"],
    "Kowloon": ["Yau Tsim Mong", "Sham Shui Po", "Kowloon City", "Wong Tai Sin", "Kwun Tong"],
    "New Territories": ["Kwai Tsing", "Tsuen Wan", "Tuen Mun", "Yuen Long", "North", "Tai Po", "Sha Tin",
                        "Sai Kung", "Islands"],
}
DISTRICT_REGION = {d: r for r, ds in REGIONS.items() for d in ds}


def region_problem(entry, loc):
    """The index's region must follow the district, or the address where there is no district."""
    region = entry.get("region")
    if region not in REGIONS:
        return f"region {region!r} is not one of {', '.join(REGIONS)}"
    if loc.get("district"):
        want = DISTRICT_REGION.get(loc["district"])
        return None if want == region else f"district {loc['district']} is in {want}, index says {region}"
    addr = loc.get("address_en") or ""
    want = "New Territories" if "New Territories" in addr else "Kowloon" if "Kowloon" in addr else None
    if want is None:
        return f"no district and the address names no region; check {region} by hand"
    return None if want == region else f"address is in {want}, index says {region}"


def fetch(url):
    # the LCSD server refuses Python's default user agent
    req = urllib.request.Request(url, headers={"User-Agent": "hkperf-venue-seats check_locations.py"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    venues = json.loads((DATA / "index.json").read_text())["venues"]
    docs = [json.loads((DATA / v["file"]).read_text()) for v in venues]
    geo_url = docs[0]["location"]["coordinates_source"]["url"]
    geo = {v.get("id"): v for v in ET.fromstring(fetch(geo_url))}
    addr_url = next(d["location"]["address_source"]["url"] for d in docs
                    if d["location"]["address_source"]["url"].endswith("venue.json"))
    addresses = {v["Name_en"]: v for v in json.loads(fetch(addr_url).decode("utf-8-sig"))}

    bad = 0
    for entry, d in zip(venues, docs):
        loc, vid = d["location"], d["venue"]["id"]
        problems = [p for p in [region_problem(entry, loc)] if p]
        g = geo.get(loc["coordinates_source"]["venue_id"])
        if g is None:
            problems.append("venue id not in venues.xml")
        else:
            if g.findtext("venuee") != loc["coordinates_source"]["name_in_source"]:
                problems.append(f"name is now {g.findtext('venuee')!r}")
            lat, lon = float(g.findtext("latitude") or "nan"), float(g.findtext("longitude") or "nan")
            if abs(lat - loc["latitude"]) > 1e-6 or abs(lon - loc["longitude"]) > 1e-6:
                problems.append(f"coordinates are now {lat}, {lon}")
        src, aside = loc["address_source"], ""
        if src["url"].endswith("venue.json"):
            a = addresses.get(src["name_in_source"])
            if a is None:
                problems.append(f"{src['name_in_source']!r} not in venue.json")
            elif a["Address_en"].strip() != loc["address_en"] or a["Address_cn"].strip() != loc["address_zh"]:
                problems.append(f"address is now {a['Address_en']!r} / {a['Address_cn']!r}")
        else:
            aside = f"(address from {src.get('title') or src['url']}, not checked here)"
        bad += bool(problems)
        print(f"{vid:10} {'OK' if not problems else 'MISMATCH'}  {'; '.join(problems)} {aside}".rstrip())
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
