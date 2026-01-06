# Testing Agent Prompt

Goal: Verify backend analytics and auth endpoints.

Checklist:
- `/api/auth/me` returns correct role and scope.
- `/api/analytics/leaderboard` returns best/worst per fleet.
- `/api/analytics/driver-ubpk` returns series for driver.
- `/api/analytics/bad-days` returns thresholds and per-driver counts.
- `/api/analytics/driver-kpis` returns KPIs per driver.

Use sqlite memory for tests (`DATABASE_URL=sqlite:///:memory:`).
