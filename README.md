# AMIS Digital Me Agent

Production-grade system for automated lead discovery, qualification, and outreach.

## Quickstart
- Create a virtual env
- Install dependencies
- Configure `.env`
- Run API: `uvicorn amis_agent.main:app --reload`

## Admin API
- All admin endpoints require `X-ADMIN-TOKEN` header.
- Configure `ADMIN_TOKEN` in `.env`.
- Core endpoints:
  - `GET /health`
  - `GET /api/stats`
  - `GET /api/outbox?status=ready_for_review&limit=50`
  - `GET /api/outbox/{id}`
  - `POST /api/outbox/{id}/approve`
  - `POST /api/outbox/{id}/regenerate`
  - `POST /api/outbox/{id}/send` (requires `ENABLE_SENDING=true`)
  - `POST /api/run/pipeline`
  - `GET /api/companies`
  - `GET /api/leads`
  - `GET /api/settings`

## React UI
- UI lives in `ui/` (Vite + React + Tailwind).
- Build locally:
  - `cd ui`
  - `npm install`
  - `npm run build`
- The UI expects the API at `/api` and uses `X-ADMIN-TOKEN` stored in localStorage.

## Deployment (EC2)
- API runs as `amis-agent-api` systemd service.
- Scheduler runs as `amis-agent-scheduler` systemd service.
- Nginx serves UI and proxies `/api` to FastAPI.
- Deploy script on EC2:
  - `bash scripts/ec2_deploy_ui.sh`
  - This pulls latest, builds UI, installs Nginx, and restarts services.

## Architecture
- Clean architecture (domain/application/infrastructure)
- Async FastAPI API
- Redis + RQ for background jobs
- Postgres for persistence

## Qualification → Enrichment → Draft Pipeline
1) Qualification
   - Allowlist source + domain.
   - Requires company name and website status = has_website.
   - Dedupe by (company_name, website_domain).
   - Stores decision + score in `company_qualification`.
2) Enrichment (safe + rate-limited)
   - Fetches only company website + up to 2 contact/about pages.
   - Respects robots.txt and uses 1 req/sec per host.
   - Max 5 requests per company; caches per-run fetches.
   - Stores emails in `contacts` with source_url + confidence.
3) Lead creation + draft
   - Leads move: new → enriched → ready_for_review → approved → sent.
   - Missing email = `contact_status=missing_email` (no fabrication).
   - Drafts live in `outbox` (status=draft) for review before send.

## Outreach Quality (Option A)
- Persona templates: Founder / CTO / Ops.
- Deterministic subject A/B variants.
- Per-domain daily caps via Redis-backed rate limiter.

## Memory + Personalization (Option B)
- Store industry insights (preferred persona + subject variant).
- Learn reply patterns (classify common phrases).
- First line personalization from website/about page text (no extra requests).

## Ops Hardening (Option C)
- Redis-backed send queue + daily quotas.
- Automatic pause on error spikes.

## LLM Drafting (No Auto-Send)
- LLMEmailWriter generates drafts only (status=draft/ready_for_review).
- Provider-agnostic OpenAI-compatible API via env vars.
- Prompt hash + model/latency/token usage audited in audit_log.

## Review Gate + Signature
- Signature is loaded from `config/email_signature.txt` (name/title/org required).
- Preflight checks placeholders, signature fields, word count, and personalization source URL.
- Only `outbox` items with `status=approved` and `approved_by_human=true` can be sent.
- Use `python scripts/render_email.py --outbox-id <id>` to preview exact send.

