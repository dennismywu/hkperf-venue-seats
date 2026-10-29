#!/usr/bin/env python3
"""Build the small Noto Sans HK subset embedded in the seat-plan PDF.

The PDF has to look the same on any printer, so it embeds the font rather than relying on the
fonts installed there. The subset covers every character in the seat lists plus the labels in
the viewer and the PDF builder; it is a few tens of KB per weight, not the 11 MB variable font.

Run after adding a venue or changing a PDF label, then check coverage:

    python3 tools/subset_font.py
    python3 tools/check_font.py

Requires fonttools (see requirements.txt). The source font is Noto Sans HK, OFL 1.1; its licence
is written to app/fonts/OFL.txt beside the subsets.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanshk/NotoSansHK%5Bwght%5D.ttf"
OFL_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanshk/OFL.txt"
CACHE = ROOT / "tools" / ".font-cache"
OUT = ROOT / "app" / "fonts"
WEIGHTS = [(400, "Regular"), (700, "Bold")]

# The text the viewer can put in the PDF. app/pdf.js and app/index.html are read whole (a few
# harmless code characters do not matter); data/*.json supplies every venue and part-of-house name.
SOURCES = ["app/pdf.js", "app/seatmap.js", "app/index.html"]
EXTRA = (
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz{|}~"
    "“”‘’—–·×→←…•°©®"
)


def walk(value, chars: set[str]) -> None:
    if isinstance(value, str):
        chars.update(value)
    elif isinstance(value, dict):
        for item in value.values():
            walk(item, chars)
    elif isinstance(value, list):
        for item in value:
            walk(item, chars)


def drawn_text() -> set[str]:
    """Every character the PDF (or the map it draws) can contain."""
    chars = set(EXTRA)
    for path in sorted((ROOT / "data").glob("*.json")):
        if path.name == "index.json":
            continue
        walk(json.loads(path.read_text(encoding="utf-8")), chars)
    for relative in SOURCES:
        path = ROOT / relative
        if path.exists():
            chars.update(path.read_text(encoding="utf-8"))
    # line breaks and other controls are layout, not glyphs
    return {c for c in chars if ord(c) >= 32 and ord(c) != 127}


def source_font(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / "NotoSansHK-wght.ttf"
    if not cached.exists():
        print(f"downloading {FONT_URL}")
        urllib.request.urlretrieve(FONT_URL, cached)
    return cached


def build(weight: int, style: str, source: Path, text: str) -> Path:
    font = TTFont(source)
    instantiateVariableFont(font, {"wght": weight}, inplace=True)

    # A stable family and style name, so the PDF's font metadata says what it is.
    family = "Noto Sans HK Seat Plan"
    for name_id, value in (
        (1, family), (2, style), (3, f"{family} {style}"),
        (4, f"{family} {style}"), (6, f"NotoSansHKSeatPlan-{style}"),
        (16, family), (17, style),
    ):
        font["name"].setName(value, name_id, 3, 1, 0x409)
    font["OS/2"].usWeightClass = weight
    if weight >= 700:
        font["head"].macStyle |= 0x01
    else:
        font["head"].macStyle &= ~0x01

    options = subset.Options()
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    options.recalc_timestamp = False
    options.hinting = True
    # Fontkit applies GSUB substitutions when laying out text. Some of Noto Sans HK's alternates
    # have no cmap entry, which makes pdf-lib's ToUnicode map them to the wrong characters
    # (copy/paste and search would say "ǧǨǩ" instead of "123"). The seat plan needs no
    # ligatures or kerning, so drop the tables and lay out straight from the cmap.
    options.drop_tables += ["GSUB", "GPOS", "GDEF", "morx", "mort", "kerx", "kern"]

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"NotoSansHK-{style}-subset.ttf"
    font.save(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, help="NotoSansHK[wght].ttf; downloaded if omitted")
    args = parser.parse_args()

    chars = drawn_text()
    text = "".join(sorted(chars))
    source = source_font(args.source)
    print(f"{len(chars)} characters ({sum('\u4e00' <= c <= '\u9fff' for c in chars)} CJK)")

    for weight, style in WEIGHTS:
        path = build(weight, style, source, text)
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024:.0f} KB)")

    licence = OUT / "OFL.txt"
    if not licence.exists():
        print(f"downloading {OFL_URL}")
        urllib.request.urlretrieve(OFL_URL, licence)


if __name__ == "__main__":
    main()
