from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/amis_agent")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_DISPLAY_NAME", "Test User")
os.environ.setdefault("COMPANY_NAME", "TestCo")
os.environ.setdefault("FOOTER_ADDRESS", "415 Mission St, 3rd Floor, San Francisco, CA 94105")
os.environ.setdefault("LLM_MODEL", "test-model")

from amis_agent.application.services.llm_email_writer import LLMEmailInput, LLMEmailWriter  # noqa: E402
from amis_agent.infrastructure.db.models import CompanyModel, ContactModel, LeadModel  # noqa: E402
from amis_agent.infrastructure.llm.client import LLMResponse  # noqa: E402


class DummyClient:
    def __init__(self, content: str):
        self.content = content

    def create_chat_completion(self, *, model: str, messages: list[dict], max_tokens: int, temperature: float = 0.4):
        return LLMResponse(content=self.content, model=model, usage={"total_tokens": 10}, latency_ms=12)


class FailingClient:
    def create_chat_completion(self, *, model: str, messages: list[dict], max_tokens: int, temperature: float = 0.4):
        raise RuntimeError("timeout")


def _make_input():
    lead = LeadModel(company_id=1, contact_email="a@example.com", contact_status="found", status="enriched")
    company = CompanyModel(name="Acme Co", industry="Technology", website_url="https://acme.example")
    contact = ContactModel(company_id=1, email="a@example.com", confidence=80)
    return LLMEmailInput(
        lead=lead,
        company=company,
        contact=contact,
        snippets={"about": "We build logistics tools."},
        value_props=["automation", "faster response"],
        persona="CTO",
        tone="concise",
    )


def test_llm_email_writer_success():
    content = """
    {
      "subject_variants": ["One", "Two", "Three"],
      "chosen_subject": "One",
      "body_text": "Hello there.",
      "followup_text": "Following up.",
      "personalization_fields": {"company_name": "Acme Co"},
      "personalization_fact": "Has a website at https://acme.example",
      "personalization_source_url": "https://acme.example",
      "confidence": 0.72,
      "rationale": "matches persona"
    }
    """
    writer = LLMEmailWriter(client=DummyClient(content))
    output, prompt_hash, usage, latency, error = writer.generate(_make_input())
    assert output.chosen_subject == "One"
    assert len(output.subject_variants) == 3
    assert prompt_hash
    assert usage["total_tokens"] == 10
    assert latency == 12
    assert error is None


def test_llm_email_writer_fallback_on_error():
    writer = LLMEmailWriter(client=FailingClient())
    output, prompt_hash, usage, latency, error = writer.generate(_make_input())
    assert output.rationale == "fallback_template"
    assert prompt_hash
    assert usage is None
    assert latency is None
    assert error is not None
