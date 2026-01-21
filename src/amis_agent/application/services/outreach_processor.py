from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from amis_agent.application.services.compliance import evaluate_compliance
from amis_agent.application.services.email import EmailMessage, SuppressionStore, prepare_message
from amis_agent.core.logging import get_logger


logger = get_logger(service="outreach_processor")


@dataclass(frozen=True)
class OutreachItem:
    outreach_id: int
    to_email: str | None
    subject: str
    body: str
    region: str | None
    is_opt_in: bool


@dataclass(frozen=True)
class OutreachResult:
    outreach_id: int
    status: str
    sent_at: datetime | None
    reason: str | None = None


class Sender(Protocol):
    def send(self, message: EmailMessage) -> dict:  # pragma: no cover - protocol
        ...


class LimitStore(Protocol):
    def can_send(self, ts: datetime, domain: str | None = None) -> bool:  # pragma: no cover - protocol
        ...

    def record_send(self, ts: datetime, domain: str | None = None) -> None:  # pragma: no cover - protocol
        ...


@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
def _send_with_retry(sender: Sender, message: EmailMessage) -> dict:
    return sender.send(message)


def process_outreach_items(
    items: list[OutreachItem],
    *,
    sender: Sender,
    suppression_store: SuppressionStore,
    limit_store: LimitStore | None = None,
) -> list[OutreachResult]:
    results: list[OutreachResult] = []
    for item in items:
        if not item.to_email:
            results.append(OutreachResult(item.outreach_id, "failed", None, "missing_email"))
            continue

        decision = evaluate_compliance(item.region, item.is_opt_in)
        if not decision.allowed:
            results.append(OutreachResult(item.outreach_id, "blocked", None, decision.reason))
            continue

        if suppression_store.is_suppressed(item.to_email):
            results.append(OutreachResult(item.outreach_id, "blocked", None, "suppressed"))
            continue

        message = prepare_message(item.to_email, item.subject, item.body)
        try:
            now = datetime.now(timezone.utc)
            domain = item.to_email.split("@", 1)[-1].lower() if "@" in item.to_email else None
            if limit_store and not limit_store.can_send(now, domain):
                results.append(OutreachResult(item.outreach_id, "blocked", None, "rate_limited"))
                continue
            _send_with_retry(sender, message)
            if limit_store:
                limit_store.record_send(now, domain)
            results.append(OutreachResult(item.outreach_id, "sent", now))
        except RetryError as exc:
            logger.warning("outreach_send_failed", outreach_id=item.outreach_id, error=str(exc))
            results.append(OutreachResult(item.outreach_id, "failed", None, "send_retry_exhausted"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("outreach_send_failed", outreach_id=item.outreach_id, error=str(exc))
            results.append(OutreachResult(item.outreach_id, "failed", None, "send_error"))
    return results

