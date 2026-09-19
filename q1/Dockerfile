FROM python:3.11 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends build-essential

WORKDIR /build
COPY requirements-train.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-train.txt

COPY app/generate_dataset.py app/train.py ./
RUN python generate_dataset.py && python train.py

RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/model.joblib /app/model.joblib
COPY app/main.py /app/main.py

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_PATH=/app/model.joblib

USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
