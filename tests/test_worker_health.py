from unittest.mock import Mock

import pytest
from kombu.exceptions import OperationalError

from app import worker_health
from app.jobs import celery, health_task


def test_ready_worker_requires_a_valid_worker_pong():
    app = Mock()
    app.control.inspect.return_value.ping.return_value = {
        "insyvera@worker": {"ok": "pong"},
        "celerybeat@worker": {"ok": "pong"},
        "insyvera@broken": {"error": "not ready"},
    }
    assert worker_health.responding_workers(app) == {"insyvera@worker": {"ok": "pong"}}


def test_readiness_retries_during_worker_startup(monkeypatch):
    app = Mock()
    app.control.inspect.return_value.ping.side_effect = [None, {}, {"insyvera@worker": {"ok": "pong"}}]
    sleep = Mock()
    monkeypatch.setattr(worker_health.time, "sleep", sleep)
    assert worker_health.wait_for_worker(app) == {"insyvera@worker": {"ok": "pong"}}
    assert sleep.call_count == 2


def test_readiness_recovers_from_a_transient_broker_error(monkeypatch):
    app = Mock()
    app.control.inspect.return_value.ping.side_effect = [
        OperationalError("sensitive broker URL"), {"insyvera@worker": {"ok": "pong"}},
    ]
    monkeypatch.setattr(worker_health.time, "sleep", Mock())
    assert worker_health.wait_for_worker(app) == {"insyvera@worker": {"ok": "pong"}}


def test_readiness_fails_within_its_budget(monkeypatch):
    app = Mock()
    app.control.inspect.return_value.ping.return_value = None
    clock = Mock(side_effect=[0, 0, 1, 2])
    monkeypatch.setattr(worker_health.time, "monotonic", clock)
    sleep = Mock()
    monkeypatch.setattr(worker_health.time, "sleep", sleep)
    with pytest.raises(RuntimeError, match="docker compose logs"):
        worker_health.wait_for_worker(app, timeout=2, interval=1)
    assert app.control.inspect.call_count == 1


def test_container_probe_targets_its_own_worker(monkeypatch):
    monkeypatch.setattr(worker_health.socket, "gethostname", lambda: "this-container")
    probe = Mock(return_value={"insyvera@this-container": {"ok": "pong"}})
    monkeypatch.setattr(worker_health, "responding_workers", probe)
    assert worker_health.main() == 0
    probe.assert_called_once_with(worker_health.celery, destination=["insyvera@this-container"])


def test_container_probe_cannot_pass_using_another_worker(monkeypatch):
    monkeypatch.setattr(worker_health.socket, "gethostname", lambda: "this-container")
    monkeypatch.setattr(worker_health, "responding_workers", Mock(return_value={"insyvera@other": {"ok": "pong"}}))
    assert worker_health.main() == 1


def test_health_task_echoes_the_probe_nonce():
    assert health_task("unique-nonce") == {"status": "ok", "nonce": "unique-nonce"}


def test_real_worker_pong_and_task_round_trip_with_memory_transport():
    from celery.contrib.testing.worker import start_worker

    # conftest selects memory:// and cache+memory://; this exercises Celery's
    # actual consumer and result path without claiming Redis/Docker coverage.
    assert celery.conf.broker_url == "memory://"
    node = "insyvera@readiness-test"
    with start_worker(celery, hostname=node, pool="solo", perform_ping_check=False):
        assert worker_health.responding_workers(celery, destination=[node]) == {node: {"ok": "pong"}}
        result = health_task.apply_async(args=["queued-nonce"], expires=60)
        try:
            assert result.get(timeout=10) == {"status": "ok", "nonce": "queued-nonce"}
        finally:
            result.forget()
