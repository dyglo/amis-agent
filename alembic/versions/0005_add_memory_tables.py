"""add memory tables and snippet

Revision ID: 0005_add_memory
Revises: 0004_add_qual_contacts
Create Date: 2026-01-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0005_add_memory"
down_revision = "0004_add_qual_contacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("about_snippet", sa.String(length=512), nullable=True))

    op.create_table(
        "industry_insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("preferred_persona", sa.String(length=64), nullable=True),
        sa.Column("preferred_subject_variant", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("industry", name="uq_industry_insights_industry"),
    )
    op.create_index("ix_industry_insights_industry", "industry_insights", ["industry"])

    op.create_table(
        "reply_patterns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_text", sa.String(length=255), nullable=False),
        sa.Column("classification", sa.String(length=64), nullable=True),
        sa.Column("occurrences", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("pattern_text", name="uq_reply_patterns_pattern_text"),
    )
    op.create_index("ix_reply_patterns_pattern_text", "reply_patterns", ["pattern_text"])


def downgrade() -> None:
    op.drop_index("ix_reply_patterns_pattern_text", table_name="reply_patterns")
    op.drop_table("reply_patterns")

    op.drop_index("ix_industry_insights_industry", table_name="industry_insights")
    op.drop_table("industry_insights")

    op.drop_column("companies", "about_snippet")
