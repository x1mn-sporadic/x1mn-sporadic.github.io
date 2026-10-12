"""LMFDB labels of the census curves, for the links on the curve pages.

Looks up every curve of data/curves.json by name in the LMFDB modular curves table
(gps_gl2zhat_fine, the table behind https://beta.lmfdb.org/ModularCurve/Q/<label>/) on the public
read-only mirror devmirror.lmfdb.xyz, checks that genus and PSL_2-index agree with the census, and
writes data/knowledge/sources/lmfdb_labels.csv; build.py turns that table into data/lmfdb.json.

LMFDB names:  X_1(1) = X(1);  X_1(2) = X0(2);  X_1(n) = X1(n);  X_1(2,2) = X(2);  X_1(2,n) = X1(2,n).
For m >= 3 the LMFDB has the arithmetic curves only (geometrically connected over Q), so we link
X_1(m,m) to Xarith(m) and X_1(m,n) to Xarith1(m,n); these become isomorphic to ours over Q(zeta_m).
A curve that is not found is left out (no link).  Needs psycopg2 (Sage's python3 has it).

    python3 -B pipeline/lmfdb_labels.py          # query, check, write the csv
"""

from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, KNOWLEDGE_DIR, read_json  # noqa: E402

MIRROR = dict(host="devmirror.lmfdb.xyz", port=5432, dbname="lmfdb", user="lmfdb", password="lmfdb", connect_timeout=30)
CSV = KNOWLEDGE_DIR / "sources" / "lmfdb_labels.csv"
FIELDS = ["m", "n", "lmfdb_name", "lmfdb_label", "level", "psl2index", "genus", "arithmetic"]


def lmfdb_name(m, n):
    if m == 1:
        return {1: "X(1)", 2: "X0(2)"}.get(n, f"X1({n})")
    if m == 2:
        return "X(2)" if n == 2 else f"X1(2,{n})"
    return f"Xarith({m})" if n == m else f"Xarith1({m},{n})"


def main():
    import psycopg2
    curves = read_json(DATA / "curves.json")["curves"]
    want = {(c["m"], c["n"]): lmfdb_name(c["m"], c["n"]) for c in curves}
    con = psycopg2.connect(**MIRROR)
    cur = con.cursor()
    cur.execute("select name, label, level, psl2index, genus from gps_gl2zhat_fine where name = any(%s)",
                (sorted(set(want.values())),))
    found = {}
    for name, label, level, psl2index, genus in cur.fetchall():
        if name in found:
            sys.exit(f"two LMFDB curves named {name}: {found[name][0]}, {label}")
        found[name] = (label, level, psl2index, genus)
    rows, missing = [], []
    for c in curves:
        m, n = c["m"], c["n"]
        name = want[(m, n)]
        if name not in found:
            missing.append(f"X_1({m},{n})")
            continue
        label, level, psl2index, genus = found[name]
        if genus != c["genus"] or psl2index != c["index"]:
            sys.exit(f"X_1({m},{n}) vs LMFDB {name} = {label}: genus {c['genus']} vs {genus}, index {c['index']} vs {psl2index}")
        rows.append({"m": m, "n": n, "lmfdb_name": name, "lmfdb_label": label, "level": level,
                     "psl2index": psl2index, "genus": genus, "arithmetic": int(m >= 3)})
    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{dt.date.today()}: wrote {CSV.relative_to(DATA.parent)} ({len(rows)} curves; genus and index agree with the census)")
    print(f"not in the LMFDB ({len(missing)}): {', '.join(missing)}")


if __name__ == "__main__":
    main()
