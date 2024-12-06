from fastapi import APIRouter
import starlette.responses as _responses

router = APIRouter()

@router.get("/")
async def index():
    """
    Provides an overview of all available endpoints in the Safe Drive Africa API.
    """
    return {
        "message": "Welcome to the Safe Drive Africa API",
        "endpoints": {
            "/api/ai_model_inputs/": {
                "GET": "Retrieve all AI model inputs",
                "POST": "Create a new AI model input",
            },
            "/api/ai_model_inputs/{input_id}/": {
                "GET": "Retrieve a specific AI model input by ID",
                "PUT": "Update a specific AI model input by ID",
                "DELETE": "Delete a specific AI model input by ID",
            },
            "/api/driver_profiles/": {
                "GET": "Retrieve all driver profiles",
                "POST": "Create a new driver profile",
            },
            "/api/driver_profiles/{profile_id}/": {
                "GET": "Retrieve a specific driver profile by ID",
                "PUT": "Update a specific driver profile by ID",
                "DELETE": "Delete a specific driver profile by ID",
            },
            "/api/unsafe_behaviours/": {
                "GET": "Retrieve all unsafe behaviours",
                "POST": "Create a new unsafe behaviour entry",
            },
            "/api/unsafe_behaviours/{behaviour_id}/": {
                "GET": "Retrieve a specific unsafe behaviour by ID",
                "PUT": "Update a specific unsafe behaviour by ID",
                "DELETE": "Delete a specific unsafe behaviour by ID",
            },
            "/api/raw_sensor_data/": {
                "GET": "Retrieve all raw sensor data",
                "POST": "Create a new raw sensor data entry",
            },
            "/api/raw_sensor_data/{sensor_data_id}/": {
                "GET": "Retrieve specific raw sensor data by ID",
                "PUT": "Update specific raw sensor data by ID",
                "DELETE": "Delete specific raw sensor data by ID",
            },
            "/api/nlg_reports/": {
                "GET": "Retrieve all NLG reports",
                "POST": "Create a new NLG report",
            },
            "/api/nlg_reports/{report_id}/": {
                "GET": "Retrieve a specific NLG report by ID",
                "PUT": "Update a specific NLG report by ID",
                "DELETE": "Delete a specific NLG report by ID",
            },
            "/api/locations/": {
                "GET": "Retrieve all locations",
                "POST": "Create a new location entry",
            },
            "/api/locations/{location_id}/": {
                "GET": "Retrieve a specific location by ID",
                "PUT": "Update a specific location by ID",
                "DELETE": "Delete a specific location by ID",
            },
            "/api/embeddings/": {
                "GET": "Retrieve all embeddings",
                "POST": "Create a new embedding entry",
            },
            "/api/embeddings/{embedding_id}/": {
                "GET": "Retrieve a specific embedding by ID",
                "PUT": "Update a specific embedding by ID",
                "DELETE": "Delete a specific embedding by ID",
            },
            "/api/driving_tips/": {
                "GET": "Retrieve all driving tips",
                "POST": "Create a new driving tip",
            },
            "/api/driving_tips/{tip_id}/": {
                "GET": "Retrieve a specific driving tip by ID",
                "PUT": "Update a specific driving tip by ID",
                "DELETE": "Delete a specific driving tip by ID",
            },
            "/api/causes/": {
                "GET": "Retrieve all causes",
                "POST": "Create a new cause",
            },
            "/api/causes/{cause_id}/": {
                "GET": "Retrieve a specific cause by ID",
                "PUT": "Update a specific cause by ID",
                "DELETE": "Delete a specific cause by ID",
            },
            "/api/trips/": {
                "GET": "Retrieve all trips",
                "POST": "Create a new trip",
            },
            "/api/trips/{trip_id}/": {
                "GET": "Retrieve a specific trip by ID",
                "PUT": "Update a specific trip by ID",
                "DELETE": "Delete a specific trip by ID",
            },
        },
        "documentation": {
            "Swagger UI": "/docs",
            "ReDoc": "/redoc"
        }
    }
