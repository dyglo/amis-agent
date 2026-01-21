# Product Requirements Document (PRD)

## Product Name
Digital Me Agent (AMIS Intelligence)

## Owner
Tafar Smith (AI Engineer and Applied ML)

## Problem
Manual lead discovery and outreach consumes time and reduces consistency. The goal is to automate lead discovery, qualification, and outreach while preserving compliance and deliverability.

## Goals
- Discover leads daily from approved public sources.
- Identify businesses without websites and enterprises that need AI integration.
- Generate and send personalized outreach emails automatically.
- Track responses and maintain compliance logs.
- Operate continuously with minimal manual intervention.

## Non-Goals
- EU/UK cold email (opt-in only).
- Paid data vendor integrations in v1.
- Multi-channel outreach beyond email (v1).

## Target Segments
1) SMBs without a website (including Facebook-only presence).
2) Enterprises needing AI integration (automation, intelligent apps, computer vision/smart city).

## Regions & Compliance
- US: CAN-SPAM compliant auto-send is allowed.
- EU/UK: opt-in only. No cold email.
- Global: unsubscribe + suppression list required; audit logs required.

## Success Metrics
- Lead discovery per day (target: 5-10 qualified sends/day initially).
- Reply rate.
- Bounce rate < 2%.
- Spam complaint rate < 0.1%.
- Meetings booked per month.

## Risks
- Deliverability issues from Gmail if not rate-limited.
- Compliance violations in EU/UK if cold outreach is not blocked.
- Scraping source TOS violations if sources are not restricted.

## Constraints
- Use Gmail for sending (separate outreach account recommended).
- Budget: OpenAI credits (~$25) + Nebius as fallback.
- English for US; localized language for EU regions (opt-in only).

## Required Email Footer
Tafar Smith | AI Engineer and Applied ML
AMIS Intelligence
415 Mission St, 3rd Floor, San Francisco, CA 94105

