# Frontend Agent Prompt

Goal: Build the React web client for Safe Drive Africa V1.

Constraints:
- Auth is API-key based. Use `/api/auth/me` to infer role and scope.
- Roles in V1, build order: Fleet Manager -> Driver -> Researcher -> Insurance Partner.
- Leaderboards are per fleet; driver view only shows peers within fleet or insurer.
- KPIs: UBPK, bad-days counts, best/worst drivers.

UI Direction:
- Propose a fresh system (no existing design constraints).
- Use expressive fonts and a bold but clean layout.
- Dashboards should emphasize KPIs, trends, and rankings.

Deliverables:
- Route map and navigation per role.
- Page components with data hooks.
- Charts for UBPK and bad-days trends.
- Download actions for report endpoints.
