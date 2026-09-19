"""Q3 -- validate exactly ONE shard, selected by JOB_COMPLETION_INDEX.

Environment:
  JOB_COMPLETION_INDEX  injected automatically by an Indexed Job (0..7)
  POD_NAME              Downward API  metadata.name
  NODE_NAME             Downward API  spec.nodeName
  WORK_SECONDS          repeat the validation pass for at least this long, so
                        the pods stay Running long enough for `kubectl get pods
                        -o wide` to capture the concurrency (and so the CPU
                        request is a real, exercised reservation, not a token).

Results are written to STDOUT only -- no shared volume. They are collected
afterwards through the Kubernetes API (see scripts/collect_results.py).
"""
import csv
import json
import os
import re
import sys
import time

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REQUIRED = ("user_id", "email", "signup_date", "country")

index = int(os.getenv("JOB_COMPLETION_INDEX", "0"))
pod = os.getenv("POD_NAME", "unknown-pod")
node = os.getenv("NODE_NAME", "unknown-node")
work_seconds = float(os.getenv("WORK_SECONDS", "25"))
path = f"/data/shard_{index}.csv"

print(f"[shard {index}] pod={pod} node={node} file={path}", flush=True)
if not os.path.exists(path):
    print(f"[shard {index}] FATAL: {path} not found", flush=True)
    sys.exit(1)


def validate_once():
    total = invalid = bad_email = missing_field = 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            total += 1
            miss = [c for c in REQUIRED if not (row.get(c) or "").strip()]
            bad = not EMAIL_RE.match((row.get("email") or "").strip())
            if miss:
                missing_field += 1
            if bad and not miss:
                bad_email += 1
            if miss or bad:
                invalid += 1
    return total, invalid, bad_email, missing_field


t0 = time.time()
passes = 0
while True:
    total, invalid, bad_email, missing_field = validate_once()
    passes += 1
    if time.time() - t0 >= work_seconds:
        break

result = {
    "shard": index,
    "pod": pod,
    "node": node,
    "total_rows": total,
    "invalid_rows": invalid,
    "malformed_email": bad_email,
    "missing_required_field": missing_field,
    "passes": passes,
    "seconds": round(time.time() - t0, 2),
}
print("RESULT " + json.dumps(result), flush=True)
print(f"[shard {index}] done: {invalid}/{total} invalid rows", flush=True)
