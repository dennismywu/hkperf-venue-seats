#!/usr/bin/env python3
"""Derive the arc geometry of a round-hall seat list from its published plan, and bake it into
data/<id>.json.

A round hall's rows are not concentric arcs but chains of straight runs. For every block the tool
finds the plan's seat rectangles, fits the run, and records:

  view    the bearing the seats face (toward the stage centre)
  offset  the perpendicular distance from the centre to the run
  start   the bearing of the block's first seat
  end     the bearing of the block's last seat
  inner   the nearest radius of the block's seats   (the inner boundary arc)
  outer   the farthest radius of the block's seats  (the outer boundary arc)

It then clusters the internal block boundaries into the hall's shared aisles (`layout.aisles`) and
snaps every internal boundary to one, so aisles line up across rows. Finally it groups blocks that
share an aisle interval into arcs (`layout.arcs`) and replaces the per-block geometry with a
reference to the arc plus the row's radial offset, keeping per-block overrides only where a block
deviates from its arc.

Usage:  python tools/derive_arc.py <venue id>
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


def find_plan(file_name):
    for p in SOURCES.glob("*.pdf"):
        if p.name == file_name or p.name.endswith(file_name):
            return p
    raise SystemExit(f"plan {file_name!r} not found under sources/")


def seat_boxes(page):
    """Every small seat rectangle on the page, upright or turned: (x, y) of its centre."""
    out = []
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "qu":
                q = it[1]
                w, h = abs(q.ur - q.ul), abs(q.ll - q.ul)
                if 8 < w < 30 and 8 < h < 30:
                    c = (q.ul + q.lr) / 2
                    out.append((c.x, c.y))
            elif it[0] == "re":
                r = it[1]
                if 8 < r.width < 30 and 8 < r.height < 30:
                    c = (r.tl + r.br) / 2
                    out.append((c.x, c.y))
    return out


def main(vid):
    doc = json.loads((DATA / f"{vid}.json").read_text())
    plan_path = find_plan(doc["source"]["file"])
    pdf = pymupdf.open(plan_path)
    page = pdf[0]

    # centre: the point the row-label bearings close on (fit from the letters on the plan, if any),
    # else the mean of the seats.  For these plans the stage centre lies on the vertical through the
    # hall; derive it by minimising the spread of the labels' radii when there are letters.
    boxes = seat_boxes(page)
    words = page.get_text("words")
    nums = [(w[4], (w[0] + w[2]) / 2, (w[1] + w[3]) / 2) for w in words if re.fullmatch(r"\d{1,3}", w[4])]
    letters = [(w[4], (w[0] + w[2]) / 2, (w[1] + w[3]) / 2) for w in words if re.fullmatch(r"[A-Z]", w[4])]
    cx = np.mean([x for x, _ in boxes]); cy = np.mean([y for _, y in boxes])
    if doc['layout'].get('arc', {}).get('centre'):
        cx, cy = doc['layout']['arc']['centre']
    elif letters:
        best = None
        for gx in np.arange(min(x for x, _ in boxes), max(x for x, _ in boxes) + 1, 10):
            for gy in np.arange(min(y for _, y in boxes) - 400, max(y for _, y in boxes) + 1, 10):
                g = collections.defaultdict(list)
                for lab, x, y in letters:
                    g[lab].append(math.hypot(x - gx, y - gy))
                s = sum(sum((v - sum(vs) / len(vs)) ** 2 for v in vs) for vs in g.values() if len(vs) > 1)
                if best is None or s < best[0]:
                    best = (s, gx, gy)
        cx, cy = best[1], best[2]

    # match each seat box to its number
    seat_num = {}
    for i, (x, y) in enumerate(boxes):
        best = None; bd = 1e9
        for n, nx, ny in nums:
            d = (nx - x) ** 2 + (ny - y) ** 2
            if d < bd: bd, best = d, n
        if bd < 120:
            seat_num[i] = int(best)

    zones = doc["zones"]
    for zi, zone in enumerate(zones):
        rows = zone["rows"]
        # rows are ordered inner -> outer; rank-match seats of each number to the rows that hold it
        row_has = {}
        for ri, r in enumerate(rows):
            for n in {int(s) for b in r["blocks"] for s in b["seats"] if s.isdigit()}:
                row_has.setdefault(n, []).append(ri)
        Pn = collections.defaultdict(list)
        for i, (x, y) in enumerate(boxes):
            if i in seat_num:
                Pn[seat_num[i]].append((x, y))
        xy = {}
        for n, ris in row_has.items():
            q = sorted(Pn.get(n, []), key=lambda p: math.hypot(p[0] - cx, p[1] - cy))
            for k, ri in enumerate(sorted(ris)):
                if k < len(q):
                    xy[(ri, n)] = q[k]

        def bearing(p):
            return (math.degrees(math.atan2(p[0] - cx, -(p[1] - cy))) + 360) % 360

        # 1) fit every block
        for ri, r in enumerate(rows):
            for b in r["blocks"]:
                for k in ("view", "offset", "start", "end", "inner", "outer", "arc"):
                    b.pop(k, None)
                pts = [(n,) + xy[(ri, n)] for n in (int(s) for s in b["seats"] if s.isdigit()) if (ri, n) in xy]
                if len(pts) >= 2:
                    P = np.array([[x, y] for _, x, y in pts]); c = P.mean(axis=0)
                    _, _, vt = np.linalg.svd(P - c); nrm = vt[1]
                    off = float(np.dot(c - [cx, cy], nrm))
                    if off < 0: off, nrm = -off, -nrm
                    b["view"] = round((math.degrees(math.atan2(nrm[0], -nrm[1])) + 180) % 360, 1)
                    b["offset"] = round(off, 1)
                    b["start"] = round(bearing(xy[(ri, int(b["seats"][0]))]), 1) if (ri, int(b["seats"][0])) in xy else None
                    b["end"] = round(bearing(xy[(ri, int(b["seats"][-1]))]), 1) if (ri, int(b["seats"][-1])) in xy else None
                    rad = [math.hypot(x - cx, y - cy) for _, x, y in pts]
                    b["inner"], b["outer"] = round(min(rad), 1), round(max(rad), 1)

        # 2) shared aisles from internal boundaries
        mids = []
        for r in rows:
            for k in range(len(r["blocks"]) - 1):
                a, c = r["blocks"][k], r["blocks"][k + 1]
                if a.get("end") is not None and c.get("start") is not None:
                    mids.append((a["end"] + c["start"]) / 2)
        mids.sort(); clusters = []
        for m in mids:
            if clusters and m - clusters[-1][-1] <= 5: clusters[-1].append(m)
            else: clusters.append([m])
        aisles = [round(sum(c) / len(c), 1) for c in clusters]

        def snap(x): return min(aisles, key=lambda a: abs(((a - x + 180) % 360) - 180)) if aisles else x
        for r in rows:
            bl = r["blocks"]
            for k in range(len(bl) - 1):
                a, c = bl[k], bl[k + 1]
                if a.get("end") is not None and c.get("start") is not None:
                    a["end"] = c["start"] = snap((a["end"] + c["start"]) / 2)
                elif a.get("end") is not None:
                    c["start"] = c["end"] = a["end"]
            for k, b in enumerate(bl):                       # inherit axis for unfitted blocks
                if b.get("view") is None:
                    src = next((bl[j] for j in range(k - 1, -1, -1) if bl[j].get("view") is not None), None) \
                        or next((bl[j] for j in range(k + 1, len(bl)) if bl[j].get("view") is not None), None)
                    if src:
                        b["view"], b["offset"] = src["view"], src["offset"]
                        b.setdefault("inner", src.get("inner")); b.setdefault("outer", src.get("outer"))
            for k, b in enumerate(bl):                       # fill any unset bounds
                if b.get("start") is None:
                    b["start"] = (bl[k - 1].get("end") if k else None) or (bl[k + 1].get("start") if k + 1 < len(bl) else None) or (b.get("end") or 0)
                if b.get("end") is None:
                    b["end"] = (bl[k + 1].get("start") if k + 1 < len(bl) else None) or (bl[k - 1].get("end") if k else None) or b["start"]

        # 3) rows carry a radial offset; internal blocks (both bounds on shared aisles) reference an
        #    arc, keeping only per-block overrides; row-end blocks keep their own geometry
        meds = [float(np.median([b["offset"] for b in r["blocks"] if b.get("offset") is not None])) if any(b.get("offset") is not None for b in r["blocks"]) else None for r in rows]
        diffs = [b - a for a, b in zip(meds, meds[1:]) if a is not None and b is not None]
        pitch = round(float(np.median(diffs)), 1) if diffs else 25.0
        for ri, r in enumerate(rows):
            r["offset"] = round(ri * pitch, 1)                 # rows are evenly spaced outward

        def is_aisle(x):
            return x is not None and any(abs(((x - a + 180) % 360) - 180) < 1.5 for a in aisles)

        arcs = {}
        for r in rows:
            for b in r["blocks"]:
                if is_aisle(b.get("start")) and is_aisle(b.get("end")):
                    a = arcs.setdefault((round(b["start"]), round(b["end"])), {"view": [], "offset": [], "inner": [], "outer": []})
                    if b.get("view") is not None: a["view"].append(b["view"])
                    if b.get("offset") is not None: a["offset"].append(b["offset"] - r["offset"])
                    if b.get("inner") is not None: a["inner"].append(b["inner"])
                    if b.get("outer") is not None: a["outer"].append(b["outer"])
        layout_arcs = []
        for (s, e), a in arcs.items():
            layout_arcs.append({"id": f"a{len(layout_arcs) + 1}", "from": s, "to": e,
                                "view": round(float(np.median(a["view"])), 1) if a["view"] else 0,
                                "offset": round(float(np.median(a["offset"])), 1) if a["offset"] else 0,
                                "inner": round(float(np.median(a["inner"])), 1) if a["inner"] else None,
                                "outer": round(float(np.median(a["outer"])), 1) if a["outer"] else None})
        layout_arcs.sort(key=lambda x: -x["from"])
        by_key = {(arc["from"], arc["to"]): arc for arc in layout_arcs}
        for r in rows:
            nb = []
            for b in r["blocks"]:
                if is_aisle(b.get("start")) and is_aisle(b.get("end")):
                    arc = by_key.get((round(b["start"]), round(b["end"])))
                    # the aisle bounds, view axis and boundaries come from the arc; the radius (offset)
                    # is per block, since the row spacing differs from arc to arc
                    out = {"seats": b["seats"], "arc": arc["id"], "offset": round(b["offset"], 1)}
                    if b.get("view") is not None and abs(((b["view"] - arc["view"] + 180) % 360) - 180) > 6:
                        out["view"] = b["view"]
                    if b.get("inner") is not None and arc["inner"] is not None and abs(b["inner"] - arc["inner"]) > 8:
                        out["inner"] = b["inner"]
                    if b.get("outer") is not None and arc["outer"] is not None and abs(b["outer"] - arc["outer"]) > 8:
                        out["outer"] = b["outer"]
                    if b.get("blocked"): out["blocked"] = b["blocked"]
                    nb.append(out)
                else:
                    nb.append(b)                     # row-end block keeps its geometry
            r["blocks"] = nb

        zone["arcs"] = layout_arcs
        doc["layout"]["aisles"] = aisles
        doc["layout"]["pitch"] = pitch

    (DATA / f"{vid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    print(f"wrote {vid}: {len(doc['zones'][0].get('arcs', []))} arcs, {len(doc['layout'].get('aisles', []))} aisles, pitch {doc['layout'].get('pitch')}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n")[0])
    main(sys.argv[1])
