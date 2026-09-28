#!/usr/bin/env python3
"""Draft the rows of a seating plan, for a person to check by eye and copy into venues/<id>.py.

The tool finds the seat boxes on a plan, reads the number printed in each, groups the boxes into rows
and blocks, and writes three files to work/<id>/ (git-ignored):

  rows.txt      one row(...) call per row, in the style of the venue scripts; "?" where it could not read
  overlay.png   the plan with every box it found outlined and its reading drawn beside it
  warnings.txt  what to look at first: numbers that skip, gaps in blocks, unread boxes, rows with no label

Nothing here is a fact until checked against the plan. The draft is only a starting point.

Usage:
  python tools/draft_rows.py <plan> --id <venue id> [--page N] [--crop x0,y0,x1,y1]

  <plan>    a PDF (the page given by --page, default 0) or an image (PNG, JPEG, GIF)
  --crop    only look inside this rectangle: in PDF points (as the page is displayed) for a PDF, in
            pixels for an image. Each row in rows.txt carries its own rectangle in the same units, so it
            can be passed back as --crop to look at one row closely.

How it works, in short:
  1. Seat boxes. If the PDF draws its boxes as vector rectangles, those are used. Otherwise the page is
     rendered as displayed (so a scan placed upside down comes out upright) and the tool looks for small
     enclosed rectangles, all of about the same size, formed by straight horizontal and vertical lines.
  2. Numbers. Taken from the PDF's text layer where it has one; otherwise each box is read with Apple
     Vision OCR (macOS only). Marks: a crossed box or a box printed X (X), a box printed W (W), a heavy
     outline (R, restricted sightline). Box fill colours (grey, yellow, ...) are reported as they are,
     since what a colour means depends on the plan's legend.
  3. Rows and blocks. Boxes are chained to their nearest neighbour at the same height, so gently curved
     or sloped rows stay together. A row is split into blocks at gaps wider than a seat. Letters printed
     beside a row (outside the boxes) become its label. Rows are listed from the stage outwards and seats
     in number order; when the stage is drawn at the bottom the plan is read upside down, as the venue
     scripts are written with the stage at the top. Boxes standing well away from the seating (a
     legend's samples) are listed at the end of rows.txt, commented out.

Limits: in a scan or image, boxes must be drawn upright (rows turned by a degree or two are fine, fanned
rows are not found); a box whose outline is broken may be missed; OCR may misread, so every number
needs checking. Unnumbered boxes are named X1, W1, ... as in the venue scripts; their numbers are
never guessed.

Requires: pymupdf, pillow, numpy, scipy, pyobjc-framework-Vision (macOS).
"""
import argparse
import io
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent

TARGET_BOX_PX = 40   # render PDFs so that a seat box is about this many pixels wide


# ---------------------------------------------------------------------------------------------------
# Loading the plan
# ---------------------------------------------------------------------------------------------------

class Plan:
    """The plan as an RGB image we work on, and how its pixels relate to the input's own units.

    input units (PDF points, or image pixels) -> working pixels:  px = (u - origin) * scale
    """

    def __init__(self, path, page_no, crop):
        self.path = Path(path)
        self.crop = crop
        self.page = None
        if self.path.suffix.lower() == ".pdf":
            self.doc = pymupdf.open(self.path)
            self.page = self.doc[page_no]
            # the area to look at, in points on the page as displayed (page.rect is already so)
            self.area = pymupdf.Rect(crop) if crop else self.page.rect
            self.origin = (self.area.x0, self.area.y0)
            self.render(300 / 72)
        else:
            img = Image.open(self.path)
            img.seek(0)                                  # first frame of a GIF
            img = img.convert("RGB")
            if crop:
                img = img.crop(tuple(int(round(v)) for v in crop))
            self.origin = (crop[0], crop[1]) if crop else (0, 0)
            self.scale = 1.0
            self.rgb = np.asarray(img).copy()
            self.gray = self.rgb.mean(axis=2)
            self._ink = None

    def render(self, scale):
        """Render the PDF page as displayed, `scale` pixels to the point. The page's rotation and the
        transform placing any scanned image are applied, so a scan stored upside down comes out upright."""
        self.scale = scale
        clip = self.area * self.page.derotation_matrix          # get_pixmap takes the clip unrotated
        pix = self.page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False)
        self.rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()
        self.gray = self.rgb.mean(axis=2)
        self._ink = None

    @property
    def ink(self):
        """Where the plan is printed (lines and text), worked out once per rendering."""
        if self._ink is None:
            self._ink = ink_mask(self.gray)
        return self._ink

    def to_px(self, x, y):
        """Input units -> working pixels."""
        return (x - self.origin[0]) * self.scale, (y - self.origin[1]) * self.scale

    def to_units(self, x, y):
        """Working pixels -> input units."""
        return x / self.scale + self.origin[0], y / self.scale + self.origin[1]

    @property
    def units(self):
        return "pt" if self.page is not None else "px"


# ---------------------------------------------------------------------------------------------------
# Seat boxes
# ---------------------------------------------------------------------------------------------------

class Box:
    """One seat box, in working pixels (x0, y0, x1, y1 is the inside of the box)."""

    def __init__(self, x0, y0, x1, y1, stroke=None):
        self.x0, self.y0, self.x1, self.y1 = float(x0), float(y0), float(x1), float(y1)
        self.stroke = stroke     # outline width, for vector boxes
        self.text = None         # raw reading (text layer or OCR)
        self.number = None       # the seat number as a string, when the reading is a number
        self.marks = set()       # "X", "W", "R"
        self.fill = None         # colour name of a non-white fill
        self.id = None           # what the draft calls it: its number, "X1"/"W1" for an unnumbered mark, or "?"

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2

    @property
    def w(self):
        return self.x1 - self.x0

    @property
    def h(self):
        return self.y1 - self.y0


def dominant_size(sizes):
    """The (width, height) shared by most of the candidate rectangles.

    Sizes are binned on a log scale (bins about 6% wide) so that the many seat boxes of one size form one
    tall peak, whatever else (legend boxes, frames, text holes) is on the page."""
    sizes = np.asarray(sizes, dtype=float)
    keys = [(int(round(np.log(w) / 0.06)), int(round(np.log(h) / 0.06))) for w, h in sizes]
    counts = Counter()
    for kw, kh in keys:                                  # let neighbouring bins vote too
        for dw in (-1, 0, 1):
            for dh in (-1, 0, 1):
                counts[(kw + dw, kh + dh)] += 1
    best = max(counts, key=counts.get)
    near = [s for s, (kw, kh) in zip(sizes, keys) if abs(kw - best[0]) <= 1 and abs(kh - best[1]) <= 1]
    return tuple(np.median(np.asarray(near), axis=0))


def keep_similar(boxes, size, tol=0.3):
    """Keep boxes whose width and height are within tol of the dominant size."""
    w0, h0 = size
    return [b for b in boxes if abs(b.w / w0 - 1) <= tol and abs(b.h / h0 - 1) <= tol]


def upright(q):
    """A quad drawn as a slightly turned rectangle (seats along a curved row often are), as the upright
    rectangle of the same centre and size; None for any other shape."""
    a, b = q.ur - q.ul, q.ll - q.ul
    if abs(q.ul + q.lr - q.ur - q.ll) > 0.05 * (abs(a) + abs(b)) or abs(a) == 0 or abs(b) == 0:
        return None                                      # not a parallelogram
    if abs(a.x * b.x + a.y * b.y) > 0.1 * abs(a) * abs(b):
        return None                                      # corners not square
    across, down = (a, b) if abs(a.x) >= abs(a.y) else (b, a)
    if abs(across.y) > 0.35 * abs(across):
        return None                                      # turned by more than about 20 degrees
    c = (q.ul + q.lr) / 2
    w, h = abs(across) / 2, abs(down) / 2
    return pymupdf.Rect(c.x - w, c.y - h, c.x + w, c.y + h)


def vector_boxes(plan):
    """Outlined rectangles drawn by the PDF (as rectangles, quads, or four joined lines), in page points."""
    rot = plan.page.rotation_matrix
    found = []
    for path in plan.page.get_drawings():
        if path["type"] not in ("s", "fs"):              # fill-only shapes are backgrounds, not outlines
            continue
        items = path["items"]
        rects = []
        if all(it[0] in ("re", "qu") for it in items):
            for it in items:
                if it[0] == "re":
                    rects.append(pymupdf.Rect(it[1]))
                else:
                    r = upright(it[1])
                    if r is not None:
                        rects.append(r)
        elif all(it[0] == "l" for it in items) and 3 <= len(items) <= 5:
            pts = [p for it in items for p in it[1:3]]
            xs = sorted({round(p.x, 2) for p in pts})
            ys = sorted({round(p.y, 2) for p in pts})
            if len(xs) == 2 and len(ys) == 2:
                rects.append(pymupdf.Rect(xs[0], ys[0], xs[1], ys[1]))
        for r in rects:
            r = r * rot
            r.normalize()
            if r.width > 0.5 and r.height > 0.5:
                found.append((r, path.get("width") or 0))
    # the same box is sometimes drawn twice (e.g. an outline over a filled copy): keep one
    found.sort(key=lambda t: (round(t[0].y0), t[0].x0))
    out = []
    for r, width in found:
        if any(abs(r.x0 - q.x0) < 0.3 * r.width and abs(r.y0 - q.y0) < 0.3 * r.height
               and abs(r.width - q.width) < 0.3 * r.width for q, _ in out[-50:]):
            continue
        out.append((r, width))
    if plan.crop:
        out = [(r, wd) for r, wd in out if r in plan.area]
    return out


def enclosed_regions(ink):
    """Bounding boxes of the white regions fully enclosed by ink (not touching the image edge)."""
    lab, n = ndimage.label(~ink)
    objs = ndimage.find_objects(lab)
    area = ndimage.sum_labels(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    H, W = ink.shape
    out = []
    for i, sl in enumerate(objs):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if y0 == 0 or x0 == 0 or y1 == H or x1 == W:
            continue
        w, h = x1 - x0, y1 - y0
        if w < 5 or h < 5:
            continue
        out.append((x0, y0, x1, y1, area[i] / (w * h)))
    return out


def ink_mask(gray):
    """Printed lines and text. Scans print thin lines in mid greys, so the threshold is generous; but solid
    areas of mid grey (a grey-filled box) are paper colour, not lines, and are left out."""
    dark = gray < 170                                    # 0 is black, 255 white
    mid = (gray > 70) & (gray < 215)
    fills = ndimage.binary_opening(mid, structure=np.ones((5, 5)))
    return dark & ~fills


def straight_lines(mask, length, horizontal):
    """The parts of mask that are straight lines at least `length` long. A scan is seldom quite square, so
    lines leaning by up to two pixels over that length count too."""
    out = np.zeros_like(mask)
    for rise in (-2, -1, 0, 1, 2):
        se = np.zeros((abs(rise) + 1, length), dtype=bool)
        for i in range(length):
            step = round(i * abs(rise) / max(1, length - 1))
            se[step if rise >= 0 else abs(rise) - step, i] = True
        out |= ndimage.binary_opening(mask, structure=se if horizontal else se.T)
    return out


def raster_boxes(plan):
    """Find seat boxes in the rendered image: small, similar, enclosed rectangles.

    First pass: every enclosed white region that is nearly rectangular; the most common size among them is
    taken as the seat box size. Second pass: keep only straight horizontal and vertical lines at least
    as long as the inside of a box (a box's own sides are longer by the line widths), after bridging
    small breaks in them (a scan often breaks thin lines). This removes the digits, the W and the crosses
    of an X box, which could otherwise cut a box in pieces. The enclosed regions of that line drawing that
    have the box size are the boxes; a region two to four boxes long in one direction (a divider line lost
    in the scan) is cut into equal boxes."""
    ink = plan.ink
    # first pass: nearly rectangular enclosed regions, not too long and thin
    first = [r for r in enclosed_regions(ink) if r[4] > 0.55 and 0.3 < (r[2] - r[0]) / (r[3] - r[1]) < 3.5]
    if len(first) < 10:
        return [], None
    w0, h0 = dominant_size([(r[2] - r[0], r[3] - r[1]) for r in first])
    bridge_w, bridge_h = max(3, int(0.15 * w0)), max(3, int(0.15 * h0))
    horiz = ndimage.binary_closing(ink, structure=np.ones((1, bridge_w)))
    vert = ndimage.binary_closing(ink, structure=np.ones((bridge_h, 1)))
    lines = (straight_lines(horiz, max(3, int(w0)), horizontal=True)
             | straight_lines(vert, max(3, int(h0)), horizontal=False))
    boxes = []
    for x0, y0, x1, y1, fill in enclosed_regions(lines):
        if fill < 0.8:
            continue
        # how many boxes long is this region, across and down?
        nx, ny = max(1, round((x1 - x0) / w0)), max(1, round((y1 - y0) / h0))
        whole = abs((x1 - x0) / (nx * w0) - 1) <= 0.2 and abs((y1 - y0) / (ny * h0) - 1) <= 0.2
        if nx * ny == 1 or not whole or min(nx, ny) > 1 or nx * ny > 4:
            if nx * ny == 1:
                boxes.append(Box(x0, y0, x1, y1))        # one box (its size is checked later)
            continue
        sw, sh = (x1 - x0) / nx, (y1 - y0) / ny          # a run of 2-4 boxes whose divider was lost
        for i in range(nx):
            for j in range(ny):
                boxes.append(Box(x0 + i * sw, y0 + j * sh, x0 + (i + 1) * sw, y0 + (j + 1) * sh))
    return boxes, lines


def find_boxes(plan):
    """Seat boxes in working pixels, and a note on how they were found."""
    if plan.page is not None:
        vec = vector_boxes(plan)
        if len(vec) >= 20:
            size = dominant_size([(r.width, r.height) for r, _ in vec])
            vec = [(r, wd) for r, wd in vec if abs(r.width / size[0] - 1) <= 0.3 and abs(r.height / size[1] - 1) <= 0.3]
        if len(vec) >= 20:
            # render so a box is about TARGET_BOX_PX wide, for reading and for the overlay
            plan.render(min(8.0, max(2.0, TARGET_BOX_PX / size[0])))
            boxes = []
            for r, width in vec:
                x0, y0 = plan.to_px(r.x0, r.y0)
                x1, y1 = plan.to_px(r.x1, r.y1)
                boxes.append(Box(x0, y0, x1, y1, stroke=width))
            return boxes, None, "vector rectangles drawn in the PDF"
    boxes, lines = raster_boxes(plan)
    if not boxes:
        return [], None, "no boxes found"
    size = dominant_size([(b.w, b.h) for b in boxes])
    if plan.page is not None and size[0] < 0.75 * TARGET_BOX_PX:
        # small boxes on a PDF page: render again, larger, and look again
        plan.render(plan.scale * TARGET_BOX_PX / size[0])
        boxes, lines = raster_boxes(plan)
        size = dominant_size([(b.w, b.h) for b in boxes])
    return keep_similar(boxes, size), lines, "enclosed rectangles found in the rendered image"


# ---------------------------------------------------------------------------------------------------
# OCR (Apple Vision)
# ---------------------------------------------------------------------------------------------------

def vision_words(img, fast=False):
    """Run Apple Vision text recognition on a PIL image. Returns [(word, (x0, y0, x1, y1))] in pixels.
    fast=True uses Vision's quicker recogniser, which sometimes reads what the accurate one skips."""
    import Vision
    from Foundation import NSData

    buf = io.BytesIO()
    img.save(buf, "PNG")
    data = NSData.dataWithBytes_length_(buf.getvalue(), len(buf.getvalue()))
    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(data, None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelFast if fast
                             else Vision.VNRequestTextRecognitionLevelAccurate)
    req.setUsesLanguageCorrection_(False)
    req.setRecognitionLanguages_(["en-US"])
    handler.performRequests_error_([req], None)
    W, H = img.size
    out = []
    for obs in req.results() or []:
        cand = obs.topCandidates_(1)[0]
        text = str(cand.string())
        for m in re.finditer(r"\S+", text):
            # the box of each word within the line; Vision's boxes are 0-1 with the origin bottom-left
            rect = None
            try:
                sub, _ = cand.boundingBoxForRange_error_((m.start(), m.end() - m.start()), None)
                rect = sub.boundingBox() if sub is not None else None
            except Exception:
                rect = None
            if rect is None:
                rect = obs.boundingBox()
            x0, x1 = rect.origin.x * W, (rect.origin.x + rect.size.width) * W
            y0, y1 = (1 - rect.origin.y - rect.size.height) * H, (1 - rect.origin.y) * H
            out.append((m.group(), (x0, y0, x1, y1)))
    return out


def to_tile(g, height=48):
    """A grey crop as an OCR tile: contrast stretched (so a grey or yellow fill reads as white paper) and
    scaled to a fixed height."""
    g = np.clip((g - 40) * 255.0 / 150, 0, 255)
    tile = Image.fromarray(g.astype(np.uint8))
    scale = height / max(1, tile.height)
    return tile.resize((max(4, round(tile.width * scale)), height), Image.LANCZOS)


def box_tile(plan, box, lines):
    """The inside of a box as a clean tile for OCR, with the box's frame lines whitened."""
    pad_x, pad_y = max(1, round(0.06 * box.w)), max(1, round(0.06 * box.h))
    x0, y0 = int(round(box.x0)) + pad_x, int(round(box.y0)) + pad_y
    x1, y1 = int(round(box.x1)) - pad_x, int(round(box.y1)) - pad_y
    g = plan.gray[y0:y1, x0:x1].copy()
    if lines is not None:
        g[lines[y0:y1, x0:x1]] = 255
    return to_tile(g)


def repeated(tile, times=3):
    """The tile printed three times in a line. Vision tends to skip a lone single character, but reads
    "7 7 7" well; the three readings then vote."""
    gap = max(8, int(tile.width * 0.6))
    strip = Image.new("L", (times * tile.width + (times + 1) * gap, tile.height), 255)
    for i in range(times):
        strip.paste(tile, (gap + i * (tile.width + gap), 0))
    return strip


# Latin capitals that Vision sometimes returns as Cyrillic or Greek look-alikes
LATIN = str.maketrans("АВСЕНІЈКМОРЅТХУШаеорсхуΑΒΕΗΙΚΜΝΟΡΤΧΥΖ", "ABCEHIJKMOPSTXYWaeopcxyABEHIKMNOPTXYZ")


def vote(words, copies=3):
    """The reading that best explains a box's repeated copies, and whether all copies agree on it.

    Vision may run copies together ("77" for two sevens), so a reading s is credited k copies for each
    word that is s written k times, and the reading closest to the number of copies wins ("11" read
    three times is 11, not 1)."""
    words = [w.translate(LATIN).upper() for w in words if w]
    if not words:
        return None, False
    # three copies read as one word of three unequal parts ("JUJ"): let the parts vote
    if len(words) == 1 and len(words[0]) == copies and len(set(words[0])) > 1:
        words = list(words[0])
    cands = set(words)
    for w in words:
        for k in (2, 3):
            if len(w) % k == 0 and w == w[:len(w) // k] * k:
                cands.add(w[:len(w) // k])

    def credit(c):
        return sum(k for w in words for k in (1, 2, 3) if w == c * k)

    best = min(cands, key=lambda c: (abs(credit(c) - copies), -words.count(c), -len(c)))
    return best, words == [best] * copies


def read_sheets(strips, scale=1.0, fast=False):
    """Read strips laid out well apart on large sheets, so one Vision call reads many.
    Returns one (reading, sure) per strip."""
    if scale != 1.0:
        strips = [s.resize((round(s.width * scale), round(s.height * scale)), Image.LANCZOS) for s in strips]
    out = [(None, False)] * len(strips)
    # 6 x 10 strips a sheet read best in trials: on bigger sheets Vision shrinks the text and misses more
    cell_w = int(max(s.width for s in strips) * 1.6)
    cell_h = int(max(s.height for s in strips) * 2.2)
    cols, rows = 6, 10
    per = cols * rows
    for start in range(0, len(strips), per):
        chunk = strips[start:start + per]
        sheet = Image.new("L", (cols * cell_w, rows * cell_h), 255)
        for k, t in enumerate(chunk):
            c, r = k % cols, k // cols
            sheet.paste(t, (c * cell_w + (cell_w - t.width) // 2, r * cell_h + (cell_h - t.height) // 2))
        found = {}
        for word, (x0, y0, x1, y1) in vision_words(sheet, fast):
            c, r = int((x0 + x1) / 2 // cell_w), int((y0 + y1) / 2 // cell_h)
            k = r * cols + c
            if 0 <= c < cols and k < len(chunk):
                found.setdefault(k, []).append(word)
        for k, words in found.items():
            out[start + k] = vote(words)
    return out


def read_tiles(tiles):
    """Read many small tiles with Vision. Returns one reading (or None) per tile.

    Each tile is repeated three times and laid out with the others on large sheets. Tiles whose copies
    were not all read alike are read again on a new sheet at a larger size, and those still unread with
    Vision's fast recogniser. The retry sheets also carry some tiles already read well: on a sheet with
    only a few digits Vision may decide the text is upside down and read 6 as 9."""
    if not tiles:
        return []
    strips = [repeated(t) for t in tiles]
    out = read_sheets(strips)
    for scale, fast in ((1.25, False), (1.0, True)):
        todo = [k for k, (text, sure) in enumerate(out) if not sure and (not fast or text is None)]
        if not todo:
            break
        anchors = [k for k, (_, sure) in enumerate(out) if sure][:max(20, len(todo))]
        again = read_sheets([strips[k] for k in todo + anchors], scale, fast)
        for k, (text, sure) in zip(todo, again):
            if sure or (text and out[k][0] is None):
                out[k] = (text, sure)
    return [text for text, _ in out]


def ocr_boxes(plan, boxes, lines):
    """Read the number (or letter) printed in each box."""
    for b, text in zip(boxes, read_tiles([box_tile(plan, b, lines) for b in boxes])):
        b.text = text


def read_row_labels(plan, boxes, rows, size, flip):
    """Read the words printed beside each row: in the gaps between its blocks and just beyond its ends.
    Returns [(row index, weight, word)]: a word in an aisle between blocks weighs 2, one beyond the row's
    ends 1 (the ends are near walls, circles and box names). rows are in view coordinates; flip() turns
    a view rectangle into the plan's own pixels (the plan's lettering is upright as drawn, so the crops
    are not turned).

    Within each gap the ink (with every box painted out) is split into letter-sized blobs, blobs close
    together are joined into words, and each word is read like a box."""
    w0, h0 = size
    ink = plan.ink.copy()
    m = 0.15 * w0
    for b in boxes:
        x0, y0, x1, y1 = flip((b.x0 - m, b.y0 - m, b.x1 + m, b.y1 + m))
        ink[max(0, int(y0)):int(y1) + 1, max(0, int(x0)):int(x1) + 1] = False
    H, W = ink.shape
    crops, owners = [], []
    for k, row in enumerate(rows):
        gaps = [(row[0].x0 - 4 * w0, row[0].x0, row[0].cy, 1), (row[-1].x1, row[-1].x1 + 4 * w0, row[-1].cy, 1)]
        gaps += [(a.x1, b.x0, (a.cy + b.cy) / 2, 2) for a, b in zip(row, row[1:]) if b.x0 - a.x1 > 0.8 * w0]
        for gx0, gx1, cy, weight in gaps:
            x0, y0, x1, y1 = (int(round(v)) for v in flip((gx0, cy - 0.6 * h0, gx1, cy + 0.6 * h0)))
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            if x1 - x0 < 3 or y1 - y0 < 3:
                continue
            lab, n = ndimage.label(ink[y0:y1, x0:x1], structure=np.ones((3, 3)))
            blobs = []
            for sl in ndimage.find_objects(lab):
                bh, bw = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
                if 0.3 * h0 <= bh <= 0.95 * h0 and bw <= 1.5 * w0:
                    blobs.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])
            blobs.sort()
            words = []
            for bl in blobs:                           # join letters closer than half a seat
                if words and bl[0] - words[-1][2] < 0.5 * w0:
                    w = words[-1]
                    words[-1] = [w[0], min(w[1], bl[1]), max(w[2], bl[2]), max(w[3], bl[3])]
                else:
                    words.append(bl)
            for wx0, wy0, wx1, wy1 in words:
                pad = 3
                g = plan.gray[max(0, y0 + wy0 - pad):y0 + wy1 + pad, max(0, x0 + wx0 - pad):x0 + wx1 + pad]
                crops.append(to_tile(g.astype(float)))
                owners.append((k, weight))
    return [(k, weight, t) for (k, weight), t in zip(owners, read_tiles(crops)) if t]


def page_text_words(plan):
    """Words of the PDF's text layer, in working pixels."""
    if plan.page is None:
        return []
    rot = plan.page.rotation_matrix
    out = []
    for x0, y0, x1, y1, word, *_ in plan.page.get_text("words"):
        r = pymupdf.Rect(x0, y0, x1, y1) * rot
        r.normalize()
        a, b = plan.to_px(r.x0, r.y0)
        c, d = plan.to_px(r.x1, r.y1)
        H, W = plan.gray.shape
        if 0 <= (a + c) / 2 <= W and 0 <= (b + d) / 2 <= H:          # inside the crop
            out.append((word, (a, b, c, d)))
    return out


def ocr_page_words(plan, boxes, size):
    """OCR the plan outside the boxes (the boxes are painted over first), in overlapping pieces: this
    finds the word STAGE and longer row labels. (Vision skips many lone letters; read_row_labels looks
    for those.)"""
    img = Image.fromarray(plan.rgb).convert("L")
    draw = ImageDraw.Draw(img)
    m = 0.2 * size[0]
    for b in boxes:
        draw.rectangle([b.x0 - m, b.y0 - m, b.x1 + m, b.y1 + m], fill=255)
    W, H = img.size
    step, overlap = 1600, 200
    words = []
    for y in range(0, max(1, H - overlap), step - overlap):
        for x in range(0, max(1, W - overlap), step - overlap):
            piece = img.crop((x, y, min(W, x + step), min(H, y + step)))
            for word, (a, b, c, d) in vision_words(piece):
                words.append((word, (a + x, b + y, c + x, d + y)))
    # the same word seen in two overlapping pieces: keep one
    out = []
    for w, r in words:
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        seen = any(w == v and abs(cx - (q[0] + q[2]) / 2) < size[0] and abs(cy - (q[1] + q[3]) / 2) < size[1]
                   for v, q in out)
        if not seen:
            out.append((w, r))
    return out


# ---------------------------------------------------------------------------------------------------
# Reading a box: number, marks, fill
# ---------------------------------------------------------------------------------------------------

DIGIT_LOOKALIKES = str.maketrans({"O": "0", "o": "0", "D": "0", "Q": "0", "l": "1", "I": "1", "i": "1", "|": "1",
                                  "!": "1", "]": "1", "[": "1", "S": "5", "s": "5", "B": "8", "Z": "2",
                                  "z": "2", "G": "6", "b": "6", "q": "9", "g": "9"})


def interpret(box):
    """Turn a box's raw reading into a number or a mark."""
    t = (box.text or "").strip().strip(".,:;'\"`-_")
    if not t:
        return
    if re.fullmatch(r"\d{1,3}", t):
        box.number = str(int(t))
    elif t.upper() in ("W", "VV", "VW", "WV"):          # a bold W is sometimes read as two Vs
        box.marks.add("W")
    elif t.upper() in ("X", "×", "✕", "✗"):
        box.marks.add("X")
    else:
        fixed = t.translate(DIGIT_LOOKALIKES)
        if re.fullmatch(r"\d{1,3}", fixed):
            box.number = str(int(fixed))


def is_crossed(plan, box):
    """True when both diagonals of the box are mostly ink (a box crossed through)."""
    ink = plan.ink
    n, hits = 24, [0, 0]
    for k in range(n):
        f = 0.15 + 0.7 * k / (n - 1)
        down_right = (box.x0 + f * box.w, box.y0 + f * box.h)
        down_left = (box.x1 - f * box.w, box.y0 + f * box.h)
        for d, (x, y) in enumerate([down_right, down_left]):
            xi, yi = int(round(x)), int(round(y))
            if ink[max(0, yi - 1):yi + 2, max(0, xi - 1):xi + 2].any():
                hits[d] += 1
    return min(hits) >= 0.75 * n


def side_thickness(plan, box):
    """How thick the outline is on each side of a box (in pixels): the run of ink going outwards from the
    inside edge, taken at a few points along the side."""
    ink = plan.ink
    H, W = ink.shape
    reach = int(max(3, 0.35 * min(box.w, box.h)))
    out = []
    for side in ("top", "bottom", "left", "right"):
        runs = []
        for f in (0.3, 0.4, 0.5, 0.6, 0.7):
            if side in ("top", "bottom"):
                x = int(box.x0 + f * box.w)
                y = int(box.y0) - 1 if side == "top" else int(box.y1)
                dy = -1 if side == "top" else 1
                run = 0
                while run < reach and 0 <= y + dy * run < H and not ink[y + dy * run, x]:
                    run += 1                                    # step over any white gap at the edge
                start = run
                while run < reach and 0 <= y + dy * run < H and ink[y + dy * run, x]:
                    run += 1
                runs.append(run - start)
            else:
                y = int(box.y0 + f * box.h)
                x = int(box.x0) - 1 if side == "left" else int(box.x1)
                dx = -1 if side == "left" else 1
                run = 0
                while run < reach and 0 <= x + dx * run < W and not ink[y, x + dx * run]:
                    run += 1
                start = run
                while run < reach and 0 <= x + dx * run < W and ink[y, x + dx * run]:
                    run += 1
                runs.append(run - start)
        out.append(float(np.median(runs)))
    return out


def colour_name(rgb):
    """A plain name for a fill colour; None for white paper."""
    r, g, b = (float(v) for v in rgb)
    hi, lo = max(r, g, b), min(r, g, b)
    if hi - lo < 30:
        return None if lo > 215 else "grey"
    if r > 180 and g > 180 and b < 150:
        return "yellow"
    if r > 180 and 100 < g < 190 and b < 120:
        return "orange"
    if r >= g and r >= b:
        return "red" if g < 120 else "pink"
    if g >= r and g >= b:
        return "green"
    return "blue" if b > r else "purple"


def box_fill(plan, box):
    """Colour of the paper inside a box, leaving out the printed digits."""
    x0, x1 = int(box.x0 + 0.15 * box.w), int(box.x1 - 0.15 * box.w)
    y0, y1 = int(box.y0 + 0.15 * box.h), int(box.y1 - 0.15 * box.h)
    px = plan.rgb[y0:y1, x0:x1].reshape(-1, 3)
    px = px[px.mean(axis=1) > 110]                       # leave out the dark printing
    if len(px) < 5:
        return None
    return colour_name(np.median(px, axis=0))


def read_marks(plan, boxes, vector):
    """Heavy outlines (R), crossed boxes with nothing else read in them (X), and fill colours.
    A heavy outline is one drawn at least 1.6 times the usual width: from the PDF's stroke widths for
    vector boxes, else measured in the image on at least three sides of the box (two neighbouring boxes
    share a side, so one thick side is not enough)."""
    if vector:
        widths = [b.stroke for b in boxes if b.stroke]
        typical = float(np.median(widths)) if widths else 0
        for b in boxes:
            if typical and b.stroke and b.stroke > 1.6 * typical:
                b.marks.add("R")
    else:
        sides = [side_thickness(plan, b) for b in boxes]
        typical = float(np.median([s for ss in sides for s in ss])) if sides else 0
        for b, ss in zip(boxes, sides):
            if sum(s >= max(1.6 * typical, typical + 2) for s in ss) >= 3:
                b.marks.add("R")
    for b in boxes:
        if b.text is None and is_crossed(plan, b):
            b.marks.add("X")
        b.fill = box_fill(plan, b)


# ---------------------------------------------------------------------------------------------------
# Rows, blocks and labels
# ---------------------------------------------------------------------------------------------------

def link_rows(boxes, size):
    """Group boxes into rows: each box is joined to its nearest neighbour to the right at about the same
    height (the closest pairs are joined first). A row is a chain of joined boxes."""
    w0, h0 = size
    n = len(boxes)
    cx = np.array([b.cx for b in boxes])
    cy = np.array([b.cy for b in boxes])
    pairs = []
    for i in range(n):
        dx = cx - cx[i]
        dy = np.abs(cy - cy[i])
        ok = (dx > 0.5 * w0) & (dx < 30 * w0) & (dy < 0.4 * h0)
        for j in np.nonzero(ok)[0]:
            pairs.append((dx[j] + 4 * dy[j], i, j))
    pairs.sort()
    right, left = [-1] * n, [-1] * n
    for _, i, j in pairs:
        if right[i] < 0 and left[j] < 0:
            right[i], left[j] = j, i
    rows = []
    for i in range(n):
        if left[i] < 0:
            chain = [i]
            while right[chain[-1]] >= 0:
                chain.append(right[chain[-1]])
            rows.append([boxes[k] for k in chain])
    return rows


def split_blocks(row, w0):
    """Split a row (boxes in left-to-right order) at gaps wider than a seat."""
    blocks = [[row[0]]]
    for a, b in zip(row, row[1:]):
        if b.x0 - a.x1 > w0:
            blocks.append([b])
        else:
            blocks[-1].append(b)
    return blocks


LABEL_LOOKALIKES = {"0": "O", "1": "I", "l": "I", "|": "I"}


def label_candidates(words):
    """Words that look like row labels: one to three capital letters."""
    out = []
    for w, r in words:
        t = w.strip(".,:;'\"`")
        t = LABEL_LOOKALIKES.get(t, t)
        if re.fullmatch(r"[A-Z]{1,3}", t):
            out.append((t, r))
    return out


def attach_labels(rows, labels, size):
    """Give each label word to the row at its height (judged by the row's nearest box), then take the
    commonest label word of each row."""
    w0, h0 = size
    heard = [Counter() for _ in rows]
    for text, (x0, y0, x1, y1) in labels:
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        for k, row in enumerate(rows):
            if x < row[0].x0 - 5 * w0 or x > row[-1].x1 + 5 * w0:
                continue
            near = min(row, key=lambda b: abs(b.cx - x))
            dy = abs(near.cy - y)
            if dy < 0.45 * h0 and (best is None or dy < best[0]):
                best = (dy, k)
        if best:
            heard[best[1]][text] += 1
    return heard


def find_stage(words):
    """Centre of the word STAGE (or 舞台) if it is on the plan."""
    for w, (x0, y0, x1, y1) in words:
        if re.search(r"stage|舞台", w, re.I):
            return (x0 + x1) / 2, (y0 + y1) / 2
    return None


# ---------------------------------------------------------------------------------------------------
# Writing the draft
# ---------------------------------------------------------------------------------------------------

def name_seats(blocks):
    """Give every box of a row the id it will have in the draft: its number; X1, X2 or W1... for an
    unnumbered marked box (as the venue scripts do); "?" for a box that could not be read."""
    count = Counter()
    for block in blocks:
        for b in block:
            if b.number is not None:
                b.id = b.number
            else:
                mark = "W" if "W" in b.marks else "X" if "X" in b.marks else None
                if mark:
                    count[mark] += 1
                    b.id = f"{mark}{count[mark]}"
                else:
                    b.id = "?"


def block_code(block):
    """A block as the scripts write it: rng(a, b) for runs of three or more, lists for the rest."""
    parts, loose = [], []
    ids = [b.id for b in block]
    i = 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and ids[j].isdigit() and ids[j + 1].isdigit() and int(ids[j + 1]) == int(ids[j]) + 1:
            j += 1
        if ids[i].isdigit() and j - i >= 2:
            if loose:
                parts.append("[" + ", ".join(f'"{s}"' for s in loose) + "]")
                loose = []
            parts.append(f"rng({ids[i]}, {ids[j]})")
            i = j + 1
        else:
            loose.append(ids[i])
            i += 1
    if loose:
        parts.append("[" + ", ".join(f'"{s}"' for s in loose) + "]")
    return " + ".join(parts)


def numbers_ascending(boxes):
    """True if the readable numbers of these boxes (in left-to-right order) mostly go up."""
    nums = [int(b.number) for b in boxes if b.number is not None]
    ups = sum(b > a for a, b in zip(nums, nums[1:]))
    downs = sum(b < a for a, b in zip(nums, nums[1:]))
    return None if ups == downs else ups > downs


def read_numbers(plan, boxes, lines, size):
    """Fill in each box's raw reading: from the PDF text layer when it covers most boxes, else by OCR.
    Returns (used the text layer?, words printed outside the boxes)."""
    inside, outside = {}, []
    for w, r in page_text_words(plan):
        x, y = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        hit = next((k for k, b in enumerate(boxes) if b.x0 <= x <= b.x1 and b.y0 <= y <= b.y1), None)
        if hit is None:
            outside.append((w, r))
        else:
            inside.setdefault(hit, []).append((r[0], w))
    if len(inside) >= 0.5 * len(boxes):
        for k, ws in inside.items():
            boxes[k].text = "".join(w for _, w in sorted(ws))
        rest = [b for b in boxes if b.text is None]
        print(f"numbers from the PDF text layer ({len(inside)} boxes); OCR for the other {len(rest)}")
        ocr_boxes(plan, rest, lines)
        return True, outside
    print("numbers by OCR (Apple Vision)")
    ocr_boxes(plan, boxes, lines)
    return False, ocr_page_words(plan, boxes, size) + outside


def which_way_up(boxes, words, size):
    """Is the plan drawn with the stage at the bottom? Judged by where the word STAGE is, or failing
    that by which way most rows are numbered. Returns (upside down?, reason)."""
    stage = find_stage(words)
    if stage is not None:
        below = stage[1] > float(np.median([b.cy for b in boxes]))
        return below, f"STAGE is printed {'below' if below else 'above'} the seats"
    votes = Counter(numbers_ascending(sorted(r, key=lambda b: b.cx)) for r in link_rows(boxes, size) if len(r) > 3)
    backwards = votes[False] > votes[True]
    return backwards, "no STAGE found; seat numbers mostly run " + ("right to left" if backwards else "left to right")


def turn_half_round(boxes, W, H):
    """Turn box coordinates by 180 degrees within a W x H image (and back again, if done twice)."""
    for b in boxes:
        b.x0, b.x1, b.y0, b.y1 = W - b.x1, W - b.x0, H - b.y1, H - b.y0


def loose_rows(rows, size):
    """Rows of one or two boxes standing well away from the main seating (a legend's sample boxes)."""
    w0, h0 = size
    main = [b for r in rows if len(r) >= 3 for b in r]
    if not main:
        return set()
    cx = np.array([b.cx for b in main])
    cy = np.array([b.cy for b in main])
    loose = set()
    for k, r in enumerate(rows):
        if len(r) <= 2 and all(np.min(np.hypot((cx - b.cx) / w0, (cy - b.cy) / h0)) > 5 for b in r):
            loose.add(k)
    return loose


def id_runs(ids):
    """"1, 2, 3, 5" -> "1-3, 5" (other ids are listed as they are)."""
    out, run = [], []
    for s in ids + [None]:
        if s is not None and s.isdigit() and run and int(s) == int(run[-1]) + 1:
            run.append(s)
            continue
        if run:
            out.append(f"{run[0]}-{run[-1]}" if len(run) > 2 else ", ".join(run))
        run = [s] if s is not None and s.isdigit() else []
        if s is not None and not s.isdigit():
            out.append(s)
    return ", ".join(out)


def draft_row(k, row, label_counts, size, where):
    """One row of the draft: the row(...) call with its comment, and the row's warnings."""
    blocks = split_blocks(row, size[0])
    asc = numbers_ascending(row)
    if asc is False:                    # numbered right to left: list from seat 1's end
        blocks = [blk[::-1] for blk in blocks[::-1]]
    name_seats(blocks)
    label = label_counts.most_common(1)[0][0] if label_counts else "?"
    tag = f"row {label}" if label != "?" else f"row {k + 1} (no label)"

    marks = {b.id: "".join(sorted(b.marks)) for blk in blocks for b in blk if b.marks and b.id != "?"}
    extra = ["marks={" + ", ".join(f'"{s}": "{m}"' for s, m in marks.items()) + "}"] if marks else []
    code = f'row("{label}", ' + ", ".join([block_code(blk) for blk in blocks] + extra) + "),"

    notes = [where]
    for colour in sorted({b.fill for b in row if b.fill}):
        named = [b.id for blk in blocks for b in blk if b.fill == colour and b.id != "?"]
        unnamed = [f"block {bi} box {si}" for bi, blk in enumerate(blocks, 1) for si, b in enumerate(blk, 1)
                   if b.fill == colour and b.id == "?"]
        notes.append(f"{colour} fill: " + ", ".join(filter(None, [id_runs(named)] + unnamed)))
    for b in (b for blk in blocks for b in blk if b.id == "?" and b.marks):
        notes.append(f"unread box marked {''.join(sorted(b.marks))}")
    if len(label_counts) > 1:
        notes.append("label words read (weighted): " + ", ".join(f"{t} x{n}" for t, n in label_counts.most_common()))

    warnings = []
    if label == "?":
        warnings.append(f"{tag}: no label found beside the row")
    elif len(label_counts) > 1:
        warnings.append(f"{tag}: label words disagree ({', '.join(label_counts)})")
    if asc is None and len(row) > 1:
        warnings.append(f"{tag}: cannot tell which way the numbers run")
    for bi, blk in enumerate(blocks, 1):
        at = f"{tag} block {bi}"
        nums = [(si, int(b.number)) for si, b in enumerate(blk, 1) if b.number is not None]
        for (sa, a), (sb, b) in zip(nums, nums[1:]):
            if b != a + (sb - sa):
                between = f" with {sb - sa - 1} box(es) between" if sb - sa > 1 else ""
                warnings.append(f"{at}: numbers do not run on: {a} then {b}{between}")
        for n, c in Counter(n for _, n in nums).items():
            if c > 1:
                warnings.append(f"{at}: number {n} appears {c} times")
        ordered = sorted(blk, key=lambda b: b.x0)
        for a, b in zip(ordered, ordered[1:]):
            if b.x0 - a.x1 > 0.4 * size[0]:
                warnings.append(f"{at}: a gap of {(b.x0 - a.x1) / size[0]:.1f} seat inside the block, "
                                f"between {a.id} and {b.id}")
        for si, b in enumerate(blk, 1):
            if b.number is None and not (b.marks & {"W", "X"}):
                prev = next((x.number for x in reversed(blk[:si - 1]) if x.number is not None), None)
                nxt = next((x.number for x in blk[si:] if x.number is not None), None)
                context = f" (between {prev} and {nxt})" if prev and nxt else ""
                raw = f", read as {b.text!r}" if b.text else ""
                warnings.append(f"{at} box {si}: no reading{raw}{context}")
    return f"{code}  # {'; '.join(notes)}", warnings


def draw_overlay(plan, boxes, rows, labels, size, path):
    """The plan with every box outlined (green: number read; blue: W or X; red: unread) and its reading
    written just above its top-left corner; each row's label in blue before its left end."""
    img = Image.fromarray(plan.rgb).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        small = ImageFont.load_default(size=max(9, int(size[1] * 0.42)))
        big = ImageFont.load_default(size=max(12, int(size[1] * 0.8)))
    except TypeError:                                    # Pillow before 10.1 has one fixed-size font
        small = big = ImageFont.load_default()
    for b in boxes:
        colour = (0, 160, 0) if b.number is not None else (0, 90, 255) if b.marks & {"W", "X"} else (230, 0, 0)
        draw.rectangle([b.x0, b.y0, b.x1, b.y1], outline=colour, width=2)
        text = b.id if b.id not in (None, "?") else "?" + (b.text or "")
        if "R" in b.marks:
            text += " R"
        if b.fill:
            text += f" {b.fill}"
        draw.text((b.x0 + 1, b.y0 - 0.1 * size[1]), text, fill=(200, 0, 160), font=small, anchor="lb")
    for row, label in zip(rows, labels):
        first = min(row, key=lambda b: b.x0)
        draw.text((first.x0 - 0.3 * size[0], first.cy), label, fill=(0, 0, 230), font=big, anchor="rm")
    img.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plan")
    ap.add_argument("--id", required=True, help="venue id, names the output folder work/<id>/")
    ap.add_argument("--page", type=int, default=0, help="PDF page, from 0")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in PDF points or image pixels")
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.id):
        sys.exit("--id: letters, digits, dot, dash and underscore only")
    crop = [float(v) for v in args.crop.split(",")] if args.crop else None
    if crop and len(crop) != 4:
        sys.exit("--crop takes four numbers: x0,y0,x1,y1")
    out_dir = ROOT / "work" / args.id
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- boxes, and what is in them
    plan = Plan(args.plan, args.page, crop)
    boxes, lines, how = find_boxes(plan)
    if not boxes:
        sys.exit("no seat boxes found; try --crop around the seating area")
    size = dominant_size([(b.w, b.h) for b in boxes])
    sized = f"{size[0] / plan.scale:.1f} x {size[1] / plan.scale:.1f} {plan.units}"
    print(f"{len(boxes)} boxes ({how}); median size {sized}")
    use_text, page_words = read_numbers(plan, boxes, lines, size)
    for b in boxes:
        interpret(b)
    read_marks(plan, boxes, vector=lines is None)

    # ---- from here on, work as seen with the stage at the top
    H, W = plan.gray.shape
    upside_down, why = which_way_up(boxes, page_words, size)

    def flip(r):
        """A rectangle as seen with the stage at the top -> the same rectangle on the plan as drawn."""
        return (W - r[2], H - r[3], W - r[0], H - r[1]) if upside_down else tuple(r)

    if upside_down:
        turn_half_round(boxes, W, H)
        page_words = [(w, flip(r)) for w, r in page_words]

    # ---- rows, labels
    rows = link_rows(boxes, size)
    rows.sort(key=lambda r: np.mean([b.cy for b in r]))
    for row in rows:
        row.sort(key=lambda b: b.cx)
    heard = attach_labels(rows, label_candidates(page_words), size)
    if not use_text:
        for k, weight, text in read_row_labels(plan, boxes, rows, size, flip):
            for label, _ in label_candidates([(text, None)]):
                heard[k][label] += weight
    loose = loose_rows(rows, size)

    # ---- the draft and its warnings
    fills = Counter(b.fill for b in boxes if b.fill)
    out, warnings, loose_out = [], [], []
    y_prev = None
    pitch = np.median(np.diff([np.mean([b.cy for b in r]) for r in rows])) if len(rows) > 1 else 0
    for k, row in enumerate(rows):
        x0, y0, x1, y1 = flip((min(b.x0 for b in row), min(b.y0 for b in row),
                               max(b.x1 for b in row), max(b.y1 for b in row)))
        m = 0.5 * size[0]
        u0, u1 = plan.to_units(x0 - m, y0 - m), plan.to_units(x1 + m, y1 + m)
        where = f"[{u0[0]:.0f},{u0[1]:.0f},{u1[0]:.0f},{u1[1]:.0f}]"
        line, row_warnings = draft_row(k, row, heard[k], size, where)
        if k in loose:
            loose_out.append("# " + line)
            continue
        y = np.mean([b.cy for b in row])
        if y_prev is not None and pitch and y - y_prev > 1.8 * pitch:
            out.append("# ---- a wider gap between rows: a new part of house?")
        y_prev = y
        out.append(line)
        warnings += row_warnings

    kept = [k for k in range(len(rows)) if k not in loose]
    given = Counter(heard[k].most_common(1)[0][0] for k in kept if heard[k])
    for label, n in given.items():
        if n > 1:
            warnings.append(f"label {label} is given to {n} rows (a misreading, or a letter used again "
                            "in another part of house)")
    unread =sum(1 for k in kept for b in rows[k] if b.number is None and not (b.marks & {"W", "X"}))
    summary = (f"{len(kept)} rows, {sum(len(rows[k]) for k in kept)} boxes in them, {unread} unread, "
               f"{sum(1 for k in kept if not heard[k])} rows without a label")
    head = [
        f"# Draft rows for {args.id}, from {Path(args.plan).name}"
        + (f" page {args.page}" if plan.page is not None else "") + (f", crop {args.crop}" if crop else ""),
        f"# {len(boxes)} boxes ({how}), median {sized}; numbers from "
        + ("the PDF text layer." if use_text else "OCR (Apple Vision)."),
        f"# Read with the stage at the top ({why}): rows from the stage outwards, seats in number order.",
        "# Marks: X crossed or printed X; W printed W; R heavy outline (restricted sightline?).",
        "# Fills found: " + (", ".join(f"{c} x{n}" for c, n in fills.most_common())
                             + " (what they mean is in the plan's legend)." if fills else "none."),
        "# [x0,y0,x1,y1] after each row is its rectangle on the plan, usable as --crop.",
        f"# {summary}",
        "# NOTHING HERE IS CHECKED: compare every row with the plan before using it.",
        "",
    ]
    tail = ["", "# Loose boxes, well away from the seating (a legend?):"] + loose_out if loose_out else []
    (out_dir / "rows.txt").write_text("\n".join(head + out + tail) + "\n")
    (out_dir / "warnings.txt").write_text(
        f"# Warnings for {args.id}: {summary}\n" + "".join(w + "\n" for w in warnings))

    # ---- the overlay, on the plan as drawn
    if upside_down:
        turn_half_round(boxes, W, H)
    labels = [heard[k].most_common(1)[0][0] if heard[k] else "?" for k in range(len(rows))]
    draw_overlay(plan, boxes, rows, labels, size, out_dir / "overlay.png")
    print(summary)
    print(f"wrote {out_dir.relative_to(ROOT)}/rows.txt, warnings.txt ({len(warnings)} warnings), overlay.png")


if __name__ == "__main__":
    main()
