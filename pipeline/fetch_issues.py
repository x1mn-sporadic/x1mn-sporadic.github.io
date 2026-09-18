#!/usr/bin/env python3
"""Pull open submission issues from GitHub into submissions/inbox/ as JSON files.

Usage:  python3 pipeline/fetch_issues.py [--dry-run]

Reads the issues labelled `submission` that are still open and not yet queued or processed, parses
the issue-form body (### Label / value blocks) into the submission schema, and writes
submissions/inbox/issue-<number>.json.  Needs a GitHub token (GITHUB_TOKEN or ~/.git-credentials)
only for private repositories or higher rate limits; reading public issues works without one.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (SCHEMA_SUBMISSION, SUBMISSION_LABEL, SUBMISSIONS_INBOX, SUBMISSIONS_PROCESSED,  # noqa: E402
                    github_request, github_token, log, repo_path, write_json)

LABELS = {
    "m": "m", "n": "n", "number field": "field", "a-invariants": "ainvs", "tate normal form (b, c)": "tate",
    "van hoeij format (eqxy)": "eqxy", "point q of order n": "Q", "point p of order m (only if m > 1)": "P",
    "degree of the point": "degree", "reference": "reference", "your name and affiliation": "name", "notes": "notes",
    "discovered by": "discoverer", "year of discovery": "year",
    "proved sporadic by": "sporadic_by", "proved isolated by": "isolated_by",
}
DONE_LABELS = {"certified", "verified", "rejected", "manual"}


def parse_body(body: str) -> dict:
    fields = {}
    parts = re.split(r"^### (.+?)\s*$", body.replace("\r\n", "\n"), flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        label = parts[i].strip().lower()
        value = parts[i + 1].strip()
        if value == "_No response_":
            value = ""
        if label in LABELS:
            fields[LABELS[label]] = value
    return fields


def coords(s: str):
    s = s.strip().strip("()[]").strip()
    if not s:
        return None
    xy = [t.strip() for t in s.split(",")]
    return xy if len(xy) == 2 else ["invalid", s]


def to_submission(issue: dict) -> dict:
    f = parse_body(issue.get("body") or "")
    sub = {"schema": SCHEMA_SUBMISSION, "m": f.get("m", "").strip(), "n": f.get("n", "").strip(),
           "field": f.get("field", "").strip(), "curve": {}, "points": {}}
    if f.get("ainvs"):
        inner = f["ainvs"].strip().strip("[]")
        sub["curve"] = {"ainvs": [t.strip() for t in inner.split(",")]}
    elif f.get("tate"):
        mm = re.match(r"\s*b\s*=\s*(.+?)\s*,\s*c\s*=\s*(.+?)\s*$", f["tate"])
        sub["curve"] = {"tate": {"b": mm.group(1), "c": mm.group(2)}} if mm else {"tate": {"b": "?", "c": f["tate"]}}
    elif f.get("eqxy"):
        sub["curve"] = {"vanhoeij": {"eqxy": f["eqxy"].strip()}}
    for name in ("P", "Q"):
        c = coords(f.get(name, ""))
        if c:
            sub["points"][name] = c
    if f.get("degree", "").strip().isdigit():
        sub["degree"] = int(f["degree"].strip())
    name = f.get("name", "").strip()
    sub["submitter"] = name.split(",")[0].strip() if name else (issue["user"]["login"] if issue.get("user") else "")
    sub["affiliation"] = ",".join(name.split(",")[1:]).strip() if "," in name else ""
    sub["github"] = issue["user"]["login"] if issue.get("user") else ""
    sub["reference"] = f.get("reference", "").strip()
    sub["discoverer"] = f.get("discoverer", "").strip()
    sub["year"] = int(f["year"].strip()) if f.get("year", "").strip().isdigit() else f.get("year", "").strip()
    sub["notes"] = f.get("notes", "").strip()
    for k in ("sporadic_by", "isolated_by"):
        if f.get(k, "").strip():
            sub[k] = f[k].strip()
    sub["date"] = (issue.get("created_at") or "")[:10]
    sub["source"] = {"kind": "issue", "number": issue["number"], "url": issue.get("html_url", "")}
    for k in ("m", "n"):
        try:
            sub[k] = int(sub[k])
        except ValueError:
            pass
    return sub


def already_known(number: int) -> bool:
    for d in (SUBMISSIONS_INBOX, SUBMISSIONS_PROCESSED):
        if list(d.glob(f"issue-{number}.*json")) or (d / f"issue-{number}.json").exists():
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    tok = github_token()
    issues = []
    page = 1
    while True:
        batch = github_request("GET", repo_path("/issues"), token=tok,
                               params={"labels": SUBMISSION_LABEL, "state": "open", "per_page": 100, "page": page})
        if not batch:
            break
        issues.extend(i for i in batch if "pull_request" not in i)
        if len(batch) < 100:
            break
        page += 1
    SUBMISSIONS_INBOX.mkdir(parents=True, exist_ok=True)
    n_new = 0
    for issue in issues:
        labels = {l["name"] for l in issue.get("labels", [])}
        if labels & DONE_LABELS or already_known(issue["number"]):
            continue
        sub = to_submission(issue)
        target = SUBMISSIONS_INBOX / f"issue-{issue['number']}.json"
        if args.dry_run:
            log(f"[dry-run] would write {target}: X_1({sub['m']},{sub['n']}) by {sub['submitter']}")
        else:
            write_json(target, sub)
            log(f"queued issue #{issue['number']} -> {target.name}")
        n_new += 1
    log(f"{len(issues)} open submission issue(s), {n_new} newly queued")


if __name__ == "__main__":
    main()
