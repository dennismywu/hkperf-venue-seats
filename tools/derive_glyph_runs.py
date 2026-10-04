#!/usr/bin/env python3
"""Derive straight-run geometry for a seat list whose plan draws its numbers as outlines (no text layer),
and bake it into data/<id>.json.

Some LCSD plans (the Hong Kong Cultural Centre Concert Hall's) are vector drawings in which every seat
number is a filled outline, not text, so tools/derive_runs.py has no words to read. This tool reads
the plan the same way it was read by hand:

  1. every seat box: a stroked rectangle or quadrilateral, upright or turned
  2. every digit: a small filled outline, recognised by its path operators (the plan's one font draws
     each digit with its own sequence of lines and curves, listed in DIGITS)
  3. a box's number: the digits inside it, read along its long side
  4. straight runs: boxes side by side, turned the same way, one box apart
  5. blocks: runs joined where the numbers run on (a block that bends)

It then finds each block of the seat list among the plan's blocks by its numbers (a box with no
number, e.g. a crossed management seat, matches any unnumbered seat id). Where blocks in several rows
share the same numbers, see assign(). Every run is
recorded as tools/derive_runs.py records it (shape "line", view, offset, start, end; inner/outer
bounds), about layout.arc.centre.

Usage:  python tools/derive_glyph_runs.py <venue id>
Reads data/<id>.json and the plan named in its `source` (under sources/; page source.pdf_page, from 1).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_runs import DATA, MARGIN, SOURCES, find_plan, fit_run  # noqa: E402

# the path operators of each digit outline (l = line, c = curve), in the plan's font
DIGITS = {
    "cccccccccccccccccccccccccccccccc": "0",
    "ccccllllll": "1",
    "lcccccccccccccclccccccccccccccccll": "2",
    "cccccccccclcccccccccclcccccccccclccccccccl": "3",
    "lllllllllllllll": "4",
    "lllllcccccccccccccclccccccccccccll": "5",
    "cccccccccccccccccccccccclccccccccccccccccccccccl": "6",
    "llcccclccccll": "7",
    "cccccccccccccccccccccclcccccccclcccccc": "8",
    "cccccccccccccccccccccclccccccccccccccccccccccl": "9",
}


def inside(pt, poly):
    x, y = pt
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def read_boxes(page):
    """Seat boxes with their numbers: centre, unit vector along the long side, length, width, number."""
    boxes, digits = [], []
    for d in page.get_drawings():
        ops = "".join(it[0] for it in d["items"])
        r = d["rect"]
        if d.get("color") is not None and ops in ("qu", "re") and 7 <= max(r.width, r.height) <= 22:
            if ops == "qu":
                q = d["items"][0][1]
                pts = [(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y)]
            else:
                q = d["items"][0][1]
                pts = [(q.x0, q.y0), (q.x1, q.y0), (q.x1, q.y1), (q.x0, q.y1)]
            boxes.append(pts)
        elif d.get("fill") is not None and d.get("color") is None and ops in DIGITS and max(r.width, r.height) < 11:
            digits.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, DIGITS[ops]))
    out = []
    for pts in boxes:
        e1 = np.subtract(pts[1], pts[0]); e2 = np.subtract(pts[2], pts[1])
        a, b = np.linalg.norm(e1), np.linalg.norm(e2)
        u = (e1 if a >= b else e2) / max(a, b)
        c = np.mean(pts, axis=0)
        ds = sorted((g for g in digits if inside(g[:2], pts)), key=lambda g: g[0] * u[0] + g[1] * u[1])
        out.append({"c": c, "u": u, "len": max(a, b), "wid": min(a, b), "digits": ds})
    return out


def runs_of(boxes):
    """Straight runs: chains of boxes turned the same way, side by side along their long side."""
    n = len(boxes)
    adj = [[] for _ in range(n)]
    for i in range(n):
        a = boxes[i]
        for j in range(i + 1, n):
            b = boxes[j]
            if abs(abs(float(np.dot(a["u"], b["u"]))) - 1) > 0.05:
                continue
            d = b["c"] - a["c"]
            along, perp = float(np.dot(d, a["u"])), float(d[1] * a["u"][0] - d[0] * a["u"][1])
            if 0.5 * a["len"] < abs(along) < 1.45 * a["len"] and abs(perp) < 0.4 * a["wid"]:
                adj[i].append(j); adj[j].append(i)
    assert all(len(v) <= 2 for v in adj), "a box with three neighbours"
    seen, runs = set(), []
    for i in range(n):
        if i in seen or len(adj[i]) == 2:
            continue
        ch = [i]; seen.add(i)
        while nxt := [j for j in adj[ch[-1]] if j not in seen]:
            ch.append(nxt[0]); seen.add(nxt[0])
        runs.append(ch)
    assert len(seen) == n, "boxes in a closed loop"
    out = []
    for ch in runs:
        # read each box's digits along the run, both ways round; keep the way the numbers count up by one
        best = None
        for sign in (1, -1):
            u = boxes[ch[-1]]["c"] - boxes[ch[0]]["c"] if len(ch) > 1 else boxes[ch[0]]["u"]
            u = sign * u / np.linalg.norm(u)
            text = ["".join(g[2] for g in sorted(boxes[k]["digits"], key=lambda g: g[0] * u[0] + g[1] * u[1]))
                    for k in ch]
            nums = [int(t) if t else None for t in text]
            score = sum(1 for x, y in zip(nums, nums[1:]) if x is not None and y is not None and abs(x - y) == 1)
            if best is None or score > best[0]:
                best = (score, text)
        text = best[1]
        nums = [int(t) for t in text if t]
        if len(nums) > 1 and nums[0] > nums[-1]:
            ch, text = ch[::-1], text[::-1]
        out.append({"boxes": ch, "text": text})
    return out


def first_last(run):
    known = [(i, int(t)) for i, t in enumerate(run["text"]) if t]
    if not known:
        return None, None
    (i0, n0), (i1, n1) = known[0], known[-1]
    return n0 - i0, n1 + len(run["text"]) - 1 - i1


def blocks_of(boxes, runs):
    """Join runs into blocks where one run's numbers carry on from the last box of another, close by."""
    cand = []
    for i, a in enumerate(runs):
        for j, b in enumerate(runs):
            if i == j or not any(a["text"]) or not any(b["text"]):
                continue
            if first_last(b)[0] != first_last(a)[1] + 1:
                continue
            d = float(np.linalg.norm(boxes[a["boxes"][-1]]["c"] - boxes[b["boxes"][0]]["c"]))
            if d < 1.7 * boxes[a["boxes"][-1]]["len"]:
                cand.append((d, i, j))
    nxt, prv = {}, {}
    for d, i, j in sorted(cand):
        if i not in nxt and j not in prv:
            nxt[i], prv[j] = j, i
    out = []
    for i in range(len(runs)):
        if i in prv:
            continue
        seq = [i]
        while seq[-1] in nxt:
            seq.append(nxt[seq[-1]])
        out.append({"runs": [runs[k] for k in seq],
                    "text": [t for k in seq for t in runs[k]["text"]],
                    "boxes": [b for k in seq for b in runs[k]["boxes"]]})
    return out


def key(seats):
    return tuple(s if s.isdigit() else None for s in seats)


def assign(doc, boxes, plan_blocks, centre):
    """(zone, row, block index) -> plan block, matched by numbers. Where several rows have a block with the
    same numbers: within one part of house, the rows count outward from the platform, so the blocks go in
    order of their distance from the centre; across parts of house, a block goes to the part of house
    whose placed blocks it sits next to."""
    want = [(zi, ri, bi, key(b["seats"])) for zi, z in enumerate(doc["zones"]) for ri, r in enumerate(z["rows"])
            for bi, b in enumerate(r["blocks"])]
    by_key = {}
    for k, pb in enumerate(plan_blocks):
        by_key.setdefault(key([t or "-" for t in pb["text"]]), []).append(k)
    name = lambda w: f"{doc['zones'][w[0]]['name']} {doc['zones'][w[0]]['rows'][w[1]]['row']} block {w[2] + 1}"
    for w in want:
        assert len(by_key.get(w[3], [])) >= sum(1 for v in want if v[3] == w[3]), f"{name(w)}: not on the plan"
    radius = lambda k: float(np.mean([np.linalg.norm(boxes[b]["c"] - centre) for b in plan_blocks[k]["boxes"]]))
    ends = lambda k: [boxes[plan_blocks[k]["boxes"][0]]["c"], boxes[plan_blocks[k]["boxes"][-1]]["c"]]
    taken, got = set(), {}

    def put(w, k):
        got[w[:3]] = k; taken.add(k)

    while len(got) < len(want):
        open_ = [w for w in want if w[:3] not in got]
        groups = {}
        for w in open_:
            groups.setdefault(w[3], []).append(w)
        done = False
        for k, ws in groups.items():
            free = [c for c in by_key[k] if c not in taken]
            if len(free) == 1 or (len({w[0] for w in ws}) == 1 and len(free) == len(ws)):
                for w, c in zip(sorted(ws, key=lambda w: w[1]), sorted(free, key=radius)):
                    put(w, c)
                done = True
        if done:
            continue
        # across parts of house: the open block nearest an already placed block of its own part of house,
        # decided where the nearest candidate is clearly nearer than the next
        best = None
        for w in open_:
            mine = [got[v] for v in got if v[0] == w[0]]
            if not mine:
                continue
            free = [c for c in by_key[w[3]] if c not in taken]
            d = sorted((min(float(np.linalg.norm(a - b)) for m in mine for a in ends(m) for b in ends(c)), c) for c in free)
            ratio = d[1][0] / max(d[0][0], 1e-6) if len(d) > 1 else math.inf
            if best is None or ratio > best[0]:
                best = (ratio, w, d[0][1])
        if best is None or best[0] < 1.2:
            raise SystemExit(f"cannot place: {', '.join(name(w) for w in open_)}")
        put(best[1], best[2])
    return got, [k for k in range(len(plan_blocks)) if k not in taken]


GEOMETRY = ("shape", "view", "offset", "start", "end", "inner", "outer", "radius", "runs")


def apply_overrides(doc, vid):
    """Hand-tuned geometry (venues/<id>.geometry.json, from the row reviewer) replaces the derived geometry
    of the blocks it names, so a rebuild keeps it. Each entry names its zone, row, block (from 1) and the
    block's first seat; a block that no longer matches fails loudly rather than tuning the wrong seats."""
    path = Path(__file__).resolve().parent.parent / "venues" / f"{vid}.geometry.json"
    if not path.exists():
        return 0
    for o in json.loads(path.read_text())["blocks"]:
        z = next((z for z in doc["zones"] if z["name"] == o["zone"]), None)
        r = z and next((r for r in z["rows"] if r["row"] == o["row"]), None)
        b = r and 0 < o["block"] <= len(r["blocks"]) and r["blocks"][o["block"] - 1]
        assert b and b["seats"][0] == o["first_seat"], \
            f"{path.name}: {o['zone']} {o['row']} block {o['block']} (first seat {o['first_seat']}) is not in the seat list"
        for f in GEOMETRY:
            b.pop(f, None)
        # keep the file's key order: seats first, then geometry as derive_runs.py writes it
        b.update({f: o[f] for f in GEOMETRY if f in o})
    return len(json.loads(path.read_text())["blocks"])


def main(vid):
    doc = json.loads((DATA / f"{vid}.json").read_text())
    exact = SOURCES / doc["source"]["file"]           # the exact name first: other copies may share a suffix
    plan = exact if exact.exists() else find_plan(doc["source"]["file"])
    page = pymupdf.open(plan)[doc["source"].get("pdf_page", 1) - 1]
    cx, cy = doc["layout"]["arc"]["centre"]
    boxes = read_boxes(page)
    plan_blocks = blocks_of(boxes, runs_of(boxes))
    got, spare = assign(doc, boxes, plan_blocks, np.array([cx, cy]))
    half = 0.5 * float(np.median([b["len"] for b in boxes]))
    for (zi, ri, bi), k in got.items():
        b = doc["zones"][zi]["rows"][ri]["blocks"][bi]
        for f in ("arc", "view", "offset", "start", "end", "inner", "outer", "shape", "runs", "radius"):
            b.pop(f, None)
        runs, radii, at = [], [], 0
        for run in plan_blocks[k]["runs"]:
            pts = [{"x": boxes[i]["c"][0], "y": boxes[i]["c"][1]} for i in run["boxes"]]
            idx = list(range(at, at + len(pts))); at += len(pts)
            u = boxes[run["boxes"][0]]["u"]
            g, first, last = fit_run(idx, pts, math.degrees(math.atan2(u[1], u[0])), cx, cy)
            runs.append({"count": len(pts), "shape": "line", **g})
            for p in pts:
                for dx in (-half, half):
                    for dy in (-half, half):
                        radii.append(math.hypot(p["x"] - cx + dx, p["y"] - cy + dy))
        if len(runs) == 1:
            b.update({f: v for f, v in runs[0].items() if f != "count"})
        else:
            b["runs"] = runs
        b["inner"] = round(min(radii) - MARGIN, 1)
        b["outer"] = round(max(radii) + MARGIN, 1)
    for z in doc["zones"]:
        z.pop("arcs", None)
    tuned = apply_overrides(doc, vid)
    (DATA / f"{vid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    if tuned:
        print(f"applied {tuned} hand-tuned block(s) from venues/{vid}.geometry.json")
    n_runs = sum(len(b.get("runs", [b])) for z in doc["zones"] for r in z["rows"] for b in r["blocks"])
    print(f"wrote {vid}: {len(got)} blocks, {n_runs} straight runs")
    for k in spare:
        pb = plan_blocks[k]
        c = boxes[pb["boxes"][0]]["c"]
        print(f"  not used: {len(pb['boxes'])} box(es) {' '.join(t or 'x' for t in pb['text'])} at ({c[0]:.0f}, {c[1]:.0f})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n")[0])
    main(sys.argv[1])
