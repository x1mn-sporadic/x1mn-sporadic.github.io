/* x1mn-sporadic: static front end.  Reads data/curves.json and data/points.json (built by
   pipeline/build.py on Mordell) and renders the census.  No framework, no build step. */
(function () {
  "use strict";

  const REPO = "https://github.com/x1mn-sporadic/x1mn-sporadic.github.io";
  const ISSUE_FORM = REPO + "/issues/new?template=submit-point.yml";
  const pageName = document.body.dataset.page || "";

  // ---------------------------------------------------------------- utilities
  const $ = (sel, root) => (root || document).querySelector(sel);
  const el = (tag, attrs, ...children) => {
    const node = document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") node.className = v;
      else if (k === "html") node.innerHTML = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else if (v !== null && v !== undefined) node.setAttribute(k, v);
    }
    for (const c of children.flat(Infinity)) {
      if (c === null || c === undefined) continue;
      node.append(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return node;
  };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const params = new URLSearchParams(location.search);
  const cache = {};
  async function load(name) {
    if (!cache[name]) {
      cache[name] = fetch("data/" + name + ".json", { cache: "no-cache" }).then((r) => {
        if (!r.ok) throw new Error("could not load data/" + name + ".json (" + r.status + ")");
        return r.json();
      });
    }
    return cache[name];
  }

  // Polynomials and field elements as Magma prints them -> readable HTML (x^3 - 3*x^2 + 3 -> x³ − 3x² + 3).
  const SUP = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
  function math(s) {
    if (s === null || s === undefined || s === "") return "";
    let t = esc(String(s));
    t = t.replace(/\^(\d+)/g, (_, d) => d.split("").map((c) => SUP[c]).join(""));
    t = t.replace(/(\d|\))\*([a-zA-Zζ(])/g, "$1$2");   // 3*x -> 3x, (..)*a -> (..)a
    t = t.replace(/\*/g, "·");
    t = t.replace(/(^|[\s(])-/g, "$1−").replace(/ - /g, " − ");
    t = t.replace(/X_1/g, "X₁").replace(/J_1/g, "J₁").replace(/zeta_(\d+)/g, "ζ$1").replace(/gon_Q/g, "gon<sub>ℚ</sub>").replace(/\bQ\b/g, "ℚ");
    return '<span class="m">' + t + "</span>";
  }
  const curveLabel = (m, n) => (m === 1 ? "X₁(" + n + ")" : "X₁(" + m + "," + n + ")");
  const curveLabelLong = (m, n) => "X₁(" + m + "," + n + ")";
  const torsionLabel = (m, n) => (m === 1 ? "ℤ/" + n : "ℤ/" + m + " ⊕ ℤ/" + n);
  const chip = (status) => {
    const text = { certified: "certified", verified: "verified · undecided", rejected: "rejected" }[status] || status;
    return el("span", { class: "chip " + status }, text);
  };
  // yes / no / maybe answer chip; `good` says which answer is the interesting one (green)
  const ans = (a, good, title) => {
    const v = typeof a === "string" ? a : a.value;
    const cls = v === good ? "yes" : v === "maybe" ? "maybe" : "no";
    return el("span", { class: "ans " + cls, title: title || (typeof a === "string" ? "" : a.rule) }, v);
  };
  const discovery = (by, year) => (by ? by + (year ? " (" + year + ")" : "") : (year ? String(year) : "—"));

  function prefillIssue(m, n) {
    const u = new URL(ISSUE_FORM);
    if (m) u.searchParams.set("m", m);
    if (n) u.searchParams.set("n", n);
    u.searchParams.set("title", "Sporadic point on X1(" + (m || "m") + "," + (n || "n") + ")");
    return u.toString();
  }

  // ---------------------------------------------------------------- header / footer
  function chrome() {
    const nav = [["index.html", "curves", "index"], ["submit.html", "submit a point", "submit"],
                 ["about.html", "about & sources", "about"], [REPO, "github", ""]];
    const header = el("header", { class: "site" },
      el("div", { class: "inner" },
        el("h1", null, el("a", { href: "index.html" }, "Sporadic points on X₁(m,n)")),
        el("nav", null, nav.map(([href, label, key]) =>
          el("a", { href, "aria-current": key && key === pageName ? "page" : null,
                    target: href.startsWith("http") ? "_blank" : null, rel: href.startsWith("http") ? "noopener" : null }, label)))));
    document.body.prepend(header);
    const footer = el("footer", { class: "site" },
      el("div", { class: "links" },
        el("a", { href: "index.html" }, "curves"), el("span", { class: "sep" }, "·"),
        el("a", { href: "submit.html" }, "submit"), el("span", { class: "sep" }, "·"),
        el("a", { href: "about.html" }, "about & sources"), el("span", { class: "sep" }, "·"),
        el("a", { href: "data/points.json" }, "all points (JSON)"), el("span", { class: "sep" }, "·"),
        el("a", { href: "data/curves.json" }, "all curves (JSON)"), el("span", { class: "sep" }, "·"),
        el("a", { href: REPO, target: "_blank", rel: "noopener" }, "source & data on GitHub")),
      el("div", null,
        "Submissions are verified with Magma on the Mordell workstation of the Department of Mathematics, ",
        "University of Zagreb, and stored with their verification logs in the GitHub repository. ",
        "Please cite the original references of the points you use."));
    document.body.append(footer);
  }

  // ---------------------------------------------------------------- sortable tables
  function makeSortable(table) {
    const ths = table.querySelectorAll("thead th.sortable");
    ths.forEach((th, idx) => th.addEventListener("click", () => {
      const asc = !(th.classList.contains("sorted") && th.classList.contains("asc"));
      ths.forEach((t) => t.classList.remove("sorted", "asc"));
      th.classList.add("sorted"); if (asc) th.classList.add("asc");
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      const key = (r) => { const c = r.cells[idx]; const v = c.dataset.sort !== undefined ? c.dataset.sort : c.textContent.trim(); const f = parseFloat(v); return isNaN(f) ? v : f; };
      rows.sort((a, b) => { const x = key(a), y = key(b); return (x < y ? -1 : x > y ? 1 : 0) * (asc ? 1 : -1); });
      rows.forEach((r) => tbody.append(r));
    }));
  }

  // ---------------------------------------------------------------- index page
  function degChips(map, cls, sources) {
    const ds = Object.keys(map).filter((k) => k !== "all").map(Number).sort((a, b) => a - b);
    if (map.all) return el("span", { class: "degs" }, el("span", { class: "d " + cls }, "all"));
    return el("span", { class: "degs" }, ds.map((d) => el("span", { class: "d " + cls, title: shortSource(sources, map[d]) }, d)));
  }

  async function renderIndex() {
    const [data, srcData] = await Promise.all([load("curves"), load("sources")]);
    const sources = srcData.sources;
    $("#stat-curves").textContent = data.n_curves;
    $("#stat-certified").textContent = data.n_certified;
    $("#stat-sporadic").textContent = data.n_sporadic;
    $("#stat-isolated").textContent = data.n_isolated;
    $("#stat-verified").textContent = data.n_verified;
    $("#stat-generated").textContent = data.generated;
    const tbody = $("#curves tbody");
    const hideG0 = $("#hide-genus0"), onlyPts = $("#only-points");
    function draw() {
      tbody.innerHTML = "";
      let lastM = null;
      for (const c of data.curves) {
        if (hideG0.checked && c.genus === 0) continue;
        if (onlyPts.checked && c.points.length === 0) continue;
        if (c.m !== lastM) {
          lastM = c.m;
          const head = c.m === 1 ? "m = 1 — X₁(n), torsion ℤ/n, defined over ℚ"
            : c.m === 2 ? "m = 2 — X₁(2,n), torsion ℤ/2 ⊕ ℤ/n, defined over ℚ"
            : "m = " + c.m + " — X₁(" + c.m + ",n), torsion ℤ/" + c.m + " ⊕ ℤ/n, defined over ℚ(ζ" + String(c.m).split("").map((x) => "₀₁₂₃₄₅₆₇₈₉"[x]).join("") + ")";
          tbody.append(el("tr", { class: "group" }, el("th", { colspan: 8 }, head)));
        }
        const gon = c.gonality.exact ? String(c.gonality.lb) : c.gonality.ub ? c.gonality.lb + "–" + c.gonality.ub : "≥ " + c.gonality.lb;
        const gonTitle = c.gonality.exact ? "gonality over " + c.base_field + " (" + shortSource(sources, c.gonality.source) + ")"
          : "lower bound: " + shortSource(sources, c.gonality.lb_source) + (c.gonality.ub ? "; upper bound: " + shortSource(sources, c.gonality.ub_source) : "");
        const rank = c.rank.value !== null ? String(c.rank.value) : c.rank.analytic_rank !== undefined ? "(" + c.rank.analytic_rank + ")" : "?";
        const href = "curve.html?m=" + c.m + "&n=" + c.n;
        const tr = el("tr", { class: "row-link" + (c.genus === 0 ? " dim" : ""), onclick: (e) => { if (e.target.tagName !== "A") location.href = href; } },
          el("td", null, el("a", { href, class: "id" }, curveLabel(c.m, c.n))),
          el("td", { class: "num" }, c.genus),
          el("td", { class: "num", title: gonTitle }, gon),
          el("td", { class: "num", title: c.rank.source ? shortSource(sources, c.rank.source.split("+")[0]) : "rank not recorded" }, rank),
          el("td", null, c.genus === 0 ? el("span", { class: "empty" }, "—") : degChips(c.degrees_finite, "fin", sources)),
          el("td", null, degChips(c.degrees_infinite, "inf", sources)),
          el("td", { class: "num", "data-sort": c.n_certified + c.n_verified }, c.points.length
            ? [el("b", null, c.points.length), el("span", { class: "muted", title: "sporadic / isolated / undecided" },
                 " (" + c.n_sporadic + " sp · " + c.n_isolated + " iso" + (c.n_verified ? " · " + c.n_verified + " ?" : "") + ")")] : ""),
          el("td", { class: "num" }, c.degrees_present.length ? c.degrees_present.join(", ") : ""));
        tbody.append(tr);
      }
    }
    hideG0.addEventListener("change", draw); onlyPts.addEventListener("change", draw);
    draw();
    loadPending();
  }

  async function loadPending() {
    const box = $("#pending");
    if (!box) return;
    try {
      const r = await fetch("https://api.github.com/repos/x1mn-sporadic/x1mn-sporadic.github.io/issues?labels=submission&state=open&per_page=100");
      if (!r.ok) return;
      const issues = (await r.json()).filter((i) => !i.pull_request);
      if (issues.length) {
        box.innerHTML = "";
        box.append(el("a", { href: REPO + "/issues?q=is%3Aissue+is%3Aopen+label%3Asubmission" },
          issues.length + " submission" + (issues.length > 1 ? "s" : "") + " awaiting verification"));
      }
    } catch (e) { /* offline or rate-limited: say nothing */ }
  }

  // ---------------------------------------------------------------- curve page
  // citations: a source key (or "key1+key2") -> short labels linked to the sources list
  function sourceLinks(sources, keys) {
    const out = [];
    const flat = [];
    (keys || []).filter(Boolean).forEach((k) => k.split("+").forEach((kk) => { if (!flat.includes(kk)) flat.push(kk); }));
    flat.forEach((k, i) => {
      if (i) out.push(", ");
      const s = sources[k];
      out.push(s ? el("a", { href: "about.html#src-" + k, title: s.cite }, s.short || k) : k);
    });
    return out;
  }
  const shortSource = (sources, k) => (sources[k] && sources[k].short) || k;

  async function renderCurve() {
    const m = parseInt(params.get("m"), 10), n = parseInt(params.get("n"), 10);
    const [data, srcData] = await Promise.all([load("curves"), load("sources")]);
    const sources = srcData.sources;
    const c = data.curves.find((x) => x.m === m && x.n === n);
    const title = $("#title");
    if (!c) { title.textContent = "Unknown curve"; $("#facts").append(el("p", { class: "error" }, "X₁(" + m + "," + n + ") is not in the census.")); return; }
    document.title = curveLabel(m, n) + " — Sporadic points on X₁(m,n)";
    title.textContent = curveLabelLong(m, n) + (m === 1 ? " = X₁(" + n + ")" : "");
    $("#subtitle").innerHTML = "Elliptic curves with a point of order " + n + (m > 1 ? " and full " + m + "-torsion: torsion subgroup containing " + torsionLabel(m, n) : "") +
      ". Defined over " + (m <= 2 ? "ℚ" : "ℚ(ζ<sub>" + m + "</sub>)") + ".";
    const gon = c.gonality;
    const facts = el("dl", { class: "facts" },
      el("dt", null, "genus"), el("dd", null, el("b", null, c.genus)),
      el("dt", null, "index in PSL₂(ℤ)"), el("dd", null, el("b", null, c.index)),
      el("dt", null, "gonality over " + (m <= 2 ? "ℚ" : "ℚ(ζ" + m + ")")),
      el("dd", null, el("b", null, gon.exact ? String(gon.lb) : (gon.ub ? gon.lb + " ≤ γ ≤ " + gon.ub : "γ ≥ " + gon.lb)), " ",
        el("span", { class: "src" }, "(", gon.exact ? sourceLinks(sources, [gon.source])
          : ["lower bound: ", sourceLinks(sources, [gon.lb_source]), gon.ub ? ["; upper bound: ", sourceLinks(sources, [gon.ub_source])] : null],
          c.table_note && (gon.lb_source === "Najman2026" || gon.source === "Najman2026") ? "; " + c.table_note : "", ")")),
      el("dt", null, "Abramovich bound"), el("dd", null, "γ ≥ " + c.abramovich_bound, " ", el("span", { class: "src" }, "(", sourceLinks(sources, ["Abramovich96"]), ")")),
      el("dt", null, "rank of J₁ over " + (m <= 2 ? "ℚ" : "ℚ(ζ" + m + ")")),
      el("dd", null, c.rank.value === null
        ? (c.rank.analytic_rank !== undefined ? ["analytic rank ", el("b", null, c.rank.analytic_rank), " ", el("span", { class: "src" }, "(", sourceLinks(sources, [c.rank.analytic_rank_source || "LMFDB"]), "; a positive rank is not certified here)")] : el("span", { class: "empty" }, "not recorded"))
        : [el("b", null, c.rank.value), " ", el("span", { class: "src" }, "(", sourceLinks(sources, c.rank.source.split("+")), ")")]),
      el("dt", null, "finitely many points in degree"),
      el("dd", null, Object.keys(c.degrees_finite).length ? Object.entries(c.degrees_finite).sort((a, b) => a[0] - b[0]).map(([d, s], i) => [i ? ", " : "", el("b", null, d), " ", el("span", { class: "src" }, "(", sourceLinks(sources, [s]), ")")]) : el("span", { class: "empty" }, "nothing recorded")),
      el("dt", null, "infinitely many points in degree"),
      el("dd", null, Object.keys(c.degrees_infinite).length ? Object.entries(c.degrees_infinite).sort((a, b) => (a[0] === "all" ? -1 : a[0] - b[0])).map(([d, s], i) => [i ? ", " : "", el("b", null, d), " ", el("span", { class: "src" }, "(", sourceLinks(sources, [s]), ")")]) : el("span", { class: "empty" }, "nothing recorded")));
    $("#facts").append(facts);
    if (c.genus === 0) $("#facts").append(el("p", { class: "notice" }, "Genus 0: every degree has infinitely many points, so there are no sporadic points on this curve."));
    if (m >= 3) $("#facts").append(el("p", { class: "notice" }, "For m ≥ 3 the degree of a point is its absolute degree [ℚ(x):ℚ]; it is a multiple of φ(" + m + ") = " + c.base_field_degree + ", and the degree over ℚ(ζ" + m + ") is the quotient. Only Abramovich's bound is recorded for the gonality over ℚ(ζ" + m + ")."));
    $("#submit-link").href = prefillIssue(m, n);
    const tbody = $("#points tbody");
    if (!c.points.length) {
      tbody.append(el("tr", null, el("td", { colspan: 9, class: "empty" }, "No points recorded yet.")));
    }
    for (const p of c.points) {
      const href = "point.html?id=" + encodeURIComponent(p.id);
      tbody.append(el("tr", { class: "row-link", onclick: (e) => { if (e.target.tagName !== "A") location.href = href; } },
        el("td", null, el("a", { href, class: "id" }, p.id)),
        el("td", { class: "num" }, p.degree),
        el("td", { class: "poly", html: math(p.field_poly) }),
        el("td", { class: "num", "data-sort": p.j_degree, title: "discriminant of the residue field: " + p.field_disc },
          p.j_rational ? el("span", { class: "m" }, p.j_rational) : String(p.j_degree), p.cm ? el("span", { class: "muted" }, " CM") : ""),
        el("td", null, p.torsion_known ? torsionLabelInv(p.torsion) : "⊇ " + torsionLabel(m, n)),
        el("td", { "data-sort": p.sporadic }, ans(p.sporadic, "yes", p.rules.sporadic)),
        el("td", { "data-sort": p.isolated }, ans(p.isolated, "yes", p.rules.isolated)),
        el("td", { "data-sort": p.infinite }, ans(p.infinite, "no", p.rules.infinite_in_degree)),
        el("td", { "data-sort": p.year || 0 }, discovery(p.discovered_by, p.year))));
    }
    makeSortable($("#points"));
  }
  const torsionLabelInv = (inv) => (inv.length === 1 ? "ℤ/" + inv[0] : inv.map((x) => "ℤ/" + x).join(" ⊕ "));

  // ---------------------------------------------------------------- point page
  async function renderPoint() {
    const id = params.get("id");
    const [pts, srcData, curves] = await Promise.all([load("points"), load("sources"), load("curves")]);
    const sources = srcData.sources;
    const p = pts.points.find((x) => x.id === id);
    if (!p) { $("#title").textContent = "Unknown point"; $("#body").append(el("p", { class: "error" }, "No point with id " + esc(id) + " in the census.")); return; }
    const c = curves.curves.find((x) => x.m === p.m && x.n === p.n) || {};
    document.title = p.id + " — Sporadic points on X₁(m,n)";
    $("#title").textContent = "Point " + p.id;
    $("#subtitle").innerHTML = "A point of degree <b>" + p.degree + "</b> on " + curveLabel(p.m, p.n) +
      (p.m >= 3 ? " (degree " + p.relative_degree + " over " + p.base_field.replace("zeta_", "ζ") + ")" : "") + ".";
    $("#crumb-curve").textContent = curveLabel(p.m, p.n);
    $("#crumb-curve").href = "curve.html?m=" + p.m + "&n=" + p.n;
    $("#json-link").href = "data/points/" + p.id + ".json";
    $("#log-link").href = p.verification.log;
    const body = $("#body");

    // status panel: the three questions
    const cl = p.classification;
    const answerRow = (label, a, good) => [
      el("dt", null, label),
      el("dd", null, ans(a, good, ""), " ", el("span", { html: math(a.rule) }),
        a.sources && a.sources.length ? [" ", el("span", { class: "src" }, "(", sourceLinks(sources, a.sources), ")")] : null)];
    body.append(el("div", { class: "panel " + (p.status === "certified" ? "accepted" : "open") },
      el("h3", null, chip(p.status)),
      el("dl", { class: "facts" },
        answerRow("sporadic", cl.sporadic, "yes"),
        answerRow("isolated", cl.isolated, "yes"),
        answerRow("infinitely many points of degree " + p.degree, cl.infinite_in_degree, "no"),
        el("dt", null, "discovered by"), el("dd", null, discovery(p.discovery.by, p.discovery.year))),
      p.reference ? el("p", { class: "wide" }, el("b", null, "Reference: "), p.reference) : null,
      p.notes ? el("p", { class: "wide" }, el("b", null, "Notes: "), p.notes) : null));

    // the point
    const rf = p.field, cv = p.curve;
    body.append(el("h3", null, "The point"),
      el("p", { class: "wide" }, "Let a be a root of the polynomial below and K = ℚ(a), the residue field of the point. The elliptic curve is given in Tate normal form, so that Q = (0,0) has order " + p.n + "."),
      el("dl", { class: "facts" },
        el("dt", null, "field K"), el("dd", { class: "poly", html: math(rf.poly) + " = 0" }),
        el("dt", null, "polredabs"), el("dd", { class: "poly", html: math(rf.polredabs || "—") }),
        el("dt", null, "discriminant"), el("dd", { html: "<b>" + esc(rf.disc) + "</b> = " + math(rf.disc_factored) }),
        el("dt", null, "signature"), el("dd", null, "(" + rf.signature.join(", ") + ")"),
        el("dt", null, "b"), el("dd", { class: "poly", html: math(cv.tate_b) }),
        el("dt", null, "c"), el("dd", { class: "poly", html: math(cv.tate_c) }),
        el("dt", null, "E"), el("dd", { class: "poly", html: "y² + (1 − c)xy − by = x³ − bx²" }),
        el("dt", null, "Q (order " + p.n + ")"), el("dd", { class: "poly" }, "(0, 0)"),
        p.m > 1 ? el("dt", null, "P (order " + p.m + ")") : null,
        p.m > 1 ? el("dd", { class: "poly", html: "(" + math(cv.P[0]) + ", " + math(cv.P[1]) + ")" }) : null,
        el("dt", null, "E(K)ₜₒᵣₛ"), el("dd", null, p.torsion.known_exactly ? el("b", null, torsionLabelInv(p.torsion.invariants)) :
          ["contains " + torsionLabel(p.m, p.n) + "; its order divides " + p.torsion.order_bound + " (not determined exactly)"]),
        el("dt", null, "j-invariant"), el("dd", { class: "poly", html: cv.j_rational ? math(cv.j_rational) : "degree " + cv.j_degree + ", minimal polynomial " + math(cv.j_minpoly) }),
        el("dt", null, "CM"), el("dd", null, cv.cm ? "yes, discriminant " + cv.cm_disc : "no"),
        el("dt", null, "norm of Δ(E)"), el("dd", null, cv.disc_norm),
        cv.conductor_norm ? el("dt", null, "norm of the conductor") : null,
        cv.conductor_norm ? el("dd", null, cv.conductor_norm) : null));

    // Magma snippet
    const magma = [
      "Qx<x> := PolynomialRing(Rationals());",
      "K<a> := NumberField(" + rf.poly + ");",
      "b := " + cv.tate_b + ";",
      "c := " + cv.tate_c + ";",
      "E := EllipticCurve([1-c, -b, -b, 0, 0]);",
      "Q := E![0, 0];  assert Order(Q) eq " + p.n + ";",
      p.m > 1 ? "P := E![" + cv.P[0] + ", " + cv.P[1] + "];  assert Order(P) eq " + p.m + ";" : null,
      "TorsionSubgroup(E);"].filter(Boolean).join("\n");
    body.append(el("h3", null, "Reproduce in Magma"), el("pre", null, el("code", null, magma)));

    // submission & verification
    const sub = p.submitted;
    body.append(el("h3", null, "Submission and verification"),
      el("dl", { class: "facts" },
        el("dt", null, "submitted by"), el("dd", null, [p.submitter.name, p.submitter.affiliation, p.submitter.github ? "@" + p.submitter.github : ""].filter(Boolean).join(", ")),
        el("dt", null, "submitted"), el("dd", null, p.dates.submitted || "—"),
        el("dt", null, "submitted as"), el("dd", null, sub.mode === "vanhoeij" ? "van Hoeij format: eqx = " : sub.mode === "tate" ? "Tate normal form (b, c) over " : "a-invariants over ",
          el("span", { class: "m", html: math(sub.field.poly) }),
          sub.mode === "vanhoeij" ? [", eqxy = ", el("span", { class: "m", html: math(sub.curve.eqxy) })] : null,
          sub.residue_field_equals_submitted_field ? "" : " (the point is defined over a proper subfield of the submitted field)"),
        el("dt", null, "source"), el("dd", null, p.source.kind === "issue" ? el("a", { href: REPO + "/issues/" + p.source.number }, "issue #" + p.source.number)
          : p.source.kind === "import" ? [p.source.file + ", line " + p.source.line + " ", el("a", { href: p.source.url }, "(original)")] : (p.source.path || "file")),
        el("dt", null, "verified"), el("dd", null, p.dates.verified + " on " + p.verification.host),
        el("dt", null, "software"), el("dd", null, "Magma " + p.verification.magma_version + ", " + p.verification.cputime_seconds + " s CPU; verify_lib.m sha256 " + p.verification.verify_lib_sha256.slice(0, 12) + "…"),
        el("dt", null, "isolation check"), el("dd", null, p.isolation && p.isolation.computed
          ? ["dim L(x mod q) = " + p.isolation.l_values.join(", ") + " for q = " + p.isolation.primes.join(", ") + " on " + p.isolation.model +
             (p.isolation.p1_isolated ? " — so dim L(x) = 1 over ℚ by upper semicontinuity: P¹-isolated" : " — P¹-isolation not established") +
             " (" + p.isolation.cputime_seconds + " s; ", el("a", { href: p.verification.isolation_log }, "log"), ")"]
          : "not computed" + (p.isolation && p.isolation.note ? " (" + p.isolation.note + ")" : "")),
        el("dt", null, "checks"), el("dd", null, "K is a number field of degree " + rf.degree + "; E is an elliptic curve over K; Q has exact order " + p.n +
          (p.m > 1 ? ", P has exact order " + p.m + " and ⟨P,Q⟩ ≅ " + torsionLabel(p.m, p.n) : "") +
          "; |E(K)ₜₒᵣₛ| divides " + p.torsion.order_bound + " (reductions modulo primes above " + p.torsion.bound_primes.join(", ") + ")" +
          "; the Tate normal form of (E,Q) and the residue field ℚ(b, c" + (p.m > 1 ? ", x(P), y(P)" : "") + ") of the point were recomputed, and its degree is " + p.degree + ".")));
  }

  // ---------------------------------------------------------------- about page: sources
  async function renderAbout() {
    const srcData = await load("sources");
    const ul = $("#sources");
    for (const [k, s] of Object.entries(srcData.sources)) {
      ul.append(el("li", { id: "src-" + k }, el("b", null, s.short || k), " — ", s.cite, s.used_for ? el("span", { class: "muted" }, " Used for: " + s.used_for + ".") : null));
    }
    const curves = await load("curves");
    $("#generated").textContent = curves.generated;
  }

  // ---------------------------------------------------------------- boot
  chrome();
  const sl = $("#submit-any");
  if (sl) sl.href = prefillIssue();
  const run = { index: renderIndex, curve: renderCurve, point: renderPoint, about: renderAbout }[pageName];
  if (run) run().catch((e) => {
    const main = $("main");
    main.append(el("p", { class: "error" }, "Could not load the census data: " + e.message));
  });
})();
