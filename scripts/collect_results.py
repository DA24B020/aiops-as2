"""Q3 part 3 -- collect each shard's invalid-row count through the Kubernetes API.

    pip install kubernetes
    python3 scripts/collect_results.py

Reads pod logs via CoreV1Api.read_namespaced_pod_log (the same REST endpoint
`kubectl logs` calls: GET /api/v1/namespaces/{ns}/pods/{pod}/log). No shared
volume is involved -- see the justification in WRITEUP for why a PVC backed by
minikube's hostPath storage provisioner would not work across a 2-node cluster.
"""
import json
import os
import sys
from collections import OrderedDict

from kubernetes import client, config

NAMESPACE = os.getenv("NAMESPACE", "default")
JOB_NAME = os.getenv("JOB_NAME", "shard-validation")
GROUND_TRUTH = {0: 12, 1: 16, 2: 20, 3: 24, 4: 28, 5: 32, 6: 36, 7: 40}

config.load_kube_config()
v1 = client.CoreV1Api()
batch = client.BatchV1Api()

job = batch.read_namespaced_job_status(JOB_NAME, NAMESPACE)
print(f"job {JOB_NAME}: completions={job.spec.completions} parallelism={job.spec.parallelism} "
      f"succeeded={job.status.succeeded} failed={job.status.failed}")

pods = v1.list_namespaced_pod(NAMESPACE, label_selector=f"job-name={JOB_NAME}").items
print(f"found {len(pods)} pods via the API\n")

results = {}
for p in pods:
    try:
        log = v1.read_namespaced_pod_log(p.metadata.name, NAMESPACE)
    except client.ApiException as exc:
        print(f"  !! cannot read logs for {p.metadata.name}: {exc.reason}")
        continue
    if log.startswith("b'") or log.startswith('b"'):
        import ast
        log = ast.literal_eval(log).decode("utf-8", "replace")
    for line in log.splitlines():
        if line.startswith("RESULT "):
            r = json.loads(line[len("RESULT "):])
            results[r["shard"]] = r

if not results:
    sys.exit("no RESULT lines found -- has the Job finished? (kubectl get job)")

hdr = f"{'shard':>5} {'invalid':>8} {'truth':>6} {'email':>6} {'missing':>8} {'node':>22} {'pod':>26}"
print(hdr)
print("-" * len(hdr))
total = 0
ok = True
for k in sorted(results):
    r = results[k]
    total += r["invalid_rows"]
    match = GROUND_TRUTH.get(k) == r["invalid_rows"]
    ok &= match
    print(f"{k:>5} {r['invalid_rows']:>8} {GROUND_TRUTH.get(k, '?'):>6} "
          f"{r['malformed_email']:>6} {r['missing_required_field']:>8} "
          f"{r['node']:>22} {r['pod']:>26}{'' if match else '   <-- MISMATCH'}")
print("-" * len(hdr))
print(f"{'TOTAL':>5} {total:>8} {sum(GROUND_TRUTH.values()):>6}")
print(f"\nshards reported: {len(results)}/8   matches ground truth: {ok}")

nodes = OrderedDict()
for r in results.values():
    nodes.setdefault(r["node"], []).append(r["shard"])
print("\npod -> node distribution (from the Downward API field spec.nodeName):")
for n, shards in nodes.items():
    print(f"  {n}: shards {sorted(shards)}")

os.makedirs("evidence", exist_ok=True)
with open("evidence/q3_results.json", "w") as f:
    json.dump(results, f, indent=2, sort_keys=True)
print("\nsaved -> evidence/q3_results.json")
