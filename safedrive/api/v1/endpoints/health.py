"""
Health check endpoint for monitoring and load balancers.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from safedrive.database.db import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns:
        dict: Health status with database connectivity check
        
    Raises:
        HTTPException: 503 if service is unhealthy
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": "2.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@router.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: API information
    """
    return {
        "name": "Safe Drive Africa API",
        "version": "2.0.0",
        "status": "online"
    }
