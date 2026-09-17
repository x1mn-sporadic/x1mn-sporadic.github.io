#!/usr/bin/env python3
"""Verify submissions in submissions/inbox/ with Magma and write certificates.

Usage
-----
  python3 pipeline/verify.py                 # process every file in submissions/inbox/
  python3 pipeline/verify.py FILE [FILE...]  # process the given submission files
  options: --timeout SECONDS (default 3600)  --mem-gb N (default 16)  --no-github
           --keep (do not move processed submissions)  --dry-run
           --no-isolation  --isolation-timeout SECONDS (default 1800)

For each submission the script
  1. validates the JSON (schema, whitelisted strings, (m,n) in the census, genus >= 1);
  2. writes a Magma job that loads pipeline/magma/verify_lib.m and runs it under `timeout`;
  3. reads the JSON that Magma wrote, canonicalises the residue field with PARI's polredabs;
  4. runs a second Magma job (pipeline/magma/isolation_lib.m) that decides P^1-isolation of the
     point by a Riemann-Roch computation on a model of X_1(m,n) modulo a good prime (m <= 2);
  5. answers the three questions "infinitely many points of degree d?", "sporadic?", "isolated?"
     with yes / no / maybe from pipeline/knowledge.py (curated, cited facts) and the isolation
     result;
  6. checks for duplicates among the already accepted points;
  7. writes data/points/<id>.json (accepted: status "certified" if sporadic or isolated is yes,
     else "verified") or data/rejected/<name>.json, keeps the Magma logs under data/logs/, and
  8. comments on / closes the GitHub issue the submission came from (unless --no-github).

Magma exits with status 0 even after an error, so success is judged from the JSON it wrote
(`ok: true`) and the VERIFY_DONE marker in the log, never from the exit code.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import knowledge  # noqa: E402
from common import (DATA, LOGS, MAX_STRING, POINTS_DIR, RE_ELEMENT, RE_FIELD_POLY, RE_XY,  # noqa: E402
                    REJECTED_DIR, SCHEMA_CERTIFICATE, SUBMISSIONS_INBOX, SUBMISSIONS_PROCESSED,
                    WORK, github_request, github_token, log, read_json, repo_path, write_json)

VERIFY_LIB = Path(__file__).resolve().parent / "magma" / "verify_lib.m"
ISOLATION_LIB = Path(__file__).resolve().parent / "magma" / "isolation_lib.m"
MDMAGMA_SPEC = Path(__file__).resolve().parent / "external" / "mdmagma" / "v2" / "mdmagma.spec"
MODELS_DIR = Path(__file__).resolve().parent / "models" / "X1_m_n"
MAGMA = shutil.which("magma") or "/usr/local/bin/magma"


class Reject(Exception):
    pass


# --------------------------------------------------------------------------- validation

def _s(v, regex, what):
    if not isinstance(v, str):
        raise Reject(f"{what} must be a string")
    v = v.strip()
    if not v or len(v) > MAX_STRING or not regex.match(v):
        raise Reject(f"{what} contains characters outside the allowed set (digits, a/x/y, + - * / ^ ( ))")
    return v


def validate(sub: dict, curves: dict) -> dict:
    """Return a normalised copy of the submission or raise Reject."""
    try:
        m, n = int(sub["m"]), int(sub["n"])
    except Exception:
        raise Reject("m and n must be integers")
    if m < 1 or n < 1 or n % m:
        raise Reject(f"need m | n, got m={m}, n={n}")
    key = f"{m}.{n}"
    if key not in curves:
        raise Reject(f"X_1({m},{n}) is not in the census list (see the home page); "
                     "open an issue if you would like it added")
    curve = curves[key]
    if curve["genus"] == 0:
        raise Reject(f"X_1({m},{n}) has genus 0, so it has infinitely many points of every degree: "
                     "no point on it is sporadic")
    if n < 4:
        raise Reject("n must be at least 4")
    out = {"m": m, "n": n, "field": _s(sub.get("field"), RE_FIELD_POLY, "field polynomial")}
    curve_in = sub.get("curve") or {}
    if "ainvs" in curve_in:
        ai = curve_in["ainvs"]
        if not isinstance(ai, list) or len(ai) != 5:
            raise Reject("ainvs must be a list of 5 elements [a1,a2,a3,a4,a6]")
        out["mode"] = "ainvs"
        out["ainvs"] = [_s(str(v), RE_ELEMENT, f"a-invariant {i+1}") for i, v in enumerate(ai)]
    elif "tate" in curve_in:
        t = curve_in["tate"]
        out["mode"] = "tate"
        out["tb"] = _s(str(t.get("b")), RE_ELEMENT, "Tate b")
        out["tc"] = _s(str(t.get("c")), RE_ELEMENT, "Tate c")
    elif "vanhoeij" in curve_in:
        out["mode"] = "vanhoeij"
        out["eqxy"] = _s(str(curve_in["vanhoeij"].get("eqxy")), RE_XY, "eqxy")
    else:
        raise Reject("the curve must be given as ainvs, tate {b,c}, or vanhoeij {eqxy}")
    pts = sub.get("points") or {}
    for name in ("P", "Q"):
        if pts.get(name):
            xy = pts[name]
            if not isinstance(xy, list) or len(xy) != 2:
                raise Reject(f"point {name} must be [x, y]")
            out[name] = [_s(str(xy[0]), RE_ELEMENT, f"{name}.x"), _s(str(xy[1]), RE_ELEMENT, f"{name}.y")]
    if out["mode"] == "ainvs" and "Q" not in out:
        log("  note: Q not given; Magma will compute the full torsion subgroup (slow for large degree)")
    for k in ("degree", "submitter", "github", "reference", "notes", "date", "source", "affiliation", "expected",
              "discoverer", "year"):
        if k in sub:
            out[k] = sub[k]
    return out


# --------------------------------------------------------------------------- Magma

def magma_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_job(v: dict, jobdir: Path, mem_gb: int, skip_full_torsion: bool) -> Path:
    lines = ["SetColumns(0);",
             f"m := {v['m']}; n := {v['n']};",
             f"fpoly := {magma_string(v['field'])};",
             f"mode := {magma_string(v['mode'])};",
             f"LogFile := {magma_string(str(jobdir / 'magma.log'))};",
             f"OutFile := {magma_string(str(jobdir / 'result.json'))};",
             f"MemGB := {mem_gb};",
             f"SkipFullTorsion := {'true' if skip_full_torsion else 'false'};"]
    if v["mode"] == "ainvs":
        lines.append("ainvs := [" + ", ".join(magma_string(s) for s in v["ainvs"]) + "];")
    elif v["mode"] == "tate":
        lines.append(f"tb := {magma_string(v['tb'])}; tc := {magma_string(v['tc'])};")
    else:
        lines.append(f"eqxy := {magma_string(v['eqxy'])};")
    for name in ("P", "Q"):
        if name in v:
            lines.append(f"{name}xy := [{magma_string(v[name][0])}, {magma_string(v[name][1])}];")
    lines.append(f'load "{VERIFY_LIB}";')
    lines.append("quit;")
    job = jobdir / "job.m"
    job.write_text("\n".join(lines) + "\n")
    return job


def run_magma(job: Path, timeout: int) -> tuple[int, bool]:
    """Run the job; return (exit code, timed_out)."""
    try:
        proc = subprocess.run([MAGMA, "-b", str(job)], stdin=subprocess.DEVNULL,
                              stdout=open(job.with_suffix(".stdout"), "w"), stderr=subprocess.STDOUT,
                              timeout=timeout, cwd=job.parent)
        return proc.returncode, False
    except subprocess.TimeoutExpired:
        return -1, True


def write_isolation_job(res: dict, jobdir: Path) -> Path:
    rf = res["residue_field"]
    P = rf["P"] if res["m"] > 1 else ["", ""]
    lines = ["SetColumns(0);",
             f"m := {res['m']}; n := {res['n']};",
             f"fpoly := {magma_string(rf['poly'])};",
             f"tb := {magma_string(rf['b'])}; tc := {magma_string(rf['c'])};",
             f"Px := {magma_string(P[0])}; Py := {magma_string(P[1])};",
             f"MdmagmaSpec := {magma_string(str(MDMAGMA_SPEC))};",
             f"ModelsDir := {magma_string(str(MODELS_DIR))};",
             f"LogFile := {magma_string(str(jobdir / 'isolation.log'))};",
             f"OutFile := {magma_string(str(jobdir / 'isolation.json'))};",
             f'load "{ISOLATION_LIB}";',
             "quit;"]
    job = jobdir / "isolation.m"
    job.write_text("\n".join(lines) + "\n")
    return job


def run_isolation(res: dict, jobdir: Path, args) -> dict:
    """Return the isolation record {computed, p1_isolated, l_values, primes, model, ...}."""
    rec = {"computed": False, "p1_isolated": None, "method": "reduction modulo good primes (upper semicontinuity of h^0)"}
    if args.no_isolation:
        rec["note"] = "not attempted (--no-isolation)"
        return rec
    if res["m"] > 2:
        rec["note"] = f"not implemented for m = {res['m']}"
        return rec
    if not MDMAGMA_SPEC.exists():
        rec["note"] = "mdmagma not available (pipeline/external/mdmagma missing)"
        return rec
    job = write_isolation_job(res, jobdir)
    rc, timed_out = run_magma(job, args.isolation_timeout)
    out = jobdir / "isolation.json"
    if timed_out or not out.exists():
        rec["note"] = f"Magma did not finish within {args.isolation_timeout} s" if timed_out else "no result"
        return rec
    iso = read_json(out)
    if not iso.get("ok"):
        rec["note"] = iso.get("error", "failed")
        return rec
    rec.update({"computed": True, "p1_isolated": iso["p1_isolated"] is True, "primes": iso["primes"],
                "l_values": iso["l_values"], "model": iso["model"], "cputime_seconds": iso["cputime"],
                "isolation_lib_sha256": sha256_file(ISOLATION_LIB)})
    if iso["p1_isolated"] is not True:
        rec["note"] = "dim L(x mod q) >= 2 for every prime tried: the point probably moves in a pencil (not proven)"
    return rec


# --------------------------------------------------------------------------- post-processing

def polredabs(poly: str) -> str | None:
    try:
        import cypari2
        pari = cypari2.Pari()
        return str(pari(f"polredabs({poly})"))
    except Exception as e:  # pragma: no cover
        log(f"  polredabs unavailable: {e}")
        return None


def existing_points():
    return [read_json(p) for p in sorted(POINTS_DIR.glob("*.json"))]


def next_id(m: int, n: int, d: int, points) -> str:
    used = {p["id"].split(".")[-1] for p in points if p["m"] == m and p["n"] == n and p["degree"] == d}
    k = 0
    while True:
        label = ""
        j = k
        while True:
            label = chr(ord("a") + j % 26) + label
            j = j // 26 - 1
            if j < 0:
                break
        if label not in used:
            return f"{m}.{n}.{d}.{label}"
        k += 1


def find_duplicate(m, n, field_polredabs, j_minpoly, points):
    for p in points:
        if p["m"] == m and p["n"] == n and p["field"].get("polredabs") == field_polredabs \
                and p["curve"]["j_minpoly"] == j_minpoly:
            return p["id"]
    return None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_certificate(v: dict, res: dict, curve: dict, points, jobdir: Path, iso: dict) -> dict:
    m, n = res["m"], res["n"]
    rf = res["residue_field"]
    d = rf["degree"]
    phi = curve["base_field_degree"]
    exp = v.get("expected") or {}
    if exp.get("j_degree") is not None and exp["j_degree"] != res["curve"]["j_degree"]:
        raise Reject(f"expected [Q(j):Q] = {exp['j_degree']} but computed {res['curve']['j_degree']}")
    if exp.get("j") and exp["j"] != res["curve"]["j_rational"]:
        raise Reject(f"expected j = {exp['j']} but computed {res['curve']['j_rational']!r}")
    if exp and v.get("degree") is not None and int(v["degree"]) != d:
        raise Reject(f"expected degree {v['degree']} but the point has degree {d}")
    cls = knowledge.classify_point(curve, d, iso)
    canon = polredabs(rf["poly"])
    dup = find_duplicate(m, n, canon, res["curve"]["j_minpoly"], points)
    if dup:
        raise Reject(f"duplicate of the existing point {dup} (same residue field and j-invariant)")
    if cls["status"] == "rejected":
        raise Reject("the point is verified but neither sporadic nor isolated: "
                     f"{cls['sporadic']['rule']}; {cls['isolated']['rule']}")
    status = cls["status"]
    pid = next_id(m, n, d, points)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    b, c = rf["b"], rf["c"]
    cert = {
        "schema": SCHEMA_CERTIFICATE,
        "id": pid,
        "m": m, "n": n,
        "degree": d,
        "relative_degree": d // phi,
        "base_field": curve["base_field"],
        "status": status,
        "classification": {k: cls[k] for k in ("infinite_in_degree", "sporadic", "isolated")},
        "isolation": iso,
        "discovery": {"by": v.get("discoverer", ""), "year": v.get("year", "")},
        "field": {
            "poly": rf["poly"], "poly_coeffs": rf["poly_coeffs"], "polredabs": canon,
            "degree": d, "disc": rf["disc"], "disc_factored": rf["disc_factored"], "signature": rf["signature"],
        },
        "curve": {
            "model": "Tate normal form over the residue field: y^2 + (1-c)xy - by = x^3 - bx^2, Q = (0,0)",
            "tate_b": b, "tate_c": c, "tate_b_coeffs": rf["b_coeffs"], "tate_c_coeffs": rf["c_coeffs"],
            "ainvs": [f"1 - ({c})", f"-({b})", f"-({b})", "0", "0"],
            "P": rf["P"], "P_coeffs": rf["P_coeffs"], "Q": ["0", "0"],
            "j_minpoly": res["curve"]["j_minpoly"], "j_degree": res["curve"]["j_degree"],
            "j_rational": res["curve"]["j_rational"],
            "cm": res["curve"]["cm"], "cm_disc": res["curve"]["cm_disc"],
            "disc_norm": res["curve"]["disc_norm"], "conductor_norm": res["curve"]["conductor_norm"],
        },
        "torsion": res["torsion"],
        "submitted": {
            "field": res["submitted_field"], "mode": v["mode"],
            "curve": {k: v[k] for k in ("ainvs", "tb", "tc", "eqxy") if k in v},
            "points": {k: v[k] for k in ("P", "Q") if k in v},
            "ainvs_as_verified": res["curve"]["ainvs"],
            "points_as_verified": res["points"],
            "working_field": res["working_field"],
            "claimed_degree": v.get("degree"),
            "residue_field_equals_submitted_field": rf["equals_K"],
        },
        "submitter": {"name": v.get("submitter", ""), "github": v.get("github", ""),
                      "affiliation": v.get("affiliation", "")},
        "reference": v.get("reference", ""),
        "notes": v.get("notes", ""),
        "source": v.get("source", {}),
        "dates": {"submitted": v.get("date", ""), "verified": now},
        "verification": {
            "host": "Mordell (Dept. of Mathematics, Univ. of Zagreb)",
            "magma_version": res["magma_version"],
            "cputime_seconds": res["cputime"],
            "verify_lib_sha256": sha256_file(VERIFY_LIB),
            "log": f"data/logs/{pid}.log",
            "isolation_log": f"data/logs/{pid}.isolation.log" if iso.get("computed") or "primes" in iso else "",
        },
    }
    return cert


# --------------------------------------------------------------------------- GitHub feedback

def github_feedback(v: dict, outcome: str, body: str, dry: bool):
    src = v.get("source") or {}
    if src.get("kind") != "issue":
        return
    tok = github_token()
    if not tok:
        log("  no GitHub token: skipping issue update")
        return
    num = src["number"]
    if dry:
        log(f"  [dry-run] would comment on issue #{num} and label it {outcome}")
        return
    github_request("POST", repo_path(f"/issues/{num}/comments"), {"body": body}, token=tok)
    github_request("POST", repo_path(f"/issues/{num}/labels"), {"labels": [outcome]}, token=tok)
    github_request("PATCH", repo_path(f"/issues/{num}"), {"state": "closed"}, token=tok)
    log(f"  issue #{num}: commented, labelled '{outcome}', closed")


def site_url(pid: str) -> str:
    return f"https://x1mn-sporadic.github.io/point.html?id={pid}"


# --------------------------------------------------------------------------- main

def process(path: Path, curves: dict, args) -> str:
    name = path.stem
    log(f"== {path.name}")
    sub = read_json(path)
    jobdir = WORK / name
    if jobdir.exists():
        shutil.rmtree(jobdir)
    jobdir.mkdir(parents=True)
    v = None
    try:
        v = validate(sub, curves)
        curve = curves[f"{v['m']}.{v['n']}"]
        job = write_job(v, jobdir, args.mem_gb, skip_full_torsion=False)
        if args.dry_run:
            log(f"  [dry-run] job written to {job}")
            return "dry"
        rc, timed_out = run_magma(job, args.timeout)
        result_file = jobdir / "result.json"
        if timed_out or not result_file.exists():
            # second attempt without the full torsion computation, if the points were given
            if "Q" in v or v["mode"] != "ainvs":
                log("  first run timed out or produced no result; retrying with SkipFullTorsion")
                job = write_job(v, jobdir, args.mem_gb, skip_full_torsion=True)
                rc, timed_out = run_magma(job, args.timeout)
            if timed_out or not result_file.exists():
                raise Reject("Magma did not finish within the time limit "
                             f"({args.timeout} s); please supply the points P and Q explicitly")
        res = read_json(result_file)
        if not res.get("ok"):
            raise Reject("verification failed: " + res.get("error", "unknown error"))
        mlog = (jobdir / "magma.log").read_text() if (jobdir / "magma.log").exists() else ""
        if "VERIFY_DONE" not in mlog:
            raise Reject("Magma did not reach VERIFY_DONE (see log)")
        iso = run_isolation(res, jobdir, args)
        log(f"  isolation: {'P1-isolated' if iso.get('p1_isolated') else iso.get('note', 'unknown')}")
        points = existing_points()
        cert = build_certificate(v, res, curve, points, jobdir, iso)
        pid = cert["id"]
        write_json(POINTS_DIR / f"{pid}.json", cert)
        (DATA / "logs").mkdir(exist_ok=True)
        shutil.copy(jobdir / "magma.log", DATA / "logs" / f"{pid}.log")
        if (jobdir / "isolation.log").exists():
            shutil.copy(jobdir / "isolation.log", DATA / "logs" / f"{pid}.isolation.log")
        c = cert["classification"]
        log(f"  ACCEPTED as {pid} [{cert['status']}] degree {cert['degree']}: infinite={c['infinite_in_degree']['value']} "
            f"sporadic={c['sporadic']['value']} isolated={c['isolated']['value']}")
        def line(name, a):
            return f"- **{name}: {a['value']}** — {a['rule']}" + (f" ({', '.join(a['sources'])})" if a['sources'] else "")
        verdict = "\n".join([line("infinitely many points of degree " + str(cert['degree']), c["infinite_in_degree"]),
                             line("sporadic", c["sporadic"]), line("isolated", c["isolated"])])
        body = (f"Verified on Mordell and added to the census as **{pid}** (degree {cert['degree']}, status {cert['status']}).\n\n"
                f"{verdict}\n\nPage: {site_url(pid)}")
        github_feedback(v, cert["status"], body, args.no_github)
        outcome = "accepted"
    except Reject as e:
        reason = str(e)
        log(f"  REJECTED: {reason}")
        rec = {"schema": "x1mn-sporadic/rejected/1", "source_file": path.name, "reason": reason,
               "submission": sub,
               "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
        if (jobdir / "magma.log").exists():
            rec["magma_log"] = (jobdir / "magma.log").read_text()[-4000:]
        write_json(REJECTED_DIR / f"{name}.json", rec)
        if v is not None:
            github_feedback(v, "rejected", f"The submission could not be certified: {reason}\n\n"
                            "You are welcome to correct the data and submit again.", args.no_github)
        outcome = "rejected"
    if not args.keep and not args.dry_run:
        SUBMISSIONS_PROCESSED.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(SUBMISSIONS_PROCESSED / f"{name}.{outcome}.json"))
    return outcome


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--mem-gb", type=int, default=16)
    ap.add_argument("--no-github", action="store_true")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-isolation", action="store_true")
    ap.add_argument("--isolation-timeout", type=int, default=1800)
    args = ap.parse_args()
    curves_file = DATA / "curves.json"
    if not curves_file.exists():
        sys.exit("data/curves.json missing: run pipeline/build.py first")
    curves = {f"{c['m']}.{c['n']}": c for c in read_json(curves_file)["curves"]}
    files = [Path(f) for f in args.files] or sorted(SUBMISSIONS_INBOX.glob("*.json"))
    if not files:
        log("nothing to verify")
        return
    WORK.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    summary = {}
    for f in files:
        summary[f.name] = process(f, curves, args)
    log("summary: " + ", ".join(f"{k}: {v}" for k, v in summary.items()))


if __name__ == "__main__":
    main()
