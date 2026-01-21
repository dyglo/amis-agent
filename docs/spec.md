# Technical Specification

## Architecture Overview
Services:
- Orchestrator: schedules jobs and enforces limits.
- Discovery: pulls businesses from approved sources.
- Qualification: detects website presence and lead fit.
- Enrichment: discovers and verifies emails.
- Outreach Agent: drafts personalized emails.
- Sender: Gmail API/SMTP with throttling and retries.
- Compliance: suppression list, opt-out handling, audit logging.
- CRM: lightweight internal pipeline + UI.

## Stack
- Backend: Python + FastAPI
- Queue: Redis + RQ (or Celery)
- DB: Postgres
- LLM: OpenAI primary, Nebius fallback
- UI: minimal admin dashboard
- Deployment: EC2 with S3 storage; Modal for model-serving workloads

## Agent Framework Decision
- Default: custom orchestration (simple, testable, no framework lock-in).
- Optional: LangGraph only if we need a state machine for complex multi-step flows.
- Not required: LangChain for v1.

## Data Model (Core)
- companies: name, industry, location, size, website_status, source
- leads: company_id, contact_name, role, email, verification_status
- outreach: lead_id, template_id, subject, body, language, status, timestamps
- replies: lead_id, sentiment, reply_text, classification
- suppression: email, reason, timestamp
- audit_log: action, source, legal_basis, timestamp

## Compliance Rules
- US auto-send allowed with CAN-SPAM footer.
- EU/UK: opt-in only; block cold outreach by policy.
- Unsubscribe must be one-click; suppression is global.
- Bounce/spam signals trigger suppression.

## Send Limits
- Start: 5-10 emails/day per account.
- Slow ramp-up; enforce per-domain and per-hour limits.

## Language Handling
- US: English
- EU: localized language based on region (opt-in only)

