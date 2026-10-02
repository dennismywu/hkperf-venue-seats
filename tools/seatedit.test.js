// Checks app/seatedit.js against every seat list in data/. Run: node --test tools/
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const E = require("../app/seatedit.js");

const DATA = path.join(__dirname, "..", "data");
const load = id => JSON.parse(fs.readFileSync(path.join(DATA, `${id}.json`), "utf8"));
const ids = fs.readdirSync(DATA).filter(f => f.endsWith(".json") && f !== "index.json").map(f => f.slice(0, -5));
const rowOf = (doc, label, zone = 0) => doc.zones[zone].rows.findIndex(r => r.row === label);

test("every row survives text and back unchanged", () => {
  for (const id of ids) {
    const doc = load(id), before = JSON.stringify(doc);
    doc.zones.forEach((z, zi) => z.rows.forEach((r, ri) => {
      const { blocks, errors } = E.parseRowText(E.rowText(r), r, Object.keys(doc.marks || {}).join(""));
      assert.deepStrictEqual(errors, [], `${id} ${z.name} ${r.row}`);
      const warnings = E.applyRow(doc, zi, ri, blocks);
      assert.deepStrictEqual(warnings, [], `${id} ${z.name} ${r.row}`);
    }));
    assert.strictEqual(JSON.stringify(doc), before, id);
  }
});

test("every file is written back byte for byte", () => {
  for (const id of ids) {
    const text = fs.readFileSync(path.join(DATA, `${id}.json`), "utf8");
    const { doc, order } = E.parseFile(text);
    assert.deepStrictEqual(doc, JSON.parse(text), id);
    assert.strictEqual(E.fileJSON(doc, order), text, id);
    // and after every row has been through the editor
    doc.zones.forEach((z, zi) => z.rows.forEach((r, ri) =>
      E.applyRow(doc, zi, ri, E.parseRowText(E.rowText(r), r, Object.keys(doc.marks || {}).join("")).blocks)));
    assert.strictEqual(E.fileJSON(doc, order), text, `${id} after editing`);
  }
});

test("every venue's counted figures match its printed totals", () => {
  for (const id of ids) {
    const doc = JSON.parse(fs.readFileSync(path.join(DATA, `${id}.json`), "utf8"));
    const cc = E.countCheck(doc);
    assert.strictEqual(cc.counted, cc.printed, id);
    for (const f of cc.figures) assert.strictEqual(f.counted, f.printed, `${id} ${f.name}`);
  }
});

test("a new mark is written in seat order", () => {
  const { doc, order } = E.parseFile(fs.readFileSync(path.join(DATA, "ncwcc-th.json"), "utf8"));
  const ri = rowOf(doc, "B"), r = doc.zones[0].rows[ri];
  E.applyRow(doc, 0, ri, E.parseRowText("1 2r 3-19 20w", r, "WXR").blocks);
  const text = E.fileJSON(doc, order);
  assert.match(text, /"marks": \{\n\s+"2": "R",\n\s+"20": "W"\n/);
});

test("unnumbered W boxes keep their mark and inferred number", () => {
  const doc = load("ncwcc-th"), ri = rowOf(doc, "A"), r = doc.zones[0].rows[ri];
  assert.strictEqual(E.rowText(r), "W1=1 W2=2 3-14 W3=15 W4=16");
  const { blocks } = E.parseRowText("W1=1 W2=2 3-14 W3=15 W4=16 W5", r, "WX");
  E.applyRow(doc, 0, ri, blocks);
  const out = doc.zones[0].rows[ri];
  assert.strictEqual(out.marks.W5, "W");
  assert.strictEqual(out.inferred_numbers.W3, "15");
  assert.strictEqual(out.note, r.note);
});

test("R and L marks parse in any combination", () => {
  const { blocks, errors } = E.parseRowText("1 2r 3l 4rl 5lr", null, "WXRL");
  assert.deepStrictEqual(errors, []);
  assert.deepStrictEqual(blocks[0].map(s => s.mark), ["", "R", "L", "RL", "RL"]);
  assert.match(E.parseRowText("1 2r", null, "WX").errors[0], /no mark/);
});

test("splitting a run keeps its geometry on both halves", () => {
  const doc = load("ekcc-th"), ri = rowOf(doc, "H"), r = doc.zones[0].rows[ri];
  const b0 = r.blocks[0];
  const { blocks } = E.parseRowText(E.rowText(r).replace(/^(\S+)/, m => m.replace(/-(\d+)$/, (_, n) => `-${+n - 4} | ${+n - 3}-${n}`)), r, "WX");
  const warnings = E.applyRow(doc, 0, ri, blocks);
  const [a, b] = doc.zones[0].rows[ri].blocks;
  for (const blk of [a, b]) for (const k of ["shape", "view", "offset", "start", "end", "inner", "outer"]) assert.ok(blk[k] != null, k);
  assert.strictEqual(a.start, b0.start);
  assert.strictEqual(b.end, b0.end);
  assert.ok(warnings.some(w => /recut/.test(w)));
});

test("merging two blocks of an arc row keeps both runs", () => {
  const doc = load("ekcc-th"), ri = rowOf(doc, "A"), r = doc.zones[0].rows[ri];
  const text = E.rowText(r).replace(" | ", " ");          // merge blocks 1 and 2
  E.applyRow(doc, 0, ri, E.parseRowText(text, r, "WX").blocks);
  const m = doc.zones[0].rows[ri].blocks[0];
  assert.strictEqual(m.runs.length, 2);
  assert.deepStrictEqual(m.runs.map(x => x.count), [5, 3]);
});

test("block edits renumber bank references", () => {
  const doc = load("hkcc-gt");
  const zi = doc.zones.findIndex(z => z.name === "Stalls 1"), ri = rowOf(doc, "D", zi), r = doc.zones[zi].rows[ri];
  assert.ok(r.blocks.length >= 3);
  const text = E.rowText(r);
  const parts = text.split(" | ");
  const merged = [parts[0] + " " + parts[1], ...parts.slice(2)].join(" | ");   // blocks 1+2 merged, 3 → 2
  const warnings = E.applyRow(doc, zi, ri, E.parseRowText(merged, r, "WXRL").blocks);
  const refs = doc.layout.banks.flatMap(b => b.rows.map(x => ({ bank: b.id, x }))).filter(({ x }) => typeof x === "object" && x.zone === "Stalls 1" && x.row === "D");
  assert.ok(refs.every(({ x }) => [].concat(x.block).every(n => n >= 1 && n <= parts.length - 1)));
  assert.ok(warnings.some(w => /→/.test(w)));
});

test("a seat moved across a block edge leaves bank references alone", () => {
  const doc = load("ekcc-hall");
  const zi = doc.zones.findIndex(z => z.name === "Balcony"), ri = rowOf(doc, "BA", zi), r = doc.zones[zi].rows[ri];
  const before = JSON.stringify(doc.layout.banks);
  const blocks = E.rowSeats(r);
  blocks[1].unshift(blocks[0].pop());
  const warnings = E.applyRow(doc, zi, ri, blocks);
  assert.strictEqual(JSON.stringify(doc.layout.banks), before);
  assert.deepStrictEqual(warnings, []);
});

test("checks catch duplicates and a W box without its mark", () => {
  const issues = E.rowIssues({ row: "A", blocks: [{ seats: ["1", "1", "W1"] }] }, { marks: { W: "" } });
  assert.ok(issues.some(i => /duplicate/.test(i.text)));
  assert.ok(issues.some(i => /W box/.test(i.text)));
});

test("row code for the venue file", () => {
  const doc = load("ncwcc-th");
  assert.strictEqual(E.rowCode(doc.zones[0].rows[rowOf(doc, "B")]), 'row("B", rng(1, 20)),');
  assert.match(E.rowCode(doc.zones[0].rows[rowOf(doc, "A")]), /^row\("A", \["W1", "W2"\] \+ rng\(3, 14\) \+ \["W3", "W4"\], marks=\{"W1": "W", .*inferred=\{"W1": "1".*note=/);
});
