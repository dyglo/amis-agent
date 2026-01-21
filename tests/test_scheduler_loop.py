from __future__ import annotations

from amis_agent.workers import scheduler_loop


def test_scheduler_loop_runs_iterations(monkeypatch):
    called = {"count": 0}

    def runner():
        called["count"] += 1

    class FakeTime:
        def sleep(self, _: int) -> None:
            return None

    monkeypatch.setattr(scheduler_loop, "time", FakeTime())

    scheduler_loop.run_loop(sleep_s=0, iterations=2, runner=runner)
    assert called["count"] == 2

