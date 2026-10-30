import hashlib
from uuid import uuid4

import redis
from celery.exceptions import TimeoutError as TaskTimeoutError
from sqlalchemy import text

from app.config import settings
from app.db import transaction
from app.jobs import celery, health_task
from app.storage import storage
from app.worker_health import wait_for_worker


def main():
    assert settings.storage == "s3", "Run this check in the Compose API container."
    with transaction() as db:
        assert db.bind.dialect.name == "postgresql"
        assert db.scalar(text("SELECT ('[1,2,3]'::vector <=> '[1,2,3]'::vector)")) == 0
        assert db.scalar(text(
            "SELECT to_tsvector('english', 'source evidence') @@ plainto_tsquery('english','evidence')"
        ))
    storage.ready()
    key = f"healthchecks/{uuid4()}.txt"
    value = b"Insyvera infrastructure verification"
    storage.put(key, value)
    try:
        assert hashlib.sha256(storage.get(key)).digest() == hashlib.sha256(value).digest()
    finally:
        storage.delete(key)
    assert redis.Redis.from_url(settings.redis_url, socket_connect_timeout=5, socket_timeout=5).ping()

    print("Waiting for Celery worker readiness...", flush=True)
    workers = wait_for_worker(celery, timeout=60)
    print("Responding Celery workers: " + ", ".join(sorted(workers)), flush=True)
    nonce = uuid4().hex
    result = health_task.apply_async(args=[nonce], expires=60)
    try:
        reply = result.get(timeout=30)
        assert reply == {"status": "ok", "nonce": nonce}, "Celery task returned an unexpected result."
    except TaskTimeoutError as exc:
        raise RuntimeError(
            "Celery replied to its readiness ping, but no queued health task completed within 30s. "
            "Inspect `docker compose logs --tail=100 worker`."
        ) from exc
    finally:
        result.forget()
    print("PostgreSQL + pgvector + full-text search + MinIO round-trip + Redis + Celery task: PASS")


if __name__ == "__main__":
    main()
