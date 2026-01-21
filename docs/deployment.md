# Deployment Notes

## Local OAuth Redirect URI
- Authorized redirect URI: http://localhost:8080/
- Authorized JavaScript origin: http://localhost

## EC2 Secrets Location
- Place `gmail_credentials.json` at: /opt/amis-agent/secrets/gmail_credentials.json
- Token file will be created at: /opt/amis-agent/secrets/gmail_token.json

## EC2 Scheduler
We run the scheduler loop as a systemd service to keep it alive.

1) Copy repository to /opt/amis-agent
2) Create a venv at /opt/amis-agent/.venv
3) Create /opt/amis-agent/.env with production values
4) Run migrations:
   - /opt/amis-agent/.venv/bin/alembic upgrade head
5) Install the service:
   - cp deploy/systemd/amis-agent-scheduler.service /etc/systemd/system/
   - systemctl daemon-reload
   - systemctl enable --now amis-agent-scheduler

