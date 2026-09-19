"""Spam-detection REST API.

Contract required by the assignment:
  POST /predict  {"text": "..."}  ->  {"label": "spam"|"ham"}   (body is EXACTLY this)
  GET  /healthz  -> HTTP 200 once the model is loaded, 503 before

Evidence channels that do NOT change the required response body:
  X-Cache        : HIT | MISS | DISABLED
  X-Compute-Ms   : server-side milliseconds spent producing the label
"""
import hashlib
import os
import time
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, Response
from pydantic import BaseModel

APP_VERSION = "2.0.0"

MODEL_PATH = os.getenv("MODEL_PATH", "model.joblib")
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

STATE = {"model": None, "redis": None}


def _cache_key(text: str) -> str:
    """Exact-input key. Hashed so arbitrarily long / non-ASCII text is a safe key."""
    return "spam:v1:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE["model"] = joblib.load(MODEL_PATH)
    STATE["model"].predict(["warmup message"])
    if REDIS_HOST:
        import redis

        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        try:
            client.ping()
            STATE["redis"] = client
            print(f"[startup] redis cache enabled at {REDIS_HOST}:{REDIS_PORT} ttl={CACHE_TTL}s")
        except Exception as exc:
            print(f"[startup] redis unavailable ({exc}); running without cache")
    else:
        print("[startup] REDIS_HOST unset; running without cache")
    print(f"[startup] model loaded from {MODEL_PATH}; version={APP_VERSION}")
    yield
    STATE["model"] = None


app = FastAPI(title="spam-detection-api", version=APP_VERSION, lifespan=lifespan)


class PredictRequest(BaseModel):
    text: str


@app.get("/healthz")
def healthz(response: Response):
    if STATE["model"] is None:
        response.status_code = 503
        return {"status": "loading"}
    return {"status": "ok", "version": APP_VERSION}


@app.post("/predict")
def predict(req: PredictRequest, response: Response):
    t0 = time.perf_counter()
    r = STATE["redis"]

    if r is None:
        label = str(STATE["model"].predict([req.text])[0])
        response.headers["X-Cache"] = "DISABLED"
        response.headers["X-Compute-Ms"] = f"{(time.perf_counter() - t0) * 1000:.3f}"
        return {"label": label}

    key = _cache_key(req.text)
    try:
        cached = r.get(key)
    except Exception as exc:
        print(f"[cache] GET failed: {exc}")
        cached = None

    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Compute-Ms"] = f"{(time.perf_counter() - t0) * 1000:.3f}"
        return {"label": cached}

    label = str(STATE["model"].predict([req.text])[0])
    try:
        r.setex(key, CACHE_TTL, label)
    except Exception as exc:
        print(f"[cache] SETEX failed: {exc}")
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Compute-Ms"] = f"{(time.perf_counter() - t0) * 1000:.3f}"
    return {"label": label}
