"""Curated knowledge about the modular curves X_1(m,n) and the rules used to
certify that a verified point is *sporadic*.

Conventions
-----------
* X_1(m,n) with m | n is the modular curve whose non-cuspidal points are
  (E, P, Q) with <P, Q> = Z/m x Z/n (P of order m, Q of order n), up to
  isomorphism.  X_1(1,n) = X_1(n).  The curve is defined over Q(zeta_m) and
  is geometrically connected there.  Papers such as Derickx-Sutherland write
  the same curve as X_1(m, mn); we always write the full cyclic order.
* The *degree* of a closed point is its absolute degree d = [Q(x) : Q].  For
  m >= 3 the degree over the base field Q(zeta_m) is d / phi(m).
* A closed point x of degree d is *sporadic* if X_1(m,n) has only finitely
  many closed points of degree d.  (This is the convention of van Hoeij and of
  Derickx-van Hoeij; the "finitely many points of degree <= d" convention is
  stricter and can be read off from `degrees_finite` for the smaller degrees.)

Every fact below carries the key of a source in SOURCES.  Nothing in this file
is derived from memory of the literature: the Phi^infty(d) lists and the
rank-0 theorem are transcribed from the TeX source of arXiv:1608.07549
(Derickx-Sutherland), which itself quotes the d <= 4 lists; the degree 7-9
data come from the torsion_inf audit tables (see SOURCES).  Anything not
covered here is reported as "open", never guessed.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd

# ----------------------------------------------------------------------------
# Sources
# ----------------------------------------------------------------------------

SOURCES = {
    "Mazur77": {
        "cite": "B. Mazur, Modular curves and the Eisenstein ideal, Publ. Math. IHES 47 (1977), 33-186; "
                "Rational isogenies of prime degree, Invent. Math. 44 (1978), 129-162.",
        "used_for": "Phi(1) = Phi^infty(1)",
        "transcribed_from": "arXiv:1608.07549 (Derickx-Sutherland), Introduction",
    },
    "KKM": {
        "cite": "M. A. Kenku, F. Momose, Torsion points on elliptic curves defined over quadratic fields, "
                "Nagoya Math. J. 109 (1988), 125-149; S. Kamienny, Torsion points on elliptic curves and "
                "q-coefficients of modular forms, Invent. Math. 109 (1992), 221-229.",
        "used_for": "Phi(2) = Phi^infty(2)",
        "transcribed_from": "arXiv:1608.07549 (Derickx-Sutherland), Introduction",
    },
    "JKS04": {
        "cite": "D. Jeon, C. H. Kim, A. Schweizer, On the torsion of elliptic curves over cubic number fields, "
                "Acta Arith. 113 (2004), 291-301.",
        "used_for": "Phi^infty(3)",
        "transcribed_from": "arXiv:1608.07549 (Derickx-Sutherland), Introduction",
    },
    "JKP06": {
        "cite": "D. Jeon, C. H. Kim, E. Park, On the torsion of elliptic curves over quartic number fields, "
                "J. London Math. Soc. 74 (2006), 1-12.",
        "used_for": "Phi^infty(4)",
        "transcribed_from": "arXiv:1608.07549 (Derickx-Sutherland), Introduction",
    },
    "DS17": {
        "cite": "M. Derickx, A. V. Sutherland, Torsion subgroups of elliptic curves over quintic and sextic "
                "number fields, Proc. Amer. Math. Soc. 145 (2017), 4233-4245, arXiv:1608.07549.",
        "used_for": "Phi^infty(5), Phi^infty(6) (Theorem 1.2); rank of J_1(m,mn) over Q(zeta_m) (Theorem 4.1)",
        "transcribed_from": "TeX source of arXiv:1608.07549",
    },
    "DvH14": {
        "cite": "M. Derickx, M. van Hoeij, Gonality of the modular curve X_1(N), J. Algebra 417 (2014), 52-71, "
                "arXiv:1307.5719.",
        "used_for": "Q-gonality of X_1(N) for N <= 40 and upper bounds for N <= 250; the (1,n) in Phi^infty(d) for d = 5..8",
        "transcribed_from": "torsion_inf/tables/X1_N.csv (columns gon_Q_ub_DvH14, gon_Q_lb, p7, p8, p9)",
    },
    "torsion_inf": {
        "cite": "F. Najman, M. Varivoda, audit tables tables/X1_N.csv and tables/X1_2_N.csv of the repository "
                "github.com/marin-varivoda/torsion_inf (genus, analytic rank of J_1, Q-gonality bounds, and "
                "whether X_1(m,n) has infinitely many points of degree 7, 8, 9); gonality lower bounds computed "
                "with CurveArith (Derickx-Terao) and the Abramovich bound.",
        "used_for": "genus, rank, gonality bounds and degree 7-9 data for X_1(N), N <= 64, and X_1(2,n), n <= 60",
        "transcribed_from": "data/knowledge/sources/X1_N.csv, data/knowledge/sources/X1_2_N.csv (copied verbatim)",
    },
    "Frey94": {
        "cite": "G. Frey, Curves with infinitely many points of fixed degree, Israel J. Math. 85 (1994), 79-83.",
        "used_for": "if X/F has infinitely many points of degree <= d over F then gon_F(X) <= 2d",
    },
    "Abramovich96": {
        "cite": "D. Abramovich, A linear lower bound on the gonality of modular curves, IMRN 1996, 1005-1011; "
                "with lambda_1 >= 975/4096 (H. Kim, P. Sarnak, appendix to J. Amer. Math. Soc. 16 (2003)).",
        "used_for": "gon_C(X_Gamma) >= (lambda_1/24) * [PSL_2(Z) : Gamma-bar] with lambda_1 >= 975/4096, i.e. >= 975/98304 * index",
    },
    "KolyvaginLogachev": {
        "cite": "V. A. Kolyvagin, D. Yu. Logachev, Finiteness of the Shafarevich-Tate group and the group of "
                "rational points for some modular abelian varieties, Leningrad Math. J. 1 (1990), 1229-1253; "
                "K. Kato, p-adic Hodge theory and values of zeta functions of modular forms, Asterisque 295 (2004).",
        "used_for": "analytic rank 0 of J_1(N) or J_1(2,2n) implies rank 0 of the Mordell-Weil group",
    },
    "Faltings": {
        "cite": "G. Faltings, Endlichkeitssaetze fuer abelsche Varietaeten ueber Zahlkoerpern, Invent. Math. 73 (1983).",
        "used_for": "a curve of genus >= 2 has finitely many points over any fixed number field",
    },
    "RankZeroLemma": {
        "cite": "Standard: if J(F) is finite and X has no F-rational map to P^1 of degree <= d, then X has finitely "
                "many closed points of degree <= d over F (the fibres of Sym^d X -> Pic^d X over the finitely many "
                "F-points are projective spaces, and a positive-dimensional fibre is a base-point-free pencil of "
                "degree <= d).  See e.g. Derickx-Sutherland arXiv:1608.07549, proof of Lemma 4.3 / Corollary 4.2.",
        "used_for": "rank 0 and d < gon_F  =>  finitely many points of degree d",
    },
    "Hilbert": {
        "cite": "Hilbert irreducibility: a map X -> P^1 of degree e defined over F has infinitely many fibres that "
                "are irreducible closed points of degree e over F.",
        "used_for": "d = gon_F(X) (known exactly)  =>  infinitely many points of degree d",
    },
}

# ----------------------------------------------------------------------------
# Phi^infty(d): the (m, n) [with n the full cyclic order] such that
# Z/m x Z/n is the torsion subgroup of infinitely many non-isomorphic
# elliptic curves over number fields of degree d.  Complete lists for d <= 6.
#
# Transcribed from the TeX of arXiv:1608.07549:
#   Phi(1)      = {(1,n): 1<=n<=12, n!=11} u {(2,2n): 1<=n<=4}                        (Mazur)
#   Phi(2)      = {(1,n): 1<=n<=18, n!=17} u {(2,2n): 1<=n<=6} u {(3,3),(3,6),(4,4)}  (Kenku-Momose, Kamienny)
#   Phi^inf(3)  = {(1,n): 1<=n<=20, n!=17,19} u {(2,2n): 1<=n<=7}                     (JKS04)
#   Phi^inf(4)  = {(1,n): 1<=n<=24, n!=19,23} u {(2,2n): 1<=n<=9}
#                 u {(3,3n): 1<=n<=3} u {(4,4),(4,8),(5,5),(6,6)}                     (JKP06)
#   Phi^inf(5)  = {(1,n): 1<=n<=25, n!=23} u {(2,2n): 1<=n<=8}                        (DS17 Thm 1.2)
#   Phi^inf(6)  = {(1,n): 1<=n<=30, n!=23,25,29} u {(2,2n): 1<=n<=10}
#                 u {(3,3n): 1<=n<=4} u {(4,4),(4,8),(6,6)}                            (DS17 Thm 1.2)
# and Phi^inf(1) = Phi(1), Phi^inf(2) = Phi(2) (DS17, Introduction).
# ----------------------------------------------------------------------------


def _pairs(m, ns):
    return [(m, m * k) for k in ns]


PHI_INFINITY = {
    1: {
        "source": "Mazur77",
        "pairs": _pairs(1, [k for k in range(1, 13) if k != 11]) + _pairs(2, range(1, 5)),
    },
    2: {
        "source": "KKM",
        "pairs": _pairs(1, [k for k in range(1, 19) if k != 17]) + _pairs(2, range(1, 7))
                 + [(3, 3), (3, 6), (4, 4)],
    },
    3: {
        "source": "JKS04",
        "pairs": _pairs(1, [k for k in range(1, 21) if k not in (17, 19)]) + _pairs(2, range(1, 8)),
    },
    4: {
        "source": "JKP06",
        "pairs": _pairs(1, [k for k in range(1, 25) if k not in (19, 23)]) + _pairs(2, range(1, 10))
                 + _pairs(3, range(1, 4)) + [(4, 4), (4, 8), (5, 5), (6, 6)],
    },
    5: {
        "source": "DS17",
        "pairs": _pairs(1, [k for k in range(1, 26) if k != 23]) + _pairs(2, range(1, 9)),
    },
    6: {
        "source": "DS17",
        "pairs": _pairs(1, [k for k in range(1, 31) if k not in (23, 25, 29)]) + _pairs(2, range(1, 11))
                 + _pairs(3, range(1, 5)) + [(4, 4), (4, 8), (6, 6)],
    },
}

# Degrees for which the classification Phi^infty(d) is complete for *all* (m, n).
PHI_INFINITY_COMPLETE_DEGREES = sorted(PHI_INFINITY)

# ----------------------------------------------------------------------------
# Rank of J_1(m,n) over Q(zeta_m).  DS17 Theorem 4.1 (transcribed):
#   The rank of J_1(m,mn) is zero over Q(zeta_m) if any of the following hold:
#   m=1 and n<=36; m=2 and n<=21; m=3 and n<=10; m=4 and n<=6; m=5 and n<=4; m=6 and n<=5.
# Stored as (m, max full cyclic order n).
# ----------------------------------------------------------------------------

RANK_ZERO_DS17 = {1: 36, 2: 42, 3: 30, 4: 24, 5: 20, 6: 30}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def euler_phi(m: int) -> int:
    return sum(1 for k in range(1, m + 1) if gcd(k, m) == 1)


def psl2_index(m: int, n: int) -> int:
    """Index of the image of Gamma_1(m,n) = Gamma(m) cap Gamma_1(n) in PSL_2(Z).

    [SL_2(Z) : Gamma_1(n)] = n^2 prod_{p|n} (1 - 1/p^2); -I lies in Gamma_1(n) iff n <= 2;
    each geometric component of X_1(m,n) is a degree-m cover of X_1(n).
    Checked against Magma's CongruenceSubgroup([n,n,m]) in data/knowledge/curves_magma.json.
    """
    idx = Fraction(n * n)
    p = 2
    nn = n
    while nn > 1:
        if nn % p == 0:
            idx *= Fraction(p * p - 1, p * p)
            while nn % p == 0:
                nn //= p
        p += 1
    if n > 2:
        idx /= 2
    return int(idx * m)


def abramovich_lower_bound(m: int, n: int) -> Fraction:
    """Abramovich: gon_C(X) >= lambda_1/24 * [PSL_2(Z):Gamma-bar], with lambda_1 >= 975/4096 (Kim-Sarnak).

    This reproduces the abramovich_lb column of the torsion_inf tables (e.g. 6.78 for X_1(37), index 684).
    """
    return Fraction(975, 4096) / 24 * psl2_index(m, n)


def base_field(m: int) -> str:
    return "Q" if m <= 2 else f"Q(zeta_{m})"


# ----------------------------------------------------------------------------
# Per-curve knowledge assembled from the sources
# ----------------------------------------------------------------------------


def phi_infinity_degrees(m: int, n: int):
    """{d: source} for the d <= 6 with (m, n) in Phi^infty(d), and the finite complement."""
    infinite, finite = {}, {}
    phi_m = euler_phi(m)
    for d, rec in PHI_INFINITY.items():
        if d % phi_m:
            continue          # no points of such degree at all (Weil pairing)
        if (m, n) in rec["pairs"]:
            infinite[d] = rec["source"]
        else:
            # (m,n) not in Phi^infty(d) and the lists are closed under subgroups, so X_1(m,n)
            # has only finitely many points of degree d (see docstring of classify_degree).
            finite[d] = rec["source"]
    return infinite, finite


def rank_zero_source(m: int, n: int, table_row=None):
    """Return (0, source) if rank J_1(m,n)(Q(zeta_m)) = 0 is proven, (None, None) if unknown."""
    if m in RANK_ZERO_DS17 and n <= RANK_ZERO_DS17[m]:
        return 0, "DS17"
    if table_row is not None and m <= 2 and table_row.get("an_r") == 0:
        return 0, "torsion_inf+KolyvaginLogachev"
    return None, None


def classify_degree(curve: dict, d: int) -> dict:
    """Decide the sporadicity status of a (verified) point of absolute degree d on the curve.

    `curve` is a record from data/curves.json (see build.py) with keys
      m, n, genus, base_field_degree (= phi(m)), gonality {lb, ub, source},
      rank {value, source}, degrees_infinite {d: source}, degrees_finite {d: source}.

    Returns {"status": "sporadic"|"not-sporadic"|"open", "rule": ..., "sources": [...]}.

    Rules (in order):
      0. a point of degree d exists only if phi(m) | d;
      1. d in degrees_infinite   -> not sporadic  (Phi^infty lists, degree 7-9 tables, or d = exact gonality);
      2. d in degrees_finite     -> sporadic      (complement of the complete Phi^infty(d) lists, or tables);
      3. Frey: 2 d' < gon_lb over the base field, d' = d/phi(m)   -> sporadic;
      4. rank 0 over the base field and d' < gon_lb               -> sporadic;
      5. otherwise open.
    Why rule 2 is valid: if X_1(m,n) had infinitely many closed points of degree d, they would give
    infinitely many non-isomorphic elliptic curves over degree-d fields whose torsion contains
    Z/m x Z/n (the map to the j-line has finite fibres), hence some torsion group G containing
    Z/m x Z/n lies in Phi^infty(d); the lists for d <= 6 are closed under passing to subgroups,
    so (m,n) itself would be in Phi^infty(d).
    """
    m, n = curve["m"], curve["n"]
    phi_m = curve["base_field_degree"]
    if d % phi_m != 0:
        return {"status": "impossible", "rule": f"phi({m}) = {phi_m} does not divide {d}: no such point (Weil pairing)",
                "sources": []}
    dd = d // phi_m
    inf = curve.get("degrees_infinite", {})
    fin = curve.get("degrees_finite", {})
    if str(d) in inf:
        return {"status": "not-sporadic", "rule": f"X_1({m},{n}) has infinitely many points of degree {d}",
                "sources": [inf[str(d)]]}
    if str(d) in fin:
        return {"status": "sporadic", "rule": f"X_1({m},{n}) has only finitely many points of degree {d}",
                "sources": [fin[str(d)]]}
    gon = curve.get("gonality") or {}
    lb = gon.get("lb")
    if lb is not None and 2 * dd < lb:
        return {"status": "sporadic",
                "rule": f"Frey: 2*{dd} < {lb} <= gon_{curve['base_field']}(X_1({m},{n}))",
                "sources": ["Frey94", gon.get("source", "")]}
    rk = curve.get("rank") or {}
    if rk.get("value") == 0 and lb is not None and dd < lb:
        return {"status": "sporadic",
                "rule": f"rank J_1({m},{n})({curve['base_field']}) = 0 and {dd} < {lb} <= gonality",
                "sources": ["RankZeroLemma", rk.get("source", ""), gon.get("source", "")]}
    return {"status": "open", "rule": "no applicable finiteness result recorded in data/knowledge", "sources": []}
