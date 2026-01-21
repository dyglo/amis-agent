from __future__ import annotations

from datetime import datetime

from amis_agent.application.services.email_render import render_email_body
from amis_agent.application.services.preflight import run_preflight
from amis_agent.core.signature import EmailSignature
from amis_agent.infrastructure.db.models import CompanyModel, LeadModel, OutboxModel


def _make_models():
    company = CompanyModel(name="Acme Co", website_url="https://acme.example")
    lead = LeadModel(company_id=1, contact_email="a@example.com", contact_status="found", status="enriched")
    outbox = OutboxModel(
        lead_id=1,
        to_email="a@example.com",
        subject="Hello",
        body_text="Hello there.",
        status="approved",
        approved_by_human=True,
        personalization_fact="Has a website at https://acme.example",
        personalization_source_url="https://acme.example",
    )
    return company, lead, outbox


def test_render_adds_signature_and_footer():
    signature = EmailSignature(name="Tafar M", title="Founder", org="AMIS")
    body = render_email_body(body_text="Hi", signature=signature)
    assert "Tafar M" in body
    assert "If I reached the wrong person" in body


def test_preflight_blocks_placeholders():
    company, lead, outbox = _make_models()
    outbox.body_text = "Hi [Your Name]"
    signature = EmailSignature(name="Tafar M", title="Founder", org="AMIS")
    result = run_preflight(outbox=outbox, lead=lead, company=company, signature=signature)
    assert result.allowed is False


def test_preflight_requires_approval():
    company, lead, outbox = _make_models()
    outbox.approved_by_human = False
    signature = EmailSignature(name="Tafar M", title="Founder", org="AMIS")
    result = run_preflight(outbox=outbox, lead=lead, company=company, signature=signature)
    assert result.allowed is False
