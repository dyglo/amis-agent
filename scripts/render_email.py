from __future__ import annotations

import argparse

from sqlalchemy import select

from amis_agent.application.services.email_render import render_email_body
from amis_agent.core.signature import load_signature
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel, OutboxModel
from amis_agent.infrastructure.db.session import SessionLocal


async def render_outbox(outbox_id: int) -> str:
    signature = load_signature()
    async with SessionLocal() as session:
        draft = (
            await session.execute(select(OutboxModel).where(OutboxModel.id == outbox_id))
        ).scalar_one_or_none()
        if not draft:
            raise SystemExit(f"outbox_id_not_found:{outbox_id}")
        lead = (
            await session.execute(select(LeadModel).where(LeadModel.id == draft.lead_id))
        ).scalar_one_or_none()
        company = None
        if lead:
            company = (
                await session.execute(select(CompanyModel).where(CompanyModel.id == lead.company_id))
            ).scalar_one_or_none()
        if not lead or not company:
            raise SystemExit("lead_or_company_missing")
        return render_email_body(body_text=draft.body_text, signature=signature)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outbox-id", type=int, required=True)
    args = parser.parse_args()
    import asyncio

    rendered = asyncio.run(render_outbox(args.outbox_id))
    print(rendered)


if __name__ == "__main__":
    main()
