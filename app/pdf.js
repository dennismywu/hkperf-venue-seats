// The viewer's seat map as a downloadable vector PDF.
//
// The map is already an SVG in the page. This module walks it, turns its handful of primitives
// (rect, line, circle, polygon, path, text) into PDF drawing operators, and puts the result on a
// fixed A4/A3 page with the venue, the configuration and the key figures. Fonts are embedded, so
// the file looks the same on a printer that has none of this machine's fonts.
//
// pdf-lib, its fontkit and the Noto Sans HK subset are loaded only when the visitor asks for a
// PDF. Nothing is sent anywhere: the file is made in the browser.
//
// Limits: the adapter covers what drawSeatMap() emits. A <path> may sit in translated groups
// (the arc map's outer translate); a path inside a rotated or scaled group is skipped rather
// than drawn in the wrong place.

const SEAT_PDF = (() => {
  const LIB_URL = "vendor/pdf-lib.min.js";
  const FONTKIT_URL = "vendor/fontkit.umd.min.js";
  const FONT_URL = {
    regular: "fonts/NotoSansHK-Regular-subset.ttf",
    bold: "fonts/NotoSansHK-Bold-subset.ttf",
  };
  // The planner's names and category names can be any text; this face is fetched only when the
  // small subsets cannot draw it, and pdf-lib embeds just the glyphs the plan uses.
  const USER_FONT_URL = "fonts/NotoSansHK-Regular-full.ttf";
  const PAPER = { A4: [595.28, 841.89], A3: [841.89, 1190.55] };   // points
  const MARGIN = 36;
  const BLOCK_GAP = 10;
  const FOOTER_H = 22;

  // light-theme colours used by the legend swatches (common.css)
  const INK = [0.114, 0.114, 0.106], MUTED = [0.42, 0.416, 0.396];
  const LINE = [0.851, 0.843, 0.816], SOFT = [0.969, 0.965, 0.953];
  const XBG = [0.933, 0.929, 0.914], RES = [0.486, 0.227, 0.929];
  const OK = [0.18, 0.49, 0.31], ORANGE = [0.957, 0.635, 0.38];
  const GRP = [0.96, 0.875, 0.78];
  const MARK_STYLE = {
    W: { fill: [0.89, 0.933, 0.98], stroke: [0.184, 0.435, 0.702], text: [0.184, 0.435, 0.702], letter: "W" },
    X: { fill: [0.933, 0.929, 0.914], stroke: [0.604, 0.596, 0.573], text: [0.604, 0.596, 0.573], cross: true },
    R: { fill: [0.984, 0.937, 0.875], stroke: [0.722, 0.416, 0.071], text: [0.722, 0.416, 0.071], inner: true },
    L: { fill: [0.827, 0.824, 0.8], stroke: [0.227, 0.227, 0.212], text: [0.227, 0.227, 0.212] },
  };

  let vendor = null;         // { PDFLib, fontkit }
  let fontBuffers = null;    // [regular, bold]
  let userFontBuffer = null; // the full regular face, for planner names/categories
  let metrics = null;        // Noto Sans HK ascent/descent, for dominant-baseline: central

  // ---------------------------------------------------------------- loading

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = () => reject(new Error(`Could not load ${src}`));
      document.head.append(s);
    });
  }

  async function loadVendor() {
    if (!vendor) vendor = (async () => {
      await Promise.all([loadScript(LIB_URL), loadScript(FONTKIT_URL)]);
      if (!window.PDFLib || !window.fontkit) throw new Error("The PDF library did not load.");
      return { PDFLib: window.PDFLib, fontkit: window.fontkit };
    })().catch(e => { vendor = null; throw e; });
    return vendor;
  }

  async function loadFonts() {
    if (!fontBuffers) fontBuffers = Promise.all(
      Object.values(FONT_URL).map(url => fetch(url).then(r => {
        if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
        return r.arrayBuffer();
      })),
    ).catch(e => { fontBuffers = null; throw e; });
    return fontBuffers;
  }

  async function loadUserFont() {
    if (!userFontBuffer) userFontBuffer = fetch(USER_FONT_URL).then(r => {
      if (!r.ok) throw new Error(`${USER_FONT_URL}: HTTP ${r.status}`);
      return r.arrayBuffer();
    }).catch(e => { userFontBuffer = null; throw e; });
    return userFontBuffer;
  }

  // ---------------------------------------------------------------- colours

  const colourCache = new Map();
  let probe = null;

  function parseColour(value) {
    if (!value || value === "none" || value === "transparent") return null;
    if (colourCache.has(value)) return colourCache.get(value);
    let out = null;
    const v = String(value).trim();
    const rgb = v.match(/^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+([\d.]+))?\s*\)$/i);
    const srgb = v.match(/^color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+))?\)$/i);
    const hex = v.match(/^#([0-9a-f]{3,8})$/i);
    if (rgb) out = [+rgb[1] / 255, +rgb[2] / 255, +rgb[3] / 255, rgb[4] == null ? 1 : +rgb[4]];
    else if (srgb) out = [+srgb[1], +srgb[2], +srgb[3], srgb[4] == null ? 1 : +srgb[4]];
    else if (hex) {
      const h = hex[1];
      const n = h.length === 3 ? h.split("").map(c => c + c).join("") : h;
      out = [parseInt(n.slice(0, 2), 16) / 255, parseInt(n.slice(2, 4), 16) / 255,
        parseInt(n.slice(4, 6), 16) / 255, n.length === 8 ? parseInt(n.slice(6, 8), 16) / 255 : 1];
    } else {
      // named colours and colour spaces the regexes above do not know: let the canvas parse it
      probe ||= document.createElement("canvas").getContext("2d");
      probe.fillStyle = "#010203";
      probe.fillStyle = v;
      const got = probe.fillStyle;
      if (got && got !== "#010203") out = parseColour(got);
    }
    colourCache.set(value, out);
    return out;
  }

  // Group opacity and faded seats are pre-blended against the white page: the PDF stays opaque,
  // which is one less thing for a printer's RIP to interpret.
  function paint(colour, alpha, lib) {
    if (!colour) return undefined;
    // colours parsed from CSS carry an alpha; the fixed light-theme swatches are RGB only
    const a = Math.max(0, Math.min(1, (colour[3] ?? 1) * alpha));
    return lib.rgb(colour[0] * a + (1 - a), colour[1] * a + (1 - a), colour[2] * a + (1 - a));
  }

  // ---------------------------------------------------------------- matrices

  const IDENT = [1, 0, 0, 1, 0, 0];
  const mul = (m, n) => [
    m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1],
    m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
    m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5],
  ];
  const apply = (m, p) => [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];

  function transformMatrix(value) {
    let m = IDENT;
    for (const match of String(value || "").matchAll(/([a-zA-Z]+)\s*\(([^)]*)\)/g)) {
      const fn = match[1], a = match[2].split(/[\s,]+/).filter(Boolean).map(Number);
      let t = IDENT;
      if (fn === "translate") t = [1, 0, 0, 1, a[0] || 0, a[1] || 0];
      else if (fn === "scale") t = [a[0] ?? 1, 0, 0, a.length > 1 ? a[1] : a[0] ?? 1, 0, 0];
      else if (fn === "rotate") {
        const r = (a[0] || 0) * Math.PI / 180, c = Math.cos(r), s = Math.sin(r);
        t = [c, s, -s, c, 0, 0];
        if (a.length > 2) t = mul(mul([1, 0, 0, 1, a[1], a[2]], t), [1, 0, 0, 1, -a[1], -a[2]]);
      } else if (fn === "matrix") t = a.slice(0, 6);
      else continue;
      m = mul(m, t);
    }
    return m;
  }

  const isTranslate = m => m[0] === 1 && m[1] === 0 && m[2] === 0 && m[3] === 1;
  const matrixScale = m => Math.hypot(m[0], m[1]);

  // ---------------------------------------------------------------- styles

  let styleCache = null;

  function styleKey(el, root) {
    let key = `${el.tagName}|${el.getAttribute("class") || ""}|${el.getAttribute("style") || ""}`;
    for (let p = el.parentElement; p && p !== root; p = p.parentElement) {
      key += `|${p.getAttribute("class") || ""}|${p.getAttribute("style") || ""}`;
    }
    return key;
  }

  function styleOf(el, root) {
    const key = styleKey(el, root);
    if (styleCache.has(key)) return styleCache.get(key);
    const cs = getComputedStyle(el);
    const weight = cs.fontWeight === "bold" ? 700 : parseInt(cs.fontWeight, 10) || 400;
    const dash = cs.strokeDasharray && cs.strokeDasharray !== "none"
      ? cs.strokeDasharray.split(/[,\s]+/).map(parseFloat).filter(n => n >= 0) : [];
    const opacity = parseFloat(cs.opacity), strokeWidth = parseFloat(cs.strokeWidth);
    const fontSize = parseFloat(cs.fontSize);
    const st = {
      display: cs.display, visibility: cs.visibility, opacity: Number.isFinite(opacity) ? opacity : 1,
      fill: parseColour(cs.fill), pattern: /^url\(/i.test(cs.fill || "") ? "block" : null,
      stroke: parseColour(cs.stroke),
      strokeWidth: Number.isFinite(strokeWidth) ? strokeWidth : 1, dash,
      fontSize: Number.isFinite(fontSize) ? fontSize : 12, weight,
      anchor: cs.textAnchor || "start", baseline: cs.dominantBaseline || "auto",
      decoration: `${cs.textDecorationLine || ""} ${cs.textDecoration || ""}`,
    };
    styleCache.set(key, st);
    return st;
  }

  // ---------------------------------------------------------------- geometry helpers

  const num = (el, name, fallback = 0) => {
    const v = el.getAttribute(name);
    return v == null || v === "" ? fallback : +v || 0;
  };

  const pathOf = (points, closed) =>
    points.map((p, i) => `${i ? "L" : "M"} ${p[0]} ${p[1]}`).join(" ") + (closed ? " Z" : "");

  // A rounded rectangle as a polyline; six segments per corner is smooth at print sizes.
  // 45° stripes for the planner's blocked seats, clipped to an axis-aligned local rectangle.
  function hatchSegments(x, y, w, h, step = 4) {
    const out = [];
    for (let c = y - (x + w); c <= (y + h) - x; c += step) {
      const x0 = Math.max(x, y - c), x1 = Math.min(x + w, y + h - c);
      if (x1 > x0 + 0.01) out.push([[x0, x0 + c], [x1, x1 + c]]);
    }
    return out;
  }

  function roundedRectPoints(x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    if (!r) return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
    const pts = [];
    const arc = (cx, cy, from, to) => {
      for (let i = 0; i <= 6; i++) {
        const a = from + (to - from) * i / 6;
        pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
      }
    };
    pts.push([x + r, y], [x + w - r, y]);
    arc(x + w - r, y + r, -Math.PI / 2, 0);
    pts.push([x + w, y + h - r]);
    arc(x + w - r, y + h - r, 0, Math.PI / 2);
    pts.push([x + r, y + h]);
    arc(x + r, y + h - r, Math.PI / 2, Math.PI);
    pts.push([x, y + r]);
    arc(x + r, y + r, Math.PI, Math.PI * 1.5);
    return pts;
  }

  // ---------------------------------------------------------------- the SVG walker

  // page-space mapping: root SVG (minX, minY) is the top-left of the map box
  // (map.x, map.y); +y in SVG runs down the page, so the PDF y is subtracted.
  function makeWriter(page, lib, map, box, fontFor) {
    const s = map.scale, minX = map.minX, minY = map.minY;
    const pick = fontFor || ((value, weight) => weight >= 600 ? page.pdfFonts.bold : page.pdfFonts.regular);
    const gx = box.x - s * minX, gy = box.y + s * minY;

    // a path whose coordinates are already in the SVG root's space (the viewBox)
    function rootPath(d, ms, st, alpha) {
      page.drawSvgPath(d, {
        x: gx, y: gy, scale: s,
        color: st.fill ? paint(st.fill, alpha, lib) : undefined,
        borderColor: st.stroke ? paint(st.stroke, alpha, lib) : undefined,
        borderWidth: st.stroke ? st.strokeWidth * ms : undefined,
        borderDashArray: st.stroke && st.dash.length ? st.dash.map(v => v * ms) : undefined,
      });
    }

    // a path whose coordinates are still in an element's local space, with its transform m
    function svgPath(d, m, st, alpha) {
      if (!isTranslate(m)) return;
      page.drawSvgPath(d, {
        x: gx + s * m[4], y: gy - s * m[5], scale: s,
        color: st.fill ? paint(st.fill, alpha, lib) : undefined,
        borderColor: st.stroke ? paint(st.stroke, alpha, lib) : undefined,
        borderWidth: st.stroke ? st.strokeWidth : undefined,
        borderDashArray: st.stroke && st.dash.length ? st.dash : undefined,
      });
    }

    function poly(points, closed, m, st, alpha) {
      rootPath(pathOf(points, closed), matrixScale(m), st, alpha);
    }

    function text(el, m, st, alpha) {
      const value = el.textContent;
      if (!value || !value.trim() || !st.fill) return;
      const font = pick(value, st.weight);
      const fs = st.fontSize;
      const w = font.widthOfTextAtSize(value, fs);
      let x = num(el, "x"), y = num(el, "y");
      if (st.anchor === "middle") x -= w / 2;
      else if (st.anchor === "end") x -= w;
      // dominant-baseline: central puts the middle of the em box on y; PDF draws from the baseline
      if (st.baseline === "central") y += metrics.central * fs;
      else if (st.baseline === "middle") y += metrics.middle * fs;
      const p = apply(m, [x, y]);
      const ms = matrixScale(m);
      const X = box.x + s * (p[0] - minX), Y = box.y - s * (p[1] - minY);
      const angle = Math.atan2(m[1], m[0]) * 180 / Math.PI;
      writeText(page, lib, value, {
        x: X, y: Y, size: fs * ms * s, font,
        color: paint(st.fill, alpha, lib), rotate: -angle,
      });
      const rule = (offset, thickness) => {
        const p1 = apply(m, [x, y + offset]), p2 = apply(m, [x + w, y + offset]);
        page.drawLine({
          start: { x: box.x + s * (p1[0] - minX), y: box.y - s * (p1[1] - minY) },
          end: { x: box.x + s * (p2[0] - minX), y: box.y - s * (p2[1] - minY) },
          thickness, color: paint(st.fill, alpha, lib),
        });
      };
      if (st.decoration.includes("underline")) rule(fs * 0.09, 0.5 * s);
      if (st.decoration.includes("line-through")) rule(-fs * 0.3, 0.6 * s);
    }

    function walk(el, m, alpha) {
      const tag = el.tagName;
      if (tag === "defs" || tag === "title" || tag === "desc" || tag === "style") return;
      if ((el.getAttribute("class") || "").split(/\s+/).includes("marquee")) return;
      const st = styleOf(el, root);
      if (st.display === "none" || st.visibility === "hidden" || alpha <= 0) return;
      // .seat.off is 22% on screen; lift it a little so faded boxes survive a printer
      const faded = (el.getAttribute("class") || "").split(/\s+/).includes("off");
      const a = faded ? Math.max(alpha * st.opacity, 0.3) : alpha * st.opacity;
      const tm = el.hasAttribute("transform") ? mul(m, transformMatrix(el.getAttribute("transform"))) : m;

      switch (tag) {
        case "svg": case "g": case "a":
          for (const child of el.children) walk(child, tm, a);
          break;
        case "rect": {
          const x = num(el, "x"), y = num(el, "y"), w = num(el, "width"), h = num(el, "height");
          const rx = num(el, "rx") || num(el, "ry");
          const points = roundedRectPoints(x, y, w, h, rx).map(p => apply(tm, p));
          if (st.pattern === "block") {
            // the planner's diagonal hatch: a pale base, then 45° stripes clipped to the box
            poly(points, true, tm, { ...st, fill: XBG, pattern: null }, a);
            const hatch = { fill: null, stroke: LINE, strokeWidth: 2, dash: [] };
            for (const [p0, p1] of hatchSegments(x, y, w, h)) {
              poly([apply(tm, p0), apply(tm, p1)], false, tm, hatch, a);
            }
          } else {
            poly(points, true, tm, st, a);
          }
          break;
        }
        case "line":
          poly([apply(tm, [num(el, "x1"), num(el, "y1")]), apply(tm, [num(el, "x2"), num(el, "y2")])], false, tm, st, a);
          break;
        case "circle": {
          const ms = matrixScale(tm), centre = apply(tm, [num(el, "cx"), num(el, "cy")]);
          const radius = num(el, "r") * ms;
          const X = box.x + s * (centre[0] - minX), Y = box.y - s * (centre[1] - minY);
          page.drawCircle({
            x: X, y: Y, size: radius * s,
            color: st.fill ? paint(st.fill, a, lib) : undefined,
            borderColor: st.stroke ? paint(st.stroke, a, lib) : undefined,
            borderWidth: st.stroke ? st.strokeWidth * ms * s : undefined,
            borderDashArray: st.stroke && st.dash.length ? st.dash.map(v => v * ms * s) : undefined,
          });
          break;
        }
        case "polygon": {
          const pts = (el.getAttribute("points") || "").trim().split(/\s+/).map(pair => {
            const [x, y] = pair.split(",").map(Number);
            return apply(tm, [x, y]);
          }).filter(p => Number.isFinite(p[0]) && Number.isFinite(p[1]));
          poly(pts, true, tm, st, a);
          break;
        }
        case "path":
          // Paths sit in the root or in the arc map's translate group. A rotated or scaled group
          // would need the path's own arc commands transformed; the seat map never does that.
          if (isTranslate(tm)) svgPath(el.getAttribute("d") || "", tm, st, a);
          break;
        case "text":
          text(el, tm, st, a);
          break;
      }
    }

    // the walker needs the root for the style-cache key; it is closed over here
    let root = null;
    return { walk: (svg, m, alpha) => { root = svg; walk(svg, m, alpha); } };
  }

  // Selection outlines, drag targets and config hovers are on-screen aids, not part of a saved
  // map; take them off for the walk and put them back afterwards.
  function stripClasses(svg) {
    const names = ["sel", "drop-ok", "drop-bad", "gain", "lose"];
    const touched = [];
    for (const el of svg.querySelectorAll(".sel, .drop-ok, .drop-bad, .gain, .lose")) {
      const had = names.filter(name => el.classList.contains(name));
      if (!had.length) continue;
      el.classList.remove(...had);
      touched.push([el, had]);
    }
    return () => { for (const [el, had] of touched) el.classList.add(...had); };
  }

  // ---------------------------------------------------------------- text helpers

  function wrap(text, font, size, width) {
    const lines = [];
    for (const para of String(text ?? "").split("\n")) {
      let line = "";
      for (const word of para.split(/(\s+)/)) {
        const next = line + word;
        if (!line || font.widthOfTextAtSize(next.trimEnd(), size) <= width) { line = next; continue; }
        lines.push(line.trimEnd());
        line = word.trimStart();
        while (line && font.widthOfTextAtSize(line, size) > width) {
          let cut = line.length - 1;
          while (cut > 0 && font.widthOfTextAtSize(line.slice(0, cut), size) > width) cut--;
          cut = Math.max(1, cut);                 // always make progress, even for one wide glyph
          lines.push(line.slice(0, cut));
          line = line.slice(cut);
        }
      }
      if (line.trim()) lines.push(line.trimEnd());
    }
    return lines.length ? lines : [""];
  }

  // pdf-lib's page.drawText() adds a font resource to the page for every call. A seat map has
  // thousands of labels, so write the text operators ourselves against the two font keys made
  // once per page; the same font stays referenced by every label.
  function writeText(page, lib, value, { x, y, size, font, color, rotate = 0 }) {
    if (!value) return;
    const rad = rotate * Math.PI / 180, c = Math.cos(rad), s = Math.sin(rad);
    page.pushOperators(
      lib.pushGraphicsState(),
      lib.beginText(),
      lib.setFillingColor(color),
      lib.setFontAndSize(font.pdfKey, size),
      lib.setTextMatrix(c, s, -s, c, x, y),
      lib.showText(font.encodeText(value)),
      lib.endText(),
      lib.popGraphicsState(),
    );
  }

  function drawLines(page, lib, lines, { x, top, size, leading, font, colour }) {
    let y = top;
    for (const line of lines) {
      writeText(page, lib, line, { x, y: y - size, size, font, color: colour });
      y -= leading;
    }
    return y;
  }

  // ---------------------------------------------------------------- legend, stats, header

  function legendLines(entries, font, width, fontFor) {
    const lines = [[]];
    let x = 0;
    for (const entry of entries) {
      const f = fontFor ? fontFor(entry.label, 400) : font;
      const w = 10 + 4 + f.widthOfTextAtSize(entry.label, 8.5) + 14;
      if (x && x + w > width) { lines.push([]); x = 0; }
      lines[lines.length - 1].push({ ...entry, w });
      x += w;
    }
    return lines;
  }

  function drawSwatch(page, lib, kind, mark, colour, x, top) {
    const y = top - 9;
    if (kind === "mark") {
      const s = MARK_STYLE[mark] || MARK_STYLE.L;
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(...s.fill), borderColor: lib.rgb(...s.stroke), borderWidth: 0.7 });
      if (s.letter) {
        const w = page.pdfFonts.regular.widthOfTextAtSize(s.letter, 6);
        writeText(page, lib, s.letter, { x: x + 4.5 - w / 2, y: y + 2.4, size: 6, font: page.pdfFonts.regular, color: lib.rgb(...s.text) });
      }
      if (s.inner) page.drawRectangle({ x: x + 1.4, y: y + 1.4, width: 6.2, height: 6.2, borderColor: lib.rgb(...s.stroke), borderWidth: 0.5 });
      if (s.cross) {
        page.drawLine({ start: { x: x + 1.6, y: y + 1.6 }, end: { x: x + 7.4, y: y + 7.4 }, thickness: 0.6, color: lib.rgb(...s.text) });
        page.drawLine({ start: { x: x + 7.4, y: y + 1.6 }, end: { x: x + 1.6, y: y + 7.4 }, thickness: 0.6, color: lib.rgb(...s.text) });
      }
    } else if (kind === "category") {
      const c = parseColour(colour) || [0.8, 0.8, 0.8, 1];
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(c[0], c[1], c[2]), borderColor: lib.rgb(...LINE), borderWidth: 0.6 });
    } else if (kind === "block") {
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(...XBG), borderColor: lib.rgb(...LINE), borderWidth: 0.6 });
      for (const [p0, p1] of hatchSegments(x, y, 9, 9, 3)) {
        page.drawLine({ start: { x: p0[0], y: p0[1] }, end: { x: p1[0], y: p1[1] }, thickness: 1.2, color: lib.rgb(...LINE) });
      }
    } else if (kind === "reserved") {
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(1, 1, 1), borderColor: lib.rgb(...RES), borderWidth: 1, borderDashArray: [2, 1.2] });
    } else if (kind === "public") {
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(0.84, 0.93, 0.87), borderColor: lib.rgb(...OK), borderWidth: 0.7 });
    } else if (kind === "reserved-fill") {
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(0.91, 0.87, 0.99), borderColor: lib.rgb(...RES), borderWidth: 1, borderDashArray: [2, 1.2] });
    } else if (kind === "grp") {
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(...GRP), borderColor: lib.rgb(...LINE), borderWidth: 0.6 });
      writeText(page, lib, "AB", { x: x + 2.4, y: y + 2.5, size: 4.5, font: page.pdfFonts.regular, color: lib.rgb(...MUTED) });
    } else if (kind === "catline" || kind === "catdash") {
      const c = parseColour(colour) || ORANGE;
      page.drawRectangle({
        x, y, width: 9, height: 9, color: lib.rgb(1, 1, 1),
        borderColor: lib.rgb(c[0], c[1], c[2]),
        borderWidth: 1.2, borderDashArray: kind === "catdash" ? [2, 1.2] : undefined,
      });
    } else if (kind === "standing") {
      page.drawCircle({ x: x + 4.5, y: y + 4.5, size: 4.5, borderColor: lib.rgb(...MUTED), borderWidth: 0.6, borderDashArray: [1.5, 1.5] });
    } else if (kind === "pit") {
      page.drawRectangle({ x, y, width: 9, height: 9, borderColor: lib.rgb(0.722, 0.416, 0.071), borderWidth: 0.6, borderDashArray: [2, 1.5] });
    } else {
      page.drawRectangle({ x, y, width: 9, height: 9, color: lib.rgb(1, 1, 1), borderColor: lib.rgb(...MUTED), borderWidth: 0.6, borderDashArray: [1.5, 1.5] });
    }
  }

  function drawLegend(page, lib, entries, font, x, top, width, fontFor) {
    const lines = legendLines(entries, font, width, fontFor);
    lines.forEach((line, row) => {
      let cx = x;
      const y = top - row * 14;
      for (const entry of line) {
        drawSwatch(page, lib, entry.kind, entry.mark, entry.colour, cx, y);
        const f = fontFor ? fontFor(entry.label, 400) : font;
        writeText(page, lib, entry.label, { x: cx + 14, y: y - 1.5, size: 8.5, font: f, color: lib.rgb(...MUTED) });
        cx += entry.w;
      }
    });
    return lines.length * 14 + 6;
  }

  function drawStats(page, lib, rows, font, bold, x, top, width, fontFor) {
    const cols = rows.length > 5 ? 2 : 1;
    const per = Math.ceil(rows.length / cols), colW = width / cols, rowH = 14;
    const h = per * rowH + 12;
    page.drawRectangle({ x, y: top - h, width, height: h, color: lib.rgb(...SOFT), borderColor: lib.rgb(...LINE), borderWidth: 0.6 });
    rows.forEach((row, i) => {
      const c = Math.floor(i / per), j = i % per;
      const rx = x + c * colW + 8, ry = top - 6 - (j + 1) * rowH + 4;
      const lf = fontFor ? fontFor(row.label, 400) : font;
      const vf = fontFor ? fontFor(row.value, 700) : bold;
      writeText(page, lib, row.label, { x: rx, y: ry, size: 8.5, font: lf, color: lib.rgb(...MUTED) });
      const colour = row.tone === "bad" ? [0.702, 0.149, 0.118] : row.tone === "ok" ? [0.18, 0.49, 0.31] : INK;
      const w = vf.widthOfTextAtSize(row.value, 9.5);
      writeText(page, lib, row.value, { x: rx + colW - 16 - w, y: ry, size: 9.5, font: vf, color: lib.rgb(...colour) });
    });
    if (cols > 1) page.drawLine({
      start: { x: x + colW, y: top - 6 }, end: { x: x + colW, y: top - h + 6 },
      thickness: 0.6, color: lib.rgb(...LINE),
    });
    return h;
  }

  // ---------------------------------------------------------------- page composition

  function mapBox(pageW, pageH, parts) {
    const contentW = pageW - 2 * MARGIN;
    const headerH = parts.title.length * 22 + parts.subtitle.length * 14 + parts.summary.length * 12 +
      6 + parts.statsH + BLOCK_GAP + parts.legendH;
    const top = pageH - MARGIN - headerH - 12;
    const bottom = MARGIN + FOOTER_H + 8;
    return { contentW, headerH, top, bottom, height: top - bottom };
  }

  function fitScale(parts, pageW, pageH, map) {
    const box = mapBox(pageW, pageH, parts);
    if (box.height <= 0) return 0;
    return Math.min(box.contentW / map.width, box.height / map.height);
  }

  async function build({ doc, svg, summary, stats, legend, content, paper = "A3", orientation = "auto", generated = new Date() }) {
    const { PDFLib, fontkit } = await loadVendor();
    const [regularBytes, boldBytes] = await loadFonts();
    // Read the map's figures and the map itself at one moment, after the libraries have loaded:
    // a configuration change during the first download cannot leave the sheet half old, half new.
    if (content) ({ summary, stats, legend } = content());
    if (!svg?.viewBox?.baseVal?.width || !svg.viewBox.baseVal.height) throw new Error("The seat map is not ready yet.");
    if (!svg.isConnected) throw new Error("The seat map changed while the PDF was being prepared; try again.");

    const vb = svg.viewBox.baseVal;
    const map = { minX: vb.x, minY: vb.y, width: vb.width, height: vb.height, scale: 1 };
    const pdf = await PDFLib.PDFDocument.create();
    pdf.registerFontkit(fontkit);
    const regular = await pdf.embedFont(regularBytes, { subset: false });
    const bold = await pdf.embedFont(boldBytes, { subset: false });

    // fontkit metrics for dominant-baseline: central; Noto Sans HK's ascent/descent are per em
    if (!metrics) {
      const fk = fontkit.create(new Uint8Array(regularBytes));
      metrics = {
        central: (fk.ascent + fk.descent) / 2 / fk.unitsPerEm,
        middle: (fk.xHeight || 0) / 2 / fk.unitsPerEm,
      };
    }

    const [pw0, ph0] = PAPER[paper] || PAPER.A3;
    const candidates = orientation === "portrait" ? [{ pageW: pw0, pageH: ph0, kind: "portrait" }]
      : orientation === "landscape" ? [{ pageW: ph0, pageH: pw0, kind: "landscape" }]
      : [{ pageW: pw0, pageH: ph0, kind: "portrait" }, { pageW: ph0, pageH: pw0, kind: "landscape" }];

    // The header wraps differently in portrait and landscape; measure both. On auto, prefer the
    // orientation that matches the map's shape unless the other is more than 5% larger, so a wide
    // map fills a landscape page instead of leaving half a portrait page empty.
    const measured = [];
    for (const candidate of candidates) {
      const { pageW, pageH } = candidate;
      const contentW = pageW - 2 * MARGIN;
      const title = wrap(doc.venue.name_en, bold, 18, contentW);
      const subtitle = wrap([doc.venue.name_zh, doc.source?.plan_code ? `plan ${doc.source.plan_code}` : ""].filter(Boolean).join(" · "), regular, 11, contentW);
      const summaryLines = wrap(summary, regular, 9.5, contentW);
      const cols = stats.length > 5 ? 2 : 1;
      const statsH = Math.ceil(stats.length / cols) * 14 + 12;
      const legendH = legendLines(legend, regular, contentW).length * 14 + 6;
      const parts = { title, subtitle, summary: summaryLines, statsH, legendH };
      measured.push({ ...candidate, parts, scale: fitScale(parts, pageW, pageH, map) });
    }
    let chosen = measured.reduce((a, b) => b.scale > a.scale ? b : a);
    if (orientation === "auto") {
      const preferred = map.width > map.height ? "landscape" : "portrait";
      const candidate = measured.find(c => c.kind === preferred);
      if (candidate && candidate.scale >= chosen.scale * 0.95) chosen = candidate;
    }
    if (chosen.scale <= 0) throw new Error("The seat map does not fit on that page.");
    const { pageW, pageH, parts } = chosen;
    map.scale = chosen.scale;

    const page = pdf.addPage([pageW, pageH]);
    // one resource name per face, reused by every label (see writeText)
    page.setFont(regular); regular.pdfKey = page.fontKey;
    page.setFont(bold); bold.pdfKey = page.fontKey;
    page.pdfFonts = { regular, bold };
    page.drawRectangle({ x: 0, y: 0, width: pageW, height: pageH, color: PDFLib.rgb(1, 1, 1) });

    // header
    let y = pageH - MARGIN;
    y = drawLines(page, PDFLib, parts.title, { x: MARGIN, top: y, size: 18, leading: 22, font: bold, colour: PDFLib.rgb(...INK) });
    y = drawLines(page, PDFLib, parts.subtitle, { x: MARGIN, top: y, size: 11, leading: 14, font: regular, colour: PDFLib.rgb(...MUTED) });
    y = drawLines(page, PDFLib, parts.summary, { x: MARGIN, top: y, size: 9.5, leading: 12, font: regular, colour: PDFLib.rgb(...MUTED) });
    y -= 6;
    y -= drawStats(page, PDFLib, stats, regular, bold, MARGIN, y, pageW - 2 * MARGIN);
    y -= BLOCK_GAP;
    y -= drawLegend(page, PDFLib, legend, regular, MARGIN, y, pageW - 2 * MARGIN);

    // map
    const box = mapBox(pageW, pageH, parts);
    const mapW = map.width * map.scale, mapH = map.height * map.scale;
    const mapX = MARGIN + (pageW - 2 * MARGIN - mapW) / 2;
    const mapY = box.bottom + (box.height - mapH) / 2;   // centre the drawing in the space left

    // force the light theme while reading the live map's computed colours
    const root = document.documentElement;
    const previousTheme = root.getAttribute("data-theme");
    root.setAttribute("data-theme", "light");
    void svg.getBoundingClientRect();
    const restoreClasses = stripClasses(svg);
    styleCache = new Map();
    try {
      const writer = makeWriter(page, PDFLib, map, { x: mapX, y: mapY + mapH });
      writer.walk(svg, IDENT, 1);
      page.drawRectangle({
        x: mapX, y: mapY, width: mapW, height: mapH,
        borderColor: PDFLib.rgb(...LINE), borderWidth: 0.5,
      });
    } finally {
      restoreClasses();
      if (previousTheme === null) root.removeAttribute("data-theme");
      else root.setAttribute("data-theme", previousTheme);
      styleCache = null;
    }

    // footer
    const footerY = MARGIN + 8;
    page.drawLine({ start: { x: MARGIN, y: MARGIN + FOOTER_H }, end: { x: pageW - MARGIN, y: MARGIN + FOOTER_H }, thickness: 0.5, color: PDFLib.rgb(...LINE) });
    const date = generated.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
    writeText(page, PDFLib, `Generated ${date} · HK Venue Seats · code.denniswu.org/hkperf-venue-seats · Not the venue's seat plan`, {
      x: MARGIN, y: footerY, size: 7.5, font: regular, color: PDFLib.rgb(...MUTED),
    });
    const pageLabel = "Page 1 of 1";
    writeText(page, PDFLib, pageLabel, { x: pageW - MARGIN - regular.widthOfTextAtSize(pageLabel, 7.5), y: footerY, size: 7.5, font: regular, color: PDFLib.rgb(...MUTED) });

    pdf.setTitle(`${doc.venue.name_en} — seat map`);
    pdf.setSubject(summary);
    pdf.setAuthor("HK Venue Seats");
    pdf.setCreator("HK Venue Seats");
    pdf.setProducer("pdf-lib");
    pdf.setCreationDate(generated);
    pdf.setModificationDate(generated);

    const bytes = await pdf.save({ useObjectStreams: true });
    const suffix = orientation === "auto" ? "" : `-${orientation}`;
    return { bytes, name: `${doc.venue.id}-seat-map-${paper}${suffix}.pdf` };
  }

  // The planner's PDF: the same map, then the ballpark, gap analysis and (optionally) the people
  // list. content() returns the figures and tables after the libraries have loaded, so a change
  // during the first download cannot mix an old map with new numbers.
  async function buildPlan({ doc, svg, summary, stats, legend, content, paper = "A3", orientation = "auto",
    generated = new Date(), onProgress, prepare, restore }) {
    const { PDFLib, fontkit } = await loadVendor();
    const [regularBytes, boldBytes] = await loadFonts();
    const data = content ? content() : { summary, stats, legend, tables: [], notes: [], userText: [] };
    if (!data) throw new Error("The plan is not ready yet.");
    if (!svg?.viewBox?.baseVal?.width || !svg.viewBox.baseVal.height) throw new Error("The seat map is not ready yet.");
    if (!svg.isConnected) throw new Error("The seat map changed while the PDF was being prepared; try again.");

    const vb = svg.viewBox.baseVal;
    const map = { minX: vb.x, minY: vb.y, width: vb.width, height: vb.height, scale: 1 };
    const pdf = await PDFLib.PDFDocument.create();
    pdf.registerFontkit(fontkit);
    const regular = await pdf.embedFont(regularBytes, { subset: false });
    const bold = await pdf.embedFont(boldBytes, { subset: false });
    const smallFk = fontkit.create(new Uint8Array(regularBytes));
    const coveredCache = new Map();
    const covered = value => {
      const text = String(value ?? "");
      if (!text) return true;
      if (coveredCache.has(text)) return coveredCache.get(text);
      let ok = true;
      for (const ch of text) if (!smallFk.hasGlyphForCodePoint(ch.codePointAt(0))) { ok = false; break; }
      coveredCache.set(text, ok);
      return ok;
    };
    let userFont = null;
    if ((data.userText || []).some(text => !covered(text))) {
      onProgress?.("Loading the full font for names…");
      const fullBytes = await loadUserFont();
      // pdf-lib's subsetter mis-maps this CJK font's glyphs, so embed the whole (6.7 MB) face,
      // once, when a plan actually needs characters outside the small subsets.
      userFont = await pdf.embedFont(fullBytes, { subset: false });
    }
    const fontFor = (value, weight) => userFont && !covered(value) ? userFont : weight >= 600 ? bold : regular;

    if (!metrics) {
      const fk = fontkit.create(new Uint8Array(regularBytes));
      metrics = { central: (fk.ascent + fk.descent) / 2 / fk.unitsPerEm, middle: (fk.xHeight || 0) / 2 / fk.unitsPerEm };
    }

    const pageFontKeys = new Map();
    function selectFonts(page) {
      const keys = pageFontKeys.get(page);
      if (!keys) return;
      regular.pdfKey = keys.regular;
      bold.pdfKey = keys.bold;
      if (userFont) userFont.pdfKey = keys.user;
    }
    function useFonts(page) {
      page.setFont(regular); const rk = page.fontKey;
      page.setFont(bold); const bk = page.fontKey;
      const keys = { regular: rk, bold: bk, user: null };
      if (userFont) { page.setFont(userFont); keys.user = page.fontKey; }
      pageFontKeys.set(page, keys);
      page.pdfFonts = { regular, bold, user: userFont };
      selectFonts(page);
      return page;
    }

    const [pw0, ph0] = PAPER[paper] || PAPER.A3;
    const candidates = orientation === "portrait" ? [{ pageW: pw0, pageH: ph0, kind: "portrait" }]
      : orientation === "landscape" ? [{ pageW: ph0, pageH: pw0, kind: "landscape" }]
      : [{ pageW: pw0, pageH: ph0, kind: "portrait" }, { pageW: ph0, pageH: pw0, kind: "landscape" }];

    const subtitleText = data.subtitle ?? [doc.venue.name_zh, "Planner"].filter(Boolean).join(" · ");
    const measured = [];
    for (const candidate of candidates) {
      const { pageW, pageH } = candidate;
      const contentW = pageW - 2 * MARGIN;
      const title = wrap(doc.venue.name_en, bold, 18, contentW);
      const subtitle = wrap(subtitleText, regular, 11, contentW);
      const summaryLines = wrap(data.summary, regular, 9.5, contentW);
      const cols = data.stats.length > 5 ? 2 : 1;
      const statsH = Math.ceil(data.stats.length / cols) * 14 + 12;
      const legendH = legendLines(data.legend, regular, contentW, fontFor).length * 14 + 6;
      const parts = { title, subtitle, summary: summaryLines, statsH, legendH };
      measured.push({ ...candidate, parts, scale: fitScale(parts, pageW, pageH, map) });
    }
    let chosen = measured.reduce((a, b) => b.scale > a.scale ? b : a);
    if (orientation === "auto") {
      const preferred = map.width > map.height ? "landscape" : "portrait";
      const candidate = measured.find(c => c.kind === preferred);
      if (candidate && candidate.scale >= chosen.scale * 0.95) chosen = candidate;
    }
    if (chosen.scale <= 0) throw new Error("The plan does not fit on that page.");
    const { pageW, pageH, parts } = chosen;
    map.scale = chosen.scale;

    const page1 = useFonts(pdf.addPage([pageW, pageH]));
    page1.drawRectangle({ x: 0, y: 0, width: pageW, height: pageH, color: PDFLib.rgb(1, 1, 1) });
    let y = pageH - MARGIN;
    y = drawLines(page1, PDFLib, parts.title, { x: MARGIN, top: y, size: 18, leading: 22, font: bold, colour: PDFLib.rgb(...INK) });
    y = drawLines(page1, PDFLib, parts.subtitle, { x: MARGIN, top: y, size: 11, leading: 14, font: regular, colour: PDFLib.rgb(...MUTED) });
    y = drawLines(page1, PDFLib, parts.summary, { x: MARGIN, top: y, size: 9.5, leading: 12, font: regular, colour: PDFLib.rgb(...MUTED) });
    y -= 6;
    y -= drawStats(page1, PDFLib, data.stats, regular, bold, MARGIN, y, pageW - 2 * MARGIN, fontFor);
    y -= BLOCK_GAP;
    y -= drawLegend(page1, PDFLib, data.legend, regular, MARGIN, y, pageW - 2 * MARGIN, fontFor);

    const box = mapBox(pageW, pageH, parts);
    const mapW = map.width * map.scale, mapH = map.height * map.scale;
    const mapX = MARGIN + (pageW - 2 * MARGIN - mapW) / 2;
    const mapY = box.bottom + (box.height - mapH) / 2;

    const root = document.documentElement;
    const previousTheme = root.getAttribute("data-theme");
    root.setAttribute("data-theme", "light");
    void svg.getBoundingClientRect();
    const restoreClasses = stripClasses(svg);
    styleCache = new Map();
    try {
      prepare?.();
      const writer = makeWriter(page1, PDFLib, map, { x: mapX, y: mapY + mapH }, fontFor);
      writer.walk(svg, IDENT, 1);
      page1.drawRectangle({
        x: mapX, y: mapY, width: mapW, height: mapH,
        borderColor: PDFLib.rgb(...LINE), borderWidth: 0.5,
      });
    } finally {
      restore?.();
      restoreClasses();
      if (previousTheme === null) root.removeAttribute("data-theme");
      else root.setAttribute("data-theme", previousTheme);
      styleCache = null;
    }

    const pages = [page1];
    const width = pageW - 2 * MARGIN;
    const bottom = MARGIN + FOOTER_H + 8;
    let page = null;
    let cy = 0;

    function tableLayout(spec) {
      const columns = spec.columns || [];
      const weights = spec.weights || columns.map(() => 1);
      const total = weights.reduce((a, b) => a + b, 0) || 1;
      const widths = weights.map(w => width * w / total);
      const xs = widths.map((_, i) => MARGIN + widths.slice(0, i).reduce((a, b) => a + b, 0));
      return { columns, widths, xs, aligns: spec.aligns || columns.map(() => "left") };
    }
    function rowLayout(row, layout) {
      const cells = layout.columns.map((_, i) => {
        const value = String(row[i] ?? "");
        const font = fontFor(value, 400);
        const lines = wrap(value, font, 8.5, Math.max(8, layout.widths[i] - 4));
        return { lines, font };
      });
      return { cells, height: Math.max(1, ...cells.map(c => c.lines.length)) * 10.5 + 4 };
    }
    function drawHeader(spec, layout) {
      layout.columns.forEach((label, i) => {
        const w = bold.widthOfTextAtSize(label, 8.5);
        const x = layout.xs[i] + (layout.aligns[i] === "right" ? layout.widths[i] - 2 - w : 2);
        writeText(page, PDFLib, label, { x, y: cy - 10, size: 8.5, font: bold, color: PDFLib.rgb(...MUTED) });
      });
      page.drawLine({ start: { x: MARGIN, y: cy }, end: { x: pageW - MARGIN, y: cy }, thickness: 0.6, color: PDFLib.rgb(...LINE) });
      cy -= 15;
    }
    function startPage(title, continued, spec) {
      page = useFonts(pdf.addPage([pageW, pageH]));
      page.drawRectangle({ x: 0, y: 0, width: pageW, height: pageH, color: PDFLib.rgb(1, 1, 1) });
      pages.push(page);
      cy = pageH - MARGIN;
      writeText(page, PDFLib, `${doc.venue.name_en} · Planner`, { x: MARGIN, y: cy - 8, size: 8.5, font: regular, color: PDFLib.rgb(...MUTED) });
      cy -= 20;
      writeText(page, PDFLib, title + (continued ? " (continued)" : ""), { x: MARGIN, y: cy - 12, size: 12, font: bold, color: PDFLib.rgb(...INK) });
      cy -= 20;
      if (spec) drawHeader(spec, spec.layout);
    }

    for (const spec of data.tables || []) {
      spec.layout = tableLayout(spec);
      const firstHeight = spec.rows.length ? rowLayout(spec.rows[0], spec.layout).height : 0;
      if (!page || cy - (20 + 15 + firstHeight) < bottom) {
        startPage(spec.title, false, spec);
      } else {
        cy -= 12;
        writeText(page, PDFLib, spec.title, { x: MARGIN, y: cy - 12, size: 12, font: bold, color: PDFLib.rgb(...INK) });
        cy -= 20;
        drawHeader(spec, spec.layout);
      }
      for (const row of spec.rows) {
        const layout = rowLayout(row, spec.layout);
        if (cy - layout.height < bottom) startPage(spec.title, true, spec);
        layout.cells.forEach((cell, i) => {
          cell.lines.forEach((line, k) => {
            const w = cell.font.widthOfTextAtSize(line, 8.5);
            const tx = spec.layout.xs[i] + (spec.layout.aligns[i] === "right" ? spec.layout.widths[i] - 2 - w : 2);
            writeText(page, PDFLib, line, { x: tx, y: cy - 10 - k * 10.5, size: 8.5, font: cell.font, color: PDFLib.rgb(...INK) });
          });
        });
        cy -= layout.height;
        page.drawLine({ start: { x: MARGIN, y: cy }, end: { x: pageW - MARGIN, y: cy }, thickness: 0.4, color: PDFLib.rgb(...LINE) });
      }
    }

    const notes = data.notes || [];
    if (notes.length) {
      const noteLines = notes.flatMap(note => wrap(note, regular, 8.5, width));
      const height = noteLines.length * 11 + 18;
      if (!page || cy - height < bottom) startPage("Notes", false, null);
      else {
        cy -= 12;
        writeText(page, PDFLib, "Notes", { x: MARGIN, y: cy - 12, size: 12, font: bold, color: PDFLib.rgb(...INK) });
        cy -= 20;
      }
      for (const line of noteLines) {
        writeText(page, PDFLib, line, { x: MARGIN, y: cy - 9, size: 8.5, font: regular, color: PDFLib.rgb(...MUTED) });
        cy -= 11;
      }
    }

    const totalPages = pages.length;
    pages.forEach((p, i) => {
      selectFonts(p);
      p.drawLine({ start: { x: MARGIN, y: MARGIN + FOOTER_H }, end: { x: pageW - MARGIN, y: MARGIN + FOOTER_H }, thickness: 0.5, color: PDFLib.rgb(...LINE) });
      const date = generated.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
      writeText(p, PDFLib, `Generated ${date} · HK Venue Seats planner · Not the venue's seat plan`,
        { x: MARGIN, y: MARGIN + 13, size: 7.5, font: regular, color: PDFLib.rgb(...MUTED) });
      const pageLabel = `Page ${i + 1} of ${totalPages}`;
      writeText(p, PDFLib, pageLabel, {
        x: pageW - MARGIN - regular.widthOfTextAtSize(pageLabel, 7.5), y: MARGIN + 13,
        size: 7.5, font: regular, color: PDFLib.rgb(...MUTED),
      });
      writeText(p, PDFLib, data.namesIncluded ? "Contains names you entered." : "Seat data CC BY 4.0.",
        { x: MARGIN, y: MARGIN + 4, size: 7, font: regular, color: PDFLib.rgb(...(data.namesIncluded ? [0.7, 0.15, 0.12] : MUTED)) });
    });

    pdf.setTitle(`${doc.venue.name_en} — plan`);
    pdf.setSubject(data.summary);
    pdf.setAuthor("HK Venue Seats");
    pdf.setCreator("HK Venue Seats");
    pdf.setProducer("pdf-lib");
    pdf.setCreationDate(generated);
    pdf.setModificationDate(generated);

    const bytes = await pdf.save({ useObjectStreams: true });
    const suffix = orientation === "auto" ? "" : `-${orientation}`;
    return { bytes, name: `${doc.venue.id}-plan-${paper}${suffix}.pdf` };
  }

  return { build, buildPlan };
})();
