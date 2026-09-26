# hkperf-venue-seats

Open, structured seat lists for Hong Kong performing-arts venues, and a viewer to explore them: every
row and seat number, the marks the venue prints (wheelchair spaces, management seats, restricted
sightline, limited legroom), and seat counts for each configuration, such as with the orchestra pit in use.

It is for anyone planning a performance in these halls: promoters, ensembles, students, box-office
and front-of-house teams.

## Venues

| Venue | Seats (printed) | Parts of house | With orchestra pit |
|---|---|---|---|
| Kwai Tsing Theatre Auditorium (`ktt-aud`) | 899 | Stalls 625 · Balcony 274 | 833 (rows A–C) |
| Yuen Long Theatre Auditorium (`ylt-aud`) | 923 | Stalls 734 · Balcony 189 | small pit 888 (A–B) · large pit 839 (A–D) |
| Hong Kong City Hall Theatre (`hkch-th`) | 463 + 10 standing | single | pit formed from forestage traps; no seats lost |
| Sha Tin Town Hall Auditorium (`stth-aud`) | 1,372 | Stalls 589 · Upper Stalls 443 · Balcony 340 | 1,299 (A–B) |
| East Kowloon Cultural Centre, The Hall (`ekcc-hall`) | 1,200 | Stalls 716 · Balcony 484 | small pit 1,126 (A–C) · large pit 1,063 (A–E) |
| Ko Shan Theatre New Wing Auditorium (`kst-nw`) | 596 | Stalls 495 · Balcony 101 | pit lift (30 m²); LCSD publishes no seats lost |
| Sai Wan Ho Civic Centre Theatre (`swhcc-th`) | 453 | single | no pit |
| East Kowloon Cultural Centre, The Turns: horizontal stage (`ekcc-turns-horizontal`) | 160 | single | no pit |
| East Kowloon Cultural Centre, The Turns: end stage (`ekcc-turns-end`) | 176 | single | no pit |
| East Kowloon Cultural Centre, The Lab: end stage (`ekcc-lab-end`) | 243 | Stalls 172 · Gallery 71 | no pit |
| East Kowloon Cultural Centre, The Lab: long thrust stage (`ekcc-lab-thrust`) | 258 | Stalls 187 · Gallery 71 | no pit |
| Sheung Wan Civic Centre Theatre (`swcc-th`) | 482 | single | 447 (rows AA–BB, stated) |
| Sheung Wan Civic Centre Lecture Hall (`swcc-lh`) | 150 | single | no pit |
| Sai Wan Ho Civic Centre Cultural Activities Hall: end stage (`swhcc-ca-end`) | 110 | single | no pit |
| Sai Wan Ho Civic Centre Cultural Activities Hall: thrust stage (`swhcc-ca-thrust`) | 100 | single | no pit |
| Tuen Mun Town Hall Auditorium (`tmth-aud`) | 1,368 | Stalls 589 · Upper Stalls 439 · Balcony 340 | 1,295 (rows A–B, stated) |
| Tuen Mun Town Hall Cultural Activities Hall (`tmth-ca`) | 290 | single (floor A–C, platform D–N) | no pit |
| Tsuen Wan Town Hall Cultural Activities Hall (`twth-ca`) | 260 | single (floor A–C, platform D–N) | no pit |
| Hong Kong Cultural Centre Grand Theatre (`hkcc-gt`) | 1,734 | Stalls 1 788 · Stalls 2 425 · Circle and Upper Circle 495 · V.I.P. Boxes 26 | two pit lifts (53 and 102 seats); LCSD publishes no rows |

Pit rows are inferred where LCSD states only the seats lost, and stated where it names the rows (Sheung Wan
Civic Centre Theatre, Tuen Mun Town Hall Auditorium). Each file says which, and gives the arithmetic.
The Turns, The Lab and the Cultural Activities Hall are flexible rooms with two seated layouts each, so each layout is its own seat list.

## What the data is, and what it is not

- **It is** a list of facts about each hall: its parts of house, the rows in each, the seat numbers in each
  row (split into blocks where the row has aisles), the marks the plan prints, and the totals LCSD
  publishes. Every count is checked against those totals.
- **It is not** a drawing. There are **no coordinates for seats, no background images and no copy of any
  plan**. The viewer draws its own schematic: each row centred, blocks side by side, seats in number order.

## Viewer

`app/index.html` loads `data/*.json` and runs entirely in the browser. For each venue it shows:

- a schematic of every seat, with its marks;
- a configuration panel: orchestra pit options, which seat types to count, which parts of house are open,
  standing places; each option shows the seats it would add (+) or remove (−), and outlines them on the map;
- key figures that follow the configuration, compared with LCSD's own figure for it;
- facts from the plan, including the venue's address and coordinates, each with its source;
- downloads: the seat list as JSON or CSV (linked to this repository), and the current configuration as
  JSON or CSV;
- credits, and a note on the map itself that it is a schematic, not the venue's seat plan.
- the map sits in its own frame: zoom in and out (buttons, or Ctrl/⌘ + wheel or a trackpad pinch), fit the
  whole plan, or view it at actual size.

"Plan with this configuration" opens the planner with the viewer's current settings.

## Planner

`app/planner.html` is for working figures that people may not want to share, so it keeps nothing:

- **Consent first.** It opens behind a statement of how it treats what you enter; nothing loads until you
  agree. Because nothing is stored, it asks again on every visit.
- **Nothing sent, nothing stored.** No cookies, no browser storage, no uploads. Close or reload the page and
  the plan is gone, unless you save it: the plan file is saved on your own device and can only be reopened in
  the planner. There is no spreadsheet export; to share a plan, take a screen capture.
- **Configuration from the viewer.** The viewer passes its settings in the URL fragment (`#c=…`), which
  browsers never send to the server. Only the seats counted in that configuration can be planned.

What it does:

- select seats by clicking, Ctrl/⌘-click, a dragged box, or a row letter;
- put the selection into price categories (name, price, colour), or mark it **Blocked / Not for Sale**;
- mark seats **Reserved / Not for Public** (e.g. sponsors, guests): they keep their price category, stay in
  the ballpark, show with a dashed border on the map and in their own column of the ballpark table;
- show the ballpark gross, the average ticket price and each category's share;
- a simple gap analysis: target revenue and expected sell-through → shortfall or surplus, the sell-through
  needed, and the average price needed on all sellable seats or on the seats not yet priced;
- names on seats, one per seat or one for a group; in the People view each name has its own light shade and
  each seat's border shows its price category (dashed if reserved); drag names to move or swap them, or drag
  a selected group to move it in shape; plus a list of who sits where;

### Plan files

A saved plan is yours to keep and to read with your own tools; the format is open.

- **`hkperf-venue-seats/plan@0.2`**: plain JSON with `venue`, `configuration` (as passed from the viewer),
  `categories` (`id`, `name`, `price`, `colour`), `target`, `sell_through_percent`, and `seats`: a map from
  `"<part of house>|<row>|<seat>"` to `{category, reserved, name}` (only what is set). `category` is a category
  `id` or `"blocked"`.
- **`hkperf-venue-seats/plan-protected@0.1`**: the same plan, encrypted in the browser with a passphrase, which
  the planner offers by default when a plan holds people's names. `kdf` gives PBKDF2-SHA-256 parameters
  (`salt`, `iterations`), `cipher` gives AES-256-GCM with its `iv`, and `data` is the ciphertext (base64). To read
  one outside the planner:

  ```python
  import base64, hashlib, json
  from cryptography.hazmat.primitives.ciphers.aead import AESGCM

  w = json.load(open("ktt-aud-plan-protected.json"))
  key = hashlib.pbkdf2_hmac("sha256", b"your passphrase", base64.b64decode(w["kdf"]["salt"]), w["kdf"]["iterations"], dklen=32)
  plan = json.loads(AESGCM(key).decrypt(base64.b64decode(w["cipher"]["iv"]), base64.b64decode(w["data"]), None))
  ```

## Usage statistics

Every page counts page views, and named interface events such as `planner-category-added` (in the
planner only after its consent), with a self-hosted GoatCounter: no cookies, no IP addresses kept, never
anything a visitor types or selects. Each page's footer says so, and using the site means agreeing to it;
`site/privacy.html` gives the detail. The web server's logs keep no IP addresses either. `app/analytics.js` does nothing until
`goatcounter` is set in `app/config.js`; `deploy/goatcounter/` has the set-up.

To run the viewer and planner locally, serve the repository root and open `/app/`:

```bash
python3 -m http.server 8770
```

Then visit http://localhost:8770/app/.

## Data format

The full description, with examples and an example prompt for drawing a map with an AI model, is published
as [Data format](https://code.denniswu.org/hkperf-venue-seats/schema.html) (`site/schema.html`). In brief:

One JSON file per venue in `data/`, listed in `data/index.json`, with a CSV beside it (one line per seat
box: part of house, row, block, bank, seat, number and its basis, marks, pit rows). Schema
`hkperf-venue-seats/seatlist@0.3`:

| Key | Holds |
|---|---|
| `venue` | `id`, English and Chinese names |
| `source` | the seating plan: publisher, URL, file name, SHA-256, plan code or version, credit |
| `location` | address, district, latitude and longitude, each with its source |
| `layout` | which end seat 1 is at (`seat_1_side`), notes on the numbering, and optionally `banks` (below) |
| `marks` | the meaning of each mark letter: `W` wheelchair, `X` management, `R` restricted sightline, `L` limited legroom |
| `printed_totals` | the totals printed on the plan, per part of house and overall |
| `orchestra_pits` | each pit option: rows removed (with basis and reasoning), seats removed, total, quoted source |
| `zones` | parts of house → `rows` → `blocks` → `seats` (seat ids in number order, from seat 1's side) |
| `references` | other LCSD documents that confirm a figure, with quotes |
| `count_check` | the counts behind the check, per part of house |

A row may also carry `marks` (seat id → one or more mark letters), `inferred_numbers` and a `note`.

**Banks: where the audience sits around the stage.** Some rooms seat the audience on more than one side
of the stage (a thrust stage, or rows along the side walls). The files still hold no coordinates; instead
`layout.banks` records the arrangement, as read from the plan:

| Key | Holds |
|---|---|
| `id` | a name for the bank, e.g. `stalls-left` |
| `side` | which side of the stage it is on: `front`, `left` or `right` |
| `rows` | its rows, nearest the stage first: a row label for a whole row, or `{"row": "A", "block": 1}` for one block of it; add `"zone"` where row letters repeat across parts of house, e.g. `{"zone": "Stalls 2", "row": "A", "block": 1}` |
| `rows_run` | side banks: `along` (each row upright, running along the side; the default) or `across` (each row level, facing the stage, one behind another, e.g. boxes on a side wall) |
| `in_line` | side banks whose rows run along: `true` when the rows follow one another down the wall rather than sit side by side |
| `seat_1` | which end seat 1 is at: `left`/`right` for rows drawn level (front banks, `across`); `downstage`/`upstage` for upright rows |
| `after` | side banks: the `id` of a front bank; the bank sits against the side wall after it (e.g. boxes between the stalls and the balcony) |
| `level_with` | side banks: a row of a front bank; the bank starts level with that row, against the side wall (e.g. boxes beside the stalls) |
| `beside` | side banks whose rows run across: the `id` of a front bank; each row sits level with the same row of that bank, across the aisle (e.g. side blocks of the same rows) |
| `align` | other side banks: beside the stage, level with its front (`downstage`) or back (`upstage`); beside the front banks (`house`); or along the room (`room`) |

The viewer draws the stage in the middle, front banks below it and side banks beside it, or against
the side walls after a front bank, or level with a front bank's rows across the aisle. Order and neighbours follow the plan; distances do not. Every block of every row must be in
exactly one bank, or the build fails. Files without `banks` are drawn as before, every row facing the stage.
Version 0.3 adds `banks` and the CSV's `bank` column; nothing else changed from 0.2.

**Seats with no printed number.** Wheelchair and management boxes often print only `W` or `X`. Such a box
is labelled `W1`, `W2`… (or `X1`…) in its row. It gets an inferred number only when the gap between its
printed neighbours fits exactly (e.g. `6 · X X · 9` → 7, 8); otherwise it stays unnumbered and the note says so.

**Totals from elsewhere, and exceptions.** Where a plan prints no totals, `totals_source` says where the
checked figures come from (for the Grand Theatre, LCSD's technical sheet). Where LCSD's figure for a part of
house also counts its management seats, the zone says so with `count_includes` and a `count_note`; the build
and the viewer both show it.

**How counts are checked.** On every plan so far, the printed total equals the boxes drawn minus the
management seats. Wheelchair, restricted and limited-legroom seats are counted. This rule is our reading;
the build fails if any part of house stops matching it.

## How a venue is added

1. Download the venue's seating plan into `sources/` (git-ignored; plans are never committed).
2. `python tools/seatplan.py extract <plan> --name <id> --out work/<id>` finds the seat boxes and reads
   the numbers into `work/<id>/` (git-ignored). `python tools/seatplan.py serve work` opens a review page.
   Scanned or low-resolution plans are read by eye from zoomed crops.
3. Write `venues/<id>.py` with the checked facts. `venues/common.py` checks every part of house against
   the printed totals and every pit against LCSD's stated figure, then writes `data/<id>.json` and `.csv`.
4. Add the venue to `data/index.json`, with its `region` (Hong Kong Island, Kowloon or New Territories)
   and the date it was `added`.
5. `python tools/check_locations.py` confirms each address and coordinate against LCSD's open data.

Python 3.11+ with the packages in `requirements.txt`. The extractor's OCR uses Apple Vision (macOS).

## Sources and rules

The data comes **only** from the venue operator's own published material.

| Allowed | Never |
|---|---|
| The venue's seating plan as published by LCSD, read directly | Ticketing or box-office data (inventories, sales, holds, price maps) |
| Names, totals and legends printed on that plan | Seat maps or seat lists compiled by others |
| Capacity statements on LCSD's own pages or technical-information sheets for the venue, quoted with URL and version | Zone codes, section names or seat decisions taken from a ticketing system |
| LCSD's open data on DATA.GOV.HK for addresses and coordinates | |

When a plan is unclear, the data says so. It does not fill the gap from anywhere else.

## Copyright

LCSD's notice (https://www.lcsd.gov.hk/en/notice.html) claims copyright in its plans and in "compilation
of data" on its site, and asks for prior written authorisation to reproduce, adapt or make them available
to the public. This project keeps its exposure low:

- **The drawings stay out.** Plans (`sources/`) and anything with positions or images (`work/`) are
  git-ignored and never published.
- **Only facts are published.** Rows, seat numbers, counts and printed marks; no layout.
- **Every venue is credited.** Each file records its sources, the plan's SHA-256 and a credit line.

A list of facts is lower risk, but not risk-free under Hong Kong law. The risk is judged low enough to
publish without asking first: only facts are published, each with its source and credit. LCSD was told
about the project on 26 September 2026, at its launch, and is welcome to ask for any change or removal, or to host the
data itself, at enquiries@lcsd.gov.hk. Any such request will be acted on. This is not legal advice.

## Contributing

- **Corrections**: open an issue with the
  [seat data correction](https://github.com/dennismywu/hkperf-venue-seats/issues/new?template=correction.yml)
  form: the venue, the row and seats, and a link to the operator's published plan.
- **New venues**: use [suggest a venue](https://github.com/dennismywu/hkperf-venue-seats/issues/new?template=venue.yml),
  with a link to the seating plan the operator publishes.
- **Code and data**: pull requests are welcome; see [How a venue is added](#how-a-venue-is-added).

Every contribution follows the [sources and rules](#sources-and-rules) above: the operator's own published
material only, never ticketing data or seat maps drawn by others.

## Project page

`site/` holds the project page for https://code.denniswu.org/hkperf-venue-seats/, with a public copy of
the viewer. `deploy/build.sh` assembles it in `dist/`; `deploy/README.md` covers the Apache virtual host
and publishing.

## License

- **Code**: MIT, see [LICENSE](LICENSE), except the planner.
- **Planner** (`app/planner.html`): [PolyForm Noncommercial 1.0.0](LICENSE-PLANNER.md). Using the hosted
  planner is free for anyone, including businesses; commercial use of the planner's code needs written
  permission.
- **Seat lists** (`data/`): this project's own contribution is licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), see [LICENSE-DATA](LICENSE-DATA).
  Keep the credit line and sources recorded in each file. Neither licence grants rights LCSD holds in
  its plans.

## Credits

Seat facts are compiled from seating plans and technical information published by the Leisure and
Cultural Services Department, HKSAR Government. Addresses and coordinates come from LCSD's open data on
DATA.GOV.HK.
