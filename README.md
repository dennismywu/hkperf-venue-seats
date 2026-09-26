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

Pit rows are inferred: LCSD states the seats lost, not the rows. Each file says so and gives the arithmetic.

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

To run it locally, serve the repository root and open `/app/`:

```bash
python3 -m http.server 8770
```

Then visit http://localhost:8770/app/.

## Data format

One JSON file per venue in `data/`, listed in `data/index.json`, with a CSV beside it (one line per seat
box: part of house, row, block, seat, number and its basis, marks, pit rows). Schema
`hkperf-venue-seats/seatlist@0.2`:

| Key | Holds |
|---|---|
| `venue` | `id`, English and Chinese names |
| `source` | the seating plan: publisher, URL, file name, SHA-256, plan code or version, credit |
| `location` | address, district, latitude and longitude, each with its source |
| `layout` | which end seat 1 is at (`seat_1_side`) and notes on the numbering |
| `marks` | the meaning of each mark letter: `W` wheelchair, `X` management, `R` restricted sightline, `L` limited legroom |
| `printed_totals` | the totals printed on the plan, per part of house and overall |
| `orchestra_pits` | each pit option: rows removed (with basis and reasoning), seats removed, total, quoted source |
| `zones` | parts of house → `rows` → `blocks` → `seats` (seat ids in number order, from seat 1's side) |
| `references` | other LCSD documents that confirm a figure, with quotes |
| `count_check` | the counts behind the check, per part of house |

A row may also carry `marks` (seat id → one or more mark letters), `inferred_numbers` and a `note`.

**Seats with no printed number.** Wheelchair and management boxes often print only `W` or `X`. Such a box
is labelled `W1`, `W2`… (or `X1`…) in its row. It gets an inferred number only when the gap between its
printed neighbours fits exactly (e.g. `6 · X X · 9` → 7, 8); otherwise it stays unnumbered and the note says so.

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
4. Add the venue to `data/index.json`.
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

A list of facts is lower risk, but not risk-free under Hong Kong law. The intended step before a wide
launch is to ask LCSD (enquiries@lcsd.gov.hk) for permission, or for them to host the data themselves.
This is not legal advice.

## Project page

`site/` holds the project page for https://code.denniswu.org/hkperf-venue-seats/, with a public copy of
the viewer. `deploy/build.sh` assembles it in `dist/`; `deploy/README.md` covers the Apache virtual host
and publishing.

## License

- **Code**: MIT, see [LICENSE](LICENSE).
- **Seat lists** (`data/`): this project's own contribution is licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), see [LICENSE-DATA](LICENSE-DATA).
  Keep the credit line and sources recorded in each file. Neither licence grants rights LCSD holds in
  its plans.

## Credits

Seat facts are compiled from seating plans and technical information published by the Leisure and
Cultural Services Department, HKSAR Government. Addresses and coordinates come from LCSD's open data on
DATA.GOV.HK.
