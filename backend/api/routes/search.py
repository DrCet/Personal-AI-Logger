# backend/api/routes/search.py
# This module defines API endpoints for searching through logs.
# It uses FastAPI's APIRouter to create a modular route and SQLAlchemy
# to query the PostgreSQL database for logs matching a text query.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.models import Log  # Import the Log model
from backend.database import get_db  # Dependency to get the database session

router = APIRouter()

@router.get("/search", summary="Search logs by text query")
def search_logs(query: str, db: Session = Depends(get_db)):
    """
    Search for logs that contain the provided query string in their text.
    
    - **query**: The text string to search for in the logs.
    """
    # Query the database for logs where the text contains the query (case-insensitive)
    logs = db.query(Log).filter(Log.text.ilike(f"%{query}%")).all()
    
    # If no logs are found, raise a 404 error
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found matching the query.")
    
    # Return the list of matching logs
    return logs
