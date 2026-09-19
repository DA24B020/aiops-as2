# AIOps Module 3 — Spam-Detection API: Docker & Kubernetes

Submission for the Module 3 Infrastructure & Containerization assignment.
Write-up: `DA3408_AS2.pdf`. Demonstration videos are submitted separately.
AI assistance is disclosed in `AI_DISCLOSURE.md`.

## Layout

```
app/                    shared application source (used by Q1, Q2 and Q4)
  generate_dataset.py     dataset generator (given in the assignment)
  train.py                TF-IDF + MultinomialNB, runs at image build time
  main.py                 FastAPI service: POST /predict, GET /healthz
requirements.txt        runtime dependencies (what ships in the image)
requirements-train.txt  build-time dependencies (pandas — never ships)

q1/  Dockerfile.naive    single-stage build         -> spam-api:naive  1599.2 MB
     Dockerfile          multi-stage build          -> spam-api:v1      445.9 MB  (-72.1%)
     Dockerfile.control  single-stage on slim base, built only to separate the
                         base-image effect from the multi-stage effect (976.6 MB)

q2/  docker-compose.yml  api + redis, service-name networking, read-through cache

q3/  validation-job.yaml Indexed Job, completions 8, parallelism 4
     validator/          validate_shard.py, generate_shards.py, Dockerfile, shards/

q4/  deployment.yaml     2 replicas, readiness probe, maxUnavailable 0
     service.yaml        NodePort 30080
     watch_downtime.sh   availability probe run during the rolling update

scripts/  bench_cache.py       averaged cache MISS vs HIT benchmark (Q2)
          watch_parallelism.sh records max concurrently Running pods (Q3)
          collect_results.py   collects shard results via the Kubernetes API (Q3)
evidence/ captured output from the runs shown in the videos
```

## API contract

- `POST /predict` `{"text": "..."}` -> `{"label": "spam"|"ham"}` — the body is exactly this
- `GET /healthz` -> 200 `{"status":"ok","version":"..."}` once the model is loaded
- Additional evidence headers that do not alter the contract: `X-Cache` (HIT/MISS/DISABLED), `X-Compute-Ms`

Redis is optional at runtime: with `REDIS_HOST` unset or unreachable the service logs a
warning and serves without a cache. That is why the one image serves Q1, Q2 and Q4 unchanged.

## Reproducing

```
# Q1
docker build -f q1/Dockerfile.naive -t spam-api:naive .
docker build -f q1/Dockerfile       -t spam-api:v1    .

# Q2
cd q2 && docker compose up -d && cd ..
N=50 python3 scripts/bench_cache.py

# Q3
minikube start --nodes=2 --cpus=2 --memory=2500 --driver=docker
python3 q3/validator/generate_shards.py
docker build -t shard-validator:v1 q3/validator/
minikube image load shard-validator:v1
kubectl apply -f q3/validation-job.yaml
python3 scripts/collect_results.py

# Q4
minikube image load spam-api:v1
kubectl apply -f q4/deployment.yaml -f q4/service.yaml
```

Build contexts are the repository root, because `app/` and the requirements files are
shared across questions; the Dockerfile is selected with `-f`.
