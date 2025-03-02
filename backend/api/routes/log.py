#backnend/api/routes/log.py
#this module defines the API endpoints for the logs table
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.models import Log
from backend.database import get_db


router = APIRouter()

class LogRequest(BaseModel):
    text: str

@router.post('/log', summary='Create a new log entry')
async def create_log(log_request: LogRequest, db: Session = Depends(get_db)):
    # Create a new log instance with the provided text
    new_log = Log(text=log_request.text)
    db.add(new_log) 
    db.commit()
    db.refresh(new_log)
    return {'message': "Log saved", 'id':new_log.id}

@router.get('/log', summary='Get all log entries')
async def get_logs(db: Session = Depends(get_db)):
    logs = db.query(Log).all()
    return logs

