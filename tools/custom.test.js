// Customisations (app/seatedit.js): id-anchored changes on top of a published seat list.
// Run: node --test tools/
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const E = require("../app/seatedit.js");

const DATA = path.join(__dirname, "..", "data");
const load = id => JSON.parse(fs.readFileSync(path.join(DATA, `${id}.json`), "utf8"));
const ids = fs.readdirSync(DATA).filter(f => f.endsWith(".json") && f !== "index.json").map(f => f.slice(0, -5));

test("no changes give the published seat list, as a copy", () => {
  for (const id of ids) {
    const doc = load(id), before = JSON.stringify(doc);
    const out = E.applyCustom(doc, []);
    assert.strictEqual(JSON.stringify(out.doc), before, id);
    assert.notStrictEqual(out.doc, doc, id);
    assert.deepStrictEqual(out.notFitting, [], id);
  }
});

const row = (doc, zone, label) => doc.zones.find(z => z.name === zone).rows.find(r => r.row === label);

test("a wheelchair space is added beside the existing ones", () => {
  const doc = load("ncwcc-th");
  const out = E.applyCustom(doc, [{ op: "add", zone: "Theatre", row: "A", at: "W4", side: "after", id: "W5", marks: "W" }]);
  assert.strictEqual(E.rowText(row(out.doc, "Theatre", "A")), "W1=1 W2=2 3-14 W3=15 W4=16 W5");
  assert.strictEqual(row(out.doc, "Theatre", "A").marks.W5, "W");
  assert.strictEqual(out.applied.length, 1);
  assert.strictEqual(E.rowText(row(doc, "Theatre", "A")), "W1=1 W2=2 3-14 W3=15 W4=16", "published doc untouched");
});

test("a seat is removed", () => {
  const out = E.applyCustom(load("ncwcc-th"), [{ op: "remove", zone: "Theatre", row: "B", id: "7" }]);
  assert.strictEqual(E.rowText(row(out.doc, "Theatre", "B")), "1-6 8-20");
});

test("a seat's marks are set, and cleared", () => {
  const doc = load("ncwcc-th");
  const out = E.applyCustom(doc, [
    { op: "marks", zone: "Theatre", row: "B", id: "7", marks: "W" },
    { op: "marks", zone: "Theatre", row: "A", id: "3", marks: "X" },
  ]);
  assert.strictEqual(row(out.doc, "Theatre", "B").marks["7"], "W");
  assert.strictEqual(row(out.doc, "Theatre", "A").marks["3"], "X");
  // a W box with its W cleared is no longer a W box: it is refused, not written broken
  const bad = E.applyCustom(doc, [{ op: "marks", zone: "Theatre", row: "A", id: "W1", marks: "" }]);
  assert.strictEqual(bad.notFitting.length, 1);
});

test("changes that no longer fit a corrected seat list are listed, the rest applied", () => {
  const doc = load("ncwcc-th");
  const changes = [
    { op: "add", zone: "Theatre", row: "A", at: "W4", side: "after", id: "W5", marks: "W" },
    { op: "remove", zone: "Theatre", row: "B", id: "7" },
    { op: "marks", zone: "Theatre", row: "C", id: "3", marks: "W" },
  ];
  // the published list is corrected: row A gains a W5 of its own, row B loses seat 7
  const fixed = structuredClone(doc);
  E.applyRow(fixed, 0, 0, E.parseRowText("W1=1 W2=2 3-14 W3=15 W4=16 W5", fixed.zones[0].rows[0], "WX").blocks);
  E.applyRow(fixed, 0, 1, E.parseRowText("1-6 8-20", fixed.zones[0].rows[1], "WX").blocks);
  const out = E.applyCustom(fixed, changes);
  assert.deepStrictEqual(out.applied, [changes[2]]);
  assert.deepStrictEqual(out.notFitting.map(n => n.change), [changes[0], changes[1]]);
  assert.match(out.notFitting[0].reason, /already has a seat W5/);
  assert.match(out.notFitting[1].reason, /seat 7 is not in row B/);
  assert.strictEqual(E.applyCustom(doc, [{ ...changes[1], zone: "Circle" }]).notFitting[0].reason, "row B is not in Circle");
});

test("no change moves a bank or pit reference, in any venue", () => {
  for (const id of ids) {
    const doc = load(id);
    // one seat added after the first seat and one removed from every block of every row
    const changes = doc.zones.flatMap(z => z.rows.flatMap(r => r.blocks.flatMap(b => [
      { op: "add", zone: z.name, row: r.row, at: b.seats[0], side: "after", id: "999Z", marks: "" },
      { op: "remove", zone: z.name, row: r.row, id: b.seats.at(-1) },
    ])));
    const out = E.applyCustom(doc, changes);
    assert.deepStrictEqual(out.doc.layout.banks, doc.layout.banks, id);
    assert.deepStrictEqual(out.doc.orchestra_pits, doc.orchestra_pits, id);
    out.doc.zones.forEach((z, zi) => z.rows.forEach((r, ri) =>
      assert.strictEqual(r.blocks.length, doc.zones[zi].rows[ri].blocks.length, `${id} ${z.name} ${r.row}`)));
  }
});

test("the last seat of a block cannot be removed", () => {
  const doc = load("ekcc-hall");
  const r = row(doc, "Balcony", "BA");
  const lone = { row: "BA", blocks: [{ seats: ["1"] }, ...r.blocks.slice(1)] };
  doc.zones.find(z => z.name === "Balcony").rows[doc.zones.find(z => z.name === "Balcony").rows.indexOf(r)] = lone;
  const out = E.applyCustom(doc, [{ op: "remove", zone: "Balcony", row: "BA", id: "1" }]);
  assert.match(out.notFitting[0].reason, /a block needs at least one seat/);
});

test("a seat added on the arc venue joins its neighbour's run", () => {
  const doc = load("ekcc-th");
  const b0 = row(doc, "Theatre", "H").blocks[0];       // seats 1-10, one straight run between two aisles
  const out = E.applyCustom(doc, [{ op: "add", zone: "Theatre", row: "H", at: "10", side: "after", id: "11A", marks: "" }]);
  const nb = row(out.doc, "Theatre", "H").blocks[0];
  assert.deepStrictEqual(nb.seats, [...b0.seats, "11A"]);
  for (const k of ["shape", "view", "offset", "start", "end", "inner", "outer"]) assert.strictEqual(nb[k], b0[k], k);
});

// recordChange takes a change as the user makes it on the customised version (seats by their id there)
const record = (doc, steps) => steps.reduce((list, c) => {
  const r = E.recordChange(doc, list, c);
  assert.ok(!r.error, r.error);
  return r.changes;
}, []);
const A = (row, at, side, id, marks = "") => ({ op: "add", zone: "Theatre", row, at, side, id, marks });

test("adding a seat and removing it again leaves no change", () => {
  const doc = load("ncwcc-th");
  assert.deepStrictEqual(record(doc, [A("A", "W4", "after", "W5", "W"), { op: "remove", zone: "Theatre", row: "A", id: "W5" }]), []);
});

test("changes to an added seat fold into its add", () => {
  const doc = load("ncwcc-th");
  const list = record(doc, [
    A("A", "W4", "after", "W5", "W"),
    { op: "marks", zone: "Theatre", row: "A", id: "W5", marks: "WX" },
    { op: "rename", zone: "Theatre", row: "A", id: "W5", to: "W7" },
  ]);
  assert.deepStrictEqual(list, [A("A", "W4", "after", "W7", "WX")]);
});

test("a seat's marks are one change, gone when set back", () => {
  const doc = load("ncwcc-th");
  const m = marks => ({ op: "marks", zone: "Theatre", row: "B", id: "7", marks });
  assert.deepStrictEqual(record(doc, [m("W"), m("X")]), [m("X")]);
  assert.deepStrictEqual(record(doc, [m("W"), m("")]), []);
});

test("a renamed seat is still named by its published id", () => {
  const doc = load("ncwcc-th");
  const list = record(doc, [
    { op: "rename", zone: "Theatre", row: "B", id: "7", to: "7A" },
    { op: "marks", zone: "Theatre", row: "B", id: "7A", marks: "W" },
    A("B", "7A", "after", "7B"),
  ]);
  assert.deepStrictEqual(list, [
    { op: "rename", zone: "Theatre", row: "B", id: "7", to: "7A" },
    { op: "marks", zone: "Theatre", row: "B", id: "7", marks: "W" },
    A("B", "7", "after", "7B"),
  ]);
  assert.strictEqual(E.rowText(row(E.applyCustom(doc, list).doc, "Theatre", "B")), "1-6 7Aw 7B 8-20");
  // renamed back: no rename left
  assert.deepStrictEqual(record(doc, [{ op: "rename", zone: "Theatre", row: "B", id: "7", to: "7A" }, { op: "rename", zone: "Theatre", row: "B", id: "7A", to: "7" }]), []);
});

test("removing a published seat replaces its other changes", () => {
  const doc = load("ncwcc-th");
  const list = record(doc, [
    { op: "marks", zone: "Theatre", row: "B", id: "7", marks: "W" },
    { op: "rename", zone: "Theatre", row: "B", id: "7", to: "7A" },
    { op: "remove", zone: "Theatre", row: "B", id: "7A" },
  ]);
  assert.deepStrictEqual(list, [{ op: "remove", zone: "Theatre", row: "B", id: "7" }]);
});

test("a seat added beside an added seat stays when that seat is removed", () => {
  const doc = load("ncwcc-th");
  const list = record(doc, [A("A", "W4", "after", "W5", "W"), A("A", "W5", "after", "W6", "W"), { op: "remove", zone: "Theatre", row: "A", id: "W5" }]);
  assert.deepStrictEqual(list, [A("A", "W4", "after", "W6", "W")]);
});

test("changes the rules forbid are refused with a reason", () => {
  const doc = load("ncwcc-th");
  const refuse = (list, c, re) => { const r = E.recordChange(doc, list, c); assert.match(r.error || "", re); assert.ok(!r.changes); };
  refuse([], A("B", "7", "after", "8"), /already has a seat 8/);
  refuse([], A("B", "7", "after", "7a"), /not a seat id/);
  refuse([], A("B", "7", "after", "W9", ""), /needs its W mark/);
  refuse([], { op: "marks", zone: "Theatre", row: "B", id: "7", marks: "R" }, /no mark R/);
  refuse([], { op: "remove", zone: "Theatre", row: "B", id: "99" }, /not in row B/);
});

test("two seats can swap ids; two seats cannot end with one id", () => {
  const doc = load("ncwcc-th");
  const ren = (id, to) => ({ op: "rename", zone: "Theatre", row: "B", id, to });
  const swap = E.applyCustom(doc, [ren("7", "8"), ren("8", "7")]);
  assert.deepStrictEqual(swap.notFitting, []);
  assert.deepStrictEqual(row(swap.doc, "Theatre", "B").blocks[0].seats.slice(5, 9), ["6", "8", "7", "9"]);
  const clash = E.applyCustom(doc, [ren("7", "8")]);
  assert.match(clash.notFitting[0].reason, /already has a seat 8/);
  // but a removed seat's id is free
  assert.deepStrictEqual(E.applyCustom(doc, [{ op: "remove", zone: "Theatre", row: "B", id: "8" }, ren("7", "8")]).notFitting, []);
});

test("Your changes: dropping an entry", () => {
  const doc = load("ncwcc-th");
  const list = record(doc, [A("A", "W4", "after", "W5", "W"), A("A", "W5", "after", "W6", "W"), { op: "remove", zone: "Theatre", row: "B", id: "7" }]);
  const left = E.dropChange(list, 0);
  assert.deepStrictEqual(left, [A("A", "W4", "after", "W6", "W"), { op: "remove", zone: "Theatre", row: "B", id: "7" }]);
  assert.deepStrictEqual(E.applyCustom(doc, left).notFitting, []);
  assert.deepStrictEqual(list.length, 3, "the list given is not changed");
});

test("changes travel in the URL as short tuples and come back unchanged", () => {
  const list = [
    A("A", "W4", "after", "W5", "W"), A("A", "W1", "before", "W0", "W"),
    { op: "remove", zone: "Theatre", row: "B", id: "7" },
    { op: "marks", zone: "Theatre", row: "C", id: "3", marks: "" },
    { op: "rename", zone: "樓座", row: "D", id: "4", to: "4A" },
  ];
  const u = E.encodeChanges(list);
  assert.match(u, /^[\w-]+$/);
  assert.deepStrictEqual(E.decodeChanges(u), list);
  assert.deepStrictEqual(JSON.parse(Buffer.from(E.encodeChanges([list[0]]), "base64url")), [["+", "Theatre", "A", "W4", ">", "W5", "W"]]);
  assert.deepStrictEqual(E.decodeChanges(E.encodeChanges([])), []);
  for (const junk of ["", "!!", Buffer.from('{"a":1}').toString("base64url"), Buffer.from('[["?","Z","A","1"]]').toString("base64url"), Buffer.from('[["-","Z",3,"1"]]').toString("base64url")])
    assert.throws(() => E.decodeChanges(junk), /not a customisation/, junk);
});

test("the base names the seat list by the SHA-256 of the file as fetched", async () => {
  const text = fs.readFileSync(path.join(DATA, "ncwcc-th.json"), "utf8");
  assert.strictEqual(await E.seatListSha256(text), "16aa78764bd16d88559a69d9b1d3cff755dd96cf415bc4952d0b109477821ea6");
});

test("a customisation file is written and read back", () => {
  const base = { venue: "ncwcc-th", seat_list_sha256: "16aa78764bd16d88559a69d9b1d3cff755dd96cf415bc4952d0b109477821ea6", configuration: { venue: "ncwcc-th", pit: -1, marks: { W: true, X: false }, zones: { Theatre: true }, standing: false } };
  const changes = [A("A", "W4", "after", "W5", "W"), { op: "remove", zone: "Theatre", row: "B", id: "7" }];
  const text = E.customFile(base, changes, "agreed with the box office");
  const f = JSON.parse(text);
  assert.strictEqual(f.schema, "hkperf-venue-seats/custom@0.1");
  assert.ok(!Number.isNaN(Date.parse(f.saved)));
  assert.deepStrictEqual(E.readCustom(text), { base, changes, note: "agreed with the box office" });
});

test("a plan file's customisation is read; older plans have none", () => {
  const base = { venue: "ncwcc-th", seat_list_sha256: "ab", configuration: {} };
  const changes = [{ op: "remove", zone: "Theatre", row: "B", id: "7" }];
  const plan = { schema: "hkperf-venue-seats/plan@0.3", venue: "ncwcc-th", customisation: { base, changes }, seats: {} };
  assert.deepStrictEqual(E.readCustom(JSON.stringify(plan)), { base, changes, note: "" });
  assert.deepStrictEqual(E.readCustom(JSON.stringify({ schema: "hkperf-venue-seats/plan@0.2", venue: "ncwcc-th", seats: {} })), null);
  for (const junk of ["nope", "{}", JSON.stringify({ schema: "hkperf-venue-seats/custom@9" }), JSON.stringify({ schema: "hkperf-venue-seats/custom@0.1", base, changes: [{ op: "explode" }] })])
    assert.throws(() => E.readCustom(junk), /customisation/, junk);
});

test("whatever the user does, the list it keeps applies cleanly and holds one change per seat", () => {
  let seed = 7;
  const rnd = n => { seed = (seed * 1103515245 + 12345) % 2 ** 31; return seed % n; };
  for (const id of ids) {
    const doc = load(id), letters = Object.keys(doc.marks || {});
    let list = [];
    for (let step = 0; step < 60; step++) {
      const view = E.applyCustom(doc, list).doc;
      const z = view.zones[rnd(view.zones.length)], r = z.rows[rnd(z.rows.length)];
      const seats = r.blocks.flatMap(b => b.seats), s = seats[rnd(seats.length)];
      const where = { zone: z.name, row: r.row };
      const pick = rnd(4);
      const c = pick === 0 ? { op: "add", ...where, at: s, side: rnd(2) ? "after" : "before", id: rnd(2) ? `W${50 + rnd(5)}` : `${rnd(3) + 1}${"ABC"[rnd(3)]}`, marks: "W" }
        : pick === 1 ? { op: "remove", ...where, id: s }
        : pick === 2 ? { op: "marks", ...where, id: s, marks: letters.filter(() => rnd(3) === 0).join("") }
        : { op: "rename", ...where, id: s, to: `${rnd(3) + 1}${"ABC"[rnd(3)]}` };
      if (c.op === "add" && !letters.includes("W")) c.marks = "";
      const res = E.recordChange(doc, list, c);
      if (res.error) continue;
      list = res.changes;
      const out = E.applyCustom(doc, list);
      assert.deepStrictEqual(out.notFitting, [], `${id} step ${step} ${JSON.stringify(c)}`);
      const keys = list.map(x => `${x.zone}|${x.row}|${x.op === "add" ? "+" + x.id : x.id}|${x.op === "add" ? "" : x.op}`);
      assert.strictEqual(new Set(keys).size, keys.length, `${id} step ${step}: two changes to one seat`);
      assert.ok(!list.some(x => x.op === "remove" && list.some(y => y !== x && y.op !== "add" && y.zone === x.zone && y.row === x.row && y.id === x.id)), `${id} step ${step}: a removed seat keeps other changes`);
      assert.deepStrictEqual(E.decodeChanges(E.encodeChanges(list)), list);
    }
  }
});

test("the view for drawing keeps removed seats in place and says what changed", () => {
  const doc = load("ncwcc-th");
  const v = E.customView(doc, [
    A("A", "W4", "after", "W5", "W"),
    { op: "remove", zone: "Theatre", row: "B", id: "7" },
    { op: "marks", zone: "Theatre", row: "B", id: "8", marks: "W" },
    { op: "rename", zone: "Theatre", row: "B", id: "9", to: "9A" },
  ]);
  assert.strictEqual(E.rowText(row(v.doc, "Theatre", "B")), "1-6 8w 9A 10-20");
  assert.strictEqual(E.rowText(row(v.shown, "Theatre", "B")), "1-7 8w 9A 10-20");
  assert.deepStrictEqual(Object.keys(v.status.get("Theatre|B|7")), ["removed"]);
  assert.strictEqual(v.status.get("Theatre|B|8").wasMarks, "");
  assert.strictEqual(v.status.get("Theatre|B|9A").wasId, "9");
  assert.ok(v.status.get("Theatre|A|W5").added);
  assert.ok(!v.status.has("Theatre|B|10"));
  // a removed seat whose id is taken again is not drawn twice
  const w = E.customView(doc, [{ op: "remove", zone: "Theatre", row: "B", id: "8" }, { op: "rename", zone: "Theatre", row: "B", id: "7", to: "8" }]);
  assert.strictEqual(E.rowText(row(w.shown, "Theatre", "B")), E.rowText(row(w.doc, "Theatre", "B")));
});

test("a new seat's id is suggested from its neighbour", () => {
  const doc = load("ncwcc-th");
  const B = row(doc, "Theatre", "B"), A_ = row(doc, "Theatre", "A");
  assert.strictEqual(E.suggestId(B, "20", "after"), "21");
  assert.strictEqual(E.suggestId(B, "7", "after"), "7A");
  assert.strictEqual(E.suggestId(B, "1", "before"), "1A");
  assert.strictEqual(E.suggestId(A_, "W4", "after", "W"), "W5");
  assert.strictEqual(E.suggestId(B, "7", "after", "X"), "X1");
  assert.strictEqual(E.suggestId(A_, "W4", "after"), "17");
  const taken = { row: "Z", blocks: [{ seats: ["7", "7A", "7B", "8"] }] };
  assert.strictEqual(E.suggestId(taken, "7", "after"), "7C");
});

test("a seat is renamed, keeping its marks", () => {
  const out = E.applyCustom(load("ncwcc-th"), [
    { op: "rename", zone: "Theatre", row: "B", id: "20", to: "20A" },
    { op: "rename", zone: "Theatre", row: "A", id: "W4", to: "W9" },
  ]);
  assert.strictEqual(E.rowText(row(out.doc, "Theatre", "B")), "1-19 20A");
  const a = row(out.doc, "Theatre", "A");
  assert.strictEqual(a.marks.W9, "W");
  assert.strictEqual(a.inferred_numbers.W9, "16");
  assert.ok(!("W4" in a.marks));
});
