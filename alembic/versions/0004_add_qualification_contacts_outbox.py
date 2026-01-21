"""add qualification, contacts, outbox

Revision ID: 0004_add_qual_contacts
Revises: 0003_add_company_website_url
Create Date: 2026-01-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0004_add_qual_contacts"
down_revision = "0003_add_company_website_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("website_domain", sa.String(length=255), nullable=True))
    op.create_index("ix_companies_website_domain", "companies", ["website_domain"])

    op.add_column(
        "leads",
        sa.Column("contact_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.add_column("leads", sa.Column("status", sa.String(length=32), nullable=False, server_default="new"))
    op.add_column("leads", sa.Column("contact_id", sa.Integer(), nullable=True))
    op.create_index("ix_leads_contact_id", "leads", ["contact_id"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_contact_status", "leads", ["contact_status"])

    op.create_table(
        "company_qualification",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False, unique=True),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_company_qualification_company_id", "company_qualification", ["company_id"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "email", name="uq_contacts_company_email"),
    )
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])

    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("personalization_vars", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_outbox_lead_id", "outbox", ["lead_id"])
    op.create_index("ix_outbox_status", "outbox", ["status"])

    op.create_foreign_key(
        "fk_leads_contact_id_contacts",
        "leads",
        "contacts",
        ["contact_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_leads_contact_id_contacts", "leads", type_="foreignkey")

    op.drop_index("ix_outbox_status", table_name="outbox")
    op.drop_index("ix_outbox_lead_id", table_name="outbox")
    op.drop_table("outbox")

    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_index("ix_contacts_company_id", table_name="contacts")
    op.drop_table("contacts")

    op.drop_index("ix_company_qualification_company_id", table_name="company_qualification")
    op.drop_table("company_qualification")

    op.drop_index("ix_leads_contact_status", table_name="leads")
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_index("ix_leads_contact_id", table_name="leads")
    op.drop_column("leads", "contact_id")
    op.drop_column("leads", "status")
    op.drop_column("leads", "contact_status")

    op.drop_index("ix_companies_website_domain", table_name="companies")
    op.drop_column("companies", "website_domain")
