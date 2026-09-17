#!/usr/bin/env bash
# One verification cycle on Mordell:
#   git pull  ->  fetch submission issues  ->  verify with Magma  ->  rebuild data  ->  commit & push
#
# Usage:  pipeline/run_cycle.sh [--no-push] [--no-github] [extra verify.py options]
# Typical cron line (every 6 hours):
#   0 */6 * * *  cd /home/fnajman/webpage_sporadic && pipeline/run_cycle.sh >> pipeline/logs/cycle.log 2>&1
#
# A lock file prevents overlapping cycles.  Only one Magma job runs at a time (the verifier is
# sequential), each under --timeout / --mem-gb (defaults: 3600 s, 16 GB).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p pipeline/logs
exec 9>pipeline/logs/cycle.lock
if ! flock -n 9; then echo "$(date -u +%FT%TZ) another cycle is running"; exit 0; fi

PUSH=1; VERIFY_OPTS=()
for a in "$@"; do
  case "$a" in
    --no-push) PUSH=0 ;;
    *) VERIFY_OPTS+=("$a") ;;
  esac
done

echo "== $(date -u +%FT%TZ) cycle start"
git pull --rebase --quiet
python3 -B pipeline/fetch_issues.py
python3 -B pipeline/verify.py "${VERIFY_OPTS[@]}"
python3 -B pipeline/build.py
git add data submissions
if git diff --cached --quiet; then
  echo "nothing new"
else
  n_pts=$(ls data/points | wc -l)
  git commit --quiet -m "Verification cycle $(date -u +%F): ${n_pts} points in the census"
  if [ "$PUSH" = 1 ]; then git push --quiet; echo "pushed"; fi
fi
echo "== $(date -u +%FT%TZ) cycle end"
