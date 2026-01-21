from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from sqlalchemy import select

from amis_agent.application.services.send_outbox import send_outbox_draft, SendBlockedError
from amis_agent.core.config import get_settings
from amis_agent.core.signature import load_signature
from amis_agent.infrastructure.db.models import OutboxModel
from amis_agent.infrastructure.db.session import SessionLocal


load_dotenv()


@dataclass(frozen=True)
class SendResult:
    status: str
    response: dict | None


def send_real_email(to_email: str, subject: str, body: str) -> SendResult:
    raise SystemExit("direct_send_disabled: use outbox flow")


async def send_outbox_email(outbox_id: int) -> SendResult:
    async with SessionLocal() as session:
        try:
            result = await send_outbox_draft(session, outbox_id)
        except SendBlockedError as exc:  # noqa: BLE001
            raise SystemExit(str(exc)) from exc
        return SendResult(status=result.status, response=result.response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outbox-id", type=int, default=None)
    args = parser.parse_args()
    if args.outbox_id is not None:
        import asyncio

        result = asyncio.run(send_outbox_email(args.outbox_id))
        print(result)
        return
    to_email = os.environ.get("REAL_EMAIL_TO")
    if not to_email:
        raise SystemExit("REAL_EMAIL_TO is required to run this script")
    subject = os.environ.get("REAL_EMAIL_SUBJECT", "AMIS Agent Test")
    body = os.environ.get("REAL_EMAIL_BODY", "This is a real send test.")
    result = send_real_email(to_email, subject, body)
    print(result)


if __name__ == "__main__":
    main()

