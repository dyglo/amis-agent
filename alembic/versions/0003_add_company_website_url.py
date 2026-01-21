"""add company website url

Revision ID: 0003_add_company_website_url
Revises: 0002_add_opt_in
Create Date: 2026-01-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_company_website_url"
down_revision = "0002_add_opt_in"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("website_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "website_url")

