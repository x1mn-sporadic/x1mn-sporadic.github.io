# Literature check of the census (2026-09-18)

Question: does the literature contain isolated/sporadic points on X_1(m,n) that the census
(146 points, 2026-09-18 build) does not have?  Everything below was checked against the cited
document on 2026-09-18 (downloaded copies in the session scratchpad); nothing is from memory.
"Missing" always means: not in `data/points/`.

## 1. Certified-quality points that are missing

### 1.1  X_1(37), degree 18, j = -7·137^3·2083^3 = -162677523113838677  (isolated, not sporadic)
* Curve 1225.h2 (Cremona 1225h2), the second non-CM rational point of X_0(37).  The kernel
  polynomial of its 37-isogeny is irreducible of degree 18, so the point on X_1(37) has degree 18
  (the -9317 curve gives degree 6 = point 1.37.6.a).
* P^1-isolated: Bourdon–Hashimoto–Keller–Klagsbrun–Lowry-Duda–Morrison–Najman–Shukla,
  *Towards a classification of isolated j-invariants*, Math. Comp. 94 (2025) 447–473,
  arXiv:2311.07740, §9.0.1 (ℓ(D̄)=1 mod 3).  AV-isolated: Theorem 48 of the appendix by
  Derickx–van Hoeij (formal immersion through X_1(37) → X_0(37) → X_0^+(37)).  Remark 3 there:
  "we did not find a result in the literature showing the degree 18 point ... is P^1-isolated,
  [but] the point itself was well-known" (BELOV Adv. Math. 2019, proof of Thm 8.1; Sutherland's
  2012 notes §4; Ejder RNT 2022 Remark 1.3).  Bourdon–Ejder arXiv:2506.19560 Theorem 4 restates:
  the two j's "give rise to isolated points on X_1(37) of degrees 6 and 18".
* Not sporadic: degree 18 = gon_Q X_1(37) (Derickx–van Hoeij).  So under the census rules it is
  a certified *isolated* point in a degree with infinitely many points, like 1.28.9.a.
* Ready-to-submit data (computed here with Sage, `2026-09-18-x1_37_deg18.sage`, checked:
  37·Q = 0, Q ≠ 0, j correct): `2026-09-18-x1_37_deg18_submission.json` — the quadratic twist of
  1225h2 by D = x0^3 + A4 x0 + A6 over K = Q(x0), K totally real of degree 18, disc 5^9·7^12·37^17,
  Q = (D x0, D^2).  Not yet run through the pipeline (copy to `submissions/inbox/` to do so).
  The isolation check of the pipeline will presumably reproduce ℓ = 1 (the paper used p = 3);
  the AV-isolation needs a knowledge entry (rank J_1(37)(Q) > 0, so the automatic rule gives
  "maybe"): add BHKKLMNS Thm 48 as a curated fact for this point.

### 1.2  van Hoeij's list beyond N = 40
* The seed copy `data/knowledge/sources/vanhoeij_LowDegreePlaces.txt` is byte-identical to the
  current file on van Hoeij's site (3152631 bytes, 2014-06-21) and **contains N = 41..60**
  (5,370 places) — `import_vanhoeij.py --max-N 40` simply stopped at 40.  Per-N counts:
  41:36 42:13 43:62 44:14 45:47 46:68 47:85 48:64 49:130 50:139 51:250 52:183 53:204 54:25
  55:159 56:298 57:499 58:599 59:414 60:458.  Van Hoeij: "for N > 42 it is likely that some
  diamond-orbits are missing".
* A second file `LowDegreePlaces_61_80` (529 KB, 2014-06-21; copy saved as
  `2026-09-18-vanhoeij_LowDegreePlaces_61_80.txt`) gives, for N = 61..80, at least one place per
  degree without a known function (no `degj`/`j` lines, so the importer needs a small change).
  Smallest degrees: 61:20 62:22 63:18 64:24 65:20 66:16 67:22 68:26 69:28 70:20 71:44 72:22
  73:24 74:18 75:25 76:30 77:40 78:24 79:26 80:20.
* What the census rules can certify today (rank 0 for N ∈ 41..60 except 43, 53, 57, 58;
  gon_Q lower bounds from `X1_N.csv`):
  - **X_1(42): five sporadic points** — degrees 8, 8, 8, 9, 9 (three + two diamond orbits);
    gon_Q ≥ 10 (Najman–Varivoda Table 1: "5 ≥ 10") and rank 0, and (1,42) ∉ Φ^∞(8), Φ^∞(9)
    (Najman–Varivoda arXiv:2602.03513, list (3) after Table 1).  These are the only literature
    points of degree ≤ 9 missing from the census.  The remaining X_1(42) places (degrees 10, 10,
    10, 10, 11, 11, 11, 11) are undecided until gon_Q X_1(42) ∈ {10, 11, 12} is known.
  - every other N = 41..60 place has degree ≥ the recorded gonality lower bound, so it enters as
    "verified · undecided", or as "isolated" when the P^1 check succeeds and the rank is 0
    (all N except 43, 53, 57, 58).  Fields go up to degree 45; verification cost untested.
* Derickx's Oct 2013 slides "Finding all points of degree < gonality on Y1(N)" (cited on
  van Hoeij's refs page) prove completeness of the list for some N — relevant for the "finite"
  claims, not for missing points; not fetched.

## 2. Points the literature proves exist but does not write down

### 2.1  Sporadic CM points (Clark–Genao–Pollack–Saia, JLMS 105 (2022), data github.com/fsaia/least-cm-degree)
* X_1(N): a sporadic CM point is *proven* for every N except 67 N with none and 227 undecided.
  Below 111 the proven ones are exactly N = 31, 34, 39 — all three in the census (1.31.10.a,
  1.34.8.a, 1.39.8.a).  N = 37 is "unknown" (matches 1.37.12.a undecided).  For N = 41..60 no N
  is proven (all "no" or "unknown"), so nothing certifiable there.  First proven N ≥ 41:
  111 (d_CM = 24, j = 0), 129, 130, 133, 139, 146, 147, 151, 157 (d = 52), 163, 169, 170, ...
  Explicit models for N = 111 and 157 are in Sutherland's notes (below).  The site lists X_1(n)
  for n ≤ 100 only, so these need new curve rows — a policy decision (infinitely many).
* X_1(M,N), M ≥ 2: proven sporadic CM points for every pair except 37 "no" and 146 "unknown".
  **No (2,2n) pair with 2n ≤ 100 is proven** (all "no"/"unknown").  Proven pairs with the
  smallest least CM degrees (exact for N < 53): X_1(8,24) d=16 (order of disc −12);
  X_1(7,21) d=24 (j=0); X_1(16,16) 32; X_1(13,13), X_1(15,15), X_1(10,30), X_1(5,35) 48;
  X_1(9,27), X_1(18,18) 54; X_1(11,22) 60; X_1(15,30) 64; X_1(12,36), X_1(21,21), X_1(13,26),
  X_1(7,42), X_1(14,42) 72; ...  None of these (m,n) is on the site's curve list.  "Unknown"
  pairs on the site with small d_CM: X_1(5,10) d=8 (j=1728), X_1(8,8) d=8, X_1(7,7) d=12 (j=0),
  X_1(3,21) d=12, X_1(2,34) d=16, X_1(4,20) d=16, X_1(5,15) d=16, X_1(2,38) d=18 — these are
  exactly the CM places the `sporadic_2x2n` f−c search found on X_1(5,10) and X_1(7,7).
* Bourdon–Ejder–Liu–Odumodu–Viray Thm 7.1: every CM j gives sporadic points on infinitely many
  X_1(N) (no explicit list).  Bourdon–Najman arXiv:2107.10909 Thm 1.5: sporadic CM points of
  odd degree on X_1(p^k) for p ≡ 3 mod 4, k large (no explicit list).

### 2.2  Candidates whose isolation is open (would enter as "undecided")
* Bourdon–Gill–Rouse–Watson (RNT 10 (2024) art. 5, arXiv:2006.14966) Theorem 2: the only
  possible rational j's of *odd-degree* isolated points are −140625/8 (deg 3, X_1(21)), 351/4
  (deg 9, X_1(28)) — both in the census — and the CM j's of discriminant −43, −67, −163, giving
  points of degree 21 on X_1(43), 33 on X_1(67), 81 on X_1(163), isolated "if and only if"
  (open; positive rank Jacobians, Remark 33).  X_1(43) and X_1(67) are on the site.

## 3. Sources checked with nothing missing
* Najman MRL 2016 (X_1(21) deg 3) — in.  Van Hoeij N ≤ 40 — all 140 orbits in (counts match
  per N).  Derickx–Sutherland PAMS 2017 (text has no explicit sporadic points).  Sutherland's
  notes 24 Dec 2012 §4.2: sporadic CM points on X_1(31) d=10, X_1(34) d=8, X_1(39) d=8 and the
  d=12 CM point on X_1(37) — all in, but see §4 (credit).  Derickx–Najman Φ(4) = Φ^∞(4): no
  quartic points.  Najman arXiv:2609.12846 (11 Sep 2026): Φ(5) = Φ^∞(5) ∪ {Z/28, Z/30, Z/2×Z/18}
  — all in.  González-Jiménez–Najman Z/4×Z/12 — in.  BGRW / BHKKLMNS / Bourdon–Ejder 2025 /
  Ejder 2022 / Terao arXiv:2507.13199: rational non-CM isolated j's are exactly the four; three
  in, the fourth is §1.1.  Novak arXiv:2506.00753 (Q-curves, degrees 3, 5, 7): no new groups.
  Adžaga–Gužvić arXiv:2602.14718: Z/3×Z/18 does not occur for E/Q over sextic fields.
  Kazancıoğlu–Sadek arXiv:2411.02351: criteria only.  Derickx–Najman arXiv:2511.09015 and
  Lee arXiv:2507.19462: X_0(N) only.  LMFDB modular-curve points (API, 2026-09-18): X_1(37) is
  stored as Xpm1(37) with only the −9317 point (isolated flag 0 = unknown) — no additional points.
  Web searches for independent discoveries of the (2,18) quintic and (2,24) sextic points: none.

## 4. Credits and wording to reconsider
* 1.34.8.a, 1.39.8.a, 1.37.12.a are credited "van Hoeij 2012", but van Hoeij's file says the
  2012 arXiv version had only N = 29, 31 and the degree-6 point of N = 37; N ≤ 60 was added in
  Aug 2013.  Sutherland's notes of 24 Dec 2012 construct exactly these three CM points (§4.2,
  via Clark–Cook–Stankewicz's isogeny construction).  Suggest: discovered by A. V. Sutherland
  2012 (notes), listed independently by van Hoeij 2013.  1.31.10.a (j = 0) is fine: N = 31 was
  in van Hoeij's Feb 2012 version, before Sutherland's notes.
* 2.18.5.a is "F. Najman, unpublished (2026)"; it is now arXiv:2609.12846 (11 Sep 2026).
  The `Najman2026` knowledge source ("unpublished") may likewise be updated where that paper
  proves the fact used.
* BHKKLMNS count closed points ("two sporadic points of degree 3 on X_1(21)", "three points of
  degree 6 on X_1(37)"); the census counts diamond orbits, so 1 and 1.  Worth a sentence on the
  about page, since readers will compare.
* `X1_N.csv` (torsion_inf tables) stops at N = 64; rows for 65..100 would be needed for the
  61..80 import to classify anything.
