from __future__ import annotations

import argparse
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import select

from amis_agent.infrastructure.db.models import OutboxModel
from amis_agent.infrastructure.db.session import SessionLocal


load_dotenv()


async def approve_outbox(outbox_id: int, approved_by: str) -> None:
    async with SessionLocal() as session:
        draft = (
            await session.execute(select(OutboxModel).where(OutboxModel.id == outbox_id))
        ).scalar_one_or_none()
        if not draft:
            raise SystemExit(f"outbox_id_not_found:{outbox_id}")
        if draft.status != "ready_for_review":
            raise SystemExit(f"outbox_status_not_ready:{draft.status}")
        draft.status = "approved"
        draft.approved_by_human = True
        draft.approved_by = approved_by
        draft.approved_at = datetime.now(timezone.utc)
        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outbox-id", type=int, required=True)
    parser.add_argument("--approved-by", type=str, default="cli")
    args = parser.parse_args()

    import asyncio

    asyncio.run(approve_outbox(args.outbox_id, args.approved_by))
    print(f"approved_outbox:{args.outbox_id}")


if __name__ == "__main__":
    main()
