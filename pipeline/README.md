# Verification pipeline (runs on Mordell)

```
submissions/inbox/*.json  ──verify.py──►  data/points/<id>.json   (+ data/logs/<id>.log)
        ▲                                 data/rejected/<name>.json
fetch_issues.py (GitHub issues)           build.py ──► data/curves.json, data/points.json, data/sources.json
```

| file | role |
|---|---|
| `run_cycle.sh` | the whole cycle: `git pull` → `fetch_issues.py` → `verify.py` → `build.py` → commit → push. Cron-able; uses a lock file. |
| `fetch_issues.py` | turns open GitHub issues labelled `submission` into `submissions/inbox/issue-<n>.json`. |
| `verify.py` | validates a submission, runs `magma/verify_lib.m` and `magma/isolation_lib.m` under timeouts, classifies the point with `knowledge.py`, writes the certificate, comments on and closes the issue. Automatic limits (`LIMITS`: field degree ≤ 30, points required above degree 8, isolation for genus ≤ 60) and per-run budgets (`--max-jobs 8`, `--budget 2700` s of Magma time); submissions beyond the limits go to `submissions/manual/` with the issue labelled `manual`, to be run by the maintainer with `--force`. |
| `build.py` | rebuilds the JSON files the site reads from `data/knowledge/` + `data/points/`. `--check` fails if they are stale (used by CI). |
| `knowledge.py` | curated, cited facts: Φ^∞(d) for d ≤ 9, rank-0 theorems, gonality bounds, Frey/Abramovich, per-point facts (`CURATED_POINTS`, e.g. a published AV-isolation proof on a positive-rank curve), and the three yes/no/maybe answers (sporadic = finitely many points of degree ≤ d; isolated; infinitely many points of degree d). |
| `import_vanhoeij.py` | converts van Hoeij's `LowDegreePlaces` into submissions (`--max-N`). |
| `reclassify.py` | recomputes the three answers and the status of every certificate from the current knowledge (no Magma); run after editing `knowledge.py` or the tables, then `build.py`. |
| `magma/verify_lib.m` | the Magma checks (see its header). `magma/curve_invariants.m` computed genus/index of every curve. |
| `magma/isolation_lib.m` | P¹-isolation: reduces the point to a divisor on Sutherland's model over 𝔽_q and computes dim L (semicontinuity gives l(x) = 1 over ℚ); m ≤ 2. Needs `external/mdmagma` (git submodule, pinned) and `models/X1_m_n/`. |
| `tests/fixtures/` | known positives (van Hoeij) and a negative control; `tests/private/` (git-ignored) holds unpublished points. |

Clone with `git clone --recurse-submodules` (or `git submodule update --init --recursive`) so that
`pipeline/external/mdmagma` is present; without it the isolation check is skipped and the isolated
column stays "maybe" (unless the degree is known to be finite).

## Running by hand

```sh
cd /home/fnajman/webpage_sporadic
python3 -B pipeline/fetch_issues.py --dry-run          # what would be queued
python3 -B pipeline/verify.py --no-github --keep pipeline/tests/fixtures/*.json   # smoke test (then delete data/points/1.*.json it created!)
python3 -B pipeline/verify.py                           # process the inbox, update issues
python3 -B pipeline/build.py                            # rebuild site data
pipeline/run_cycle.sh                                   # everything, then push
```

Magma is always started with `< /dev/null` (otherwise a script error leaves it waiting on stdin) and its
exit status is ignored (it is 0 even after errors): `verify.py` trusts only the JSON that
`verify_lib.m` writes and the `VERIFY_DONE` marker in the log.

Every change to `magma/verify_lib.m` changes the SHA-256 recorded in new certificates; old certificates
keep the hash of the code that produced them.

## Credits

A certificate credits the discovery of the point (`discovery`: `by`, `year`) separately from the
proofs that it is sporadic or isolated (`credits`: `sporadic` / `isolated`, each `by`, `year`,
`reference`). The `credits` are only recorded when such a proof preceded this census -- given in the
submission as `"credits": {"isolated": {"by": ..., "year": ..., "reference": ...}}` or, on the issue
form, as the free text "names (year), reference" of the fields *Proved sporadic by* / *Proved
isolated by*. When no explicit credit is recorded the point page credits the cited results the
answer follows from (the `sources` of the classification), or the census's own computation of
`dim L(x) = 1` for isolation. To credit an already accepted point, add the `credits` block to its
certificate by hand (the three points 1.21.3.a, 1.28.9.a and 1.37.18.a were done this way).

## Processing deferred submissions by hand

```sh
python3 -B pipeline/verify.py --force --max-jobs 0 --budget 0 --timeout 7200 --isolation-timeout 7200 submissions/manual/issue-12.json
```
Only three concurrent Magma jobs are allowed on Mordell; the verifier is sequential, so run one such command at a time.

## Adding knowledge

Facts about curves (gonality, rank, degrees with finitely/infinitely many points) live in
`knowledge.py` and `data/knowledge/sources/`. To add e.g. a new gonality result, add a source to
`SOURCES` and the fact to the relevant table, rebuild with `build.py`, and re-run `verify.py` on the
affected "verified" points if you want them re-classified (delete their certificate and put the
submission back into the inbox; the id is re-assigned).
