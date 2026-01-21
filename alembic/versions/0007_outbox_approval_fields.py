"""add outbox approval and personalization fields

Revision ID: 0007_outbox_approval
Revises: 0006_outbox_llm
Create Date: 2026-01-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_outbox_approval"
down_revision = "0006_outbox_llm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbox", sa.Column("personalization_fact", sa.Text(), nullable=True))
    op.add_column("outbox", sa.Column("personalization_source_url", sa.String(length=512), nullable=True))
    op.add_column("outbox", sa.Column("approved_by_human", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("outbox", sa.Column("approved_by", sa.String(length=255), nullable=True))
    op.add_column("outbox", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("outbox", "approved_at")
    op.drop_column("outbox", "approved_by")
    op.drop_column("outbox", "approved_by_human")
    op.drop_column("outbox", "personalization_source_url")
    op.drop_column("outbox", "personalization_fact")
