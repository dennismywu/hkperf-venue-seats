#!/usr/bin/env python3
"""Derive straight-run geometry for a round-hall seat list from its published plan, and bake it into
data/<id>.json.

The EKCC Theatre plan draws no curved rows: every block is one or more straight runs of seat boxes,
and where a row turns a corner the plan inserts a single box turned to the in-between angle. This
tool reads every seat box (centre and angle) off the plan, assigns it to its row and seat, splits each
block into runs of boxes that share an angle, and records each run as a straight line:

  shape   "line"
  count   how many of the block's seats (in file order) the run takes
  view    the bearing the run faces (toward the centre); the line is perpendicular to it
  offset  the perpendicular distance from the centre to the line
  start   the bearing of the run's first seat centre
  end     the bearing of the run's last seat centre

A block with a single run carries these directly (shape/view/offset/start/end); a block that bends
lists them under `runs`. Each block's inner/outer are the nearest and farthest radius of its seat
corners, with a small margin, so the boundary arcs enclose the seats without cutting them. Vomitoria
are re-cut to the clear bearing gap between the blocks on either side. Shared arcs (zone.arcs) are
dropped: a run's own geometry replaces them.

Usage:  python tools/derive_runs.py <venue id>
Reads data/<id>.json (the reviewed rows) and the plan named in its `source` (under sources/).
"""
import collections
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pymupdf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCES = ROOT / "sources"
MARGIN = 1.0          # plan units between a seat corner and its block's inner/outer boundary


def find_plan(file_name):
    for p in SOURCES.glob("*.pdf"):
        if p.name == file_name or p.name.endswith(file_name):
            return p
    raise SystemExit(f"plan {file_name!r} not found under sources/")


def seat_boxes(page):
    """Every small seat rectangle on the page: centre, size and the angle of its first edge."""
    out = []
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "qu":
                q = it[1]
                w, h = abs(q.ur - q.ul), abs(q.ll - q.ul)
                if 8 < w < 30 and 8 < h < 30:
                    c = (q.ul + q.lr) / 2
                    out.append({"x": c.x, "y": c.y, "w": w, "h": h,
                                "a": math.degrees(math.atan2(q.ur.y - q.ul.y, q.ur.x - q.ul.x))})
            elif it[0] == "re":
                r = it[1]
                if 8 < r.width < 30 and 8 < r.height < 30:
                    c = (r.tl + r.br) / 2
                    out.append({"x": c.x, "y": c.y, "w": r.width, "h": r.height, "a": 0.0})
    ded = []
    for b in out:
        if not any(abs(b["x"] - o["x"]) < 1 and abs(b["y"] - o["y"]) < 1 for o in ded):
            ded.append(b)
    return ded


def assign(boxes, words, rows, cx, cy):
    """Map (row, seat) -> box. Boxes are grouped by run direction and their perpendicular distance from
    the centre; on each side of the centre the groups are matched to rows in order, inner first."""
    order = [r["row"] for r in rows]
    have = {r["row"]: [s for b in r["blocks"] for s in b["seats"]] for r in rows}
    nums = [w for w in words if re.fullmatch(r"\d{1,3}|W", w["t"])]
    for b in boxes:
        w = min(nums, key=lambda w: (w["x"] - b["x"]) ** 2 + (w["y"] - b["y"]) ** 2)
        b["n"] = w["t"] if (w["x"] - b["x"]) ** 2 + (w["y"] - b["y"]) ** 2 < 40 else None
        long_axis = (b["a"] + (0 if b["w"] < b["h"] else 90)) % 180     # boxes stand across the row
        b["d"] = round(long_axis / 22.5) * 22.5 % 180                  # row direction, 22.5 deg steps
        t = math.radians(b["d"])
        b["p"] = (b["x"] - cx) * -math.sin(t) + (b["y"] - cy) * math.cos(t)
        b["along"] = (b["x"] - cx) * math.cos(t) + (b["y"] - cy) * math.sin(t)

    groups = collections.defaultdict(list)
    for b in boxes:
        groups[b["d"]].append(b)
    corners = []
    for d, bs in groups.items():
        bs.sort(key=lambda b: b["p"])
        cl = []
        for b in bs:
            if cl and abs(b["p"] - cl[-1][-1]["p"]) < 4: cl[-1].append(b)
            else: cl.append([b])
        for side in (-1, 1):
            cs = sorted((c for c in cl if (c[0]["p"] > 0) == (side > 0)), key=lambda c: abs(c[0]["p"]))
            if d % 45:                       # turned corner boxes: placed next to their neighbours below
                corners += cs
                continue
            ri = 0
            for c in cs:
                ns = [b["n"] for b in c if b["n"] and b["n"] != "W"]
                if not ns:
                    continue                 # legend boxes
                while ri < len(order) and not all(n in have[order[ri]] for n in ns): ri += 1
                if ri >= len(order):
                    raise SystemExit(f"no row holds seats {ns}")
                for b in c: b["row"] = order[ri]
                ri += 1
    placed = {(b["row"], b["n"]): b for b in boxes if "row" in b and b["n"] and b["n"].isdigit()}
    for c in corners:
        ns = [b["n"] for b in c]
        best = None
        for r in order:
            if not all(n in have[r] for n in ns) or any((r, n) in placed for n in ns): continue
            dist = [math.hypot(q["x"] - b["x"], q["y"] - b["y"])
                    for b in c for k in (-1, 1) if (q := placed.get((r, str(int(b["n"]) + k))))]
            if dist and (best is None or min(dist) < best[0]): best = (min(dist), r)
        if not best:
            raise SystemExit(f"corner seats {ns}: no row")
        for b in c:
            b["row"] = best[1]
            placed[(best[1], b["n"])] = b

    # boxes without a printed number (W, X) take theirs from the run they sit in
    runs = collections.defaultdict(list)
    for b in boxes:
        if "row" in b: runs[(b["row"], b["d"], round(b["p"]))].append(b)
    for bs in runs.values():
        bs.sort(key=lambda b: b["along"])
        known = [(i, int(b["n"])) for i, b in enumerate(bs) if b["n"] and b["n"].isdigit()]
        sgn = 1 if len(known) < 2 or (known[-1][1] - known[0][1]) * (known[-1][0] - known[0][0]) > 0 else -1
        for i, b in enumerate(bs):
            if not (b["n"] and b["n"].isdigit()):
                j, n = min(known, key=lambda kn: abs(kn[0] - i))
                b["n"] = str(n + sgn * (i - j))
    out = {}
    for b in boxes:
        if "row" in b:
            assert (b["row"], b["n"]) not in out, f"two boxes for {b['row']} {b['n']}"
            out[(b["row"], b["n"])] = b
    return out


def bearing(x, y):
    return (math.degrees(math.atan2(x, -y)) + 360) % 360


def fit_run(idx, pts, d, cx, cy):
    """A straight run through the seats at indices idx (some may lack a box): returns its view, offset
    and the first/last seat centres, from a least-squares fit of position against seat index."""
    I = np.array([i for i, p in zip(idx, pts) if p is not None], float)
    P = np.array([[p["x"] - cx, p["y"] - cy] for p in pts if p is not None])
    if len(P) >= 2:
        A = np.vstack([I, np.ones_like(I)]).T
        coef, *_ = np.linalg.lstsq(A, P, rcond=None)
        first, last = coef[0] * idx[0] + coef[1], coef[0] * idx[-1] + coef[1]
        u = coef[0] / np.linalg.norm(coef[0])
    else:
        first = last = P[0]
        t = math.radians(d)
        u = np.array([math.cos(t), math.sin(t)])
    nrm = np.array([-u[1], u[0]])
    off = float(np.dot(first, nrm))
    if off < 0: off, nrm = -off, -nrm
    view = (bearing(*nrm) + 180) % 360            # facing the centre
    return {"view": round(view, 2), "offset": round(off, 2),
            "start": round(bearing(*first), 2), "end": round(bearing(*last), 2)}, first, last


def main(vid):
    doc = json.loads((DATA / f"{vid}.json").read_text())
    page = pymupdf.open(find_plan(doc["source"]["file"]))[0]
    cx, cy = doc["layout"]["arc"]["centre"]
    words = [{"t": w[4], "x": (w[0] + w[2]) / 2, "y": (w[1] + w[3]) / 2} for w in page.get_text("words")]
    zone = doc["zones"][0]
    rows = zone["rows"]
    seat = assign(seat_boxes(page), words, rows, cx, cy)
    half = 0.5 * float(np.median([max(b["w"], b["h"]) for b in seat.values()]))   # half box diagonal, below

    corner_r = {}                                   # (row, block index) -> seat corner radii
    corners = []                                    # (row, x, y) of every seat corner, about the centre
    for r in rows:
        for bi, b in enumerate(r["blocks"]):
            for k in ("arc", "view", "offset", "start", "end", "inner", "outer", "shape", "runs", "radius"):
                b.pop(k, None)
            ids = b["seats"]
            boxes = [seat.get((r["row"], s)) for s in ids]
            # a seat with no box (the plan drew it some other way) joins the run of its neighbours
            dirs = [bx["d"] if bx else None for bx in boxes]
            for i in range(len(dirs)):
                if dirs[i] is None:
                    dirs[i] = next((dirs[j] for j in range(i - 1, -1, -1) if dirs[j] is not None), None) \
                        or next(dirs[j] for j in range(i + 1, len(dirs)) if dirs[j] is not None)
            # split into runs: a change of angle, or a gap wider than 1.6 seat pitches
            pieces, cur = [], [0]
            for i in range(1, len(ids)):
                p, q = boxes[i - 1], boxes[i]
                gap = p and q and math.hypot(p["x"] - q["x"], p["y"] - q["y"]) > 1.6 * 14
                if dirs[i] != dirs[i - 1] or gap:
                    pieces.append(cur); cur = []
                cur.append(i)
            pieces.append(cur)
            runs, radii = [], []
            for idx in pieces:
                g, first, last = fit_run(idx, [boxes[i] for i in idx], dirs[idx[0]], cx, cy)
                runs.append({"count": len(idx), "shape": "line", **g})
                # seat corners along the fitted line, for the boundaries
                u = (last - first) / (np.linalg.norm(last - first) or 1)
                if not np.linalg.norm(last - first):
                    t = math.radians(dirs[idx[0]]); u = np.array([math.cos(t), math.sin(t)])
                n = np.array([-u[1], u[0]])
                for k, i in enumerate(idx):
                    t = k / (len(idx) - 1) if len(idx) > 1 else 0
                    c = first + (last - first) * t
                    for a in (-half, half):
                        for e in (-half, half):
                            q = c + a * u + e * n
                            radii.append(float(np.linalg.norm(q)))
                            corners.append((r["row"], float(q[0]), float(q[1])))
            if len(runs) == 1:
                b.update({k: v for k, v in runs[0].items() if k != "count"})
            else:
                b["runs"] = runs
            b["inner"] = round(min(radii) - MARGIN, 1)
            b["outer"] = round(max(radii) + MARGIN, 1)
            corner_r[(r["row"], bi)] = radii
    zone.pop("arcs", None)

    # bearings of every seat centre, per block, for the aisles and vomitoria
    def seat_bearings(r, b):
        out = []
        runs = b.get("runs") or [{"count": len(b["seats"]), **{k: b[k] for k in ("start", "end")}}]
        for run in runs:
            out += [run["start"], run["end"]]
        return out

    # shared aisles: the bearing midway between adjacent blocks of a row, clustered across rows
    mids = []
    for r in rows:
        for a, c in zip(r["blocks"], r["blocks"][1:]):
            mids.append((seat_bearings(r, a)[-1] + seat_bearings(r, c)[0]) / 2)
    mids.sort(); clusters = []
    for m in mids:
        if clusters and m - clusters[-1][-1] <= 5: clusters[-1].append(m)
        else: clusters.append([m])
    doc["layout"]["aisles"] = [round(sum(c) / len(c), 1) for c in clusters]

    # vomitoria: the clear bearing gap between the seats either side, over the radius band of the rows it
    # cuts through. A seat corner of those rows bounds the bearings; a corner of any other row (the rows
    # that continue across the entrance) bounds the radii.
    def ang(x, y): return bearing(x, y)
    for v in zone.get("vomitoria", []):
        lo, hi = min(v["from"], v["to"]), max(v["from"], v["to"])
        mid = (lo + hi) / 2
        mine = [(ang(x, y), math.hypot(x, y)) for rl, x, y in corners if rl in v["rows"]]
        near = [(b_, r_) for b_, r_ in mine if abs(b_ - mid) < 20]
        upper = min(b_ for b_, _ in near if b_ > mid)       # first seat corner either side of the gap
        lower = max(b_ for b_, _ in near if b_ < mid)
        others = [math.hypot(x, y) for rl, x, y in corners if rl not in v["rows"]
                  and lower - 2 < ang(x, y) < upper + 2]
        beside = [r_ for b_, r_ in mine if lower - 3 < b_ < upper + 3]   # the seats flanking the gap
        rin, rout = min(beside), max(beside)
        if others: rout = min(rout, min(others) - MARGIN)
        v["from"], v["to"] = round(upper - 0.3, 2), round(lower + 0.3, 2)
        v["inner"], v["outer"] = round(rin - MARGIN, 1), round(rout, 1)
        assert v["from"] > v["to"], f"vomitorium {v['note']}: no clear gap ({v['from']} -> {v['to']})"

    (DATA / f"{vid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    n_runs = sum(len(b.get("runs", [b])) for r in rows for b in r["blocks"])
    print(f"wrote {vid}: {n_runs} straight runs, {len(doc['layout']['aisles'])} aisles")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n")[0])
    main(sys.argv[1])
