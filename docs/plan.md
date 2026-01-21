# Project Plan

## Phase 1: Core Infrastructure
- Initialize FastAPI app
- Postgres schema + migrations
- Redis queue + worker
- Config system for limits and region policies

## Phase 2: Discovery + Qualification
- Connectors for approved sources
- Website/FB-only detection
- Lead scoring model

## Phase 3: Enrichment + Verification
- Email discovery
- Email verification
- Suppression logic

## Phase 4: Outreach Engine
- Templates + personalization
- Localization pipeline
- Gmail send + tracking
- Follow-up logic

## Phase 5: CRM + Monitoring
- Lightweight pipeline UI
- Metrics dashboard
- Alerts for bounce/spam thresholds

## Deployment
- EC2 for API/worker runtime
- S3 for storage
- Modal for model-serving workloads

## Deliverability Milestones
- Separate Gmail account
- Gradual warmup
- DMARC/SPF/DKIM plan for dedicated domain later

