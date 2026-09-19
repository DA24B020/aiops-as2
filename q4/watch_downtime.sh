#!/usr/bin/env bash
set -uo pipefail
URL=${URL:-http://$(minikube ip):30080}
DURATION=${DURATION:-120}
mkdir -p evidence
OUT=evidence/q4_downtime_probe.txt
: > "$OUT"

ok=0; fail=0
end=$(( $(date +%s) + DURATION ))
while [ "$(date +%s)" -lt "$end" ]; do
  code=$(curl -s -o /tmp/h.$$ -w '%{http_code}' --max-time 2 "$URL/healthz" || echo 000)
  ver=$(python3 -c "import json,sys;print(json.load(open('/tmp/h.$$')).get('version','-'))" 2>/dev/null || echo '-')
  if [ "$code" = "200" ]; then ok=$((ok+1)); else fail=$((fail+1)); fi
  echo "$(date +%H:%M:%S.%3N)  http=$code  version=$ver  ok=$ok fail=$fail" | tee -a "$OUT"
  sleep 0.2
done
rm -f /tmp/h.$$

{
  echo "========================================================"
  echo "requests: $((ok+fail))   HTTP 200: $ok   non-200/timeout: $fail"
  echo "availability during the rollout = $(awk -v o=$ok -v t=$((ok+fail)) 'BEGIN{printf "%.2f%%", o/t*100}')"
} | tee -a "$OUT"
echo "saved -> $OUT"
