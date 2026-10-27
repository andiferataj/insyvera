import hashlib
from sqlalchemy import text
from app.db import transaction
from app.jobs import celery
from app.storage import storage
from app.config import settings

assert settings.storage == "s3", "Run this check in the Compose API container."
with transaction() as db:
    assert db.bind.dialect.name == "postgresql"
    assert db.scalar(text("SELECT ('[1,2,3]'::vector <=> '[1,2,3]'::vector)")) == 0
    assert db.scalar(text("SELECT to_tsvector('english', 'source evidence') @@ plainto_tsquery('english','evidence')"))
storage.ready()
key = "healthchecks/infrastructure-test.txt"
value = b"Insyvera infrastructure verification"
storage.put(key, value)
assert hashlib.sha256(storage.get(key)).digest() == hashlib.sha256(value).digest()
storage.delete(key)
import redis
assert redis.Redis.from_url(settings.redis_url).ping()
workers = celery.control.inspect(timeout=5).ping()
assert workers, "No responding Celery worker."
print("PostgreSQL + pgvector + full-text search + MinIO round-trip + Redis + Celery worker: PASS")
