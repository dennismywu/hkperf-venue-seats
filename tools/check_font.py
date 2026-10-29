#!/usr/bin/env python3
"""Check that the PDF font subsets cover every character the viewer can print.

Run after changing a venue file or a PDF label. Exits non-zero if a character is missing, so a
new hall with an unusual name cannot silently produce a PDF full of blank boxes.

    python3 tools/check_font.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from subset_font import OUT, ROOT, drawn_text

FONTS = ["NotoSansHK-Regular-subset.ttf", "NotoSansHK-Bold-subset.ttf"]
FULL = "NotoSansHK-Regular-full.ttf"


def main() -> int:
    chars = drawn_text()
    failed = False
    for name in FONTS:
        path = OUT / name
        if not path.exists():
            print(f"missing {path.relative_to(ROOT)}; run tools/subset_font.py", file=sys.stderr)
            failed = True
            continue
        cmap = TTFont(path).getBestCmap()
        missing = sorted(c for c in chars if ord(c) not in cmap)
        if missing:
            print(f"{name}: missing {len(missing)} character(s): {''.join(missing)}", file=sys.stderr)
            failed = True
        else:
            print(f"{name}: covers all {len(chars)} characters")
    full = OUT / FULL
    if not full.exists():
        print(f"missing {full.relative_to(ROOT)}; run tools/subset_font.py", file=sys.stderr)
        failed = True
    else:
        print(f"{FULL}: present ({full.stat().st_size / 1024 / 1024:.1f} MB)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
