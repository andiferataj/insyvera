"""Celery readiness probes shared by Compose and infrastructure verification."""
import socket
import sys
import time

from kombu.exceptions import OperationalError

from .jobs import celery


def responding_workers(app, *, destination=None, timeout=3):
    """Require a real worker's pong, not merely a running container or beat."""
    replies = app.control.inspect(destination=destination, timeout=timeout).ping() or {}
    return {
        node: reply
        for node, reply in replies.items()
        if node.startswith("insyvera@") and isinstance(reply, dict) and reply.get("ok") == "pong"
    }


def wait_for_worker(app, *, timeout=60, interval=2, probe_timeout=3):
    deadline = time.monotonic() + timeout
    last_error = "No worker returned pong."
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(
                f"No responding Insyvera Celery worker within {timeout:g}s. {last_error} "
                "Inspect `docker compose ps -a` and `docker compose logs --tail=100 worker`."
            )
        try:
            workers = responding_workers(app, timeout=min(probe_timeout, remaining))
            if workers:
                return workers
            last_error = "No worker returned pong."
        except (OperationalError, OSError) as exc:
            # Avoid printing broker connection strings or credentials in CI logs.
            last_error = f"Broker probe raised {type(exc).__name__}."
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(interval, remaining))


def main():
    node = "insyvera@" + socket.gethostname()
    try:
        workers = responding_workers(celery, destination=[node])
    except (OperationalError, OSError):
        print(f"Celery worker {node} is not ready.", file=sys.stderr)
        return 1
    if node not in workers:
        print(f"Celery worker {node} did not return pong.", file=sys.stderr)
        return 1
    print(f"Celery worker {node}: pong")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
