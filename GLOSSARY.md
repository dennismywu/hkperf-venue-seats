# HK Performance Venue Seats

Seat lists of Hong Kong public performance venues, read from LCSD's published seat plans, with a public Viewer, Planner and Customiser built on them.

## Published data

**Venue**:
One hall in one stage layout; each layout of a hall is its own venue with its own seat list.
_Avoid_: Hall (when a layout is meant), house

**Seat list**:
The published record of every seat of a venue, by part of house, row and block.
_Avoid_: Seat plan (that is LCSD's printed document), seat map (that is the drawing)

**Seat plan**:
The venue's own printed plan published by LCSD, from which the seat list is read.
_Avoid_: Seat list, map

**Part of house**:
A named area of a venue, such as Stalls or Balcony, holding rows.
_Avoid_: Zone (the data field name, not the term), section, level

**Row**:
A line of seats in one part of house with one label; row labels are unique within a part of house only.

**Block**:
A run of seats within a row, split from its neighbours by an aisle.
_Avoid_: Section

**Bank**:
A group of rows, or of single blocks, drawn together on one side of the stage.

**Orchestra pit**:
An option of a venue that removes named rows or blocks when the pit is in use.
_Avoid_: Pit seats

**Mark**:
A letter the seat plan prints on a seat: W wheelchair space, X management seat, R restricted sightline, L limited legroom; a seat may carry several.

**Seat id**:
The label of a seat, unique within its row: a number, or `W<n>` / `X<n>` for a box the plan prints without a number.
_Avoid_: Seat number (not every seat has one)

## Viewing and planning

**Configuration**:
A choice of orchestra pit, marks counted, parts of house open and standing, which decides which seats of a venue are active.
_Avoid_: Setup, layout, mode

**Active seat**:
A seat that the current configuration counts.
_Avoid_: Enabled seat, available seat

**Published data**:
The seat list as released in this repo, unchanged by any user.

## Customising

**Customisation**:
A user's list of changes to one venue's seat list, made on top of a base; never a copy of the seat list.
_Avoid_: Custom seat list, custom venue, override

**Change**:
One edit in a customisation to one seat, anchored by part of house, row and seat id: add a seat, remove a seat, set its marks, or rename it.
_Avoid_: Op, patch, edit (in user-facing text)

**Anchor**:
The part of house, row and seat id a change points at; for an added seat, the neighbour it is placed beside.

**Base**:
The venue, seat list version and configuration a customisation was made on.

**Customised version**:
The seat list as it appears after a customisation is applied to its base; the user's own, not published data.
_Avoid_: Custom map, modified venue

**Customisation file**:
A file the user saves to their own device holding one customisation and its base; the only way a customisation is kept.
_Avoid_: Custom seat list file, export

**Change that no longer fits**:
A change whose anchor is missing, or whose result is no longer possible, after the published seat list was corrected.
_Avoid_: Conflict, broken change

## Pages

**Viewer**:
The public page that draws published data under a configuration; it never shows a customised version.

**Planner**:
The public page for planning a performance's seats on a configuration, or on a customised version.

**Customiser**:
The public page where a user makes a customisation, seat by seat, from a Viewer configuration.

**Reviewer**:
The internal page for checking and correcting a seat list against its seat plan; never published.
