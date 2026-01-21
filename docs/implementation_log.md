# Implementation Log (2026-01-21)

This document captures what was implemented/changed so future agents can continue work quickly.

## Core pipeline additions
- Qualification step added for companies -> leads, with rules:
  - allowlist domain/source, must have website, non-empty company name, country/region if available.
  - dedupe by (company_name, website_domain).
  - decision + score stored in DB.
- Enrichment step (rate-limited + cached, no spam):
  - checks website + at most 2 contact/about pages, 1 req/sec, max 5 requests/company.
  - respects robots.txt; caches HTML responses.
  - extracts emails from mailto + page text.
  - no placeholders if email missing; creates lead with contact_status="missing_email".
  - stores contacts in `contacts` table with unique constraints.
- Lead creation & state transitions:
  - lead status chain: `new → enriched → ready_for_review → approved → sent`.
  - outbox table for draft emails with explicit approval gating.

## LLM draft generation (NO auto-send)
- Added provider-agnostic LLM client and `LLMEmailWriter`.
- Inputs: lead/company/contact, website snippets, product value props, persona, tone, constraints.
- Outputs: 3 subject variants, chosen subject, body, follow-up, personalization, confidence/rationale.
- Caching/dedupe: does not regenerate if draft/ready_for_review exists for lead.
- Fallback template used when LLM fails or output invalid.
- Audit logging: prompt hash, model, latency, token usage, errors.
- Env vars:
  - `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT`, `LLM_MAX_TOKENS`.

## Gmail sending safety + approvals
- Added approval gate: only `status="approved"` and `approved_by_human=true` can send.
- Preflight validation before send:
  - signature present and required fields exist,
  - no unresolved placeholders,
  - word count <= 110,
  - personalization fact + source URL when provided.
- Audit log captures preflight details.
- Global send gate:
  - `ENABLE_SENDING` must be true to send; otherwise sending is refused.
- Sender enforcement:
  - `GMAIL_SENDER` is required.
  - Gmail profile email must match `GMAIL_SENDER`, else hard-fail.
  - token file is sender-specific (suffixing email).
- Gmail OAuth improvements:
  - Added `gmail.readonly` scope (required to read profile).
  - Manual OAuth mode to avoid localhost 404 (`GOOGLE_OAUTH_MODE=manual`).
  - OOB redirect for manual mode shows a code to paste.

## Signature and template enforcement
- Single source of truth for signature at `config/email_signature.txt`.
  - Required fields: name, title, org (no hardcoded SF address).
- Signature appended in render step + compliance footer:
  - "If I reached the wrong person, reply 'no' and I won’t follow up."
- Placeholder detection blocks sending (e.g., `[Your Name]`, `{{...}}`).

## DB / migrations
Migrations added:
- `0004_add_qual_contacts.py`: `company_qualification`, `contacts`, `outbox`.
- `0005_add_memory_tables.py`: `industry_insights`, `reply_patterns`, `companies.about_snippet`.
- `0006_outbox_llm_fields.py`: LLM fields for drafts.
- `0007_outbox_approval_fields.py`: approval fields.

Models added/updated:
- `CompanyModel`: `website_url`, `website_domain`, `about_snippet`.
- `LeadModel`: `contact_status`, `status`, `contact_id`.
- `OutboxModel`: subjects, body, personalization fields, LLM metadata, approval fields.

## Scripts and CLI
- `scripts/render_email.py --outbox-id <id>`: render final email with signature/footer.
- `scripts/send_real_email.py --outbox-id <id>`: send only if approved + preflight passes.
- `scripts/approve_outbox.py --outbox-id <id> --approved-by "<name>"`: approve drafts without SQL.

## Known fixes performed
- Fixed invalid placeholders in drafts (e.g., `[Your Name]`) that blocked preflight.
- Ensured personalization facts are present for preflight when required.
- Updated Gmail scopes to include `gmail.readonly`.
- Added manual OAuth mode and out-of-band code flow.

## Operational notes
- To re-auth Gmail sender, delete the sender-specific token file:
  - `secrets/gmail_token.<sender>.json`
- For manual OAuth, set:
  - `GOOGLE_OAUTH_MODE=manual`
- For sender enforcement:
  - `GMAIL_SENDER=<email>`
- Optional S3 wiring (off by default):
  - `S3_ENABLED=false`, `S3_BUCKET=`, `AWS_REGION=`

## Latest manual send test
- Manual OAuth code flow succeeded.
- Send result: Gmail returned `labelIds: ['SENT']`.
