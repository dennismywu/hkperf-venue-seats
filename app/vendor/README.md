# Vendored PDF libraries

These are unmodified release builds, loaded only when someone asks the viewer for a PDF. They
are served from this repository so the export works without a CDN and never sends anything to a
third party.

| File | Package | Version | Licence |
|---|---|---|---|
| `pdf-lib.min.js` | [pdf-lib](https://github.com/Hopding/pdf-lib) | 1.17.1 | MIT (`LICENSE-pdf-lib.md`) |
| `fontkit.umd.min.js` | [@pdf-lib/fontkit](https://github.com/Hopding/fontkit) | 1.1.1 | MIT (`LICENSE-fontkit.txt`) |

`pdf-lib.min.js` also contains tslib, © Microsoft Corporation, Apache-2.0; its notice is kept in
the minified file.

The fonts beside this directory (`app/fonts/`) are subsets of Noto Sans HK, © The Noto Project
Authors, SIL Open Font License 1.1; see `app/fonts/OFL.txt`. They are built by
`tools/subset_font.py` from the characters the viewer can print, so the PDF embeds only a few tens
of KB per weight.

To update a library, replace the file and update the version above, then check the export on a
small hall, a banked hall and an arc hall (`ncwcc-th`, `hkcc-gt`, `hkcc-ch`).
