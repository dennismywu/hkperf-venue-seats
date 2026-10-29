# The seat-map PDF is generated in the browser

The viewer's PDF has to survive someone else's printer: a fixed page, embedded fonts, vector lines and a white background that does not depend on a print dialog's "background graphics" or scaling settings. Browser print-to-PDF does not give that, and a server-side exporter would send the page — and, in the planner, people's names — somewhere, which the project promises never to do. The viewer therefore builds a PDF in the browser from the SVG it has already drawn: `app/pdf.js` walks the map's handful of primitives and writes them with pdf-lib, embedding small subsets of Noto Sans HK.

The adapter covers what `drawSeatMap()` emits. A `<path>` may sit in a translated group (the arc map's outer translate); a path inside a rotated or scaled group is skipped rather than drawn in the wrong place, and the current maps do not use one. Text stays real text, so it is searchable and selectable, and the PDF is painted opaque: faded seats are blended against white rather than layered with transparency.

## Consequences

- `app/vendor/` carries pdf-lib 1.17.1 and @pdf-lib/fontkit 1.1.1 (MIT), loaded only on the first export; `app/fonts/` carries the Noto Sans HK subsets (OFL), about 50 KB per weight, and a 6.7 MB full regular face.
- `tools/subset_font.py` rebuilds the subsets and the full face from the seat lists and the strings in the viewer and planner; `tools/check_font.py` fails if a new venue or label needs a character that is missing, rather than shipping a PDF with blank boxes.
- A4 and A3 are offered, with portrait, landscape or auto orientation. A3 is the practical limit for the largest halls: `hkcc-ch` prints its seat numbers at about 3 pt on A3, so A4 is left to smaller rooms.
- The planner reuses the adapter. Its free-text category and people's names trigger the full face only when the small subsets cannot draw them; pdf-lib's subsetter mis-maps this CJK font, so the whole face is embedded in that case and a plan PDF with names is about 4–5 MB. Without names or unusual category text it stays around 300 KB. The customiser is not part of this export.
