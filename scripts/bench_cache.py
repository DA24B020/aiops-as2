"""Q2 part 3 -- averaged cache MISS vs HIT benchmark (stdlib only).

Run from the repo root while `docker compose up` is running:
    python3 scripts/bench_cache.py            # N=30 by default
    N=100 python3 scripts/bench_cache.py

Fairness:
  * warm-up request on a different string, excluded from statistics, so the
    MISS mean is not inflated by sklearn's one-off lazy imports;
  * MISS = N distinct never-seen texts, HIT = N repeats of one cached text;
  * reports end-to-end wall time AND the server-side X-Compute-Ms header.
"""
import json
import os
import statistics
import urllib.request
from datetime import datetime, timezone

URL = os.getenv("URL", "http://localhost:8000/predict")
N = int(os.getenv("N", "30"))
BASE = "URGENT: Your account will be suspended. Verify at bit.ly/xyz123"


def call(text):
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json"}
    )
    t0 = __import__("time").perf_counter()
    with urllib.request.urlopen(req) as r:
        payload = json.loads(r.read())
        cache = r.headers.get("X-Cache")
        compute = float(r.headers.get("X-Compute-Ms", "nan"))
    return (__import__("time").perf_counter() - t0) * 1000, cache, compute, payload


lines = [f"=== Q2 averaged cache benchmark  {datetime.now(timezone.utc).isoformat()} ===",
         f"URL={URL}  N={N}"]

call("warm-up string, excluded from statistics")

e2e_miss, e2e_hit, srv_miss, srv_hit = [], [], [], []
for i in range(N):
    t, c, s, p = call(f"{BASE} unique-{i}")
    assert c == "MISS", f"expected MISS, got {c} -- is REDIS_HOST set?"
    e2e_miss.append(t); srv_miss.append(s)
    if i == 0:
        lines.append(f"first call  : X-Cache={c} e2e={t:.3f}ms server={s:.3f}ms body={p}")
    t, c, s, p = call(BASE)
    if i == 0:
        lines.append(f"second call : X-Cache={c} e2e={t:.3f}ms server={s:.3f}ms body={p}")
        assert c in ("MISS", "HIT")
    e2e_hit.append(t); srv_hit.append(s)

m, h = statistics.mean(e2e_miss), statistics.mean(e2e_hit)
sm, sh = statistics.mean(srv_miss), statistics.mean(srv_hit)
lines += [
    "",
    f"end-to-end   MISS mean={m:7.3f} ms  median={statistics.median(e2e_miss):7.3f} ms",
    f"end-to-end   HIT  mean={h:7.3f} ms  median={statistics.median(e2e_hit):7.3f} ms",
    f"server-side  MISS mean={sm:7.3f} ms   (tfidf.transform + nb.predict + SETEX)",
    f"server-side  HIT  mean={sh:7.3f} ms   (single redis GET)",
    "",
    f"end-to-end speed-up : {m / h:.2f}x  ({(m - h) / m * 100:.1f}% faster)",
    f"server-side speed-up: {sm / sh:.2f}x  ({(sm - sh) / sm * 100:.1f}% faster)",
]

out = "\n".join(lines)
print(out)
os.makedirs("evidence", exist_ok=True)
with open("evidence/q2_cache_benchmark.txt", "w") as f:
    f.write(out + "\n")
print("\nsaved -> evidence/q2_cache_benchmark.txt")
