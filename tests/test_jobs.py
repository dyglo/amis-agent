from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")
os.environ.setdefault("GMAIL_SENDER", "test@example.com")

from amis_agent.application.services import jobs as jobs_module


class DummyQueue:
    def __init__(self, name: str, connection: object):
        self.name = name
        self.connection = connection
        self.enqueued = []

    def enqueue(self, func_path: str, job_id: str | None, timeout: int, kwargs: dict):
        self.enqueued.append(
            {
                "func_path": func_path,
                "job_id": job_id,
                "timeout": timeout,
                "kwargs": kwargs,
            }
        )
        return self.enqueued[-1]


def test_enqueue_job(monkeypatch):
    dummy = DummyQueue("discover", connection=object())

    def fake_queue(name: str, connection: object):
        assert name == "discover"
        return dummy

    monkeypatch.setattr(jobs_module, "Queue", fake_queue)

    job = jobs_module.DEFAULT_JOBS["discover"]
    result = jobs_module.enqueue_job(job, job_id="jid", lead="x")

    assert result["func_path"] == "amis_agent.workers.discovery.run"
    assert result["job_id"] == "jid"
    assert result["kwargs"]["lead"] == "x"

