from celery import Celery
from .config import settings

celery = Celery("insyvera", broker=settings.redis_url or "memory://",
    backend=settings.redis_url or "cache+memory://")
celery.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"],
    task_acks_late=True, worker_prefetch_multiplier=1, task_reject_on_worker_lost=True,
    task_track_started=True, task_time_limit=210, task_soft_time_limit=195,
    broker_connection_retry_on_startup=True, result_expires=3600)

@celery.task(name="insyvera.ingest", autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def ingest_task(version_id):
    from .ingestion import ingest
    ingest(version_id)

@celery.task(name="insyvera.research")
def research_task(run_id, resume=False):
    from .research import execute_run
    execute_run(run_id, resume)

def dispatch(kind, identifier, resume=False):
    task = ingest_task if kind == "ingest" else research_task
    args = (identifier,) if kind == "ingest" else (identifier, resume)
    if settings.eager:
        # API BackgroundTasks invokes this after the response; durable statuses permit explicit retry.
        task(*args)
    else:
        try:
            task.delay(*args)
        except Exception as exc:
            from .db import Run, Version, transaction
            with transaction() as db:
                item = db.get(Version if kind == "ingest" else Run, identifier)
                if item:
                    item.status = "failed"
                    item.error = "Queue unavailable. Retry after the broker recovers."
            raise ConnectionError("Queue dispatch failed") from exc


@celery.task(name="insyvera.cleanup")
def cleanup_task():
    from .gc import retry_failed
    return retry_failed()

celery.conf.beat_schedule = {"storage-cleanup": {"task": "insyvera.cleanup", "schedule": 60.0}}


@celery.task(name="insyvera.health", expires=60, acks_late=False)
def health_task(nonce):
    """A harmless queue/result-backend round trip for infrastructure verification."""
    return {"status": "ok", "nonce": nonce}
