# Safe Drive Africa Backend API Documentation

## Overview
The Safe Drive Africa backend is a FastAPI application that exposes RESTful and analytical endpoints to manage driving data (trips, sensor readings, unsafe behaviours, etc.) and to surface UBPK (Unsafe Behaviours Per Kilometer) metrics. The API serves JSON responses and expects JSON request bodies unless stated otherwise. Default response codes follow HTTP semantics (200 for successful reads, 201 for creates, 204 for deletes without bodies, 400/404 for client errors, and 500 for unhandled server errors).

## Base URL and Versioning
All resources below assume the service root (e.g., `https://api.safedriveafrica.com`). Core resources are mounted under the `/api` prefix, while UBPK metric endpoints are served beneath `/metrics/behavior`. FastAPI's interactive documentation is available at `/docs` and `/redoc`.

## Authentication
No authentication or authorization guards are enforced in the current codebase—requests do not require tokens or API keys. All endpoints are publicly accessible once the service is reachable.【F:main.py†L21-L48】【F:safedrive/api/v1/api_router.py†L1-L38】

## Common Conventions
* **Content type** – JSON request/response bodies encoded in UTF‑8.
* **UUIDs** – Resource identifiers are UUID strings in canonical format.
* **Timestamps** – Unless otherwise specified, integer timestamps represent Unix epoch milliseconds; ISO 8601 strings are used for explicit datetime fields.
* **Pagination** – Many list endpoints accept `skip` (offset) and `limit` query parameters.

## Resource Endpoints (`/api`)

### Driver Profiles
| Method & Path | Description |
| --- | --- |
| `POST /api/driver_profiles/` | Create a driver profile (returns existing profile if the email already exists). Required body fields: `driverProfileId` (UUID), `email` (string); optional `sync` (bool). Response: `driverProfileId`, `email`, `sync`.| 
| `POST /api/driver_profiles/batch_create` | Bulk create profiles from an array of `DriverProfileCreate` objects. Returns an array of responses mirroring the single create schema. |
| `GET /api/driver_profiles/{profile_id}` | Fetch a profile by UUID. |
| `GET /api/driver_profiles/` | List profiles with optional `skip` and `limit` (default limit 5000). |
| `PUT /api/driver_profiles/{profile_id}` | Update email and/or sync status using `DriverProfileUpdate`. |
| `DELETE /api/driver_profiles/{profile_id}` | Remove a profile. |
| `GET /api/driver-profiles/by-profile-id/{email}` | Retrieve a profile and its trips/sensor data by email; supports `limit_sensor_data` query param. |
| `GET /api/driver-profiles/by-email/{email}` | Same as above but returns validated Pydantic schema. |
| `GET /api/driver-profile-by-email/{email}` | Minimal profile lookup by email. |
| `DELETE /api/driver_profiles/by-profile-id/{email}` | Delete by email with cascading removal of related records. |

**Schema highlights**: `DriverProfileCreate` requires `driverProfileId` (UUID) and `email`; responses expose `driverProfileId`, `email`, `sync`. Nested `DriverProfileOut` includes a `trips` array, each embedding limited raw sensor data.【F:safedrive/api/v1/endpoints/driver_profile.py†L1-L195】【F:safedrive/schemas/driver_profile.py†L1-L56】

### Trips
| Method & Path | Description |
| --- | --- |
| `POST /api/trips/` | Create a trip. Required fields include `id`, `driverProfileId`, `startTime` (ISO datetime), optional `start_date`, `end_date`, `end_time`, `sync`, `influence`, `tripNotes`. |
| `GET /api/trips/{trip_id}` | Retrieve a trip by UUID. |
| `GET /api/trips/` | List trips (`skip`, `limit`). |
| `PUT /api/trips/{trip_id}` | Partial update using `TripUpdate`. |
| `DELETE /api/trips/{trip_id}` | Delete and return the deleted record. |
| `POST /api/trips/batch_create` | Bulk create trips (array of `TripCreate`). |
| `DELETE /api/trips/batch_delete` | Bulk delete by array of UUIDs (returns message). |

> **Trip alcohol metadata**: `alcoholProbability` (float 0-1) and `userAlcoholResponse` (string) persist questionnaire context on each trip.



**Schema highlights**: `TripResponse` includes `id`, `driverProfileId`, `start_date`, `end_date`, `start_time`, `end_time`, `sync`, `influence`, `tripNotes`. `TripCreate`/`TripUpdate` mirror these fields; `startTime` uses camelCase alias when serialized.【F:safedrive/api/v1/endpoints/trip.py†L1-L200】【F:safedrive/schemas/trip.py†L1-L76】

### Raw Sensor Data
| Method & Path | Description |
| --- | --- |
| `POST /api/raw_sensor_data/` | Create sensor sample. Required: `id`, `sensor_type`, `sensor_type_name`, `values` (float array), `timestamp`, `accuracy`; optional `date`, `location_id`, `trip_id`, `sync`. |
| `GET /api/raw_sensor_data/{data_id}` | Retrieve by UUID. |
| `GET /api/raw_sensor_data/` | List sensor rows (`skip`, `limit` default 5000). |
| `PUT /api/raw_sensor_data/{data_id}` | Update any subset via `RawSensorDataUpdate`. |
| `DELETE /api/raw_sensor_data/{data_id}` | Delete entry. |
| `POST /api/raw_sensor_data/batch_create` | Bulk create. |
| `DELETE /api/raw_sensor_data/batch_delete` | Bulk delete by UUID list. |

Responses include all baseline fields defined in `RawSensorDataResponse` (matching `RawSensorDataBase`).【F:safedrive/api/v1/endpoints/raw_sensor_data.py†L1-L142】【F:safedrive/schemas/raw_sensor_data.py†L1-L78】

### Unsafe Behaviours
| Method & Path | Description |
| --- | --- |
| `POST /api/unsafe_behaviours/` | Record an unsafe behaviour. Required fields: `trip_id`, `driverProfileId`, `behaviour_type`, `severity`, `timestamp`; optional `location_id`, `date`, `alcohol_influence`, `sync`. |
| `GET /api/unsafe_behaviours/{unsafe_behaviour_id}` | Retrieve by UUID. |
| `GET /api/unsafe_behaviours/` | Paginated list (`skip`, `limit`, max 100). |
| `PUT /api/unsafe_behaviours/{unsafe_behaviour_id}` | Update behaviour details. |
| `DELETE /api/unsafe_behaviours/{unsafe_behaviour_id}` | Delete entry. |
| `POST /api/unsafe_behaviours/batch_create` | Bulk insert. |
| `DELETE /api/unsafe_behaviours/batch_delete` | Bulk delete. |

`UnsafeBehaviourResponse` echoes `UnsafeBehaviourBase` fields, including `driverProfileId`, `severity`, `timestamp`, `updated`, and `sync` flags.【F:safedrive/api/v1/endpoints/unsafe_behaviour.py†L1-L141】【F:safedrive/schemas/unsafe_behaviour.py†L1-L74】

### Locations
| Method & Path | Description |
| --- | --- |
| `POST /api/locations/` | Create a location sample. Required: `id`, `latitude`, `longitude`, `timestamp`, `date`, `altitude`, `speed`, `speedLimit`, `distance`; optional `sync`. |
| `GET /api/locations/{location_id}` | Retrieve by UUID. |
| `GET /api/locations/` | Paginated list (`skip`, `limit` up to 100). |
| `PUT /api/locations/{location_id}` | Update using `LocationUpdate` (all optional). |
| `DELETE /api/locations/{location_id}` | Delete entry. |
| `POST /api/locations/batch_create` | Bulk insert. |
| `DELETE /api/locations/batch_delete` | Bulk delete. |

Responses expose all base attributes, including `latitude`, `longitude`, `speed`, `speedLimit`, `distance`, and `sync`.【F:safedrive/api/v1/endpoints/location.py†L1-L140】【F:safedrive/schemas/location.py†L1-L70】

### Driving Tips
| Method & Path | Description |
| --- | --- |
| `POST /api/driving_tips/` | Create a driving tip (fields include `tip_id`, `title`, optional narrative fields, `sync`, `date`, `profile_id`, optional `llm`). |
| `GET /api/driving_tips/{tip_id}` | Retrieve by UUID. |
| `GET /api/driving_tips/` | List with `skip`/`limit`. Optional filters: `profile_id`, `llm`, `start_date`, `end_date`, `sync`. |
| `PUT /api/driving_tips/{tip_id}` | Update tip content. |
| `DELETE /api/driving_tips/{tip_id}` | Delete tip. |
| `POST /api/driving_tips/batch_create` | Bulk insert tips (array of `DrivingTipCreate`). |
| `DELETE /api/driving_tips/batch_delete` | Bulk delete tips by UUID list. |

Responses serialize the same attributes defined in `DrivingTipBase`.【F:safedrive/api/v1/endpoints/driving_tips.py†L1-L104】【F:safedrive/schemas/driving_tip_sch.py†L1-L58】

### Causes
| Method & Path | Description |
| --- | --- |
| `POST /api/causes/` | Create cause linked to an unsafe behaviour (`unsafe_behaviour_id`, `name`, optional `influence`, timestamps). |
| `GET /api/causes/{cause_id}` | Retrieve by UUID. |
| `GET /api/causes/` | List (`skip`, `limit`). |
| `PUT /api/causes/{cause_id}` | Update cause metadata. |
| `DELETE /api/causes/{cause_id}` | Delete cause. |

`CauseResponse` contains `id`, `unsafe_behaviour_id`, `name`, `influence`, `created_at`, `updated_at`, `synced`.【F:safedrive/api/v1/endpoints/cause.py†L1-L50】【F:safedrive/schemas/cause.py†L1-L53】

### Embeddings
| Method & Path | Description |
| --- | --- |
| `POST /api/embeddings/` | Store an embedding chunk (`chunk_text`, `embedding`, `source_type`, `source_page`, optional `synced`). |
| `GET /api/embeddings/{embedding_id}` | Retrieve by UUID. |
| `GET /api/embeddings/` | Paginated list. |
| `PUT /api/embeddings/{embedding_id}` | Update embedding content. |
| `DELETE /api/embeddings/{embedding_id}` | Delete embedding. |

Responses return `chunk_id`, `chunk_text`, serialized `embedding`, `source_type`, `source_page`, `created_at`, `synced`.【F:safedrive/api/v1/endpoints/embedding.py†L1-L74】【F:safedrive/schemas/embedding.py†L1-L28】

### NLG Reports
| Method & Path | Description |
| --- | --- |
| `POST /api/nlg_reports/` | Create a narrative report (`id`, `driverProfileId`, `startDate`, `endDate`, `report_text`, `generated_at`, optional `sync`). |
| `GET /api/nlg_reports/{report_id}` | Retrieve by UUID. |
| `GET /api/nlg_reports/` | Paginated list. Optional filters: `driverProfileId`, `startDate`, `endDate`, `sync`. |
| `PUT /api/nlg_reports/{report_id}` | Update report text or sync flag. |
| `DELETE /api/nlg_reports/{report_id}` | Delete report. |
| `POST /api/nlg_reports/batch_create` | Bulk insert reports (array of `NLGReportCreate`). |
| `DELETE /api/nlg_reports/batch_delete` | Bulk delete reports by UUID list. |

Responses align with `NLGReportResponse`: `id`, `driverProfileId`, `startDate`, `endDate`, `report_text`, `generated_at`, `sync`.【F:safedrive/api/v1/endpoints/nlg_report.py†L1-L64】【F:safedrive/schemas/nlg_report.py†L1-L44】

### AI Model Inputs
| Method & Path | Description |
| --- | --- |
| `POST /api/ai_model_inputs/` | Create AI feature snapshot (`trip_id`, `driverProfileId`, `start_time`, `timestamp`, `date`, `hour_of_day_mean`, `day_of_week_mean`, `speed_std`, `course_std`, `acceleration_y_original_mean`, optional `sync`). |
| `GET /api/ai_model_inputs/{input_id}` | Retrieve by UUID. |
| `GET /api/ai_model_inputs/` | List with pagination (limit ≤ 100). |
| `PUT /api/ai_model_inputs/{input_id}` | Update any subset of the metrics. |
| `DELETE /api/ai_model_inputs/{input_id}` | Delete entry. |
| `POST /api/ai_model_inputs/batch_create` | Bulk insert. |
| `DELETE /api/ai_model_inputs/batch_delete` | Bulk delete. |

Responses return the same fields as `AIModelInputBase` plus server-generated `id`.【F:safedrive/api/v1/endpoints/ai_model_inputs_router.py†L1-L112】【F:safedrive/schemas/ai_model_input.py†L1-L44】

### Alcohol Questionnaire
| Method & Path | Description |
| --- | --- |
| `POST /api/alcohol-questionnaire/questionnaire/` | Submit questionnaire results (fields such as `driverProfileId`, `drankAlcohol`, beverage quantities, `firstDrinkTime`, `impairmentLevel`, `plansToDrive`, `sync`). |
| `GET /api/alcohol-questionnaire/questionnaire/{questionnaire_id}/` | Retrieve by UUID. |
| `GET /api/alcohol-questionnaire/questionnaire/` | List all questionnaires. |
| `PUT /api/alcohol-questionnaire/questionnaire/{questionnaire_id}/` | Update questionnaire answers. |
| `DELETE /api/alcohol-questionnaire/questionnaire/{questionnaire_id}/` | Delete (returns 204). |
| `POST /api/questionnaire/` | Mobile compatibility alias for submitting questionnaires. |
| `GET /api/questionnaire/{user_id}` | Mobile compatibility history lookup by driver profile ID. |

Response schema mirrors `AlcoholQuestionnaireBaseSchema`, including the submitted answers and metadata timestamps.【F:safedrive/api/v1/endpoints/alcohol_questionnaire.py†L1-L93】【F:safedrive/schemas/alcohol_questionnaire.py†L1-L43】

### Behaviour Metrics (Analytics)
| Method & Path | Description |
| --- | --- |
| `GET /api/behaviour_metrics/ubpk` | Aggregate UBPK per driver. Response: array of `{ driverProfileId, ubpk }`. |
| `GET /api/behaviour_metrics/trip` | UBPK per trip (`{ trip_id, driverProfileId, ubpk }`). |
| `GET /api/behaviour_metrics/weekly` | Weekly UBPK per driver with `week_start` dates. |
| `GET /api/behaviour_metrics/improvement` | Identifies drivers with statistically significant UBPK improvement using Welch’s t-test (`{ driverProfileId, improved, p_value }`). |

All endpoints are read-only and do not accept parameters beyond implicit database state.

### Fleet Monitoring
| Method & Path | Description |
| --- | --- |
| `GET /api/fleet/driver_monitor/{driver_profile_id}` | Driver-specific monitoring snapshot with active trip status, unsafe behaviour counts (total + last 24h), recent violations, and speed compliance ratios (speed vs. speedLimit). Matches the Fleet Manager requirement in backend_requirements_dev/user-role-usecases.md and AGENT.md. |

> Notes: Status mirrors the mobile `DrivingStateManager` (ACTIVE/IDLE) and aggregates location data through the Location ? RawSensorData ? Trip join so dashboards stay in sync with sensor telemetry.
【F:safedrive/api/v1/endpoints/behaviour_metrics.py†L1-L101】【F:safedrive/schemas/behaviour_metrics.py†L1-L32】

### Fleet Management & Notifications
| Method & Path | Description |
| --- | --- |
| `POST /api/fleet/assignments/` | Assign a driver to a fleet/vehicle group, capture onboarding status, and store compliance notes so assignment history matches the Android `DriverProfileViewModel` flows. The response returns the persisted assignment along with nested `Fleet`/`VehicleGroup` metadata. |
| `GET /api/fleet/assignments/{driver_id}` | Retrieve the latest assignment for a driver plus the most recent alcohol questionnaire (if any) so managers can verify onboarding/compliance data before trips start. |
| `POST /api/fleet/events/` | Emit a driver trip event (VERIFYING, RECORDING, NOT DRIVING, GPS stale warning, trip start/stop) so notification listeners mirror the sensor transition log. |
| `GET /api/fleet/events/{driver_id}` | Stream the most recent driver events (`limit` query param) for dashboards to display GPS health notes and trip lifecycle changes even if the app goes backgrounded. |
| `GET /api/fleet/trips/{trip_id}/context` | Return a per-trip context bundle containing the latest tip threads, severity-ranked unsafe behaviours, and recent NLG reports for that driver so managers can coach with the same narrative the driver sees. |
| `GET /api/fleet/reports/{driver_id}` | Generate an actionable fleet report summarizing trips, unsafe behaviour logs, alcohol questionnaire responses, and overall speed compliance for leadership/insurer reviews. |
| `GET /api/fleet/reports/{driver_id}/download` | Download the same fleet report as a JSON attachment (`Content-Disposition` header) so partners can store or re-process the file offline. |

> Notes: Events capture the `sensor` module transitions (VERIFYING ? RECORDING ? NOT DRIVING) plus GPS health annotations; clients can replay them to deliver notifications if the app was backgrounded.

### Researcher Data Access
| Method & Path | Description |
| --- | --- |
| `GET /api/researcher/unsafe_behaviours/summary` | Aggregated unsafe behaviour counts and severity statistics grouped by `behaviour_type`. Optional filters: `driverProfileId`, `tripId`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`), `minSeverity`, `maxSeverity`. |
| `GET /api/researcher/raw_sensor_data/summary` | Summarize raw sensor counts per sensor type with min/max timestamps and average accuracy. Optional filters: `driverProfileId`, `tripId`, `sensorType`, `sensorTypeName`, `startTimestamp`, `endTimestamp`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`). |
| `GET /api/researcher/alcohol_trip_bundle` | Return trip metadata alongside alcohol questionnaire responses for correlation. Each trip includes `matchedQuestionnaire` computed using same UTC calendar day. Optional filters: `driverProfileId`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`), `skip`, `limit`. Response includes `matchingRule` and `matchingTimezone` notes. |
| `GET /api/researcher/nlg_reports/export` | Stream NLG reports as `jsonl` (default) or `csv` using report period filters (`startDate`/`endDate`) or ISO week (`YYYY-Www`). Optional filters: `driverProfileId`, `startDate`, `endDate`, `week`, `sync`, `format`. |
| `GET /api/researcher/raw_sensor_data/export` | Stream raw sensor datasets as `jsonl` (default) or `csv`. Optional filters: `driverProfileId`, `tripId`, `sensorType`, `sensorTypeName`, `startTimestamp`, `endTimestamp`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`), `format`. |
| `GET /api/researcher/trips/export` | Stream trips as `jsonl` (default) or `csv`, including `matchedQuestionnaire` plus `matchingRule`/`matchingTimezone` metadata (UTC day matching). Optional filters: `driverProfileId`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`), `format`. |
| `GET /api/researcher/snapshots/aggregate` | Aggregated snapshot containing UBPK per driver/trip plus unsafe behaviour and raw sensor summaries. Optional filters: `driverProfileId`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`). |
| `GET /api/researcher/snapshots/aggregate/download` | Download the aggregated snapshot as a JSON attachment (`Content-Disposition` header). |
| `POST /api/researcher/trips/backfill_alcohol` | Backfill `Trip.alcoholProbability` and `Trip.userAlcoholResponse` from matched questionnaires using UTC day matching. Optional filters: `driverProfileId`, `startDate`, `endDate`, `week` (ISO `YYYY-Www`), `overwrite` (default `false`). Response includes `matchingRule`/`matchingTimezone` notes. |
| `GET /api/researcher/ingestion/status` | Dataset ingestion status counts (total, synced, unsynced) with latest record timestamps for upload monitoring. |


## UBPK Metric Endpoints (`/metrics/behavior`)
These endpoints expose both legacy and enhanced UBPK analytics.

| Method & Path | Description |
| --- | --- |
| `GET /metrics/behavior/v2/trip/{trip_id}` | Returns UBPK metrics for a trip, including ISO week label, week start/end dates, unsafe count, distance (km), and computed UBPK. |
| `GET /metrics/behavior/v2/driver/{driver_id}` | Computes per-driver UBPK for the specified ISO week (`week` query parameter, default current week). Response includes week metadata, `numTrips`, per-trip `ubpkValues`, and `meanUBPK`. |
| `GET /metrics/behavior/v2/driver/{driver_id}/improvement` | Compares current week vs. previous week UBPK; returns `pValue` and `meanDifference`. Optional `week` query param (defaults to current). |
| `GET /metrics/behavior/trip/{trip_id}/ubpk` | Legacy endpoint returning `TripUBPKResponse` (trip ID, driver profile, week window, `totalUnsafeCount`, `distanceKm`, `ubpk`). Raises 404 if no unsafe events found. |
| `GET /metrics/behavior/driver/{driver_id}` | Legacy weekly UBPK summary for a driver; optional `week` query (format `YYYY-Www`). Response includes number of trips, `ubpkValues`, `meanUBPK`. |
| `GET /metrics/behavior/driver/{driver_id}/improvement` | Legacy paired t-test comparison between consecutive weeks; returns `pValue`, `meanDifference`, previous week metadata. |
| `GET /metrics/behavior/trips` | Aggregates UBPK for all trips in a week (query `week`, default current). Returns array of `TripUBPKResponse` objects. |

Request/response models come from `safedrive.schemas.ubpk_metrics` (Trip/Driver UBPK responses, driver improvement metrics). Week query parameters accept ISO strings in `YYYY-Www` or `YYYY-WW` formats depending on endpoint version.【F:app/routers/ubpk_metrics.py†L1-L420】

## Index and Documentation Redirect
`GET /api/` (root of the mounted API router) redirects to `/docs` via Starlette `RedirectResponse`. The FastAPI app also exposes a root handler returning a welcome message when launched directly in development mode.【F:safedrive/api/v1/endpoints/index.py†L1-L18】【F:main.py†L60-L76】

## Error Handling
Endpoints use FastAPI `HTTPException` to signal validation issues (400), missing resources (404), and server/database errors (500). Bulk operations typically return a JSON body summarizing the outcome or raise on constraint violations.【F:safedrive/api/v1/endpoints/trip.py†L21-L200】【F:safedrive/api/v1/endpoints/raw_sensor_data.py†L21-L142】

## Status Codes Summary
* `200 OK` – Successful retrieval or update.
* `201 Created` – Successful creation (bulk create endpoints may also return 201).
* `204 No Content` – Successful delete without body (batch deletes often respond with confirmation JSON despite 204 status in decorators—check client expectations).
* `400 Bad Request` – Validation or business-rule failure.
* `404 Not Found` – Missing resource or insufficient data for UBPK analytics.
* `500 Internal Server Error` – Unhandled or database exceptions.
