from __future__ import annotations

from datetime import datetime, timezone

from amis_agent.application.services.jobs import DEFAULT_JOBS
from amis_agent.application.services.scheduler import CronJob, run_scheduler
from amis_agent.core.logging import get_logger
from amis_agent.infrastructure.queue.scheduler_store import SchedulerStore


logger = get_logger(worker="scheduler")


def run() -> None:
    store = SchedulerStore()
    jobs = [
        CronJob("discover", "0 */6 * * *", DEFAULT_JOBS["discover"]),
        CronJob("qualify", "15 */6 * * *", DEFAULT_JOBS["qualify"]),
        CronJob("enrich", "25 */6 * * *", DEFAULT_JOBS["enrich"]),
        CronJob("outreach", "30 */6 * * *", DEFAULT_JOBS["outreach"]),
    ]
    enqueued = run_scheduler(
        jobs,
        last_run_lookup=store.get_last_run,
        last_run_store=store.set_last_run,
        now=datetime.now(timezone.utc),
    )
    logger.info("scheduler_run", enqueued=enqueued)

