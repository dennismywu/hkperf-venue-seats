# Embedded fonts

All three files are subsets or instances of **Noto Sans HK**, © The Noto Project Authors, released
under the SIL Open Font License 1.1; see `OFL.txt`.

| File | Used by | Size |
|---|---|---|
| `NotoSansHK-Regular-subset.ttf` | viewer PDF, planner PDF chrome | ~51 KB |
| `NotoSansHK-Bold-subset.ttf` | viewer PDF, planner PDF headings and figures | ~51 KB |
| `NotoSansHK-Regular-full.ttf` | planner PDF, only when a name or category uses a character outside the small subsets | ~6.8 MB |

The two small subsets cover every character in `data/*.json` and the labels in the viewer, the
planner and `app/pdf.js`. They are built by `tools/subset_font.py`, and `tools/check_font.py` fails
if a new venue or label needs a character they do not have.

The full regular face is not embedded in every PDF. The planner fetches it only when the plan has
user text that the small subsets cannot draw, and embeds the whole face: pdf-lib's subsetter mis-maps
this CJK font's glyphs, so a plan PDF with names is about 4–5 MB. The file is downloaded on demand and
cached by the browser; a plan without names or unusual category text does not fetch it and stays around
300 KB.

Rebuild all three after changing the venue data or the PDF labels:

```sh
python3 tools/subset_font.py
python3 tools/check_font.py
```
