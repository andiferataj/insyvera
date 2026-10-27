from .db import StorageDeletion, transaction
from .storage import storage

def purge(identifier):
    with transaction() as db:
        job = db.get(StorageDeletion, identifier)
        if not job or job.status == "completed":
            return
        try:
            storage.delete(job.key)
        except Exception:
            job.status = "failed"
            job.error = "Object store unavailable; retry cleanup after recovery."
        else:
            job.status = "completed"
            job.error = None

def retry_failed():
    from sqlalchemy import select
    with transaction() as db:
        identifiers = list(db.scalars(select(StorageDeletion.id).where(StorageDeletion.status != "completed")))
    for identifier in identifiers:
        purge(identifier)
    return len(identifiers)

if __name__ == "__main__":
    print(f"Retried {retry_failed()} pending object deletions.")
