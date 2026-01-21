# Implementation Notes (2026-01-21)

## Current production status (EC2)
- Host: 51.20.184.138 (Ubuntu, /opt/amis-agent)
- Services:
  - amis-agent-api (FastAPI)
  - amis-agent-scheduler (scheduler loop)
  - amis-agent-worker (RQ worker for discover/qualify/enrich/outreach/send_outbox)
  - nginx (UI + /api proxy)
- Postgres: docker-compose only
- ENABLE_SENDING: true (set in /opt/amis-agent/.env)
- DEMO_MODE: false (demo behavior disabled)

## What was changed for sending enablement
- On EC2: set ENABLE_SENDING=true in /opt/amis-agent/.env
- Restarted:
  - amis-agent-api
  - amis-agent-worker

## Real discovery + pipeline
- Discovery uses deterministic seeds from config/discovery_seed.json (seed_static source)
- Scrape connectors remain in place, but deterministic seed ensures discover inserts at least seed data
- Qualification uses allowlist sources; seed_static is allowed
- Enrichment now generates drafts even when contact emails are missing
- Outbox drafts are created with status ready_for_review

## How to verify on EC2
1) Check sending gate:
   - grep '^ENABLE_SENDING=' /opt/amis-agent/.env
2) Run pipeline:
   - curl -X POST -H "X-ADMIN-TOKEN: $ADMIN_TOKEN" http://127.0.0.1:8000/api/run/pipeline
3) Check counts:
   - sudo docker exec -i amis-agent_postgres_1 psql -U postgres -d amis_agent -c \
     "select count(1) as companies from companies; select count(1) as leads from leads; select count(1) as outbox from outbox;"

## Notes for future agents
- DEMO paths removed from API and UI; do not re-enable in prod.
- Worker service is required for RQ jobs to execute:
  - /etc/systemd/system/amis-agent-worker.service
  - ExecStart: /opt/amis-agent/.venv/bin/rq worker discover qualify enrich outreach send_outbox
- Use scripts/ec2_deploy_ui.sh to deploy API + UI updates (pull, build UI, restart services).
