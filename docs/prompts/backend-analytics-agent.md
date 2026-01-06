# Backend Analytics Agent Prompt

Goal: Extend analytics endpoints for the web client when needed.

Current endpoints:
- `/api/analytics/leaderboard`
- `/api/analytics/driver-ubpk`
- `/api/analytics/bad-days`
- `/api/analytics/driver-kpis`

Key rules:
- Leaderboards are per fleet (or insurer for drivers without a fleet).
- Bad-days uses 75th percentile delta thresholds across periods.
- Access is scoped by role (driver/fleet_manager/insurance_partner/admin/researcher).

Suggested next improvements:
- Add pagination for `driver-kpis`.
- Add fleet-level aggregate summaries.
- Add caching after measuring load (Redis).
