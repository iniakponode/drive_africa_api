import os
import dotenv
import uvicorn
from fastapi import FastAPI
import logging
from safedrive import safe_drive_africa_api_router as api_router
from fastapi.middleware.cors import CORSMiddleware

# Load .env only for local development
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "development":
    dotenv.load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Safe Drive API",
    description="This is an API powering Safe Drive Africa, a PhD research app",
    version="1.0.0"
)

# Example usage of environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG") == "True"

# Include API router
app.include_router(api_router)

# Define allowed CORS origins
origins = [
    "https://api.safedriveafrica.com",
    "http://api.safedriveafrica.com",
    # Add other origins if necessary
]

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if ENVIRONMENT == "production" else ["*"],  # Allow all in local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on app startup
@app.on_event("startup")
async def on_startup():
    Base.metadata.create_all(bind=engine)  # Ensure tables are created

# Run the app using uvicorn when executed directly
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Set host and port based on environment
    host = "0.0.0.0" if ENVIRONMENT == "production" else "127.0.0.1"
    port = int(os.environ.get("PORT", 8000))  # Use Heroku's $PORT or default for local

    uvicorn.run("main:app", reload=(ENVIRONMENT == "development"), host=host, port=port)