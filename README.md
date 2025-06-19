# Safe Drive Africa API

This repository contains the FastAPI backend for Safe Drive Africa. The service exposes REST endpoints used to collect driving information and generate reports.

## Prerequisites

- Python 3.12
- A PostgreSQL (or compatible) database instance

## Installation

1. Clone the repository and enter the project folder.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and define at least the following variables:
   ```
   DATABASE_URL=<your database connection url>
   SECRET_KEY=<random secret string>
   ENVIRONMENT=development
   ```

## Running the server

Start the API with:

```bash
uvicorn main:app --reload
```

The service will be available at `http://127.0.0.1:8000` by default. Interactive
Swagger documentation is served at `/docs` and a ReDoc view is available at
`/redoc`.

## API overview

All endpoints are grouped under `/api`. Common resources include:

| Path prefix | Purpose | Example |
|-------------|---------|---------|
| `/trips/` | Manage trip records | `GET /api/trips/` |
| `/driver_profiles/` | CRUD driver profiles | `POST /api/driver_profiles/` |
| `/unsafe_behaviour/` | Unsafe driving behaviour logs | `GET /api/unsafe_behaviour/` |
| `/raw_sensor_data/` | Upload or query sensor data | `GET /api/raw_sensor_data/` |
| `/driving_tips/` | Retrieve safe driving tips | `GET /api/driving_tips/` |
| `/cause/` | Accident or incident causes | `GET /api/cause/` |
| `/embedding/` | Embeddings for ML models | `GET /api/embedding/` |
| `/nlg_report/` | Natural language reports | `GET /api/nlg_report/` |
| `/ai_model_inputs/` | Data fed to AI models | `GET /api/ai_model_inputs/` |
| `/location/` | Location lookups | `GET /api/location/` |
| `/alcohol-questionnaire/` | Submit alcohol questionnaire | `POST /api/alcohol-questionnaire/questionnaire/` |
| `/behaviour_metrics/` | Aggregated behaviour metrics | `GET /api/behaviour_metrics/ubpk` |

The complete schema, including request and response models, can be explored via
Swagger UI.

## Database migrations

Alembic is used to manage schema migrations. Apply the latest migrations with:

```bash
alembic upgrade head
```

## License

This project is distributed under the MIT License.
