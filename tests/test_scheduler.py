from __future__ import annotations

from datetime import datetime, timedelta, timezone

from amis_agent.application.services.jobs import DEFAULT_JOBS
from amis_agent.application.services.scheduler import CronJob, is_due, run_scheduler


class InMemoryStore:
    def __init__(self):
        self.values = {}

    def get(self, name: str):
        return self.values.get(name)

    def set(self, name: str, ts: datetime):
        self.values[name] = ts


def test_is_due_false_immediately():
    now = datetime(2026, 1, 21, 12, 0, tzinfo=timezone.utc)
    last = now
    assert not is_due("*/5 * * * *", last, now)


def test_is_due_true_after_interval():
    last = datetime(2026, 1, 21, 12, 0, tzinfo=timezone.utc)
    now = last + timedelta(minutes=6)
    assert is_due("*/5 * * * *", last, now)


def test_run_scheduler_initializes_without_enqueue(monkeypatch):
    store = InMemoryStore()
    enqueued = []

    def fake_enqueue(job, job_id=None, **kwargs):
        enqueued.append(job.name)

    monkeypatch.setattr("amis_agent.application.services.scheduler.enqueue_job", fake_enqueue)

    jobs = [CronJob("discover", "*/5 * * * *", DEFAULT_JOBS["discover"])]
    now = datetime(2026, 1, 21, 12, 0, tzinfo=timezone.utc)
    result = run_scheduler(jobs, store.get, store.set, now=now)
    assert result == 0
    assert store.get("discover") == now


def test_run_scheduler_enqueues_when_due(monkeypatch):
    store = InMemoryStore()
    enqueued = []

    def fake_enqueue(job, job_id=None, **kwargs):
        enqueued.append(job.name)

    monkeypatch.setattr("amis_agent.application.services.scheduler.enqueue_job", fake_enqueue)

    jobs = [CronJob("discover", "*/5 * * * *", DEFAULT_JOBS["discover"])]
    first = datetime(2026, 1, 21, 12, 0, tzinfo=timezone.utc)
    later = first + timedelta(minutes=6)
    store.set("discover", first)

    result = run_scheduler(jobs, store.get, store.set, now=later)
    assert result == 1
    assert enqueued == ["discover"]

