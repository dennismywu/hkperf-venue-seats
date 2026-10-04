// Shared by the viewer and the planner: seat-list helpers, what counts in a configuration,
// and the seat-map drawing. Loaded as a plain script; its top-level names are global.

const MARK_NAMES = { W: "Wheelchair spaces", X: "Management seats", R: "Restricted sightline", L: "Limited legroom" };
const MARK_ONE = { W: "Wheelchair space", X: "Management seat", R: "Restricted sightline", L: "Limited legroom" };
// The printed totals count wheelchair, restricted and limited-legroom seats and leave management seats out.
const DEFAULT_MARKS = { W: true, X: false, R: true, L: true };
const S = 15, GAP = 2, BLOCK_GAP = 14, ROW_GAP = 5, LABEL_W = 30, ZONE_GAP = 34;
const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs = {}, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
};
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const link = u => u ? `<a href="${esc(u)}">${esc(u)}</a>` : "URL not recorded";
const seatsOf = row => row.blocks.flatMap(b => b.seats);
// a seat's mark is one or more letters, e.g. "R" or "RL"
const markOf = (row, s) => row.marks?.[s] || "";
const letters = mark => [...mark];
const fmt = n => n.toLocaleString("en");
// The seats an orchestra pit removes, as "zone/row/seat" keys. rows_removed takes the same references as a
// bank: a row label, or {row, zone?, block?} when the label repeats or the pit takes one block of a row.
const pitKeys = new WeakMap();
function pitSeats(doc, pit) {
  if (!pitKeys.has(pit)) {
    const keys = new Set();
    for (const ref of pit.rows_removed) {
      const { z, row } = findRow(doc, ref);
      row.blocks.forEach((b, i) => {
        if (refBlocks(ref, row).includes(i)) b.seats.forEach(s => keys.add(`${z.name}/${row.row}/${s}`));
      });
    }
    pitKeys.set(pit, keys);
  }
  return pitKeys.get(pit);
}
// The pits that remove a seat, or any seat of the row when seat is left out.
const pitsFor = (doc, zone, row, seat) => (doc.orchestra_pits || []).filter(p => {
  const keys = pitSeats(doc, p);
  return (seat === undefined ? seatsOf(row) : [seat]).some(s => keys.has(`${zone}/${row.row}/${s}`));
});
// "rows A–B" (short) or "rows A, B"; references to one block, or one part of house, say so.
function pitRows(pit, short) {
  const refs = pit.rows_removed.map(r => typeof r === "string" ? { row: r } : r);
  const zones = [...new Set(refs.map(r => r.zone || ""))];
  const whole = refs.filter(r => !r.block).map(r => r.row);
  const parts = [...(short && whole.length > 1 ? [`${whole[0]}–${whole.at(-1)}`] : whole), ];
  const blocks = refs.filter(r => r.block).map(r => `; block ${[].concat(r.block).join("–")} of row ${r.row}`).join("");
  return `${zones.length === 1 && zones[0] ? zones[0] + " " : ""}rows ${parts.join(", ")}${blocks}`;
}

async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}

// "W1, W2, 3–44, W3, W4": consecutive numbers collapse to a range, other labels stay as they are
function runs(seats) {
  const out = [];
  for (const s of seats) {
    const n = /^\d+$/.test(s) ? +s : NaN, last = out[out.length - 1];
    if (!isNaN(n) && last && last.to === n - 1) last.to = n;
    else out.push(isNaN(n) ? { label: s } : { from: n, to: n });
  }
  return out.map(r => r.label ?? (r.from === r.to ? r.from : `${r.from}–${r.to}`)).join(", ");
}

// ---------------------------------------------------------------- configurations

const defaults = d => ({
  pit: -1,
  marks: Object.fromEntries(Object.keys(d.marks || {}).map(m => [m, DEFAULT_MARKS[m] ?? true])),
  zones: Object.fromEntries(d.zones.map(z => [z.name, !z.default_off])),
  standing: false,
});

// The reason a seat is left out of configuration st, or "" when it counts.
function excludedIn(doc, st, zone, row, mark, seat) {
  if (zone === "Standing") return st.standing ? "" : "standing places not added";
  if (!st.zones[zone]) return `${zone} closed`;
  const pit = doc.orchestra_pits?.[st.pit];
  if (pit && pitSeats(doc, pit).has(`${zone}/${row}/${seat}`)) return `${pit.name} in use`;
  const off = letters(mark).find(m => !st.marks[m]);
  if (off) return `${MARK_NAMES[off]} not counted`;
  return "";
}

// A configuration travels from the viewer to the planner in the URL fragment (#c=...), which the
// browser never sends to the server: base64url of UTF-8 JSON {venue, pit, marks, zones, standing}.
function encodeConfig(obj) {
  const bytes = new TextEncoder().encode(JSON.stringify(obj));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function decodeConfig(s) {
  const b = atob(s.replace(/-/g, "+").replace(/_/g, "/"));
  return JSON.parse(new TextDecoder().decode(Uint8Array.from(b, c => c.charCodeAt(0))));
}

// ---------------------------------------------------------------- seat map

function seatGlyph(g, x, y, mark, label) {
  el("rect", { x, y, width: S, height: S, rx: 2 }, g);
  if (mark.includes("R")) el("rect", { class: "inner", x: x + 2.2, y: y + 2.2, width: S - 4.4, height: S - 4.4, rx: 1 }, g);
  if (mark.includes("X")) { el("line", { x1: x + 2, y1: y + 2, x2: x + S - 2, y2: y + S - 2 }, g); el("line", { x1: x + S - 2, y1: y + 2, x2: x + 2, y2: y + S - 2 }, g); }
  const t = el("text", { x: x + S / 2, y: y + S / 2 + .5 }, g);
  t.textContent = mark.includes("W") ? "W" : label;
  if (label.length > 2) t.setAttribute("font-size", "6");
}

// One seat, with what the viewer and planner read from it (zone, row, seat, mark, notes).
function seatAt(svg, z, row, s, b, inPits, x, y) {
  const mark = markOf(row, s);
  const g = el("g", { class: `seat ${letters(mark).join(" ")}`, tabindex: 0 }, svg);
  Object.assign(g.dataset, { mark, row: row.row, seat: s, zone: z.name });
  if (row.inferred_numbers?.[s]) g.dataset.inferred = row.inferred_numbers[s];
  if (row.note) g.dataset.note = row.note;
  if (b.area) g.dataset.area = b.area;
  const pits = inPits(s);
  if (pits) g.dataset.pits = pits;
  seatGlyph(g, x, y, mark, s);
  return g;
}
// seat -> the pits that remove it, for the seat's tooltip
const pitNote = (doc, z, row) => s => pitsFor(doc, z.name, row, s).map(p => `${p.name} (rows ${p.rows_basis})`).join(", ");

function rowLayout(row, rightFirst) {
  // Blocks in drawn order, left to right (the file lists them from seat 1's side). Each block's
  // items are its seats plus any blocked slots, which follow the seats in number order.
  let blocks = row.blocks.map(b => ({
    side: b.side, area: b.area,
    items: [...b.seats.map(id => ({ id })), ...(b.blocked?.skipped_numbers || []).map(id => ({ id, blocked: true }))],
  }));
  if (rightFirst) { blocks.reverse(); blocks.forEach(b => b.items.reverse()); }
  return blocks;
}

function blockWidth(b) { return b.items.length * S + (b.items.length - 1) * GAP; }

// Space between two blocks: room for any seat numbers missing between them (e.g. Y 1-2 · Y 34-35
// lines up under the ends of row X), otherwise an aisle.
function between(a, b) {
  const p = +a.items.at(-1).id, n = +b.items[0].id;
  const missing = Number.isInteger(p) && Number.isInteger(n) ? Math.abs(n - p) - 1 : 0;
  return missing > 0 ? GAP + missing * (S + GAP) : BLOCK_GAP;
}

// Split text into lines of at most n characters, at spaces.
function wrap(text, n) {
  const out = [];
  let line = "";
  for (const w of text.split(" ")) {
    if (line && (line + " " + w).length > n) { out.push(line); line = w; }
    else line = line ? line + " " + w : w;
  }
  if (line) out.push(line);
  return out;
}

function rowWidth(bl) { return bl.reduce((a, b, i) => a + blockWidth(b) + (i ? between(bl[i - 1], b) : 0), 0); }

// Numbered standing places, drawn as round places in a row centred at cx; the numbers run with seat 1
// (right to left when the hall's seat 1 is at the right). Returns the y just below the row.
function drawStanding(svg, doc, cx, y) {
  const places = doc.standing.places, n = places.length, w = n * S + (n - 1) * GAP;
  const rightFirst = (doc.layout?.seat_1_side || "right") === "right";
  let x = cx - w / 2;
  const g = el("g", { class: "standing" }, svg);
  (rightFirst ? [...places].reverse() : places).forEach(pl => {
    // each place is a seat-like element, so hover, tooltip and the planner treat it as one
    const place = el("g", { class: "seat place", tabindex: 0 }, g);
    Object.assign(place.dataset, { zone: "Standing", row: "Standing", seat: pl, mark: "" });
    el("rect", { x, y, width: S, height: S, rx: 7 }, place);
    el("text", { x: x + S / 2, y: y + S / 2 + .5 }, place).textContent = pl;
    x += S + GAP;
  });
  el("text", { class: "rowlabel", x: cx, y: y + S + 10, "text-anchor": "middle" }, svg).textContent = "Standing";
  return y + S + 24;
}

// Draws the whole map for doc and returns the <svg>; the caller places it and styles the seats.
// opts.custom = {changes: n}: the map is a user's customised version; finishMap says so inside the drawing.
function drawSeatMap(doc, opts = {}) {
  if (doc.layout?.arrangement === "arc") return drawArcMap(doc, opts);
  if (doc.layout?.banks?.length) return drawBankedMap(doc, opts);
  const rightFirst = (doc.layout?.seat_1_side || "right") === "right";
  // width of the widest row (centred rows); side blocks push to the edges of this width
  let maxW = 0;
  for (const z of doc.zones) for (const r of z.rows) {
    const bl = rowLayout(r, rightFirst);
    if (!bl.some(b => b.side)) maxW = Math.max(maxW, rowWidth(bl));
  }
  const W = maxW + LABEL_W * 2 + 8;
  const svg = el("svg", { role: "img", "aria-label": `Seat schematic for ${doc.venue.name_en}` });
  let y = 4;
  const stageW = Math.min(260, maxW * .45);
  el("rect", { class: "stage", x: (W - stageW) / 2, y, width: stageW, height: 30, rx: 3 }, svg);
  el("text", { class: "stagetext", x: W / 2, y: y + 15 }, svg).textContent = doc.layout?.stage_label || "STAGE 舞台";
  y += 30 + 22;
  const x0 = LABEL_W + 4;
  const rowY = {};
  let standingDrawn = false;

  for (const z of doc.zones) {
    const zl = el("text", { class: "zonelabel", x: W / 2, y: y + 4 }, svg);
    zl.textContent = `${z.name} ${z.name_zh || ""}`.trim();
    zl.dataset.zone = z.name;
    y += 16;
    for (const row of z.rows) {
      const bl = rowLayout(row, rightFirst);
      let xs;
      if (bl.some(b => b.side)) {
        xs = bl.map(b => b.side === "left" ? x0 : b.side === "right" ? x0 + maxW - blockWidth(b) : x0 + (maxW - blockWidth(b)) / 2);
      } else {
        let x = x0 + (maxW - rowWidth(bl)) / 2;
        xs = bl.map((b, i) => { if (i) x += between(bl[i - 1], b); const at = x; x += blockWidth(b); return at; });
      }
      const minX = Math.min(...xs), maxX = Math.max(...bl.map((b, i) => xs[i] + blockWidth(b)));
      for (const [x, anchor] of [[minX - 6, "end"], [maxX + 6, "start"]]) {
        const t = el("text", { class: "rowlabel", x, y: y + S / 2, "text-anchor": anchor }, svg);
        t.textContent = row.row;
        Object.assign(t.dataset, { row: row.row, zone: z.name });
      }
      const inPits = pitNote(doc, z, row);
      bl.forEach((b, i) => b.items.forEach(({ id: s, blocked }, j) => {
        if (blocked) {
          if (j && b.items[j - 1].blocked) return;          // one filled area per run of blocked slots
          let k = j; while (b.items[k + 1]?.blocked) k++;
          const r = el("rect", { class: "blockedarea", x: xs[i] + j * (S + GAP), y, width: (k - j + 1) * (S + GAP) - GAP, height: S, rx: 1 }, svg);
          el("title", {}, r).textContent = `${row.row}: solid area where ${b.items.slice(j, k + 1).map(t => t.id).join(", ")} would be (not seats)`;
          return;
        }
        seatAt(svg, z, row, s, b, inPits, xs[i] + j * (S + GAP), y);
      }));
      rowY[row.row] = y;
      y += S + ROW_GAP;
    }
    // standing places sit after the part of house the plan prints them by (default: after every zone)
    if (doc.standing?.places?.length && doc.standing.after === z.name) {
      y = drawStanding(svg, doc, x0 + maxW / 2, y + 6) + ZONE_GAP;
      standingDrawn = true;
    }
    y += ZONE_GAP;
  }
  (doc.orchestra_pits || []).forEach((pit, i) => {
    const ys = pit.rows_removed.map(r => rowY[typeof r === "string" ? r : r.row]);
    const top = Math.min(...ys), bottom = Math.max(...ys) + S;
    pitBand(svg, i, pit, 2, top - 3, W - 4, bottom - top + 6);
  });
  if (doc.standing?.places?.length && !standingDrawn) {
    y = drawStanding(svg, doc, x0 + maxW / 2, y - ZONE_GAP + 10) + ZONE_GAP;
  }
  return finishMap(svg, doc, W, y - ZONE_GAP + 14, opts);
}

// A pit's dashed outline: a rectangle with its name inside the top-left corner, or the polygon pts with its
// name at label (outside the outline).
function pitBand(svg, i, pit, x, y, w, h, pts, label) {
  const band = el("g", { class: "pitband" }, svg);
  band.dataset.pit = i;
  if (pts) el("polygon", { points: pts.map(q => q.join(",")).join(" ") }, band);
  else el("rect", { x, y, width: w, height: h, rx: 4 }, band);
  el("text", label || { x: x + 8, y: y + h / 2 }, band).textContent = pit.name;
}

// Disclaimer inside the drawing, so it stays with any screenshot of the map; then size the drawing. A
// customised version (opts.custom) also says, beside it, that it is the user's own and not published data.
function finishMap(svg, doc, W, y, opts = {}) {
  const chars = Math.floor((W - 24) / 5.1);
  const lines = wrap("This map is drawn from the seat data published with it: a machine-assisted reading of the rows " +
    "and seats of the venue. It is not the actual seat plan. For the actual seat plan, refer to the version " +
    "published by LCSD:", chars);
  const box = el("g", { class: "disclaimer" }, svg);
  const boxH = (lines.length + 2) * 13 + 10;
  el("rect", { x: 2, y, width: W - 4, height: boxH, rx: 4 }, box);
  el("text", { class: "lead", x: 12, y: y + 16 }, box).textContent = "Not the venue's seat plan";
  lines.forEach((l, i) => { el("text", { x: 12, y: y + 16 + (i + 1) * 13 }, box).textContent = l; });
  const a = el("a", { href: doc.source.url, target: "_blank", rel: "noopener" }, box);
  el("text", { x: 12, y: y + 16 + (lines.length + 1) * 13 }, a).textContent = doc.source.url;
  let H = y + boxH + 4;
  if (opts.custom) {
    const n = opts.custom.changes;
    const more = wrap(`Not the venue's seat plan and not published data. ${n === 1 ? "1 change" : `${n} changes`} from the ` +
      "published seat list, made by you.", chars);
    const c = el("g", { class: "disclaimer custom" }, svg);
    const cH = (more.length + 1) * 13 + 10;
    el("rect", { x: 2, y: H, width: W - 4, height: cH, rx: 4 }, c);
    el("text", { class: "lead", x: 12, y: H + 16 }, c).textContent = "Customised by you";
    more.forEach((l, i) => { el("text", { x: 12, y: H + 16 + (i + 1) * 13 }, c).textContent = l; });
    H += cH + 4;
  }
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  return svg;
}

// ---------------------------------------------------------------- banked maps
// For rooms where the audience sits on more than one side of the stage. layout.banks groups rows (or
// single blocks of rows) by the side of the stage they are on, nearest the stage first; the stage is
// drawn in the middle, front banks below it and side banks beside it as upright columns. Order and
// neighbours follow the plan; distances do not. Each bank:
//   side: "front" | "left" | "right"
//   rows: ["AA", ...] or [{row: "A", block: 1}, ...]   nearest the stage first
//   seat_1: front banks "left" | "right"; side banks "downstage" | "upstage" (the end seat 1 is at)
//   align (side banks): "downstage" (level with the stage's front), "upstage" (with its back),
//     "stage" (centred on the stage, columns centred on one another), "house" (beside the front banks,
//     from their first row), "room" (centred on stage and front banks)
//   rows_run (side banks): "along" (default; each row upright, running along the side) or "across"
//     (each row level, facing the stage; rows one behind another, e.g. boxes on a side wall)
//   in_line (side banks, rows along): rows one after another down the wall, not side by side
//   after (side banks): the id of a front bank; the bank sits against the side wall after it
//   rows may name their part of house, {"zone": "Stalls 2", "row": "A"}, where row letters repeat
//   level_with (side banks): a row of a front or back bank ("R", or {zone, row}); the bank starts level with that row,
//     outside the front rows (e.g. boxes on the side walls beside the stalls)
//   beside (side banks, rows across): the id of a front bank; each row sits level with the same row of
//     that bank, across the aisle from it (rows the front bank lacks continue below it)
//   label: optional heading drawn with the bank
const BANK_GAP = 18, COL_GAP = 8;

// A bank's rows: "AA" (a whole row), or {row, zone?, block?} where zone names the part of house when row
// letters repeat across levels, and block picks one block of the row (1 = seat 1's side), or a list of them.
function findRow(doc, ref) {
  const label = typeof ref === "string" ? ref : ref.row, zone = typeof ref === "string" ? null : ref.zone;
  for (const z of doc.zones) if (!zone || z.name === zone) for (const r of z.rows) if (r.row === label) return { z, row: r };
  throw new Error(`no row ${zone ? zone + " " : ""}${label}`);
}
const rowKey = (z, row) => `${z.name}/${row.row}`;
// The block indexes a reference covers: every block, or the one (or list) it names, counted from 1.
const refBlocks = (ref, row) => typeof ref === "string" || !ref.block ? row.blocks.map((_, i) => i) : [].concat(ref.block).map(b => b - 1);

function bankPieces(doc, bank) {
  return bank.rows.map(ref => {
    const { z, row } = findRow(doc, ref);
    const blocks = refBlocks(ref, row).map(i => row.blocks[i]);
    return { z, row, blocks };
  });
}

// A piece's seats (and blocked slots) in order from seat 1's end, with the space before each.
function pieceItems(piece, reversed, aisle) {
  const bl = rowLayout({ blocks: piece.blocks }, reversed);          // reversed: seat 1 at the right
  const src = reversed ? [...piece.blocks].reverse() : piece.blocks;
  const out = [];
  // aisle: blocks of a row within a side bank sit an aisle apart, not spaced for the numbers between them
  bl.forEach((b, i) => b.items.forEach((it, j) => out.push({ ...it, b: src[i], before: j ? GAP : i ? (aisle ? BLOCK_GAP : between(bl[i - 1], b)) : 0 })));
  return out;
}
const pieceLength = items => items.reduce((a, it) => a + it.before + S, 0);

function drawBankedMap(doc, opts = {}) {
  const banks = doc.layout.banks.map(bk => {
    const level = bk.side === "front" || bk.side === "back" || bk.rows_run === "across";   // rows drawn level, facing the stage
    const aisle = bk.side === "left" || bk.side === "right";
    const pieces = bankPieces(doc, bk).map(p => ({ ...p, items: pieceItems(p, level && bk.seat_1 === "right", aisle) }));
    const lens = pieces.map(p => pieceLength(p.items)), n = pieces.length, longest = Math.max(...lens);
    // w, h: the bank's extent on the map
    const [w, h] = level ? [longest, n * (S + ROW_GAP) - ROW_GAP]
      : bk.in_line ? [S, lens.reduce((a, l) => a + l, 0) + (n - 1) * BLOCK_GAP]
      : [n * (S + COL_GAP) - COL_GAP, longest];
    return { ...bk, level, pieces, lens, w, h };
  });
  const front = banks.filter(b => b.side === "front");
  const back = banks.filter(b => b.side === "back");
  const sides = banks.filter(b => b.side !== "front" && b.side !== "back");
  const outer = b => b.align === "room" || b.align === "house";   // beside the front banks, not the stage
  const byStage = sides.filter(b => !b.after && !b.beside && !b.level_with && !outer(b));
  const frontW = Math.max(0, ...front.map(b => b.w));
  const stageW = Math.min(300, Math.max(120, frontW * .7));
  const stageH = Math.max(36, ...byStage.map(b => b.h));
  const LBL = 14;                                   // room for labels above and below side columns

  // positions around a stage centred on x = 0, top at y = 0 (shifted into view at the end)
  const place = [];                                 // {bank, x, y} of each bank's top-left corner
  const houseTop = stageH + BANK_GAP + LBL;
  let y = houseTop;
  const zonesSeen = new Set();
  let outerHalf = frontW / 2;                       // half-width of the rows so far, side blocks included
  const frontRowY = new Map();                      // "zone/row" -> its y in a front bank
  let standingPlaced = false;
  for (const b of front) {
    // a heading for the bank's own label, or for the first front bank of each part of house
    b.heading = b.label || (!zonesSeen.has(b.pieces[0].z.name) ? `${b.pieces[0].z.name} ${b.pieces[0].z.name_zh || ""}`.trim() : "");
    b.pieces.forEach(p => zonesSeen.add(p.z.name));
    if (b.heading && b !== front[0]) y += 14;
    // side banks level with this bank's rows, across the aisle (where the row labels are). Side rows the
    // front bank lacks keep their order: those before its first row go above it, those after it below.
    const alongside = sides.filter(s => s.beside === b.id);
    const idx = new Map(b.pieces.map((p, i) => [rowKey(p.z, p.row), i]));
    let lead = 0, extra = 0;
    for (const s of alongside) {
      const first = s.pieces.findIndex(p => idx.has(rowKey(p.z, p.row)));
      const before = first < 0 ? 0 : first;
      let last = b.pieces.length - 1;
      s.rix = s.pieces.map((p, i) => {
        const k = rowKey(p.z, p.row);
        if (idx.has(k)) return (last = idx.get(k));
        return i < before ? i - before : ++last;
      });
      lead = Math.max(lead, before);
      extra = Math.max(extra, Math.max(...s.rix) - (b.pieces.length - 1));
    }
    b.lead = lead;
    y += lead * (S + ROW_GAP);
    place.push({ b, x: -b.w / 2, y });
    b.pieces.forEach((p, i) => frontRowY.set(rowKey(p.z, p.row), y + i * (S + ROW_GAP)));
    for (const s of alongside) {
      s.pos = s.pieces.map((p, i) => {
        const r = s.rix[i], matched = r >= 0 && r < b.pieces.length;
        const edge = matched ? b.lens[r] / 2 : b.w / 2;
        return { x: s.side === "left" ? -edge - LABEL_W - s.lens[i] : edge + LABEL_W, y: y + r * (S + ROW_GAP), matched };
      });
      s.pos.forEach((q, i) => { outerHalf = Math.max(outerHalf, s.side === "left" ? -q.x : q.x + s.lens[i]); });
      place.push({ b: s, x: 0, y });
    }
    y += b.h + Math.max(0, extra) * (S + ROW_GAP) + BANK_GAP;
    // standing places sit after the part of house the plan prints them by (default: after every front bank)
    if (doc.standing?.places?.length && doc.standing.after === b.pieces[0].z.name) {
      place.push({ standing: true, x: 0, y });
      y += S + 24 + BANK_GAP;
      standingPlaced = true;
    }
    // side banks that follow this front bank: against the side walls, before the next front bank
    const band = sides.filter(s => s.after === b.id);
    if (band.length) {
      let inL = 0, inR = 0;
      for (const s of band) {
        if (s.side === "left") { place.push({ b: s, x: -outerHalf + inL, y: y + LBL }); inL += s.w + BANK_GAP; }
        else { place.push({ b: s, x: outerHalf - s.w - inR, y: y + LBL }); inR += s.w + BANK_GAP; }
      }
      y += Math.max(...band.map(s => s.h)) + 2 * LBL + BANK_GAP;
    }
  }
  if (doc.standing?.places?.length && !standingPlaced) {
    place.push({ standing: true, x: 0, y });
    y += S + 24 + BANK_GAP;
  }
  // banks on the far side of the stage: drawn above it, first row nearest the stage
  let backBottom = -BANK_GAP;
  for (const b of back) {
    b.heading = b.label || (!zonesSeen.has(b.pieces[0].z.name) ? `${b.pieces[0].z.name} ${b.pieces[0].z.name_zh || ""}`.trim() : "");
    b.pieces.forEach(p => zonesSeen.add(p.z.name));
    const top = backBottom - b.h;
    place.push({ b, x: -b.w / 2, y: top });
    // back rows can be named by level_with too (side columns beside the far house)
    b.pieces.forEach((p, i) => frontRowY.set(rowKey(p.z, p.row), top + (b.pieces.length - 1 - i) * (S + ROW_GAP)));
    backBottom = top - BANK_GAP;
  }
  const houseBottom = y - BANK_GAP;
  const frontHalf = frontW / 2 + LABEL_W;
  for (const dir of [-1, 1]) {
    let edge = stageW / 2 + BANK_GAP;               // distance from the centre line to the bank's inner edge
    for (const b of sides.filter(s => s.level_with && s.side === (dir < 0 ? "left" : "right"))) {
      // against the side wall, level with a row of the front banks
      const x = dir < 0 ? -(outerHalf + LABEL_W + BANK_GAP) - b.w : outerHalf + LABEL_W + BANK_GAP;
      const lw = b.level_with, at = typeof lw === "string" ? [...frontRowY].find(([k]) => k.endsWith("/" + lw))?.[1] : frontRowY.get(`${lw.zone}/${lw.row}`);
      place.push({ b, x, y: at ?? houseTop });
    }
    for (const b of sides.filter(s => !s.after && !s.beside && !s.level_with && s.side === (dir < 0 ? "left" : "right"))) {
      if (outer(b)) edge = Math.max(edge, frontHalf + BANK_GAP);
      const x = dir < 0 ? -edge - b.w : edge;
      const top = b.align === "upstage" ? 0 : b.align === "stage" ? (stageH - b.h) / 2 : b.align === "house" ? houseTop
        : b.align === "room" ? (houseBottom - b.h) / 2 : stageH - b.h;
      place.push({ b, x, y: top });
      edge += b.w + BANK_GAP;
    }
  }
  // extents: whole banks, or each row of a bank placed row by row
  const ext = place.filter(p => p.b).flatMap(p => p.b.pos ? p.b.pos.map((q, i) => ({ x0: q.x, x1: q.x + p.b.lens[i], y0: q.y, y1: q.y + S }))
    : [{ x0: p.x, x1: p.x + p.b.w, y0: p.y, y1: p.y + p.b.h }]);
  // room for the row labels: side banks carry theirs at the column's centre, so long names need more
  const labelHalf = Math.max(0, ...sides.flatMap(b => b.pieces.map(p => String(p.row.row).length))) * 3.2;
  const pad = Math.max(LABEL_W, labelHalf + 6);
  const minX = Math.min(-stageW / 2, ...ext.map(e => e.x0)) - pad;
  const maxX = Math.max(stageW / 2, ...ext.map(e => e.x1)) + pad;
  const minY = Math.min(0, ...ext.map(e => e.y0)) - LBL - 18;
  const W = maxX - minX, ox = -minX, oy = -minY + 4;

  const svg = el("svg", { role: "img", "aria-label": `Seat schematic for ${doc.venue.name_en}` });
  el("rect", { class: "stage", x: ox - stageW / 2, y: oy, width: stageW, height: stageH, rx: 3 }, svg);
  el("text", { class: "stagetext", x: ox, y: oy + stageH / 2 }, svg).textContent = doc.layout?.stage_label || "STAGE 舞台";
  const boxes = {};                                 // "zone/row/block index" -> bounding box, for the pit bands
  const grow = (p, x0, y0, x1, y1) => p.blocks.forEach(blk => {
    const k = `${p.z.name}/${p.row.row}/${p.row.blocks.indexOf(blk)}`;
    const r = boxes[k] || (boxes[k] = { x0, y0, x1, y1 });
    Object.assign(r, { x0: Math.min(r.x0, x0), y0: Math.min(r.y0, y0), x1: Math.max(r.x1, x1), y1: Math.max(r.y1, y1) });
  });
  const rowLabel = (piece, x, y, anchor) => {
    const t = el("text", { class: "rowlabel", x, y, "text-anchor": anchor }, svg);
    t.textContent = piece.row.row;
    Object.assign(t.dataset, { row: piece.row.row, zone: piece.z.name });
  };
  const blockedAt = (row, id, x, y) => {
    const r = el("rect", { class: "blockedarea", x, y, width: S, height: S, rx: 1 }, svg);
    el("title", {}, r).textContent = `${row.row}: solid area where ${id} would be (not seats)`;
  };

  for (const piece of place) {
    if (piece.standing) { drawStanding(svg, doc, ox + piece.x, oy + piece.y); continue; }
    const { b, x, y: top } = piece;
    const X = ox + x, Y = oy + top;
    const flat = b.side === "front" || b.side === "back";
    const heading = flat ? b.heading : b.label || "";
    if (heading) {
      const hx = flat ? ox : X + b.w / 2;
      const hy = b.side === "front" ? Y - 8 - (b.lead || 0) * (S + ROW_GAP) : b.side === "back" ? Y - 8 : Y - LBL - 6;
      const zl = el("text", { class: "zonelabel", x: hx, y: hy }, svg);
      zl.textContent = heading;
      zl.dataset.zone = b.pieces[0].z.name;
    }
    let run = Y;                                    // in-line columns: where the next row starts
    b.pieces.forEach((p, i) => {
      const inPits = pitNote(doc, p.z, p.row), len = b.lens[i];
      if (b.pos) {
        // level with the front bank's row; its label is already in the aisle, unless the front bank lacks the row
        const q = b.pos[i], x0 = ox + q.x, ry = oy + q.y;
        let cx = x0;
        p.items.forEach(it => {
          cx += it.before;
          if (it.blocked) blockedAt(p.row, it.id, cx, ry); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, ry);
          cx += S;
        });
        if (!q.matched) b.side === "left" ? rowLabel(p, x0 + len + 6, ry + S / 2, "start") : rowLabel(p, x0 - 6, ry + S / 2, "end");
        grow(p, x0, ry, x0 + len, ry + S);
      } else if (b.level && (b.side === "left" || b.side === "right")) {
        // a short row facing the stage, against its side wall; rows one behind another
        const ry = Y + i * (S + ROW_GAP), x0 = b.side === "left" ? X : X + b.w - len;
        let cx = x0;
        p.items.forEach(it => {
          cx += it.before;
          if (it.blocked) blockedAt(p.row, it.id, cx, ry); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, ry);
          cx += S;
        });
        rowLabel(p, x0 - 6, ry + S / 2, "end");
        rowLabel(p, x0 + len + 6, ry + S / 2, "start");
        grow(p, x0, ry, x0 + len, ry + S);
      } else if (b.in_line) {
        // upright rows one after another down the side wall, nearest the stage first
        const up = b.seat_1 === "upstage";
        let cy = up ? run : run + len - S;
        p.items.forEach((it, j) => {
          if (j) cy += (up ? 1 : -1) * (it.before + S);
          if (it.blocked) blockedAt(p.row, it.id, X, cy); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, X, cy);
        });
        const lx = b.side === "left" ? X - 6 : X + S + 6;
        rowLabel(p, lx, run + len / 2, b.side === "left" ? "end" : "start");
        grow(p, X, run, X + S, run + len);
        run += len + BLOCK_GAP;
      } else if (b.side === "back") {
        // level rows facing the stage from the far side; nearest the stage is the bottom row
        const ry = Y + (b.pieces.length - 1 - i) * (S + ROW_GAP);
        let cx = ox - len / 2;
        p.items.forEach(it => {
          cx += it.before;
          if (it.blocked) blockedAt(p.row, it.id, cx, ry); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, ry);
          cx += S;
        });
        rowLabel(p, ox - len / 2 - 6, ry + S / 2, "end");
        rowLabel(p, ox + len / 2 + 6, ry + S / 2, "start");
        grow(p, ox - len / 2, ry, ox + len / 2, ry + S);
      } else if (b.side === "front") {
        const ry = Y + i * (S + ROW_GAP);
        let cx = ox - len / 2;
        p.items.forEach(it => {
          cx += it.before;
          if (it.blocked) blockedAt(p.row, it.id, cx, ry); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, ry);
          cx += S;
        });
        rowLabel(p, ox - len / 2 - 6, ry + S / 2, "end");
        rowLabel(p, ox + len / 2 + 6, ry + S / 2, "start");
        grow(p, ox - len / 2, ry, ox + len / 2, ry + S);
      } else {
        // columns: nearest the stage on the stage side of the bank
        const col = b.side === "left" ? b.pieces.length - 1 - i : i;
        const cx = X + col * (S + COL_GAP);
        // columns in a bank line up at the end given by align (downstage by default)
        const y0 = b.align === "upstage" || b.align === "house" || b.level_with ? Y
          : b.align === "room" || b.align === "stage" ? Y + (b.h - len) / 2 : Y + b.h - len;
        const up = b.seat_1 === "upstage";          // seat 1 at the top
        let cy = up ? y0 : y0 + len - S;
        p.items.forEach((it, j) => {
          if (j) cy += (up ? 1 : -1) * (it.before + S);
          if (it.blocked) blockedAt(p.row, it.id, cx, cy); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, cy);
        });
        rowLabel(p, cx + S / 2, y0 - 7, "middle");
        rowLabel(p, cx + S / 2, y0 + len + 8, "middle");
        grow(p, cx, y0, cx + S, y0 + len);
      }
    });
  }
  (doc.orchestra_pits || []).forEach((pit, i) => {
    // each row's extent: the blocks the pit takes
    const rows = pit.rows_removed.map(ref => {
      const { z, row } = findRow(doc, ref);
      const bx = refBlocks(ref, row)
        .map(j => boxes[`${z.name}/${row.row}/${j}`]).filter(Boolean);
      return bx.length && { x0: Math.min(...bx.map(r => r.x0)), y0: Math.min(...bx.map(r => r.y0)),
        x1: Math.max(...bx.map(r => r.x1)), y1: Math.max(...bx.map(r => r.y1)) };
    }).filter(Boolean);
    if (!rows.length) return;
    const x0 = Math.min(...rows.map(r => r.x0)), y0 = Math.min(...rows.map(r => r.y0));
    const x1 = Math.max(...rows.map(r => r.x1)), y1 = Math.max(...rows.map(r => r.y1));
    if (pit.rows_removed.every(ref => typeof ref === "string" || !ref.block)) {
      pitBand(svg, i, pit, x0 - LABEL_W, y0 - 3, x1 - x0 + 2 * LABEL_W, y1 - y0 + 6);
      return;
    }
    // part rows: a stepped outline, row by row, so the blocks the pit leaves stay outside it
    rows.sort((a, b) => a.y0 - b.y0);
    const cut = rows.map((r, k) => k ? (rows[k - 1].y1 + r.y0) / 2 : r.y0 - 3);
    const end = rows.map((r, k) => k < rows.length - 1 ? cut[k + 1] : r.y1 + 3);
    const pts = [...rows.flatMap((r, k) => [[r.x1 + LABEL_W, cut[k]], [r.x1 + LABEL_W, end[k]]]),
      ...rows.flatMap((r, k) => [[r.x0 - LABEL_W, cut[k]], [r.x0 - LABEL_W, end[k]]]).reverse()];
    pitBand(svg, i, pit, 0, 0, 0, 0, pts, { x: rows[0].x0 - LABEL_W - 6, y: (rows[0].y0 + rows[0].y1) / 2, "text-anchor": "end" });
  });
  const bottom = oy + Math.max(houseBottom, ...ext.map(e => e.y1)) + LBL + 10;
  return finishMap(svg, doc, W, bottom, opts);
}

// ---------------------------------------------------------------- arc maps
// For round halls. layout.arrangement: "arc" selects this. layout.arc holds the venue-wide centre and
// the stage wedge; each zone's arc holds its angular span (360 = a closed ring), its bearing (where the
// arc begins: 0 = up, clockwise) and its radius band (tier, ring). Rows are concentric rings about the
// centre; the seats of a row are spread along its arc, rotated to the tangent.
function drawArcMap(doc, opts = {}) {
  const layout = doc.layout || {}, arc = layout.arc || {};
  const RAD = Math.PI / 180;
  const stageSpan = arc.stage_span ?? 150;
  const rotateSeats = arc.rotate_seats !== false;
  const pitch = S * (arc.ring_gap ?? 1.6);
  const R0 = pitch * 3;
  const tierGap = arc.tier_gap ?? pitch * 4;      // extra radius per tier (a higher ring set)
  const pos = (r, deg) => [r * Math.sin(deg * RAD), -r * Math.cos(deg * RAD)];
  const svg = el("svg", { role: "img", "aria-label": `Seat schematic for ${doc.venue.name_en}` });
  const devg = el("g", { class: "dev" }, svg);     // developer overlay (shown by the Developer mode toggle)
  const ext = [];                                 // seat/label extents, for the viewBox
  const remember = (x, y, m = S) => ext.push({ x0: x - m, x1: x + m, y0: y - m, y1: y + m });
  const inPits = () => "";

  // the stage: a wedge in the opening at the top, bearing 0
  // (layout.arc.stage {shape: "circle", radius}: a round stage at the centre, for a hall seated all round;
  // radius in the file's units, before scale)
  const roundStage = arc.stage?.shape === "circle";
  const sr = roundStage ? arc.stage.radius * (arc.scale ?? 1) : R0 * 0.9;
  if (roundStage) {
    el("circle", { class: "stage", cx: 0, cy: 0, r: sr }, svg);
  } else {
    const a0 = -stageSpan / 2, a1 = stageSpan / 2;
    const [sx0, sy0] = pos(sr, a0), [sx1, sy1] = pos(sr, a1);
    el("path", { class: "stage", d: `M 0 0 L ${sx0} ${sy0} A ${sr} ${sr} 0 0 1 ${sx1} ${sy1} Z` }, svg);
  }
  const st = el("text", { class: "stagetext", x: 0, y: roundStage ? 0 : -sr * 0.45 }, svg);
  st.textContent = layout.stage_label || "STAGE 舞台";

  const gapW = 1.2;                               // aisle between blocks, in seat-widths
  let maxR = sr;
  const headings = [];
  doc.zones.forEach((z, zi) => {
    const za = z.arc; if (!za) return;
    const tier = za.tier ?? 0, ring0 = za.ring ?? 0;
    // a block may reference a shared arc (aisle interval) and carry only overrides; resolve it here
    const arcsById = Object.fromEntries((z.arcs || []).map(a => [a.id, a]));
    // layout.arc.scale enlarges the plan's units (radii and offsets) so seats drawn S wide fit the plan's
    // seat pitch; bearings are unchanged
    const k = arc.scale ?? 1;
    const sc = v => v == null ? v : v * k;
    const geom = (row, b) => {
      const a = b.arc ? arcsById[b.arc] : null;
      return {
        shape: b.shape ?? a?.shape,
        view: b.view ?? a?.view,
        offset: sc(b.offset ?? a?.offset ?? 0),  // the radius is kept per block; the arc shares the rest
        radius: sc(b.radius),
        start: b.start ?? a?.from,                // a block may override its arc's aisle bounds
        end: b.end ?? a?.to,
        inner: sc(b.inner ?? a?.inner),
        outer: sc(b.outer ?? a?.outer),
      };
    };
    // start = bearing of seat 1; dir cw (increasing bearing, clockwise) or ccw; span in degrees
    const span = za.span ?? 360;
    const dir = za.dir === "cw" ? 1 : -1;
    const start = za.start ?? ((za.bearing ?? 180) + (dir > 0 ? -span / 2 : span / 2));
    z.rows.forEach((row, ri) => {
      const radius = R0 + (tier * tierGap + (ring0 + ri) * pitch);
      maxR = Math.max(maxR, radius);
      // a row whose blocks each carry a view axis is drawn as straight runs (a non-radial row):
      // each block faces `view` at distance `offset`, its seats evenly spaced from `start` to `end`
      if (row.blocks.length && row.blocks.every(b => { const g = geom(row, b); return b.runs?.length || (g.view != null && g.start != null && g.end != null); })) {
        let firstP = null, lastP = null, firstU = null, lastU = null;
        // a block whose seats bend (a straight run, a turned corner seat, another straight run) lists
        // its pieces as runs: each takes the next `count` seats and carries its own shape and geometry
        const pieces = block => {
          const items = [...(block.seats || []).map(id => ({ id })),
                         ...((block.blocked && block.blocked.skipped_numbers) || []).map(id => ({ id, blocked: true }))];
          if (!block.runs?.length) return [{ g: geom(row, block), items }];
          let at = 0;
          return block.runs.map(r => {
            const g = { shape: r.shape ?? "line", view: r.view, offset: sc(r.offset), radius: sc(r.radius),
                        start: r.start, end: r.end, inner: sc(block.inner), outer: sc(block.outer) };
            const part = items.slice(at, at + r.count); at += r.count;
            return { g, items: part };
          });
        };
        row.blocks.forEach((block, bi) => pieces(block).forEach(({ g, items }, pi, all) => {
          const lastPiece = pi === all.length - 1;
          const bo = (g.view + 180) % 360;          // outward normal bearing
          // chord mode places seats on a straight line perpendicular to the view axis at
          // distance g.offset; good when the block's angular span is narrow. For wide
          // spans the chord cuts inward from the seats' true radius by (R - R*cos(half)),
          // which can be tens of units: Row G seats 30-44 (57 deg span) end up ~38 units
          // closer to centre than they belong. Switch to arc mode when the span is wide:
          // each seat sits on the circle of radius R = g.offset / cos(half_span), rotated
          // to the tangent at its own bearing.
          // A block with an explicit shape ("line" or "arc") says which, and its start/end are then the
          // bearings of its first and last seat centres (no aisle inset); an arc block may give its radius.
          const spanDeg = Math.abs(((g.end - g.start + 540) % 360) - 180);
          const useArc = g.shape ? g.shape === "arc" : spanDeg > 20;
          const exact = !!g.shape;
          const seatR = useArc ? (g.radius ?? g.offset / Math.cos(spanDeg / 2 * RAD)) : g.offset;
          const at = bearing => {
            if (useArc) return [seatR * Math.sin(bearing * RAD), -seatR * Math.cos(bearing * RAD)];
            const d = g.offset / Math.cos((bearing - bo) * RAD);
            return [d * Math.sin(bearing * RAD), -d * Math.cos(bearing * RAD)];
          };
          const P0 = at(g.start), P1 = at(g.end);
          // the run's direction at each end, for row labels placed along it (layout.arc.row_labels "along")
          const len = Math.hypot(P1[0] - P0[0], P1[1] - P0[1]);
          const u = len ? [(P1[0] - P0[0]) / len, (P1[1] - P0[1]) / len] : null;
          if (!firstP) { firstP = P0; firstU = u && [-u[0], -u[1]]; }
          if (lastPiece) { lastP = P1; lastU = u; }
          // developer overlay: the block's axis, its shared-aisle ends and its inner/outer boundaries
          // data-geo names the block and run (zone/row/block/run), for the reviewer's Geometry tab
          const marked = { "data-geo": `${zi}/${ri}/${bi}/${block.runs?.length ? pi : -1}`, ...(block.arc ? { "data-arc": block.arc } : {}) };
          el("line", { class: "dev-axis", ...marked, x1: P0[0], y1: P0[1], x2: P1[0], y2: P1[1] }, devg);
          el("circle", { class: "dev-dot", ...marked, cx: P0[0], cy: P0[1], r: 1.7 }, devg);
          el("circle", { class: "dev-dot", ...marked, cx: P1[0], cy: P1[1], r: 1.7 }, devg);
          // inner/outer boundaries as radial arcs spanning the block's aisles
          const delta = ((g.end - g.start + 540) % 360) - 180, cw = delta > 0;
          const arcPath = (r) => {
            const [x0, y0] = pos(r, g.start), [x1, y1] = pos(r, g.end);
            return `M ${x0} ${y0} A ${r} ${r} 0 ${Math.abs(delta) > 180 ? 1 : 0} ${cw ? 1 : 0} ${x1} ${y1}`;
          };
          for (const [cls, r] of [["dev-inner", g.inner], ["dev-outer", g.outer]]) {
            if (r == null) continue;
            el("path", { class: cls, ...marked, d: arcPath(r) }, devg);
          }
          const lt = el("text", { class: "dev-label", ...marked, x: (P0[0] + P1[0]) / 2, y: (P0[1] + P1[1]) / 2 }, devg);
          lt.textContent = `${g.shape ?? ""} ${g.view}° o${g.offset} [${g.inner}-${g.outer}]`;
          const n = items.length;
          // In chord mode seats interpolate linearly between the two chord endpoints, inset
          // by half an aisle. In arc mode they interpolate in BEARING along the arc, also
          // inset by half an aisle (converted to degrees along the circle); each seat
          // rotates to its own tangent so the whole run follows the ring.
          const dx = P1[0] - P0[0], dy = P1[1] - P0[1], L = Math.hypot(dx, dy) || 1;
          const inset = exact ? 0 : S * 0.6;
          const gx = dx / L * inset, gy = dy / L * inset;
          const Ax = P0[0] + gx, Ay = P0[1] + gy, Bx = P1[0] - gx, By = P1[1] - gy;
          const bearingInset = useArc ? Math.atan2(inset, seatR) / RAD : 0;
          const bStart = useArc ? g.start + (g.end > g.start ? bearingInset : -bearingInset) : null;
          const bEnd = useArc ? g.end + (g.end > g.start ? -bearingInset : bearingInset) : null;
          items.forEach((it, i) => {
            const t = n > 1 ? i / (n - 1) : 0.5;
            let x, y, rot;
            if (useArc) {
              const deg = bStart + (bEnd - bStart) * t;
              x = seatR * Math.sin(deg * RAD);
              y = -seatR * Math.cos(deg * RAD);
              rot = deg + 180;                      // along the tangent: level at the front (bearing 180)
            } else {
              x = Ax + (Bx - Ax) * t;
              y = Ay + (By - Ay) * t;
              rot = g.view;                         // along the run, as the plan prints its numbers
            }
            // a seat is square, so turning it a half turn changes nothing but keeps its number upright
            rot = ((rot % 360) + 360) % 360;
            if (rot > 90 && rot <= 270) rot -= 180;
            remember(x, y);
            if (it.blocked) {
              const g2 = el("g", { class: "seat blocked" }, svg);
              const r = el("rect", { x: -S / 2, y: -S / 2, width: S, height: S, rx: 1 }, g2);
              el("title", {}, r).textContent = `${row.row}: solid area where ${it.id} would be (not seats)`;
              g2.setAttribute("transform", `translate(${x} ${y}) rotate(${rotateSeats ? rot : 0})`);
            } else {
              const seatG = seatAt(svg, z, row, it.id, block, inPits, -S / 2, -S / 2);
              seatG.dataset.geo = marked["data-geo"];
              seatG.setAttribute("transform", `translate(${x} ${y}) rotate(${rotateSeats ? rot : 0})`);
            }
          });
        }));
        // row labels: above each end of the row, or (row_labels "along") just beyond each end, in line with
        // the run, so they clear the seats however the run is turned. A long label (a named row such as
        // "Wheel Chair Box") is drawn once, beside the middle of the row on the side away from the centre.
        const along = arc.row_labels === "along";
        const long = along && row.row.length > 3 && lastU;
        const place = [];
        if (long) {
          const mid = [(firstP[0] + lastP[0]) / 2, (firstP[1] + lastP[1]) / 2];
          let nrm = [-lastU[1], lastU[0]];
          if (nrm[0] * mid[0] + nrm[1] * mid[1] < 0) nrm = [-nrm[0], -nrm[1]];
          place.push([mid, nrm, S * 1.1]);
        } else {
          place.push([firstP, firstU, S * 0.9], [lastP, lastU, S * 0.9]);
        }
        for (const [P, U, d] of place) {
          let x = P[0], y = P[1] - S, anchor = "middle";
          if (along && U) {
            x = P[0] + U[0] * d; y = P[1] + U[1] * d;
            anchor = U[0] > 0.35 ? "start" : U[0] < -0.35 ? "end" : "middle";
            if (anchor === "middle") y += U[1] * S * 0.2;
          }
          const t = el("text", { class: "rowlabel", x, y, "text-anchor": anchor }, svg);
          t.textContent = row.row;
          Object.assign(t.dataset, { row: row.row, zone: z.name });
          remember(P[0], P[1]);
          remember(x, y);
        }
        return;
      }
      const blocks = rowLayout(row, false);       // arc rows keep the file order (seat 1 first)
      const items = [];
      blocks.forEach((b, bi) => { if (bi) items.push({ gap: true }); b.items.forEach(it => items.push(it)); });
      const total = items.reduce((a, it) => a + (it.gap ? gapW : 1), 0);
      const step = span / total;
      let cum = 0;
      items.forEach(it => {
        const w = it.gap ? gapW : 1;
        if (!it.gap) {
          const deg = start + dir * (cum + w / 2) * step;
          const [x, y] = pos(radius, deg);
          remember(x, y);
          if (it.blocked) {
            const g = el("g", { class: "seat blocked" }, svg);
            const r = el("rect", { x: -S / 2, y: -S / 2, width: S, height: S, rx: 1 }, g);
            el("title", {}, r).textContent = `${row.row}: solid area where ${it.id} would be (not seats)`;
            g.setAttribute("transform", `translate(${x} ${y}) rotate(${rotateSeats ? deg + 90 : 0})`);
          } else {
            const g = seatAt(svg, z, row, it.id, {}, inPits, -S / 2, -S / 2);
            g.setAttribute("transform", `translate(${x} ${y}) rotate(${rotateSeats ? deg + 90 : 0})`);
          }
        }
        cum += w;
      });
      // the row label near each end of the arc, outside it
      for (const deg of [start, start + dir * span]) {
        const [x, y] = pos(radius + pitch * 0.9, deg);
        const t = el("text", { class: "rowlabel", x, y, "text-anchor": "middle" }, svg);
        t.textContent = row.row;
        Object.assign(t.dataset, { row: row.row, zone: z.name });
        remember(x, y);
      }
    });
    // za.label_at: where the plan prints the part of house's name, as [x, y] from the centre in the file's
    // units (before scale); without it the heading is stacked below the seats
    headings.push({ name: z.name, zh: z.name_zh || "", at: za.label_at && za.label_at.map(v => v * k) });
  });
  // vomitoria: entrances that cut an angular gap through some rows only (drawn as a shaded wedge)
  doc.zones.forEach((z, zi) => (z.vomitoria || []).forEach((v, vi) => {
    const r0 = (v.inner ?? 0) * (arc.scale ?? 1), r1 = (v.outer ?? 0) * (arc.scale ?? 1);
    const a0 = Math.min(v.from, v.to), a1 = Math.max(v.from, v.to);
    const large = (a1 - a0) > 180 ? 1 : 0;
    const [x0, y0] = pos(r0, a0), [x1, y1] = pos(r0, a1), [x2, y2] = pos(r1, a1), [x3, y3] = pos(r1, a0);
    el("path", { class: "vomitorium", "data-vom": vi, d: `M ${x0} ${y0} A ${r0} ${r0} 0 ${large} 1 ${x1} ${y1} L ${x2} ${y2} A ${r1} ${r1} 0 ${large} 0 ${x3} ${y3} Z` }, svg);
    el("text", { class: "vomitorium-label", "data-vom": vi, x: (x0 + x3) / 2, y: (y0 + y3) / 2 }, svg).textContent = "V";
    remember(x0, y0); remember(x1, y1); remember(x2, y2); remember(x3, y3);
  }));
  // developer overlay: the shared aisles as radial lines from the centre
  const far = 1.04 * Math.max(...ext.map(e => Math.max(Math.hypot(e.x0, e.y0), Math.hypot(e.x1, e.y1))));
  (layout.aisles || []).forEach((a, i) => {
    const [x, y] = pos(far, a);
    el("line", { class: "dev-aisle", "data-aisle": i, x1: 0, y1: 0, x2: x, y2: y }, devg);
    el("text", { class: "dev-label", "data-aisle": i, x, y, "text-anchor": "middle" }, devg).textContent = a;
    remember(x, y);
  });
  // developer overlay: a polar grid behind everything, in the file's units (radius before scale)
  const grid = el("g", { class: "dev-grid" });
  devg.prepend(grid);
  const k0 = arc.scale ?? 1, step = 50;
  for (let r = step; r * k0 < far; r += step) {
    el("circle", { class: r % 100 ? "" : "major", cx: 0, cy: 0, r: r * k0 }, grid);
    el("text", { x: 2, y: -r * k0 - 1 }, grid).textContent = r;
  }
  for (let b = 0; b < 360; b += 10) {
    const [x, y] = pos(far, b);
    el("line", { class: b % 30 ? "" : "major", x1: 0, y1: 0, x2: x, y2: y }, grid);
    if (!(b % 30)) { const [tx, ty] = pos(far - 8, b); el("text", { x: tx, y: ty, "text-anchor": "middle" }, grid).textContent = `${b}°`; }
  }
  // part-of-house headings: where the file places them (label_at), else stacked below the seats (clear of
  // the seating, radial or not)
  const seatBottom = Math.max(...ext.map(e => e.y1));
  headings.filter(h => !h.at).forEach((h, i) => {
    h.at = [0, seatBottom + pitch * (1.5 + i * 1.6)];
    h.stacked = true;
  });
  headings.forEach(h => {
    const hl = el("text", { class: "zonelabel", x: h.at[0], y: h.at[1], "text-anchor": "middle",
                            ...(h.stacked ? {} : { "dominant-baseline": "central" }) }, svg);
    hl.textContent = `${h.name} ${h.zh}`.trim();
    hl.dataset.zone = h.name;
    remember(h.at[0], h.at[1], h.stacked ? 60 : S);
  });

  const pad = pitch * 2;
  const minX = Math.min(...ext.map(e => e.x0)) - pad, maxX = Math.max(...ext.map(e => e.x1)) + pad;
  const minY = Math.min(...ext.map(e => e.y0)) - pad, maxY = Math.max(...ext.map(e => e.y1)) + pad;
  const W = maxX - minX, ox = -minX, oy = -minY;
  const g = el("g", { transform: `translate(${ox} ${oy})` });
  for (const c of [...svg.children]) g.appendChild(c);
  svg.appendChild(g);
  // where the centre is in the drawing, and the scale, so a tool can turn a pointer into bearing and radius
  Object.assign(svg.dataset, { ox, oy, scale: arc.scale ?? 1 });
  return finishMap(svg, doc, W, maxY - minY, opts);
}

// ---------------------------------------------------------------- zoom
// The map sits in a fixed frame (#map) that scrolls. It starts fitted to the frame; − / + / Fit / 100% and
// Ctrl/⌘ + wheel (or a trackpad pinch) zoom it, keeping the point under the pointer in place.
const zoom = { frame: null, svg: null, scale: 1, fit: true, label: null };
const ZOOM_STEP = 1.25, ZOOM_MAX = 4;

function zoomControls(box) {
  box.classList.add("zoomctl");
  box.innerHTML = `<button type="button" data-z="out" aria-label="Zoom out" title="Zoom out">−</button>
    <span class="zlevel" aria-live="polite"></span>
    <button type="button" data-z="in" aria-label="Zoom in" title="Zoom in">+</button>
    <button type="button" data-z="fit" title="Fit the whole map in the frame">Fit</button>
    <button type="button" data-z="one" title="Actual size">100%</button>`;
  zoom.label = box.querySelector(".zlevel");
  box.querySelector('[data-z="out"]').onclick = () => zoomTo(zoom.scale / ZOOM_STEP);
  box.querySelector('[data-z="in"]').onclick = () => zoomTo(zoom.scale * ZOOM_STEP);
  box.querySelector('[data-z="fit"]').onclick = () => { zoom.fit = true; applyZoom(fitScale()); };
  box.querySelector('[data-z="one"]').onclick = () => zoomTo(1);
}

// Put a freshly drawn map in the frame, fitted.
function showMap(frame, svg) {
  const first = !zoom.frame;
  zoom.frame = frame; zoom.svg = svg; zoom.fit = true;
  frame.replaceChildren(svg);
  applyZoom(fitScale());
  if (first) {
    new ResizeObserver(() => { if (zoom.fit && zoom.svg) applyZoom(fitScale()); }).observe(frame);
    frame.addEventListener("wheel", e => {
      if (!(e.ctrlKey || e.metaKey)) return;              // plain wheel scrolls the frame
      e.preventDefault();
      zoomTo(zoom.scale * Math.exp(-e.deltaY * 0.0022), e.clientX, e.clientY);
    }, { passive: false });
  }
}

function fitScale() {
  const vb = zoom.svg.viewBox.baseVal, f = zoom.frame;
  return Math.max(0.05, Math.min((f.clientWidth - 4) / vb.width, (f.clientHeight - 4) / vb.height));
}

function zoomTo(scale, cx, cy) {
  zoom.fit = false;
  const min = Math.min(fitScale(), 1) * 0.5;
  applyZoom(Math.min(ZOOM_MAX, Math.max(min, scale)), cx, cy);
}

// Resize the drawing to scale; keep the map point under (cx, cy) - or the frame's centre - where it was.
function applyZoom(scale, cx, cy) {
  const { svg, frame } = zoom, vb = svg.viewBox.baseVal;
  const fr = frame.getBoundingClientRect();
  if (cx === undefined) { cx = fr.left + frame.clientWidth / 2; cy = fr.top + frame.clientHeight / 2; }
  const before = svg.getBoundingClientRect(), old = before.width / vb.width || scale;
  const u = (cx - before.left) / old, v = (cy - before.top) / old;
  zoom.scale = scale;
  svg.setAttribute("width", Math.round(vb.width * scale));
  svg.setAttribute("height", Math.round(vb.height * scale));
  const after = svg.getBoundingClientRect();
  frame.scrollLeft += after.left + u * scale - cx;
  frame.scrollTop += after.top + v * scale - cy;
  if (zoom.label) zoom.label.textContent = `${Math.round(scale * 100)}%`;
}
