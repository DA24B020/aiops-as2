#!/usr/bin/env bash
set -uo pipefail
JOB=${JOB:-shard-validation}
DURATION=${DURATION:-120}
mkdir -p evidence
OUT=evidence/q3_parallelism.txt
: > "$OUT"

max=0
end=$(( $(date +%s) + DURATION ))
while [ "$(date +%s)" -lt "$end" ]; do
  snap=$(kubectl get pods -l job-name="$JOB" -o wide --no-headers 2>/dev/null)
  running=$(echo "$snap" | grep -c ' Running ' || true)
  [ "$running" -gt "$max" ] && max=$running
  {
    echo "===== $(date -Is)  Running=$running  (max so far=$max) ====="
    kubectl get pods -l job-name="$JOB" -o wide --no-headers
  } | tee -a "$OUT"
  done_n=$(kubectl get job "$JOB" -o jsonpath='{.status.succeeded}' 2>/dev/null || echo 0)
  [ "${done_n:-0}" = "8" ] && break
  sleep 3
done

echo "=====================================================" | tee -a "$OUT"
echo "MAX CONCURRENTLY RUNNING PODS OBSERVED = $max" | tee -a "$OUT"
echo "(manifest declares parallelism: 4)"              | tee -a "$OUT"
echo "saved -> $OUT"
