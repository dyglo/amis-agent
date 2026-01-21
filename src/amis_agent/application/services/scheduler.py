from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from croniter import croniter

from amis_agent.application.services.jobs import JobSpec, enqueue_job


@dataclass(frozen=True)
class CronJob:
    name: str
    schedule: str
    job: JobSpec


def is_due(schedule: str, last_run: datetime | None, now: datetime) -> bool:
    base = last_run or now
    itr = croniter(schedule, base)
    next_run = itr.get_next(datetime)
    return next_run <= now


def run_scheduler(
    jobs: Iterable[CronJob],
    last_run_lookup: callable,
    last_run_store: callable,
    now: datetime | None = None,
) -> int:
    timestamp = now or datetime.now(timezone.utc)
    enqueued = 0
    for job in jobs:
        last_run = last_run_lookup(job.name)
        if last_run is None:
            # initialize without firing on first run
            last_run_store(job.name, timestamp)
            continue
        if is_due(job.schedule, last_run, timestamp):
            enqueue_job(job.job)
            last_run_store(job.name, timestamp)
            enqueued += 1
    return enqueued

