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

// One seat, with what the viewer and planner read from it (zone, row, seat, mark, notes).
function seatAt(svg, z, row, s, b, inPits, x, y) {
  const mark = markOf(row, s);
  const g = el("g", { class: `seat ${letters(mark).join(" ")}`, tabindex: 0 }, svg);
  Object.assign(g.dataset, { mark, row: row.row, seat: s, zone: z.name });
  if (row.inferred_numbers?.[s]) g.dataset.inferred = row.inferred_numbers[s];
  if (row.note) g.dataset.note = row.note;
  if (b.area) g.dataset.area = b.area;
  if (inPits) g.dataset.pits = inPits;
  seatGlyph(g, x, y, mark, s);
  return g;
}
const pitNote = (doc, row) => pitsFor(doc, row.row).map(p => `${p.name} (rows ${p.rows_basis})`).join(", ");

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
  if (doc.layout?.banks?.length) return drawBankedMap(doc);
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
      const inPits = pitNote(doc, row);
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
    y += ZONE_GAP;
  }
  (doc.orchestra_pits || []).forEach((pit, i) => {
    const ys = pit.rows_removed.map(r => rowY[r]);
    const top = Math.min(...ys), bottom = Math.max(...ys) + S;
    pitBand(svg, i, pit, 2, top - 3, W - 4, bottom - top + 6);
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
  return finishMap(svg, doc, W, y - ZONE_GAP + 14);
}

function pitBand(svg, i, pit, x, y, w, h) {
  const band = el("g", { class: "pitband" }, svg);
  band.dataset.pit = i;
  el("rect", { x, y, width: w, height: h, rx: 4 }, band);
  el("text", { x: x + 8, y: y + h / 2 }, band).textContent = pit.name;
}

// Disclaimer inside the drawing, so it stays with any screenshot of the map; then size the drawing.
function finishMap(svg, doc, W, y) {
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
  const H = y + boxH + 4;
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
//     "house" (beside the front banks, from their first row), "room" (centred on stage and front banks)
//   label: optional heading drawn with the bank
const BANK_GAP = 18, COL_GAP = 8;

function bankPieces(doc, bank) {
  const byName = new Map();
  for (const z of doc.zones) for (const r of z.rows) byName.set(r.row, { z, row: r });
  return bank.rows.map(ref => {
    const { z, row } = byName.get(typeof ref === "string" ? ref : ref.row);
    const blocks = typeof ref === "string" ? row.blocks : [row.blocks[ref.block - 1]];
    return { z, row, blocks };
  });
}

// A piece's seats (and blocked slots) in order from seat 1's end, with the space before each.
function pieceItems(piece, reversed) {
  const blocks = reversed ? [...piece.blocks].reverse() : piece.blocks;
  const bl = rowLayout({ blocks }, reversed);
  const out = [];
  bl.forEach((b, i) => b.items.forEach((it, j) => out.push({ ...it, b: blocks[i], before: j ? GAP : i ? between(bl[i - 1], b) : 0 })));
  return out;
}
const pieceLength = items => items.reduce((a, it) => a + it.before + S, 0);

function drawBankedMap(doc) {
  const banks = doc.layout.banks.map(bk => {
    const pieces = bankPieces(doc, bk).map(p => ({ ...p, items: pieceItems(p, bk.side === "front" && bk.seat_1 === "right") }));
    const lens = pieces.map(p => pieceLength(p.items));
    const along = Math.max(...lens), across = pieces.length * (S + (bk.side === "front" ? ROW_GAP : COL_GAP)) - (bk.side === "front" ? ROW_GAP : COL_GAP);
    return { ...bk, pieces, lens, along, across };
  });
  const front = banks.filter(b => b.side === "front"), left = banks.filter(b => b.side === "left"), right = banks.filter(b => b.side === "right");
  const outer = b => b.align === "room" || b.align === "house";   // beside the front banks, not the stage
  const beside = [...left, ...right].filter(b => !outer(b));
  const frontW = Math.max(0, ...front.map(b => b.along));
  const stageW = Math.min(300, Math.max(120, frontW * .7));
  const stageH = Math.max(36, ...beside.map(b => b.along));
  const LBL = 14;                                   // room for labels above and below side columns

  // positions around a stage centred on x = 0, top at y = 0 (shifted into view at the end)
  const place = [];                                 // {bank, x, y} of each bank's top-left corner
  const houseTop = stageH + BANK_GAP + LBL;
  let y = houseTop;
  const zonesSeen = new Set();
  for (const b of front) {
    // a heading for the bank's own label, or for the first front bank of each part of house
    b.heading = b.label || (!zonesSeen.has(b.pieces[0].z.name) ? `${b.pieces[0].z.name} ${b.pieces[0].z.name_zh || ""}`.trim() : "");
    b.pieces.forEach(p => zonesSeen.add(p.z.name));
    if (b.heading && b !== front[0]) y += 14;
    place.push({ b, x: -b.along / 2, y });
    y += b.across + BANK_GAP;
  }
  const houseBottom = y - BANK_GAP;
  const frontHalf = frontW / 2 + LABEL_W;
  for (const [list, dir] of [[left, -1], [right, 1]]) {
    let edge = stageW / 2 + BANK_GAP;               // distance from the centre line to the bank's inner edge
    for (const b of list) {
      if (outer(b)) edge = Math.max(edge, frontHalf + BANK_GAP);
      const x = dir < 0 ? -edge - b.across : edge;
      const top = b.align === "upstage" ? 0 : b.align === "house" ? houseTop : b.align === "room" ? (houseBottom - b.along) / 2 : stageH - b.along;
      place.push({ b, x, y: top });
      edge += b.across + BANK_GAP;
    }
  }
  const minX = Math.min(-stageW / 2, ...place.map(p => p.x)) - LABEL_W;
  const maxX = Math.max(stageW / 2, ...place.map(p => p.x + (p.b.side === "front" ? p.b.along : p.b.across))) + LABEL_W;
  const minY = Math.min(0, ...place.map(p => p.y)) - LBL - 18;
  const W = maxX - minX, ox = -minX, oy = -minY + 4;

  const svg = el("svg", { role: "img", "aria-label": `Seat schematic for ${doc.venue.name_en}` });
  el("rect", { class: "stage", x: ox - stageW / 2, y: oy, width: stageW, height: stageH, rx: 3 }, svg);
  el("text", { class: "stagetext", x: ox, y: oy + stageH / 2 }, svg).textContent = "STAGE 舞台";
  const boxes = {};                                 // row -> bounding box, for the pit bands
  const grow = (row, x0, y0, x1, y1) => {
    const r = boxes[row] || (boxes[row] = { x0, y0, x1, y1 });
    Object.assign(r, { x0: Math.min(r.x0, x0), y0: Math.min(r.y0, y0), x1: Math.max(r.x1, x1), y1: Math.max(r.y1, y1) });
  };
  const rowLabel = (piece, x, y, anchor) => {
    const t = el("text", { class: "rowlabel", x, y, "text-anchor": anchor }, svg);
    t.textContent = piece.row.row;
    Object.assign(t.dataset, { row: piece.row.row, zone: piece.z.name });
  };
  const blockedAt = (row, id, x, y) => {
    const r = el("rect", { class: "blockedarea", x, y, width: S, height: S, rx: 1 }, svg);
    el("title", {}, r).textContent = `${row.row}: solid area where ${id} would be (not seats)`;
  };

  for (const { b, x, y: top } of place) {
    const X = ox + x, Y = oy + top;
    const heading = b.side === "front" ? b.heading : b.label || "";
    if (heading) {
      const hx = b.side === "front" ? ox : X + b.across / 2, hy = b.side === "front" ? Y - 8 : Y - LBL - 6;
      const zl = el("text", { class: "zonelabel", x: hx, y: hy }, svg);
      zl.textContent = heading;
      zl.dataset.zone = b.pieces[0].z.name;
    }
    b.pieces.forEach((p, i) => {
      const inPits = pitNote(doc, p.row), len = b.lens[i];
      if (b.side === "front") {
        const ry = Y + i * (S + ROW_GAP);
        let cx = ox - len / 2;
        p.items.forEach(it => {
          cx += it.before;
          if (it.blocked) blockedAt(p.row, it.id, cx, ry); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, ry);
          cx += S;
        });
        rowLabel(p, ox - len / 2 - 6, ry + S / 2, "end");
        rowLabel(p, ox + len / 2 + 6, ry + S / 2, "start");
        grow(p.row.row, ox - len / 2, ry, ox + len / 2, ry + S);
      } else {
        // columns: nearest the stage on the stage side of the bank
        const col = b.side === "left" ? b.pieces.length - 1 - i : i;
        const cx = X + col * (S + COL_GAP);
        // columns in a bank line up at the end given by align (downstage by default)
        const y0 = b.align === "upstage" || b.align === "house" ? Y : b.align === "room" ? Y + (b.along - len) / 2 : Y + b.along - len;
        const up = b.seat_1 === "upstage";          // seat 1 at the top
        let cy = up ? y0 : y0 + len - S;
        p.items.forEach((it, j) => {
          if (j) cy += (up ? 1 : -1) * (it.before + S);
          if (it.blocked) blockedAt(p.row, it.id, cx, cy); else seatAt(svg, p.z, p.row, it.id, it.b, inPits, cx, cy);
        });
        rowLabel(p, cx + S / 2, y0 - 7, "middle");
        rowLabel(p, cx + S / 2, y0 + len + 8, "middle");
        grow(p.row.row, cx, y0, cx + S, y0 + len);
      }
    });
  }
  (doc.orchestra_pits || []).forEach((pit, i) => {
    const bx = pit.rows_removed.map(r => boxes[r]).filter(Boolean);
    if (!bx.length) return;
    const x0 = Math.min(...bx.map(r => r.x0)), y0 = Math.min(...bx.map(r => r.y0));
    const x1 = Math.max(...bx.map(r => r.x1)), y1 = Math.max(...bx.map(r => r.y1));
    pitBand(svg, i, pit, x0 - LABEL_W, y0 - 3, x1 - x0 + 2 * LABEL_W, y1 - y0 + 6);
  });
  const bottom = oy + Math.max(houseBottom, ...place.map(p => p.y + (p.b.side === "front" ? p.b.across : p.b.along))) + LBL + 10;
  return finishMap(svg, doc, W, bottom);
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
