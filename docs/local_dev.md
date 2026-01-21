# Local Development

## Start Postgres
```
docker compose up -d
```

## Environment
Update `.env` to use:
- DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/amis_agent

## Migrate
```
alembic upgrade head
```

