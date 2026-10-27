"""Per-run process locks. Files are on the shared application volume, never user-controlled paths."""
from contextlib import contextmanager
from .config import settings

class BusyRun(Exception):
    pass

@contextmanager
def run_lock(run_id):
    from uuid import UUID
    UUID(run_id)
    directory = settings.data_dir / "locks"
    directory.mkdir(exist_ok=True)
    with (directory / (run_id + ".lock")).open("a+b") as file:
        file.seek(0, 2)
        if file.tell() == 0:
            file.write(b"0")
            file.flush()
        file.seek(0)
        try:
            import os
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise BusyRun("This run is still finishing its current stage. Try again shortly.") from exc
        try:
            yield
        finally:
            file.seek(0)
            if os.name == "nt":
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)
