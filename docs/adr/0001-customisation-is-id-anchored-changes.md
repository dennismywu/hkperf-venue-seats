# A customisation is a list of id-anchored changes, not a copy

A user's customised version of a venue is stored and shared as a list of changes on top of the published seat list. Each change points at a seat by part of house, row and seat id (an added seat names the neighbour it sits beside), never by block or seat index. Published seat lists are corrected over time; a copy would freeze the user on old data, and index anchors would silently move onto the wrong seat when a correction adds or splits a block. Id anchors survive corrections and fail visibly: a change whose anchor is gone is listed as no longer fitting, never dropped or misapplied.

## Consequences

- The base records a SHA-256 of the seat list file as fetched, computed in the browser; a mismatch means "re-check every change", not "refuse".
- Changes are seat-level only (add, remove, set marks, rename one seat). Renumbering a run of seats is left out, as it would rewrite many planner seat keys at once.
