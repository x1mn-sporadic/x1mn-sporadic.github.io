#!/usr/bin/env python3
"""Build the static data files the web site reads.

  data/curves.json   every curve of the census with genus, index, gonality bounds, rank, the
                     degrees known to have finitely / infinitely many points (with sources),
                     and the list of accepted points on it;
  data/points.json   every accepted point (the certificates in data/points/, verbatim);
  data/sources.json  the bibliography used by the certificates.

Inputs: data/knowledge/curves_magma.json (Magma genus/index), data/knowledge/sources/*.csv
(torsion_inf tables), pipeline/knowledge.py (curated, cited facts), data/points/*.json.

Usage:  python3 pipeline/build.py [--check]     (--check: fail if the outputs would change)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import knowledge  # noqa: E402
from common import DATA, KNOWLEDGE_DIR, POINTS_DIR, REJECTED_DIR, read_json, write_json  # noqa: E402


def load_tables():
    """torsion_inf tables keyed by (m, n) with n the full cyclic order."""
    rows = {}
    for fn, m in (("X1_N.csv", 1), ("X1_2_N.csv", 2)):
        with open(KNOWLEDGE_DIR / "sources" / fn, newline="") as fh:
            for r in csv.DictReader(fh):
                n = int(r["N"])
                rec = {"genus": int(r["g"]), "an_r": int(r["an_r"]), "index": int(r["index"]),
                       "gon_lb": int(r["gon_Q_lb"]), "gon_ub": int(r["gon_Q_ub_DvH14"]),
                       "note": r.get("note", "").strip()}
                for d in (7, 8, 9):
                    val = r[f"p{d}"].strip()
                    rec[f"p{d}"] = True if val == "True" else False if val == "False" else None
                rows[(m, n)] = rec
    return rows


def curve_record(m, n, magma_rec, table_row):
    phi = knowledge.euler_phi(m)
    genus = magma_rec["genus"]
    index = magma_rec["index"]
    if table_row is not None:
        assert table_row["genus"] == genus, (m, n, table_row["genus"], genus)
        assert table_row["index"] == index, (m, n, table_row["index"], index)
    abr = knowledge.abramovich_lower_bound(m, n)
    abr_int = int(abr) + 1 if abr.denominator != 1 else int(abr)   # ceiling
    if genus == 0:
        gon = {"lb": 1, "ub": 1, "source": "genus 0", "exact": True, "lb_source": "genus 0", "ub_source": "genus 0"}
    elif genus == 1:
        gon = {"lb": 2, "ub": 2, "source": "genus 1", "exact": True, "lb_source": "genus 1", "ub_source": "genus 1"}
    elif table_row is not None:
        exact = table_row["gon_lb"] == table_row["gon_ub"]
        gon = {"lb": max(table_row["gon_lb"], abr_int), "ub": table_row["gon_ub"], "exact": exact}
        inf0, fin0 = knowledge.phi_infinity_degrees(m, n)
        g = table_row["gon_ub"]
        # first appearance of the gonality:
        #  * gamma = d follows from the Phi^infty lists when (m,n) is in Phi^infty(d) but in no Phi^infty(e), e < d
        #    (with rank 0 a degree-d function exists and none of smaller degree): credit the list source;
        #  * X_1(N), N <= 40: Derickx-van Hoeij (exact); N > 40: their upper bound, lower bound from the
        #    torsion_inf computations (unpublished) or Abramovich;
        #  * X_1(2,2n) otherwise: unpublished (Najman 2026), or Abramovich for the lower bound.
        derivable = exact and g in inf0 and all(e in fin0 for e in range(1, g) if e % phi == 0)
        if derivable:
            gon["lb_source"] = gon["ub_source"] = inf0[g]
        elif m == 1:
            gon["ub_source"] = "DvH14"
            gon["lb_source"] = "DvH14" if n <= 40 else ("Abramovich96" if table_row["gon_lb"] <= abr_int else "Najman2026")
        else:
            gon["ub_source"] = "Najman2026"
            gon["lb_source"] = "Abramovich96" if table_row["gon_lb"] <= abr_int else "Najman2026"
        gon["source"] = gon["ub_source"] if exact else gon["lb_source"]
    else:
        gon = {"lb": max(abr_int, 2 if genus >= 1 else 1), "ub": None, "source": "Abramovich96", "exact": False,
               "lb_source": "Abramovich96", "ub_source": None}
    # gonality over the base field Q(zeta_m): the tables are Q-gonalities for m <= 2; for m >= 3 we only
    # have the geometric Abramovich bound, which is a lower bound for the gonality over any field.
    rank_val, rank_src = knowledge.rank_zero_source(m, n, table_row)
    if genus == 0:
        rank_val, rank_src = 0, "genus 0"
    rank = {"value": rank_val, "source": rank_src} if rank_val is not None else {"value": None, "source": None}
    if table_row is not None:
        rank["analytic_rank"] = table_row["an_r"]
        rank["analytic_rank_source"] = "LMFDB" if m == 1 else "Najman2026"
    inf, fin = knowledge.phi_infinity_degrees(m, n)
    degrees_infinite = {str(d): s for d, s in sorted(inf.items())}
    degrees_finite = {str(d): s for d, s in sorted(fin.items())}
    if genus == 0:
        degrees_finite = {}
        degrees_infinite = {"all": "genus 0"}
    else:
        if table_row is not None:
            for d in (7, 8, 9):
                val = table_row[f"p{d}"]
                if val is None:
                    continue
                # first appearance: X_1(N), d = 7, 8: Derickx-van Hoeij Thm 3; X_1(2,2k), d = 7: Derickx-Sutherland
                # Remark 1.3 for k <= 10 (infinite) and k > 15 (finite); everything else: torsion_inf
                if m == 1 and d in (7, 8):
                    src = "DvH14"
                elif m == 2 and d == 7 and ((n // 2 <= 10 and val) or (n // 2 > 15 and not val)):
                    src = "DS17"
                else:
                    src = "Najman2026"
                (degrees_infinite if val else degrees_finite)[str(d)] = src
        if gon["exact"] and m <= 2:
            # degree = gonality: a function of that degree over Q exists (source of the gonality), hence
            # infinitely many points of that degree by Hilbert irreducibility
            degrees_infinite.setdefault(str(gon["ub"]), gon["ub_source"])
        # degrees below phi(m) multiples are impossible; degrees d' = d/phi(m) with 2d' < gon_lb are finite (Frey)
        for d in range(1, 13):
            if d % phi:
                continue
            dd = d // phi
            if str(d) in degrees_infinite or str(d) in degrees_finite:
                continue
            if 2 * dd < gon["lb"]:
                degrees_finite[str(d)] = "Frey94"
            elif rank_val == 0 and dd < gon["lb"]:
                degrees_finite[str(d)] = "RankZeroLemma"
    return {
        "m": m, "n": n, "label": f"X1({m},{n})",
        "torsion": f"Z/{m} x Z/{n}" if m > 1 else f"Z/{n}",
        "base_field": knowledge.base_field(m), "base_field_degree": phi,
        "genus": genus, "index": index,
        "abramovich_bound": float(round(abr, 3)),
        "gonality": gon,
        "rank": rank,
        "degrees_infinite": degrees_infinite,
        "degrees_finite": degrees_finite,
        "table_note": table_row["note"] if table_row else "",
        "in_tables": table_row is not None,
    }


def point_summary(p):
    c = p["classification"]
    return {"id": p["id"], "degree": p["degree"], "status": p["status"], "j_degree": p["curve"]["j_degree"],
            "cm": p["curve"]["cm"], "field_poly": p["field"]["poly"], "field_disc": p["field"]["disc"],
            "j_rational": p["curve"]["j_rational"], "torsion": p["torsion"]["invariants"],
            "torsion_known": p["torsion"]["known_exactly"],
            "infinite": c["infinite_in_degree"]["value"], "sporadic": c["sporadic"]["value"], "isolated": c["isolated"]["value"],
            "rules": {k: c[k]["rule"] for k in ("infinite_in_degree", "sporadic", "isolated")},
            "discovered_by": p["discovery"]["by"], "year": p["discovery"]["year"],
            "submitter": p["submitter"]["name"], "reference": p["reference"], "verified": p["dates"]["verified"]}


def build():
    magma = read_json(KNOWLEDGE_DIR / "curves_magma.json")
    tables = load_tables()
    points = [read_json(p) for p in sorted(POINTS_DIR.glob("*.json"))]
    points.sort(key=lambda p: (p["m"], p["n"], p["degree"], p["id"]))
    curves = []
    for rec in magma["curves"]:
        m, n = rec["m"], rec["n"]
        c = curve_record(m, n, rec, tables.get((m, n)))
        mine = [p for p in points if p["m"] == m and p["n"] == n]
        c["points"] = [point_summary(p) for p in mine]
        c["n_certified"] = sum(1 for p in mine if p["status"] == "certified")
        c["n_verified"] = sum(1 for p in mine if p["status"] == "verified")
        c["n_sporadic"] = sum(1 for p in mine if p["classification"]["sporadic"]["value"] == "yes")
        c["n_isolated"] = sum(1 for p in mine if p["classification"]["isolated"]["value"] == "yes")
        c["degrees_present"] = sorted({p["degree"] for p in mine})
        curves.append(c)
    curves.sort(key=lambda c: (c["m"], c["n"]))
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    curves_out = {
        "generated": now,
        "magma_version": magma["magma_version"],
        "conventions": {
            "curve": "X1(m,n), m | n, parametrises (E,P,Q) with <P,Q> = Z/m x Z/n; defined over Q(zeta_m)",
            "degree": "absolute degree [Q(x):Q] of the closed point x; relative degree = degree / phi(m)",
            "sporadic": "a closed point of degree d is sporadic if the curve has only finitely many closed points of degree <= d",
            "isolated": "P^1-isolated (dim L(x) = 1) and AV-isolated (Bourdon-Ejder-Liu-Odumodu-Viray); finitely many points of degree d implies isolated",
            "answers": "each of 'infinitely many points of degree d', 'sporadic', 'isolated' is yes, no or maybe",
            "gonality": "Q-gonality for m <= 2 (from the Phi^infty results, Derickx-van Hoeij, Abramovich, or Najman's unpublished computations); for m >= 3 only Abramovich's geometric lower bound",
        },
        "n_curves": len(curves),
        "n_points": len(points),
        "n_certified": sum(1 for p in points if p["status"] == "certified"),
        "n_verified": sum(1 for p in points if p["status"] == "verified"),
        "n_sporadic": sum(1 for p in points if p["classification"]["sporadic"]["value"] == "yes"),
        "n_isolated": sum(1 for p in points if p["classification"]["isolated"]["value"] == "yes"),
        "n_rejected": len(list(REJECTED_DIR.glob("*.json"))),
        "curves": curves,
    }
    points_out = {"generated": now, "points": points}
    sources_out = {"generated": now, "sources": knowledge.SOURCES}
    return curves_out, points_out, sources_out


def stable(obj):
    o = json.loads(json.dumps(obj))
    o.pop("generated", None)
    return json.dumps(o, sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    curves_out, points_out, sources_out = build()
    targets = [(DATA / "curves.json", curves_out), (DATA / "points.json", points_out), (DATA / "sources.json", sources_out)]
    if args.check:
        changed = [str(p) for p, o in targets if not p.exists() or stable(read_json(p)) != stable(o)]
        if changed:
            sys.exit("out of date: " + ", ".join(changed))
        print("data files up to date")
        return
    for p, o in targets:
        write_json(p, o)
    print(f"wrote data/curves.json ({curves_out['n_curves']} curves), data/points.json "
          f"({curves_out['n_points']} points: {curves_out['n_certified']} certified, {curves_out['n_verified']} verified)")


if __name__ == "__main__":
    main()
