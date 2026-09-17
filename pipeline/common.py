"""Shared helpers for the x1mn-sporadic pipeline (paths, GitHub API, JSON I/O)."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
POINTS_DIR = DATA / "points"
REJECTED_DIR = DATA / "rejected"
KNOWLEDGE_DIR = DATA / "knowledge"
SUBMISSIONS_INBOX = ROOT / "submissions" / "inbox"
SUBMISSIONS_PROCESSED = ROOT / "submissions" / "processed"
PIPELINE = ROOT / "pipeline"
WORK = PIPELINE / "work"
LOGS = PIPELINE / "logs"

GITHUB_ORG = "x1mn-sporadic"
GITHUB_REPO = "x1mn-sporadic.github.io"
GITHUB_API = "https://api.github.com"
SUBMISSION_LABEL = "submission"

SCHEMA_SUBMISSION = "x1mn-sporadic/submission/1"
SCHEMA_CERTIFICATE = "x1mn-sporadic/point/1"

# Whitelists for strings that reach Magma's `eval`.  Nothing else is ever evaluated.
RE_FIELD_POLY = re.compile(r"^[0-9x\s+\-*/^()]+$")
RE_ELEMENT = re.compile(r"^[0-9a\s+\-*/^()]+$")
RE_XY = re.compile(r"^[0-9xy\s+\-*/^()]+$")
MAX_STRING = 20000


def read_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- GitHub

def github_token() -> str | None:
    """GITHUB_TOKEN from the environment, else the github.com entry of ~/.git-credentials."""
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok.strip()
    cred = Path.home() / ".git-credentials"
    if cred.exists():
        for line in cred.read_text().splitlines():
            if "github.com" in line:
                m = re.match(r"https://(?:[^:@]*:)?([^@]+)@github\.com", line.strip())
                if m:
                    return m.group(1)
    return None


def github_request(method: str, path: str, data=None, token: str | None = None, params=None):
    url = GITHUB_API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "x1mn-sporadic-pipeline"}
    if token:
        headers["Authorization"] = f"token {token}"
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            txt = resp.read().decode()
            return json.loads(txt) if txt else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub {method} {path} -> {e.code}: {e.read().decode()[:500]}") from e


def repo_path(suffix: str) -> str:
    return f"/repos/{GITHUB_ORG}/{GITHUB_REPO}{suffix}"
