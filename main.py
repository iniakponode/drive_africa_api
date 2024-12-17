# Registering router to main API
import os
import dotenv
import uvicorn
from fastapi import FastAPI
import sys
import logging
from safedrive import safe_drive_africa_api_router as api_router

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv()

# Create FastAPI app
app = FastAPI()

# Example usage of environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG") == "True"

app.include_router(api_router)

# Run the app using uvicorn when executed directly
if __name__ == "__main__":
    logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))  # Added a default port value
    uvicorn.run("main:app", reload=True, host=host, port=port)
