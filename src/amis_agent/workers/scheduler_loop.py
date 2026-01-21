from __future__ import annotations

import time
from typing import Callable

from amis_agent.core.logging import get_logger
from amis_agent.workers.scheduler import run as run_scheduler


logger = get_logger(worker="scheduler_loop")


def run_loop(*, sleep_s: int = 60, iterations: int | None = None, runner: Callable[[], None] = run_scheduler) -> None:
    count = 0
    while True:
        runner()
        count += 1
        if iterations is not None and count >= iterations:
            break
        logger.info("scheduler_sleep", sleep_s=sleep_s)
        time.sleep(sleep_s)


if __name__ == "__main__":
    run_loop()

