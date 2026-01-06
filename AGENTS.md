# Agent Guide

This file helps other agents continue work on the Safe Drive Africa system.

## Project Summary
- Backend: FastAPI with SQLAlchemy and Alembic.
- Auth: API key via `X-API-Key`, role-based access control.
- Roles: admin, driver, researcher, fleet_manager, insurance_partner.
- Analytics endpoints added for web client KPIs.
- Seeded test data documented in `docs/seedings.md`.

## Key Paths
- API routers: `safedrive/api/v1/api_router.py`
- Endpoints: `safedrive/api/v1/endpoints/`
- Models: `safedrive/models/`
- Schemas: `safedrive/schemas/`
- Alembic: `alembic/`
- Tests: `tests/`
- Web plan: `docs/web-client-plan.md`
- Prompts: `docs/prompts/`

## Runbook
- Set DB: `DATABASE_URL=mysql+pymysql://.../drive_safe_db`
- Migrations: `.venv\\Scripts\\alembic -c alembic.ini upgrade head`
- Tests (sqlite): `DATABASE_URL=sqlite:///:memory: .venv\\Scripts\\python -m pytest`

## Web Client Notes
- Use API key login with `/api/auth/me` to infer role and scopes.
- Leaderboards are per fleet; driver view shows peers within fleet or insurer.
- Bad-days uses 75th percentile of UBPK deltas per period.
- Build order: Fleet Manager -> Driver -> Researcher -> Insurance Partner.
- Full IA and data flow are in `docs/web-client-plan.md`.

## Seeded IDs
See `docs/seedings.md` for IDs, assignments, and API keys.

## Safety
- Avoid destructive git operations.
- Do not alter unrelated files.
- Keep edits ASCII-only unless file already uses Unicode.
