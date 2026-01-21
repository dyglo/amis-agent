"""add outbox llm fields

Revision ID: 0006_outbox_llm
Revises: 0005_add_memory
Create Date: 2026-01-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0006_outbox_llm"
down_revision = "0005_add_memory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbox", sa.Column("subject_variants", sa.JSON(), nullable=True))
    op.add_column("outbox", sa.Column("followup_text", sa.Text(), nullable=True))
    op.add_column("outbox", sa.Column("prompt_hash", sa.String(length=64), nullable=True))
    op.add_column("outbox", sa.Column("llm_model", sa.String(length=128), nullable=True))
    op.add_column("outbox", sa.Column("llm_latency_ms", sa.Integer(), nullable=True))
    op.add_column("outbox", sa.Column("llm_token_usage", sa.JSON(), nullable=True))
    op.add_column("outbox", sa.Column("llm_confidence", sa.Float(), nullable=True))
    op.add_column("outbox", sa.Column("llm_rationale", sa.Text(), nullable=True))
    op.create_index("ix_outbox_prompt_hash", "outbox", ["prompt_hash"])


def downgrade() -> None:
    op.drop_index("ix_outbox_prompt_hash", table_name="outbox")
    op.drop_column("outbox", "llm_rationale")
    op.drop_column("outbox", "llm_confidence")
    op.drop_column("outbox", "llm_token_usage")
    op.drop_column("outbox", "llm_latency_ms")
    op.drop_column("outbox", "llm_model")
    op.drop_column("outbox", "prompt_hash")
    op.drop_column("outbox", "followup_text")
    op.drop_column("outbox", "subject_variants")
