#!/usr/bin/env python3
"""Re-derive the three answers (and the status) of every certificate from the current knowledge.

Usage:  python3 pipeline/reclassify.py [--dry-run]

The verification (Magma) results stored in the certificates -- field, curve, torsion, degree, and
the isolation record -- are kept; only `classification` and `status` are recomputed with
pipeline/knowledge.py against the freshly rebuilt data/curves.json.  Use it after correcting or
extending the curated knowledge (sources, gonality bounds, Phi^infty data, rank results).

A certificate whose new status would be "rejected" is reported and left unchanged (a human
decides whether to remove it), so that a knowledge edit can never silently delete points.
Run pipeline/build.py afterwards.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402
import knowledge  # noqa: E402
from common import POINTS_DIR, log, read_json, write_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    curves_out, _, _ = build.build()
    curves = {(c["m"], c["n"]): c for c in curves_out["curves"]}
    changed = 0
    for path in sorted(POINTS_DIR.glob("*.json")):
        cert = read_json(path)
        curve = curves[(cert["m"], cert["n"])]
        cls = knowledge.classify_point(curve, cert["degree"], cert.get("isolation"))
        new_cl = {k: cls[k] for k in ("infinite_in_degree", "sporadic", "isolated")}
        if cls["status"] == "rejected":
            log(f"{cert['id']}: would now be REJECTED ({cls['sporadic']['rule']}; {cls['isolated']['rule']}) -- left unchanged")
            continue
        if new_cl == cert.get("classification") and cls["status"] == cert.get("status"):
            continue
        old = cert.get("classification", {})
        diff = [k for k in new_cl if new_cl[k] != old.get(k)]
        log(f"{cert['id']}: {cert.get('status')} -> {cls['status']}; changed: {', '.join(diff)}")
        cert["classification"] = new_cl
        cert["status"] = cls["status"]
        changed += 1
        if not args.dry_run:
            write_json(path, cert)
    log(f"{changed} certificate(s) {'would be ' if args.dry_run else ''}updated")


if __name__ == "__main__":
    main()
