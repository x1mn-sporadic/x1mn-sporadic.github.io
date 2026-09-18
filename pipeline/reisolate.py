#!/usr/bin/env python3
"""Run (or re-run) the isolation check for the points of one curve in a single Magma process.

Usage:  python3 pipeline/reisolate.py --m 1 --n 62 [--all] [--timeout SECONDS] [--max-degree D]

Selects the certificates of X_1(m,n) whose isolation was not computed (all of them with --all),
writes one batch job (pipeline/magma/isolation_batch.m) so that the models over F_q -- whose
integral closures cost minutes to an hour for high genus -- are built once and shared, runs it
under the timeout, and updates each certificate's `isolation` record, re-classifying the point
with pipeline/knowledge.py.  Results are read incrementally, so a run killed by the timeout keeps
the points it finished; the others stay "not computed" for a later run.  Run pipeline/build.py
afterwards.  Points are processed in order of increasing degree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402
import knowledge  # noqa: E402
from common import DATA, POINTS_DIR, WORK, log, read_json, write_json  # noqa: E402
from verify import ISOLATION_LIB, MAGMA, MDMAGMA_SPEC, MODELS_DIR, magma_string  # noqa: E402

BATCH = Path(__file__).resolve().parent / "magma" / "isolation_batch.m"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--all", action="store_true", help="also re-run points whose isolation was already computed")
    ap.add_argument("--timeout", type=int, default=6 * 3600)
    ap.add_argument("--max-degree", type=int, default=0)
    ap.add_argument("--max-primes", type=int, default=4)
    args = ap.parse_args()
    certs = [read_json(p) for p in sorted(POINTS_DIR.glob(f"{args.m}.{args.n}.*.json"))]
    todo = [c for c in certs if args.all or not c.get("isolation", {}).get("computed")]
    if args.max_degree:
        todo = [c for c in todo if c["degree"] <= args.max_degree]
    todo.sort(key=lambda c: (c["degree"], c["id"]))
    if not todo:
        log(f"X_1({args.m},{args.n}): nothing to do")
        return
    jobdir = WORK / f"reisolate_{args.m}_{args.n}"
    if jobdir.exists():
        shutil.rmtree(jobdir)
    jobdir.mkdir(parents=True)
    out = jobdir / "results.jsonl"
    pts = []
    for c in todo:
        cv = c["curve"]
        P = cv["P"] if c["m"] > 1 else ["", ""]
        pts.append("<" + ", ".join(magma_string(x) for x in [c["id"], c["field"]["poly"], cv["tate_b"], cv["tate_c"], P[0], P[1]]) + ">")
    job = jobdir / "batch.m"
    job.write_text("\n".join([
        "SetColumns(0);", f"m := {args.m}; n := {args.n};", f"MaxPrimes := {args.max_primes};",
        f"MdmagmaSpec := {magma_string(str(MDMAGMA_SPEC))};", f"ModelsDir := {magma_string(str(MODELS_DIR))};",
        f"LogFile := {magma_string(str(jobdir / 'batch.log'))};", f"OutFile := {magma_string(str(out))};",
        "POINTS := [", ",\n".join(pts), "];", f'load "{BATCH}";']) + "\n")
    log(f"X_1({args.m},{args.n}): {len(todo)} point(s), degrees {todo[0]['degree']}..{todo[-1]['degree']}; running Magma (timeout {args.timeout} s)")
    try:
        subprocess.run([MAGMA, "-b", str(job)], stdin=subprocess.DEVNULL, stdout=open(jobdir / "batch.stdout", "w"),
                       stderr=subprocess.STDOUT, timeout=args.timeout, cwd=jobdir)
    except subprocess.TimeoutExpired:
        log("  timeout: keeping the results obtained so far")
    results = {}
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                results[r["id"]] = r["result"]
    curves_out, _, _, _ = build.build()
    curves = {(c["m"], c["n"]): c for c in curves_out["curves"]}
    curve = curves[(args.m, args.n)]
    lib_hash = hashlib.sha256(ISOLATION_LIB.read_bytes()).hexdigest()
    n_iso = n_unk = n_fail = 0
    (DATA / "logs").mkdir(exist_ok=True)
    for c in todo:
        r = results.get(c["id"])
        rec = {"computed": False, "p1_isolated": None, "method": "reduction modulo good primes (upper semicontinuity of h^0)"}
        if r is None:
            rec["note"] = "not reached within the time limit of the batch run"; n_fail += 1
        elif not r.get("ok"):
            rec["note"] = r.get("error", "failed"); n_fail += 1
        else:
            rec.update({"computed": True, "p1_isolated": r["p1_isolated"] is True, "primes": r["primes"], "l_values": r["l_values"],
                        "model": r["model"], "cputime_seconds": r["cputime"], "isolation_lib_sha256": lib_hash})
            if r["p1_isolated"] is True:
                n_iso += 1
            else:
                rec["note"] = "dim L(x mod q) >= 2 for every prime tried: the point probably moves in a pencil (not proven)"; n_unk += 1
        c["isolation"] = rec
        cls = knowledge.classify_point(curve, c["degree"], rec, c["curve"].get("j_rational", ""))
        c["classification"] = {k: cls[k] for k in ("infinite_in_degree", "sporadic", "isolated")}
        if cls["status"] == "rejected":
            log(f"  {c['id']}: would now be rejected ({cls['isolated']['rule']}); left as is")
        else:
            c["status"] = cls["status"]
        c["verification"]["isolation_log"] = f"data/logs/{c['id']}.isolation.log"
        write_json(POINTS_DIR / f"{c['id']}.json", c)
    if (jobdir / "batch.log").exists():
        # one shared log for the batch, referenced by every point of it
        shutil.copy(jobdir / "batch.log", DATA / "logs" / f"batch_{args.m}_{args.n}.isolation.log")
        for c in todo:
            c["verification"]["isolation_log"] = f"data/logs/batch_{args.m}_{args.n}.isolation.log"
            write_json(POINTS_DIR / f"{c['id']}.json", c)
    log(f"X_1({args.m},{args.n}): {n_iso} P1-isolated, {n_unk} not established, {n_fail} not computed")


if __name__ == "__main__":
    main()
