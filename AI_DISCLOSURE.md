# AI Disclosure

## 1. Which tools were used

Claude (Anthropic), used interactively through the course of the assignment.

## 2. How they were used

- **Boilerplate generation:** initial drafts of `q1/Dockerfile`, `q1/Dockerfile.naive`,
  `q2/docker-compose.yml`, `q3/validation-job.yaml`, `q4/deployment.yaml`,
  `q4/service.yaml`, the FastAPI service in `app/main.py` including its Redis
  read-through cache, and the helper scripts in `scripts/`.
- **Debugging and troubleshooting:** diagnosing disk exhaustion on my VM; a
  `libgomp1` dependency missing from the `python:3.11-slim` base, which made
  scikit-learn fail to import in the runtime stage; a log-decoding bug in the
  Kubernetes Python client that broke `scripts/collect_results.py`; and the
  single dropped request observed during pod termination in Q4.
- **Conceptual clarification:** multi-stage build semantics, Compose's
  service-name DNS, Indexed Job completion indices, and the difference between
  ReplicaSet reconciliation and event handling.
- **Write-up:** prose drafting of `writeup.tex` from measurements I had already taken.

Not AI-assisted: `app/generate_dataset.py` is reproduced verbatim from the
assignment brief. All execution, measurement and verification is my own — every
figure in the write-up and the videos comes from runs on my own machine, and no
result was supplied by the model. The decision to add `q1/Dockerfile.control` is
also mine: I observed that comparing a full-base single-stage image against a
slim-base multi-stage image confounds two variables, and built the control to
separate them, which produced the 622.6 MB / 530.7 MB decomposition reported in
the write-up.

## 3. Impact

AI assistance accelerated the writing of configuration and boilerplate and
shortened debugging, but the design decisions reported in the write-up — the
parallelism calculation, the requirements split that keeps pandas out of the
runtime image, and the control experiment — were made and justified by me, and
every number reported was measured rather than generated.
