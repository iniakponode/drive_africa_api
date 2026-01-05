## Safe Drive Africa Backend Use Cases

Documented below are the primary user roles that the future FastAPI backend must serve, based on the current Android codebase.

### 1. Admin
- Manage all driver profiles and associated metadata (see `driverprofile` module's repository/use cases that insert, update, delete, and fetch profiles via `DriverProfileApiService` and local `DriverProfileDAO`).  
- Orchestrate uploads of raw sensor, trip, unsafe behaviour, and report data (`core/apiServices/workManager/UploadAllDataWorker.kt`) so the backend can store and serve summaries for other roles.  
- Configure and monitor cloud endpoints that provide road limit, tips, and model responses; offline-capable clients request these via `UploadAllDataWorker` and cache results locally.  
- Oversee authentication/authorization for the other roles and control which datasets are exposed to researchers, fleet teams, or insurers.

### 2. Researcher
- Retrieve aggregated unsafe behaviour metrics and raw sensor summaries (see `dbda` analysis utilities and DAOs such as `TripDao`, `UnsafeBehaviourEntity`, and `ReportStatisticsEntity`) to study patterns over time.  
- Access alcohol questionnaire responses and trip metadata (`alcoholquestionnaire` module + `QuestionnaireViewModel` combined with `Trip` data) for correlational studies.  
- Export or stream NLG-generated driver feedback (`nlgengine` module’s reports stored through `NLGReportRepositoryImpl`) for qualitative analysis.  
- Download raw sensor datasets and aggregated snapshots so researchers can perform offline/custom analytics in their preferred tools.  
- Request timely status updates on data ingestion jobs (mirrors the worker logs in `UploadAllDataWorker`) and verify that offline-first uploads eventually reach the research dataset.

### 3. Fleet Manager
- Monitor individual drivers’ trip status, unsafe behaviour alerts, and fuel/speed compliance (sensor data + `DrivingStateManager` logic in the `sensor` module), ideally via dashboards that query driver-specific aggregates.  
- Assign drivers to fleets/vehicle groups and track onboarding/compliance questionnaires (driven by `DriverProfileViewModel` and repeated alcohol questionnaires).  
- Receive notifications when driver trips start/stop, including GPS health notes (the `sensor` module logs transitions between VERIFYING, RECORDING, and NOT DRIVING plus the GPS stale warning).  
- Pull per-trip tip threads and severity findings (`driverprofile` tips + `nlgengine` reports) so managers can coach drivers with contextualised summaries.  
- Generate and download operational/actionable reports (trip summaries, unsafe behaviour logs, alcohol responses, speed compliance) for leadership or insurer review.

### 4. Driver
- Create and maintain a personal profile (email-driven driver profile flows in `DriverProfileCreationScreen`, `DriverProfileViewModel`, and related APIs) for syncing history and tip generation.  
- Automatically collect sensor/location data, unsafe behaviours, alcohol response, and road speed metadata while on the move (`sensor`, `ml`, `dbda`, and `alcoholquestionnaire` modules) even when offline.  
- Fetch personalised driving tips and ChatGPT/Gemini reports when connectivity returns (`driverprofile` tips syncing + `nlgengine` report store); any backend endpoints must honor offline caching strategies described in the app.  
- Submit once-daily alcohol questionnaires, trip notes, and optionally attach supplementary data (e.g., alcohol form tied to trip updates via `UpdateTripUseCase` and `TripViewModel`) so the backend can correlate behaviour with self-reported state.

### 5. Insurance Partner
- Ingest driver telematics data (trip logs, unsafe behaviours, speeds) to assess policy compliance and inform coverage tiers; the backend should expose filtered views per insurer label.  
- Retrieve consolidated reports (per driver/fleet) that combine unsafe behaviour trends, alcohol questionnaire history, and trip summaries for underwriting or claims validation.  
- Stream/download raw/aggregated datasets and report packages in formats suitable for insurance analytics, with fine-grained access controls to keep each partner’s windows isolated.  
- Trigger alerts when a driver’s data exhibits severe violations so insurers can initiate interventions; this mirrors the high-frequency monitoring already present in the `sensor` and `core` modules.

### Data throughput expectations
- The backend is data intensive: raw sensor ingestion is high-volume, aggregated queries are heavy, and downloads (both raw and aggregated) must stay performant. Prioritise batch uploads (mirroring `UploadAllDataWorker`’s periodic sync), pagination/cursoring for bulky endpoints, and caching strategies so researchers, fleet managers, and insurers experience low-latency access.

These roles provide constraints for the backend API surface, data models, authentication flows, and reporting/analytics pipelines when translating the current Android client into a FastAPI-powered service.
