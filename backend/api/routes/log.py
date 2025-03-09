#backnend/api/routes/log.py
#this module defines the API endpoints for the logs table
from backend.services.transcribe_service import transcribe_stream
from fastapi import APIRouter, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from backend.models import Log
from backend.database import get_db
from backend.services.log_service import process_audio_log


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
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(Log).all()
    return logs


# Define an endpoint to upload an audio file and create a new log entry
# Post a file to the /log/audio endpoint to create a new log entry with an audio file
# The file parameter is an UploadFile object that represents the uploaded file
# The process_audio_log function processes the audio file and returns the transcription
# The transcription is saved in the database along with the audio file name
@router.post('/log/audio', summary='Create a new log entry with an audio file')
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    transcript = await process_audio_log(file, db, Log)  # Pass Log model
    return {"message": "Audio saved", "file_name": file.filename}

