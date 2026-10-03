// Seat-list editing, shared by the row reviewer (tools/review.html) and the customiser. Pure functions on
// seatlist JSON: no DOM. A row is edited as blocks of seat objects {id, mark, inf, from}, where `from` is
// the seat's place in the row before the edit ("block:index"), and rebuilt into JSON with its geometry,
// side/area and blocked slots following the seats. Bank and pit references to blocks are renumbered.
(function (root) {
const MARK_ORDER = "WXRL";
const GEOM_KEYS = ["shape", "view", "offset", "radius", "start", "end"];
const BOUND_KEYS = ["inner", "outer"];

const normMark = m => [...new Set(m)].sort((a, b) => MARK_ORDER.indexOf(a) - MARK_ORDER.indexOf(b)).join("");
// an unnumbered W or X box is labelled W1, X2...: its prefix implies its mark
const impliedMark = id => (id.match(/^([WX])\d+$/) || [])[1] || "";

// the seats of a JSON row, as blocks of seat objects
function rowSeats(row) {
  return row.blocks.map((b, bi) => b.seats.map((id, i) => ({
    id, mark: row.marks?.[id] || "", inf: row.inferred_numbers?.[id] || "", from: `${bi}:${i}`,
  })));
}

// "1-5 | W1 W2=7 8r 9rl" -> blocks of seats. Marks are lowercase suffixes (any letters in `letters`), an
// inferred number follows "=". Seats keep their identity in oldRow (first unused seat with the same id).
function parseRowText(text, oldRow, letters = MARK_ORDER) {
  const errors = [], blocks = [];
  const pool = new Map();
  if (oldRow) rowSeats(oldRow).forEach(b => b.forEach(s => { if (!pool.has(s.id)) pool.set(s.id, []); pool.get(s.id).push(s.from); }));
  const take = id => pool.get(id)?.shift();
  const allowed = new Set([...letters].map(l => l.toLowerCase()));
  const parts = text.split("|");
  parts.forEach((blk, bi) => {
    const seats = [];
    for (const tok of blk.trim().split(/\s+/).filter(Boolean)) {
      const r = tok.match(/^(\d+)-(\d+)$/);
      if (r) {
        let a = +r[1], b = +r[2];
        if (b < a) [a, b] = [b, a];
        if (b - a > 400) { errors.push(`${tok}: range too long`); continue; }
        for (let n = a; n <= b; n++) seats.push({ id: String(n), mark: "", inf: "", from: take(String(n)) });
        continue;
      }
      const m = tok.match(/^(\d+|[A-Z]+\d+)([a-z]*)(?:=(\d+))?$/);
      if (!m) { errors.push(`“${tok}” is not a seat (e.g. 12, 12r, W1, W1=7)`); continue; }
      const bad = [...m[2]].filter(c => !allowed.has(c));
      if (bad.length) { errors.push(`${tok}: no mark “${bad.join("")}” in this venue`); continue; }
      const mark = normMark(impliedMark(m[1]) + m[2].toUpperCase());
      seats.push({ id: m[1], mark, inf: m[3] || "", from: take(m[1]) });
    }
    if (!seats.length && parts.length > 1) errors.push(`block ${bi + 1} is empty`);
    blocks.push(seats);
  });
  if (!blocks.flat().length) errors.push("the row has no seats");
  return { blocks, errors };
}

function seatToken(s) {
  const extra = [...s.mark].filter(c => c !== impliedMark(s.id)).join("").toLowerCase();
  return s.id + extra + (s.inf ? `=${s.inf}` : "");
}
const plain = s => /^\d+$/.test(s.id) && !s.mark && !s.inf;
// blocks of seats -> "1-5 | W1 W2=7 8r"
function blocksText(blocks) {
  return blocks.map(blk => {
    const out = [];
    for (let i = 0; i < blk.length;) {
      let j = i;
      if (plain(blk[i])) while (j + 1 < blk.length && plain(blk[j + 1]) && +blk[j + 1].id === +blk[j].id + 1) j++;
      out.push(j > i ? `${blk[i].id}-${blk[j].id}` : seatToken(blk[i]));
      i = j + 1;
    }
    return out.join(" ");
  }).join(" | ");
}
const rowText = row => blocksText(rowSeats(row));

// ---------------------------------------------------------------- rebuilding a row

const fromOf = s => s.from ? s.from.split(":").map(Number) : null;
const signed = (a, b) => ((b - a + 540) % 360) - 180;
// a block's runs: its own `runs`, or the block itself as one run
const runsOf = b => b.runs?.length ? b.runs : [{ count: b.seats.length, ...Object.fromEntries(GEOM_KEYS.filter(k => b[k] != null).map(k => [k, b[k]])) }];
const hasGeom = b => !!(b.runs?.length || GEOM_KEYS.some(k => b[k] != null));
function runIndex(b) {
  const out = [];
  runsOf(b).forEach((r, ri) => { for (let k = 0; k < r.count; k++) out.push([ri, k]); });
  return out;
}
const round = (v, d = 2) => Math.round(v * 10 ** d) / 10 ** d;

// blocks of seats -> the JSON row, carrying everything the old row knew about each block.
// Returns {row, map, warnings}: map[old block index] = the new block indexes holding its seats.
function rebuildRow(old, blocks) {
  const warnings = [];
  // an old block maps to the new blocks made mostly of its seats; failing that (merged into another), to
  // the blocks its seats went to. A seat or two crossing a block edge so moves no bank reference.
  const map = old.blocks.map(() => []), holds = old.blocks.map(() => []);
  const out = { row: old.row, blocks: [] };
  blocks.filter(b => b.length).forEach((seats, nb) => {
    const tally = new Map();
    seats.forEach(s => { const f = fromOf(s); if (f) tally.set(f[0], (tally.get(f[0]) || 0) + 1); });
    for (const ob of tally.keys()) holds[ob].push(nb);
    const major = [...tally.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0])[0]?.[0];
    if (major != null) map[major].push(nb);
    const src = major != null ? old.blocks[major] : null;
    const blk = {};
    const order = src ? Object.keys(src) : ["seats"];
    const extra = {};
    if (src) for (const k of Object.keys(src)) if (!["seats", "runs", "blocked", ...GEOM_KEYS, ...BOUND_KEYS].includes(k)) extra[k] = structuredClone(src[k]);
    for (const ob of tally.keys()) {
      const o = old.blocks[ob];
      for (const k of ["side", "area"]) if (o[k] !== src[k]) warnings.push(`new block ${nb + 1}: takes seats from blocks with different ${k}; kept “${src[k] ?? "none"}”`);
    }
    // blocked slots follow the seats in number order: they stay with the old block's last seat
    for (const ob of tally.keys()) {
      const o = old.blocks[ob];
      if (o.blocked && seats.some(s => s.from === `${ob}:${o.seats.length - 1}`)) extra.blocked = structuredClone(o.blocked);
    }
    // geometry: consecutive seats from the same run of the same old block form one run; a run cut short
    // takes the bearings of its first and last remaining seat (interpolated along the old run)
    const geo = {};
    if ([...tally.keys()].some(ob => hasGeom(old.blocks[ob]))) {
      const src2 = seats.map(s => {
        const f = fromOf(s);
        if (!f) return null;
        const ob = old.blocks[f[0]];
        if (!hasGeom(ob)) return null;
        const [ri, k] = runIndex(ob)[f[1]];
        return { ob: f[0], ri, k };
      });
      // a new seat joins the run of the seat before it (or after it, at the start)
      for (let i = 1; i < src2.length; i++) if (!src2[i] && src2[i - 1]) src2[i] = { ...src2[i - 1], added: true };
      for (let i = src2.length - 2; i >= 0; i--) if (!src2[i] && src2[i + 1]) src2[i] = { ...src2[i + 1], added: true };
      const pieces = [];
      src2.forEach(s => {
        const last = pieces.at(-1);
        if (s && last && last.ob === s.ob && last.ri === s.ri) last.items.push(s);
        else pieces.push({ ob: s?.ob, ri: s?.ri, items: [s] });
      });
      let estimated = false;
      const runs = pieces.map(p => {
        if (p.ob == null) return { count: p.items.length };
        const r = runsOf(old.blocks[p.ob])[p.ri];
        const g = { count: p.items.length };
        for (const k of GEOM_KEYS) if (r[k] != null) g[k] = r[k];
        const ks = p.items.filter(s => !s.added).map(s => s.k);
        const whole = !p.items.some(s => s.added) && ks.length === r.count && ks.every((k, i) => k === i);
        if (!whole && r.start != null && r.end != null && r.count > 1) {
          const at = k => round(((r.start + signed(r.start, r.end) * k / (r.count - 1)) % 360 + 360) % 360);
          g.start = at(Math.min(...ks)); g.end = at(Math.max(...ks));
          estimated = true;
        }
        return g;
      });
      if (estimated) warnings.push(`new block ${nb + 1}: geometry recut from the old runs; check it in the Geometry tab`);
      if (runs.length === 1) { const { count, ...g } = runs[0]; Object.assign(geo, g); }
      else geo.runs = runs;
      const bounds = [...tally.keys()].map(ob => old.blocks[ob]);
      for (const [k, f] of [["inner", Math.min], ["outer", Math.max]]) {
        const v = bounds.map(b => b[k]).filter(v => v != null);
        if (v.length) geo[k] = f(...v);
      }
    }
    const fields = { seats: seats.map(s => s.id), ...extra, ...geo };
    for (const k of order) if (k in fields) blk[k] = fields[k];
    for (const k of Object.keys(fields)) if (!(k in blk)) blk[k] = fields[k];
    out.blocks.push(blk);
  });
  map.forEach((m, ob) => { if (!m.length) m.push(...holds[ob]); });
  const all = blocks.flat();
  const marks = Object.fromEntries(all.filter(s => s.mark).map(s => [s.id, s.mark]));
  const inf = Object.fromEntries(all.filter(s => s.inf).map(s => [s.id, s.inf]));
  if (Object.keys(marks).length) out.marks = marks;
  if (Object.keys(inf).length) out.inferred_numbers = inf;
  for (const k of Object.keys(old)) if (!["row", "blocks", "marks", "inferred_numbers"].includes(k)) out[k] = structuredClone(old[k]);
  // an unchanged row is returned exactly as it was (key order, marks order)
  if (sameRow(old, out)) return { row: structuredClone(old), map: old.blocks.map((_, i) => [i]), warnings: [] };
  return { row: out, map, warnings };
}

function canon(v) {
  if (Array.isArray(v)) return v.map(canon);
  if (v && typeof v === "object") return Object.fromEntries(Object.keys(v).sort().map(k => [k, canon(v[k])]));
  return v;
}
const sameRow = (a, b) => JSON.stringify(canon(a)) === JSON.stringify(canon(b));

// ---------------------------------------------------------------- bank and pit references

// [zone index, row index] a reference names: a row label, or {row, zone?, block?} (as findRow in seatmap.js)
function refRow(doc, ref) {
  const label = typeof ref === "string" ? ref : ref.row, zone = typeof ref === "string" ? null : ref.zone;
  for (let zi = 0; zi < doc.zones.length; zi++) {
    if (zone && doc.zones[zi].name !== zone) continue;
    const ri = doc.zones[zi].rows.findIndex(r => r.row === label);
    if (ri >= 0) return [zi, ri];
  }
  return null;
}
function refHolders(doc) {
  const out = [];
  for (const b of doc.layout?.banks || []) out.push({ what: `bank ${b.id}`, refs: b.rows });
  for (const p of doc.orchestra_pits || []) out.push({ what: `pit “${p.name}”`, refs: p.rows_removed });
  return out;
}
// After row (zi, ri) was rebuilt with block map `map`, point every bank and pit reference to one of its
// blocks at the blocks now holding those seats. Returns warnings.
function remapRefs(doc, zi, ri, map, nBlocks) {
  const warnings = [];
  const label = doc.zones[zi].rows[ri].row;
  const covered = Array.from({ length: nBlocks }, () => []);
  let byBlock = false, whole = [];
  for (const h of refHolders(doc)) for (let k = h.refs.length - 1; k >= 0; k--) {
    const ref = h.refs[k];
    const at = refRow(doc, ref);
    if (!at || at[0] !== zi || at[1] !== ri) continue;
    if (typeof ref === "string" || !ref.block) { whole.push(h.what); continue; }
    byBlock = true;
    const next = [...new Set([].concat(ref.block).flatMap(b => map[b - 1] || []))].sort((a, b) => a - b).map(i => i + 1);
    if (!next.length) { warnings.push(`${h.what}: row ${label} block ${[].concat(ref.block).join(", ")} no longer exists; reference removed`); h.refs.splice(k, 1); continue; }
    const was = JSON.stringify(ref.block);
    ref.block = next.length === 1 ? next[0] : next;
    if (JSON.stringify(ref.block) !== was) warnings.push(`${h.what}: row ${label} block ${was} → ${JSON.stringify(ref.block)}`);
    if (h.what.startsWith("bank")) next.forEach(i => covered[i - 1].push(h.what));
  }
  if (byBlock && doc.layout?.banks?.length && !whole.some(w => w.startsWith("bank"))) covered.forEach((c, i) => {
    if (!c.length) warnings.push(`row ${label} block ${i + 1} is in no bank: the map cannot draw it; add it to a bank`);
    if (c.length > 1) warnings.push(`row ${label} block ${i + 1} is in ${c.join(" and ")}`);
  });
  return warnings;
}

// Replace row (zi, ri) of doc with blocks of seats. Returns warnings (the row, then its references).
function applyRow(doc, zi, ri, blocks) {
  const old = doc.zones[zi].rows[ri];
  const { row, map, warnings } = rebuildRow(old, blocks);
  doc.zones[zi].rows[ri] = row;
  const moved = map.some((m, i) => m.length !== 1 || m[0] !== i) || row.blocks.length !== old.blocks.length;
  return moved ? [...warnings, ...remapRefs(doc, zi, ri, map, row.blocks.length)] : warnings;
}

// ---------------------------------------------------------------- checks

// Problems in a row that the build would reject or that look like slips.
function rowIssues(row, doc) {
  const out = [];
  const ids = row.blocks.flatMap(b => b.seats);
  const seen = new Set(), dup = new Set();
  for (const id of ids) { if (seen.has(id)) dup.add(id); seen.add(id); }
  if (dup.size) out.push({ level: "bad", text: `duplicate seat ${[...dup].join(", ")}`, seats: [...dup] });
  const letters = new Set(Object.keys(doc?.marks || {}));
  for (const [id, m] of Object.entries(row.marks || {})) {
    const unknown = [...m].filter(c => !letters.has(c));
    if (unknown.length) out.push({ level: "bad", text: `${id}: mark ${unknown.join("")} is not in this venue's legend`, seats: [id] });
  }
  for (const id of ids) {
    const p = impliedMark(id);
    if (p && !(row.marks?.[id] || "").includes(p)) out.push({ level: "bad", text: `${id} is labelled as a ${p} box but has no ${p} mark`, seats: [id] });
  }
  const printed = new Set(ids.filter(id => /^\d+$/.test(id)));
  for (const [id, n] of Object.entries(row.inferred_numbers || {})) {
    if (/^\d+$/.test(id)) out.push({ level: "warn", text: `${id} is printed; it needs no inferred number`, seats: [id] });
    if (printed.has(n)) out.push({ level: "bad", text: `${id}=${n}: ${n} is a printed seat in this row`, seats: [id] });
  }
  return out;
}

// Seat counts for the whole document, by the project's rule (printed total = boxes − management).
function totals(doc) {
  const t = { boxes: 0, X: 0, W: 0, R: 0, L: 0, zones: {} };
  for (const z of doc.zones) {
    const zt = t.zones[z.name] = { boxes: 0, X: 0 };
    for (const r of z.rows) for (const id of r.blocks.flatMap(b => b.seats)) {
      t.boxes++; zt.boxes++;
      const m = r.marks?.[id] || "";
      for (const c of m) if (c in t) t[c]++;
      if (m.includes("X")) zt.X++;
    }
  }
  return t;
}

// The figures venues/common.py finish() checks: each part of house (or group named by counted_in) against its
// printed total, with count_includes X and count_excludes (a mark, or "*" for the whole zone) applied.
function countCheck(doc) {
  const printed = doc.printed_totals || {};
  const figures = [], groups = new Map();
  for (const z of doc.zones) {
    const ids = z.rows.flatMap(r => r.blocks.flatMap(b => b.seats).map(id => r.marks?.[id] || ""));
    const boxes = ids.length, x = ids.filter(m => m.includes("X")).length;
    if (z.counted_in) {
      const g = groups.get(z.counted_in) || { name: z.counted_in, counted: 0 };
      g.counted += boxes - x; groups.set(z.counted_in, g);
      continue;
    }
    const without = z.count_excludes || [];
    const left = without.includes("*") ? boxes : without.reduce((a, m) => a + ids.filter(s => s.includes(m)).length, 0);
    const counted = ((z.count_includes || []).includes("X") ? boxes : boxes - x) - left;
    figures.push({ name: z.name, counted, printed: printed[z.name] });
  }
  for (const g of groups.values()) figures.push({ ...g, printed: printed[g.name] });
  const counted = figures.reduce((a, f) => a + f.counted, 0);
  return { counted, printed: printed.Total, figures };
}

// ---------------------------------------------------------------- venue file code (venues/<id>.py)

function pyList(ids) {
  const parts = [];
  for (let i = 0; i < ids.length;) {
    let j = i;
    if (/^\d+$/.test(ids[i])) while (j + 1 < ids.length && /^\d+$/.test(ids[j + 1]) && +ids[j + 1] === +ids[j] + 1) j++;
    if (j - i >= 2) { parts.push(`rng(${ids[i]}, ${ids[j]})`); i = j + 1; continue; }
    const lone = [];
    for (; i <= j; i++) lone.push(ids[i]);
    if (parts.length && parts.at(-1).startsWith("[")) parts[parts.length - 1] = parts.at(-1).slice(0, -1) + ", " + lone.map(q).join(", ") + "]";
    else parts.push(`[${lone.map(q).join(", ")}]`);
  }
  return parts.join(" + ") || "[]";
}
const q = s => JSON.stringify(String(s));
const pyValue = v => JSON.stringify(v).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False").replace(/\bnull\b/g, "None");
const pyDict = o => "{" + Object.entries(o).map(([k, v]) => `${q(k)}: ${pyValue(v)}`).join(", ") + "}";
// row(...) for venues/<id>.py. Geometry (view, offset, runs...) is left out: tools/derive_runs.py writes it.
function rowCode(row) {
  const blocks = row.blocks.map(b => {
    const extra = Object.fromEntries(Object.entries(b).filter(([k]) => !["seats", "runs", ...GEOM_KEYS, ...BOUND_KEYS].includes(k)));
    const list = pyList(b.seats);
    return Object.keys(extra).length ? `{"seats": ${list}, ${Object.entries(extra).map(([k, v]) => `${q(k)}: ${pyValue(v)}`).join(", ")}}` : list;
  });
  const kw = [];
  if (row.marks) kw.push(`marks=${pyDict(row.marks)}`);
  if (row.inferred_numbers) kw.push(`inferred=${pyDict(row.inferred_numbers)}`);
  if (row.note) kw.push(`note=${q(row.note)}`);
  return `row(${[q(row.row), ...blocks, ...kw].join(", ")}),`;
}

// ---------------------------------------------------------------- changes against the loaded file

// A readable list of what differs between two documents: [{where, was, now}].
function diffDocs(a, b) {
  const out = [];
  const label = (path, docB) => {
    const p = [...path];
    const words = [];
    if (p[0] === "zones" && typeof p[1] === "number") {
      const z = docB.zones[p[1]] || a.zones[p[1]];
      words.push(z?.name ?? `zone ${p[1] + 1}`);
      p.splice(0, 2);
      if (p[0] === "rows" && typeof p[1] === "number") {
        const r = z?.rows?.[p[1]] ?? a.zones[path[1]]?.rows?.[p[1]];
        words.push(`row ${r?.row ?? p[1] + 1}`); p.splice(0, 2);
        if (p[0] === "blocks" && typeof p[1] === "number") { words.push(`block ${p[1] + 1}`); p.splice(0, 2); }
        if (p[0] === "runs" && typeof p[1] === "number") { words.push(`run ${p[1] + 1}`); p.splice(0, 2); }
      }
    } else if (p[0] === "layout" && p[1] === "banks" && typeof p[2] === "number") {
      words.push(`bank ${(docB.layout.banks[p[2]] || a.layout.banks[p[2]])?.id}`); p.splice(0, 3);
    }
    return [...words, ...p.map(x => typeof x === "number" ? `#${x + 1}` : x)].join(" · ");
  };
  const show = v => v === undefined ? "—" : typeof v === "object" ? JSON.stringify(v) : String(v);
  const walk = (x, y, path) => {
    if (JSON.stringify(x) === JSON.stringify(y)) return;
    const leafish = v => v === null || typeof v !== "object" || (Array.isArray(v) && v.every(e => typeof e !== "object"));
    if (path.at(-1) === "seats" || leafish(x) || leafish(y) || Array.isArray(x) !== Array.isArray(y)) {
      out.push({ where: label(path, b), was: show(x), now: show(y), path });
      return;
    }
    const keys = Array.isArray(x) ? [...Array(Math.max(x.length, y.length)).keys()] : [...new Set([...Object.keys(x), ...Object.keys(y)])];
    for (const k of keys) walk(x?.[k], y?.[k], [...path, k]);
  };
  walk(a, b, []);
  return out;
}

// ---------------------------------------------------------------- writing data/<id>.json

// Numbers venues/common.py writes as floats (geometry from tools/derive_runs.py): kept as "90.0", not "90".
const FLOAT_KEYS = new Set(["view", "offset", "radius", "start", "end", "inner", "outer", "from", "to"]);
function floatAt(path) {
  const k = path.at(-1), up = path.filter(p => typeof p === "string");
  if (up.at(-2) === "layout" && up.at(-1) === "aisles") return true;
  if (typeof k !== "string" || !FLOAT_KEYS.has(k)) return false;
  return up.includes("blocks") || up.includes("vomitoria") || up.includes("arcs");
}
// JavaScript puts integer-like keys first and in number order ("2", "4", "52"), so a row's marks lose the
// order the file gave them. parseFile records, by path, the key order of every object that has such keys.
function parseFile(text) {
  const order = new Map();
  let i = 0;
  const ws = () => { while (/\s/.test(text[i])) i++; };
  const str = () => { const s = i; i++; while (text[i] !== '"') i += text[i] === "\\" ? 2 : 1; i++; return JSON.parse(text.slice(s, i)); };
  const val = path => {
    ws();
    const c = text[i];
    if (c === "{") {
      i++; const o = {}, keys = [];
      ws(); if (text[i] === "}") { i++; return o; }
      for (;;) {
        ws(); const k = str(); ws(); i++;              // the ":"
        o[k] = val(`${path}/${k}`); keys.push(k);
        ws(); if (text[i++] === "}") break;
      }
      if (keys.some(k => /^\d+$/.test(k))) order.set(path, keys);
      return o;
    }
    if (c === "[") {
      i++; const a = [];
      ws(); if (text[i] === "]") { i++; return a; }
      for (;;) { a.push(val(`${path}/${a.length}`)); ws(); if (text[i++] === "]") break; }
      return a;
    }
    if (c === '"') return str();
    const m = text.slice(i).match(/^(?:true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/);
    i += m[0].length;
    return JSON.parse(m[0]);
  };
  const doc = val("");
  return { doc, order };
}

// The document as venues/common.py writes it: json.dump(doc, ensure_ascii=False, indent=1). order (from
// parseFile) keeps the file's key order where the keys are unchanged; a row's new marks and inferred numbers
// otherwise follow its seats.
function fileJSON(doc, order = new Map()) {
  const keysOf = (v, path) => {
    const ks = Object.keys(v).filter(k => v[k] !== undefined);
    const was = order.get("/" + path.join("/"));
    if (was && was.length === ks.length && was.every(k => k in v)) return was;
    const last = path.at(-1);
    if ((last === "marks" || last === "inferred_numbers") && path.at(-4) === "rows") {
      const row = path.slice(0, -1).reduce((o, p) => o[p], doc);
      const seats = row.blocks.flatMap(b => b.seats);
      return [...ks].sort((a, b) => seats.indexOf(a) - seats.indexOf(b));
    }
    return ks;
  };
  const out = (v, path, ind) => {
    if (v === null || typeof v === "boolean" || typeof v === "string") return JSON.stringify(v);
    if (typeof v === "number") return Number.isInteger(v) && floatAt(path) ? `${v}.0` : String(v);
    const pad = " ".repeat(ind + 1), end = " ".repeat(ind);
    if (Array.isArray(v)) return v.length ? `[\n${v.map((x, i) => pad + out(x, [...path, i], ind + 1)).join(",\n")}\n${end}]` : "[]";
    const ks = keysOf(v, path);
    return ks.length ? `{\n${ks.map(k => `${pad}${JSON.stringify(k)}: ${out(v[k], [...path, k], ind + 1)}`).join(",\n")}\n${end}}` : "{}";
  };
  return out(doc, [], 0);
}

// ---------------------------------------------------------------- customisations

// A customisation is a list of changes on top of a published seat list (docs/adr/0001):
//   {op: "add", zone, row, at, side: "before"|"after", id, marks}   a new seat beside seat `at`
//   {op: "remove", zone, row, id}
//   {op: "marks", zone, row, id, marks}
//   {op: "rename", zone, row, id, to}
// Published seats are named by their published id, whatever they are renamed to; added seats by their own
// id. "before"/"after" is order in the row's seat list (from seat 1's side), not left/right on the map.
// The list holds at most one net change per seat (recordChange keeps it so).

// a seat id a user may give: a number, a W or X box, or a number with one capital letter (14A)
const SEAT_ID = /^(\d+|[WX]\d+|\d+[A-Z])$/;
const NOT_ID = id => `“${id}” is not a seat id (e.g. 12, 12A, W1)`;
const NEEDS_MARK = (id, p) => `${id} is a ${p} box: it needs its ${p} mark`;
const noMark = (marks, letters) => { const u = [...marks].filter(m => !letters.has(m)); return u.length ? `this venue has no mark ${u.join("")}` : ""; };

// The customised version with each seat's origin: rows.get("zone\u0000row") = {zi, ri, blocks} with seats
// {id, mark, inf, from, pub (published id) | addBy (its add), gone, marksBy, renameBy}; anchors maps each
// applied add to the seat it was placed beside.
function build(doc, changes) {
  const out = structuredClone(doc);
  const letters = new Set(Object.keys(out.marks || {}));
  const bad = new Map(), anchors = new Map(), rows = new Map();
  const refuse = (c, reason) => { if (!bad.has(c)) bad.set(c, reason); };
  const byRow = new Map();
  for (const c of changes) {
    const key = `${c.zone}\u0000${c.row}`;
    if (!byRow.has(key)) byRow.set(key, []);
    byRow.get(key).push(c);
  }
  for (const [key, list] of byRow) {
    const [zone, label] = key.split("\u0000");
    const zi = out.zones.findIndex(z => z.name === zone);
    const ri = zi < 0 ? -1 : out.zones[zi].rows.findIndex(r => r.row === label);
    if (ri < 0) { list.forEach(c => refuse(c, `row ${label} is not in ${zone}`)); continue; }
    const blocks = rowSeats(out.zones[zi].rows[ri]).map(b => b.map(s => ({ ...s, pub: s.id })));
    rows.set(key, { zi, ri, blocks });
    const pubSeat = id => blocks.flat().find(s => s.pub === id && !s.gone);
    const missing = id => `seat ${id} is not in row ${label}`;
    const finalId = s => s.renameBy ? s.renameBy.to : s.id;
    const of = op => list.filter(c => c.op === op);
    for (const c of list) if (!(c.op in { add: 1, remove: 1, marks: 1, rename: 1 })) refuse(c, `unknown change “${c.op}”`);

    // removes leave the seat in place, gone, until the end: a seat may still be added beside it
    for (const c of of("remove")) {
      const s = pubSeat(c.id);
      if (!s) refuse(c, missing(c.id)); else { s.gone = true; s.removeBy = c; }
    }
    for (const c of of("marks")) {
      const s = pubSeat(c.id), why = s ? noMark(c.marks || "", letters) : missing(c.id);
      if (why) refuse(c, why); else { s.pubMark ??= s.mark; s.mark = normMark(c.marks || ""); s.marksBy = c; }
    }
    for (const c of of("rename")) {
      const s = pubSeat(c.id);
      if (!s) refuse(c, missing(c.id));
      else if (!SEAT_ID.test(c.to)) refuse(c, NOT_ID(c.to));
      else s.renameBy = c;
    }
    // renames are made together (7 → 8 with 8 → 7 is fine); where two seats end with one id, the later
    // rename is undone
    for (let again = true; again;) {
      again = false;
      const live = blocks.flat().filter(s => !s.gone), seen = new Map();
      for (const s of live) {
        const id = finalId(s);
        if (!seen.has(id)) { seen.set(id, s); continue; }
        const pair = [seen.get(id), s].filter(x => x.renameBy).sort((a, b) => changes.indexOf(b.renameBy) - changes.indexOf(a.renameBy));
        if (!pair.length) continue;
        refuse(pair[0].renameBy, `row ${label} already has a seat ${id}`);
        delete pair[0].renameBy;
        again = true;
        break;
      }
    }
    for (const s of blocks.flat()) {
      const p = s.renameBy && impliedMark(s.renameBy.to);
      if (p && !s.mark.includes(p)) { refuse(s.renameBy, NEEDS_MARK(s.renameBy.to, p)); delete s.renameBy; }
      const q = s.marksBy && impliedMark(finalId(s));
      if (q && !s.mark.includes(q)) { refuse(s.marksBy, NEEDS_MARK(finalId(s), q)); s.mark = s.pubMark; delete s.marksBy; }
    }
    // adds, each placed once the seat it sits beside is in the row (published seats by published id)
    let pending = of("add").filter(c => !bad.has(c));
    for (let moved = true; moved && pending.length;) {
      moved = false;
      for (const c of [...pending]) {
        const all = blocks.flat();
        const at = all.find(s => s.pub === c.at) || all.find(s => s.addBy && s.id === c.at);
        if (!at) continue;
        pending = pending.filter(x => x !== c);
        moved = true;
        const marks = normMark(c.marks || ""), p = impliedMark(c.id);
        const why = !SEAT_ID.test(c.id) ? NOT_ID(c.id)
          : all.some(s => !s.gone && finalId(s) === c.id) ? `row ${label} already has a seat ${c.id}`
          : noMark(marks, letters) || (p && !marks.includes(p) ? NEEDS_MARK(c.id, p) : "");
        if (why) { refuse(c, why); continue; }
        const b = blocks.find(x => x.includes(at));
        b.splice(b.indexOf(at) + (c.side === "before" ? 0 : 1), 0, { id: c.id, mark: marks, inf: "", addBy: c });
        anchors.set(c, at);
      }
    }
    pending.forEach(c => refuse(c, missing(c.at)));
    // no block is ever emptied, so bank and pit references never move: the later removes are undone
    for (const b of blocks) {
      const removes = b.filter(s => s.gone).sort((x, y) => changes.indexOf(y.removeBy) - changes.indexOf(x.removeBy));
      while (b.length && b.every(s => s.gone)) {
        const s = removes.shift();
        refuse(s.removeBy, `a block needs at least one seat; mark seat ${s.id} X instead?`);
        s.gone = false; delete s.removeBy;
      }
    }
  }
  for (const { zi, ri, blocks } of rows.values()) {
    const seats = blocks.map(b => b.filter(s => !s.gone).map(s => {
      const id = s.renameBy ? s.renameBy.to : s.id;
      return { id, mark: s.mark, inf: s.renameBy && !impliedMark(id) ? "" : s.inf, from: s.from };
    }));
    out.zones[zi].rows[ri] = rebuildRow(out.zones[zi].rows[ri], seats).row;
  }
  const notFitting = changes.filter(c => bad.has(c)).map(change => ({ change, reason: bad.get(change) }));
  return { doc: out, applied: changes.filter(c => !bad.has(c)), notFitting, rows, anchors };
}

// The customised version of doc: a copy, with {doc, applied, notFitting: [{change, reason}]}. Changes that
// no longer fit (after a correction to the published list) are listed with the reason, never half made.
function applyCustom(doc, changes) {
  const { rows, anchors, ...out } = build(doc, changes);
  return out;
}

// Add change c, made by the user on the customised version (seats named by their id there), to the list.
// Returns {changes} (a new list, with at most one net change per seat) or {error} when it cannot be made.
function recordChange(doc, changes, c) {
  const zone = doc.zones.find(z => z.name === c.zone), published = zone?.rows.find(x => x.row === c.row);
  if (!published) return { error: `row ${c.row} is not in ${c.zone}` };
  const now = build(doc, changes);
  const r = now.rows.get(`${c.zone}\u0000${c.row}`);
  const seats = r ? r.blocks.flat() : rowSeats(published).flat().map(s => ({ ...s, pub: s.id }));
  const idOf = s => s.renameBy ? s.renameBy.to : s.id;
  const target = c.op === "add" ? c.at : c.id;
  const s = seats.find(x => !x.gone && idOf(x) === target);
  if (!s) return { error: `seat ${target} is not in row ${c.row}` };
  const same = x => x.zone === c.zone && x.row === c.row;
  let list = [...changes];
  const put = (old, next) => { list = old ? list.map(x => x === old ? next : x).filter(Boolean) : next ? [...list, next] : list; };
  const where = { zone: c.zone, row: c.row };
  if (c.op === "add") {
    put(null, { op: "add", ...where, at: s.addBy ? s.addBy.id : s.pub, side: c.side, id: c.id, marks: normMark(c.marks || "") });
  } else if (s.addBy) {
    const a = s.addBy;
    if (c.op === "marks") put(a, { ...a, marks: normMark(c.marks || "") });
    else if (c.op === "rename") {
      list = list.map(x => x.op === "add" && same(x) && x.at === a.id ? { ...x, at: c.to } : x);
      put(a, { ...a, id: c.to });
    } else if (c.op === "remove") {
      // seats added beside it take its place beside its own neighbour
      list = list.map(x => x.op === "add" && same(x) && x.at === a.id ? { ...x, at: a.at, side: a.side } : x);
      put(a, null);
    } else return { error: `unknown change “${c.op}”` };
  } else {
    const pub = s.pub, mine = op => list.find(x => x.op === op && same(x) && x.id === pub);
    if (c.op === "marks") {
      const m = normMark(c.marks || ""), was = published.marks?.[pub] || "";
      put(mine("marks"), m === was ? null : { op: "marks", ...where, id: pub, marks: m });
    } else if (c.op === "rename") put(mine("rename"), c.to === pub ? null : { op: "rename", ...where, id: pub, to: c.to });
    else if (c.op === "remove") { put(mine("marks"), null); put(mine("rename"), null); put(null, { op: "remove", ...where, id: pub }); }
    else return { error: `unknown change “${c.op}”` };
  }
  const next = build(doc, list);
  const fresh = next.notFitting.find(n => !now.notFitting.some(o => JSON.stringify(o.change) === JSON.stringify(n.change)));
  if (fresh) return { error: fresh.reason };
  return { changes: list };
}

// Remove entry i from the list ("Your changes"). Seats added beside an added seat move beside its neighbour.
function dropChange(changes, i) {
  const c = changes[i];
  if (!c) return [...changes];
  return changes.filter((_, k) => k !== i).map(x => c.op === "add" && x.op === "add" && x.zone === c.zone && x.row === c.row && x.at === c.id ? { ...x, at: c.at, side: c.side } : x);
}

// ---------------------------------------------------------------- customisations in the URL (#c=…&u=…)

// base64url of UTF-8 JSON, as #c= (encodeConfig in seatmap.js), with each change as a short tuple:
// ["+", zone, row, at, "<"|">", id, marks], ["-", zone, row, id], ["m", zone, row, id, marks], ["r", zone, row, id, to]
const b64url = s => {
  const bytes = new TextEncoder().encode(s);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
const unb64url = s => new TextDecoder("utf-8", { fatal: true }).decode(Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), c => c.charCodeAt(0)));
function encodeChanges(changes) {
  return b64url(JSON.stringify(changes.map(c =>
    c.op === "add" ? ["+", c.zone, c.row, c.at, c.side === "before" ? "<" : ">", c.id, c.marks || ""]
    : c.op === "remove" ? ["-", c.zone, c.row, c.id]
    : c.op === "marks" ? ["m", c.zone, c.row, c.id, c.marks || ""]
    : ["r", c.zone, c.row, c.id, c.to])));
}
const TUPLE = { "+": 7, "-": 4, m: 5, r: 5 };
function decodeChanges(u) {
  let list;
  try { list = JSON.parse(unb64url(u)); } catch { list = null; }
  const ok = Array.isArray(list) && list.every(t => Array.isArray(t) && TUPLE[t[0]] === t.length && t.slice(1).every(v => typeof v === "string")
    && (t[0] !== "+" || t[4] === "<" || t[4] === ">"));
  if (!ok) throw new Error("this link does not hold a customisation it can read (not a customisation)");
  return list.map(t => {
    const [k, zone, row] = t, where = { zone, row };
    if (k === "+") return { op: "add", ...where, at: t[3], side: t[4] === "<" ? "before" : "after", id: t[5], marks: t[6] };
    if (k === "-") return { op: "remove", ...where, id: t[3] };
    if (k === "m") return { op: "marks", ...where, id: t[3], marks: t[4] };
    return { op: "rename", ...where, id: t[3], to: t[4] };
  });
}

// ---------------------------------------------------------------- customisation files

const CUSTOM_SCHEMA = "hkperf-venue-seats/custom@0.1";
// plan files that may hold a customisation (in `customisation`), and those that never do
const PLAN_WITH_CUSTOM = ["hkperf-venue-seats/plan@0.3"];
const PLAN_WITHOUT = ["hkperf-venue-seats/plan@0.1", "hkperf-venue-seats/plan@0.2"];

// hex SHA-256 of a seat list file's text, as fetched (the base of a customisation)
async function seatListSha256(text) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function customFile(base, changes, note = "") {
  return JSON.stringify({ schema: CUSTOM_SCHEMA, saved: new Date().toISOString(), base, changes, note }, null, 1) + "\n";
}

const isChange = c => c && typeof c === "object" && typeof c.zone === "string" && typeof c.row === "string" && (
  c.op === "add" ? [c.at, c.id, c.marks].every(v => typeof v === "string") && (c.side === "before" || c.side === "after")
  : c.op === "remove" ? typeof c.id === "string"
  : c.op === "marks" ? typeof c.id === "string" && typeof c.marks === "string"
  : c.op === "rename" && typeof c.id === "string" && typeof c.to === "string");
// The customisation in a custom@0.1 or plan@0.3 file: {base, changes, note}; null for a plan without one.
// Throws on anything else.
function readCustom(text) {
  const no = why => new Error(`this file is not a customisation it can read (${why})`);
  let f;
  try { f = JSON.parse(text); } catch { throw no("not JSON"); }
  if (PLAN_WITHOUT.includes(f?.schema)) return null;
  const c = f?.schema === CUSTOM_SCHEMA ? f : PLAN_WITH_CUSTOM.includes(f?.schema) ? f.customisation : undefined;
  if (c === undefined && !PLAN_WITH_CUSTOM.includes(f?.schema)) throw no(f?.schema ? `schema ${f.schema}` : "no schema");
  if (c == null) return null;
  const b = c.base;
  if (!b || typeof b.venue !== "string" || typeof b.seat_list_sha256 !== "string" || typeof b.configuration !== "object") throw no("no base");
  if (!Array.isArray(c.changes) || !c.changes.every(isChange)) throw no("a change it does not know");
  return { base: b, changes: c.changes, note: typeof c.note === "string" ? c.note : "" };
}

const api = { MARK_ORDER, applyCustom, recordChange, dropChange, encodeChanges, decodeChanges, seatListSha256, customFile, readCustom,
  CUSTOM_SCHEMA, fileJSON, parseFile, countCheck, normMark, impliedMark, rowSeats, parseRowText, blocksText, rowText, seatToken,
  rebuildRow, applyRow, remapRefs, refRow, rowIssues, totals, rowCode, pyList, diffDocs, sameRow, runsOf, hasGeom };
if (typeof module !== "undefined") module.exports = api;
else root.SeatEdit = api;
})(this);
