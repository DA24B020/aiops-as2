# Q3 -- shard validator. Pure stdlib (csv + re), so no pip install at all and
# no builder stage is needed: python:3.11-slim + 8 small CSVs is the whole image.
FROM python:3.11-slim

WORKDIR /app
COPY validate_shard.py /app/validate_shard.py
COPY shards/ /data/

ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/validate_shard.py"]
