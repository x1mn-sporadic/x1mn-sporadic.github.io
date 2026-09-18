#!/usr/bin/env python3
"""Turn Mark van Hoeij's list of low-degree places on X_1(N) into submissions.

Source: https://www.math.fsu.edu/~hoeij/files/X1N/LowDegreePlaces (Aug 2013), a copy of which is
kept verbatim in data/knowledge/sources/vanhoeij_LowDegreePlaces.txt.  Each line

    N = 25, degv = 6, degj = 3, [x^3-x^2+1 = 0, y^2+(x^2-2*x-1)*y+x = 0]

becomes one submission in "vanhoeij" format (the pipeline rebuilds (b, c) from (x0, y0) with the
formulas given in the file's header and re-verifies everything).

Usage:  python3 pipeline/import_vanhoeij.py --max-N 40 [--min-N 21] [--out submissions/inbox]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import KNOWLEDGE_DIR, SCHEMA_SUBMISSION, SUBMISSIONS_INBOX, write_json  # noqa: E402

SRC = KNOWLEDGE_DIR / "sources" / "vanhoeij_LowDegreePlaces.txt"
SRC2 = KNOWLEDGE_DIR / "sources" / "vanhoeij_LowDegreePlaces_61_80.txt"      # N = 61..80: one place per degree
URL = "https://www.math.fsu.edu/~hoeij/files/X1N/LowDegreePlaces"
URL2 = "https://www.math.fsu.edu/~hoeij/files/X1N/LowDegreePlaces_61_80"
LINE = re.compile(r"^N = (\d+), degv = (\d+)(?:, degj = (\d+))?(?:, j = (-?\d+(?:/\d+)?))?, \[(.*) = 0, (.*) = 0\]\s*$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-N", type=int, default=21)
    ap.add_argument("--max-N", type=int, default=40)
    ap.add_argument("--out", default=str(SUBMISSIONS_INBOX))
    ap.add_argument("--degrees", default="", help="comma-separated degrees to keep (default: all)")
    ap.add_argument("--max-per-N-degree", type=int, default=0, help="keep at most this many places per (N, degree); 0 = all")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    keep_degrees = {int(t) for t in args.degrees.split(",") if t.strip()}
    counts = {}
    written = 0
    lines = [(SRC.name, URL, i, l) for i, l in enumerate(SRC.read_text().splitlines(), 1)]
    if SRC2.exists():
        lines += [(SRC2.name, URL2, i, l) for i, l in enumerate(SRC2.read_text().splitlines(), 1)]
    for srcname, url, lineno, line in lines:
        m = LINE.match(line)
        if not m:
            if line.startswith("N = ") and "degv" in line:
                sys.exit(f"unparsed line {lineno}: {line}")
            continue
        N, degv, degj, jval, eqx, eqxy = m.groups()
        N, degv = int(N), int(degv)
        if not (args.min_N <= N <= args.max_N) or (keep_degrees and degv not in keep_degrees):
            continue
        k = counts.get((N, degv), 0) + 1
        counts[(N, degv)] = k
        if args.max_per_N_degree and k > args.max_per_N_degree:
            continue
        # attribution: the point on X_1(21) was found by Najman and presented in 2011 (arXiv:1211.2188);
        # van Hoeij's data first appeared with the 2012 preprint of arXiv:1202.4355 (the file header lists
        # what the 2012 and 2013 versions contained; the census dates all of it to the first preprint)
        if N == 21:
            disc_by, year = "F. Najman", 2011
        else:
            disc_by, year = "M. van Hoeij", 2012
        sub = {
            "schema": SCHEMA_SUBMISSION,
            "m": 1, "n": N,
            "field": eqx.strip(),
            "curve": {"vanhoeij": {"eqxy": eqxy.strip()}},
            "degree": degv,
            "expected": {"j_degree": int(degj) if degj else degv, "j": jval},
            "discoverer": disc_by, "year": year,
            "submitter": "Mark van Hoeij",
            "affiliation": "Florida State University",
            "github": "",
            "reference": f"M. van Hoeij, Low degree places on the modular curve X1(N), arXiv:1202.4355; "
                         f"data file {srcname.replace('vanhoeij_', '').replace('.txt', '')} (2013/2014), line {lineno}"
                         + (" (point found earlier by Najman, arXiv:1211.2188)" if N == 21 else ""),
            "notes": ("Imported from van Hoeij's list; one representative per diamond orbit." if N <= 60 else
                      "Imported from van Hoeij's list for N = 61..80 (one place for each degree without a known function of that degree)."),
            "date": "2013-08-01",
            "source": {"kind": "import", "file": srcname, "line": lineno, "url": url},
        }
        write_json(out / f"vanhoeij_{N}_{degv}_{k}.json", sub)
        written += 1
    print(f"wrote {written} submissions to {out}")


if __name__ == "__main__":
    main()
