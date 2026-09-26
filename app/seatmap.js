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
const pitsFor = (doc, row) => (doc.orchestra_pits || []).filter(p => p.rows_removed.includes(row));

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
  zones: Object.fromEntries(d.zones.map(z => [z.name, true])),
  standing: false,
});

// The reason a seat is left out of configuration st, or "" when it counts.
function excludedIn(doc, st, zone, row, mark) {
  if (!st.zones[zone]) return `${zone} closed`;
  const pit = doc.orchestra_pits?.[st.pit];
  if (pit?.rows_removed.includes(row)) return `${pit.name} in use`;
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

// Draws the whole map for doc and returns the <svg>; the caller places it and styles the seats.
function drawSeatMap(doc) {
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
  el("text", { class: "stagetext", x: W / 2, y: y + 15 }, svg).textContent = "STAGE 舞台";
  y += 30 + 22;
  const x0 = LABEL_W + 4;
  const rowY = {};

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
      const inPits = pitsFor(doc, row.row).map(p => p.name).join(", ");
      bl.forEach((b, i) => b.items.forEach(({ id: s, blocked }, j) => {
        if (blocked) {
          if (j && b.items[j - 1].blocked) return;          // one filled area per run of blocked slots
          let k = j; while (b.items[k + 1]?.blocked) k++;
          const r = el("rect", { class: "blockedarea", x: xs[i] + j * (S + GAP), y, width: (k - j + 1) * (S + GAP) - GAP, height: S, rx: 1 }, svg);
          el("title", {}, r).textContent = `${row.row}: solid area where ${b.items.slice(j, k + 1).map(t => t.id).join(", ")} would be (not seats)`;
          return;
        }
        const mark = markOf(row, s);
        const g = el("g", { class: `seat ${letters(mark).join(" ")}`, tabindex: 0 }, svg);
        Object.assign(g.dataset, { mark, row: row.row, seat: s, zone: z.name });
        if (row.inferred_numbers?.[s]) g.dataset.inferred = row.inferred_numbers[s];
        if (row.note) g.dataset.note = row.note;
        if (b.area) g.dataset.area = b.area;
        if (inPits) g.dataset.pits = inPits;
        seatGlyph(g, xs[i] + j * (S + GAP), y, mark, s);
      }));
      rowY[row.row] = y;
      y += S + ROW_GAP;
    }
    y += ZONE_GAP;
  }
  (doc.orchestra_pits || []).forEach((pit, i) => {
    const ys = pit.rows_removed.map(r => rowY[r]);
    const top = Math.min(...ys), bottom = Math.max(...ys) + S;
    const band = el("g", { class: "pitband" }, svg);
    band.dataset.pit = i;
    el("rect", { x: 2, y: top - 3, width: W - 4, height: bottom - top + 6, rx: 4 }, band);
    el("text", { x: 10, y: (top + bottom) / 2 }, band).textContent = pit.name;
  });
  if (doc.standing?.places?.length) {
    const places = doc.standing.places, n = places.length;
    y -= ZONE_GAP - 10;
    const w = n * S + (n - 1) * GAP;
    let x = x0 + (maxW - w) / 2;
    const g = el("g", { class: "standing" }, svg);
    (rightFirst ? [...places].reverse() : places).forEach(pl => {
      el("rect", { x, y, width: S, height: S, rx: 7 }, g);
      el("text", { x: x + S / 2, y: y + S / 2 + .5 }, g).textContent = pl;
      x += S + GAP;
    });
    el("text", { class: "rowlabel", x: W / 2, y: y + S + 10, "text-anchor": "middle" }, svg).textContent = "Standing";
    y += S + 24 + ZONE_GAP;
  }
  // Disclaimer inside the drawing, so it stays with any screenshot of the map.
  y = y - ZONE_GAP + 14;
  const lines = wrap("This map is drawn from the seat data published with it: a machine-assisted reading of the rows " +
    "and seats of the venue. It is not the actual seat plan. For the actual seat plan, refer to the version " +
    "published by LCSD:", Math.floor((W - 24) / 5.1));
  const box = el("g", { class: "disclaimer" }, svg);
  const boxH = (lines.length + 2) * 13 + 10;
  el("rect", { x: 2, y, width: W - 4, height: boxH, rx: 4 }, box);
  el("text", { class: "lead", x: 12, y: y + 16 }, box).textContent = "Not the venue's seat plan";
  lines.forEach((l, i) => { el("text", { x: 12, y: y + 16 + (i + 1) * 13 }, box).textContent = l; });
  const a = el("a", { href: doc.source.url, target: "_blank", rel: "noopener" }, box);
  el("text", { x: 12, y: y + 16 + (lines.length + 1) * 13 }, a).textContent = doc.source.url;
  y += boxH + ZONE_GAP;
  const H = y - ZONE_GAP + 4;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  return svg;
}
