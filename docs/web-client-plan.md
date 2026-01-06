# Web Client Plan (React V1)

Date: 2026-01-06

## Goals
- Deliver a React web client that supports all roles in V1.
- Build order: Fleet Manager -> Driver -> Researcher -> Insurance Partner.
- Use API key authentication with `/api/auth/me` to infer role and scope.
- Provide KPIs: UBPK and "Bad Days" per driver, plus best/worst performers.
- Leaderboards are per fleet; driver view shows peers within fleet or insurer.

## Auth Model
- Login screen accepts API key.
- App calls `GET /api/auth/me` to retrieve role + scope and routes accordingly.
- Store API key in memory + optional local storage for testing.
- All API requests attach `X-API-Key`.

## Information Architecture

### Fleet Manager
- Dashboard (KPIs)
  - Avg UBPK (cohort), bad-days counts, best/worst drivers
  - Data: `/api/analytics/leaderboard`, `/api/analytics/driver-kpis`, `/api/analytics/bad-days`
- Driver Monitor
  - Status + alerts + recent behaviours
  - Data: `/api/fleet/driver_monitor/{driver_id}`, `/api/fleet/events/{driver_id}`
- Assignments
  - Fleet/vehicle group mapping and onboarding notes
  - Data: `/api/fleet/assignments/`, `/api/fleet/{fleet_id}/vehicle-groups`
- Reports
  - Per driver downloadable report
  - Data: `/api/fleet/reports/{driver_id}`, `/api/fleet/reports/{driver_id}/download`

### Driver
- Dashboard
  - UBPK trend + bad-days + personal highlights
  - Data: `/api/analytics/driver-ubpk`, `/api/analytics/bad-days`
- Trips
  - Trip list and detail
  - Data: `/api/trips/`, `/api/trips/{trip_id}`
- Tips + Reports
  - Driving tips + NLG reports
  - Data: `/api/driving_tips/`, `/api/nlg_reports/`
- Leaderboard (peer ranking)
  - Scoped to driver's fleet; fallback to insurer cohort
  - Data: `/api/analytics/leaderboard`

### Researcher
- Summary
  - Unsafe behaviour + raw sensor summaries
  - Data: `/api/researcher/unsafe_behaviours/summary`, `/api/researcher/raw_sensor_data/summary`
- Exports
  - NLG, raw sensor, trips exports
  - Data: `/api/researcher/nlg_reports/export`, `/api/researcher/raw_sensor_data/export`, `/api/researcher/trips/export`
- Aggregate Snapshot
  - UBPK + summaries
  - Data: `/api/researcher/snapshots/aggregate`, `/download`
- Ingestion Status
  - Dataset health
  - Data: `/api/researcher/ingestion/status`

### Insurance Partner
- Dashboard
  - UBPK and bad-days per driver
  - Data: `/api/analytics/driver-kpis`, `/api/analytics/bad-days`, `/api/analytics/leaderboard`
- Telematics
  - Trip summaries
  - Data: `/api/insurance/telematics/trips`
- Alerts
  - Severe events and speed violations
  - Data: `/api/insurance/alerts`
- Aggregate Reports
  - Partner-level report download
  - Data: `/api/insurance/reports/aggregate`, `/download`
- Raw Export
  - Data: `/api/insurance/raw_sensor_data/export`

## KPI Definitions

### UBPK
- Unsafe Behaviours per Kilometer for a driver within a time window.
- Computed as `unsafe_count / distance_km`.
- Use `/api/analytics/driver-ubpk` and `/api/analytics/driver-kpis`.

### Bad Days (75th Percentile Threshold)
- For each period (day/week/month), compute UBPK deltas between consecutive periods.
- Collect all deltas across the cohort.
- Threshold = 75th percentile of deltas.
- A "bad" period is a delta greater than the threshold (and > 0).
- Endpoint: `/api/analytics/bad-days`.

### Best/Worst Drivers
- Sorted by UBPK (lower is better) within the period window.
- Endpoint: `/api/analytics/leaderboard` (best + worst lists).

## Technical Stack
- React + TypeScript (Vite)
- React Router
- TanStack Query
- React Hook Form
- Charting: Recharts or ECharts
- UI: Tailwind or CSS Modules (TBD)

## Build Milestones
1. Fleet Manager dashboard and driver monitor.
2. Driver dashboard + leaderboard.
3. Researcher summary + exports.
4. Insurance partner dashboards + reports.
5. UX polish and responsive layout.

## Open Decisions
- UI framework selection (Tailwind vs CSS Modules).
- Charting library choice.
- API key storage (session vs local storage).

## Redis Later
- Add caching for analytics endpoints after UI usage confirms bottlenecks.
