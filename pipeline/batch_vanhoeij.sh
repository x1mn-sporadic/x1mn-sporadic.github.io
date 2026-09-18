#!/usr/bin/env bash
# Import van Hoeij's places for the rank-0 curves X_1(N), 41 <= N <= 60 (all degrees), and
# N = 62, 64, 66 (degree <= 30): verification of every place (sequential, seconds each), then
# one batch isolation run per curve (pipeline/reisolate.py), two curves at a time, in order of
# increasing genus.  Resumable: verified places are skipped as duplicates, reisolate.py only
# takes points whose isolation is not yet computed.  Logs in pipeline/logs/batch_*.log.
set -uo pipefail
cd "$(dirname "$0")/.."
RANK0_41_60="41 44 45 46 47 48 49 50 51 52 54 55 56 59 60"
RANK0_61_66="62 64 66"
mkdir -p pipeline/logs
if [ "${1:-}" != "--resume" ]; then
echo "== $(date -u +%FT%TZ) import"
for N in $RANK0_41_60; do python3 -B pipeline/import_vanhoeij.py --min-N $N --max-N $N; done
for N in $RANK0_61_66; do python3 -B pipeline/import_vanhoeij.py --min-N $N --max-N $N; done
# drop places of degree > 30 for N = 62, 64, 66
python3 - <<'PY'
import json, glob, os
for f in glob.glob("submissions/inbox/vanhoeij_6[246]_*.json"):
    if json.load(open(f))["degree"] > 30: os.remove(f)
PY
fi
echo "== $(date -u +%FT%TZ) verification of $(ls submissions/inbox | wc -l) submissions (no isolation)"
python3 -B pipeline/verify.py --no-github --no-isolation --force --max-jobs 0 --budget 0 --timeout 900 > pipeline/logs/batch_verify.log 2>&1
grep -c ACCEPTED pipeline/logs/batch_verify.log; grep REJECTED pipeline/logs/batch_verify.log | sed 's/.*REJECTED: //' | cut -c1-60 | sort | uniq -c | sort -rn | head
python3 -B pipeline/build.py
echo "== $(date -u +%FT%TZ) isolation, two curves at a time, by increasing genus"
# genus order: 44(36) 48(37) 45(41) 46(45) 50(48) 41(51) 54(52) 52(55) 60(57) 56(61) 51(65) 49(69) 47(70) 55(81) 66(81) 62(91) 64(93) 59(117)
printf "%s\n" 44 48 45 46 50 41 54 52 60 56 51 49 47 55 66 62 64 59 | xargs -P 2 -I{} sh -c 'python3 -B pipeline/reisolate.py --m 1 --n {} --timeout 43200 > pipeline/logs/batch_iso_{}.log 2>&1; tail -1 pipeline/logs/batch_iso_{}.log'
python3 -B pipeline/build.py
echo "== $(date -u +%FT%TZ) done"
