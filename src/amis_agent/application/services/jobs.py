from __future__ import annotations

from dataclasses import dataclass

from rq import Queue

from amis_agent.infrastructure.queue.redis import get_redis_client


@dataclass(frozen=True)
class JobSpec:
    name: str
    func_path: str
    timeout_s: int = 300


DEFAULT_JOBS = {
    "discover": JobSpec(name="discover", func_path="amis_agent.workers.discovery.run"),
    "qualify": JobSpec(name="qualify", func_path="amis_agent.workers.qualification.run"),
    "enrich": JobSpec(name="enrich", func_path="amis_agent.workers.enrichment.run"),
    "outreach": JobSpec(name="outreach", func_path="amis_agent.workers.outreach.run"),
    "send_outbox": JobSpec(name="send_outbox", func_path="amis_agent.workers.outbox_sender.run"),
}


def get_queue(name: str = "default") -> Queue:
    return Queue(name, connection=get_redis_client())


def enqueue_job(job: JobSpec, job_id: str | None = None, **kwargs: object):
    queue = get_queue(job.name)
    return queue.enqueue(job.func_path, job_id=job_id, timeout=job.timeout_s, kwargs=kwargs)


def enqueue_discovery(job_id: str | None = None, **kwargs: object):
    return enqueue_job(DEFAULT_JOBS["discover"], job_id=job_id, **kwargs)


def enqueue_qualification(job_id: str | None = None, **kwargs: object):
    return enqueue_job(DEFAULT_JOBS["qualify"], job_id=job_id, **kwargs)


def enqueue_outreach(job_id: str | None = None, **kwargs: object):
    return enqueue_job(DEFAULT_JOBS["outreach"], job_id=job_id, **kwargs)


def enqueue_enrichment(job_id: str | None = None, **kwargs: object):
    return enqueue_job(DEFAULT_JOBS["enrich"], job_id=job_id, **kwargs)


def enqueue_outbox_send(job_id: str | None = None, **kwargs: object):
    return enqueue_job(DEFAULT_JOBS["send_outbox"], job_id=job_id, **kwargs)

