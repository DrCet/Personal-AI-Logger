#backnend/api/routes/log.py
#this module defines the API endpoints for the logs table
from backend.services.transcribe_service import transcribe_stream
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
import logging
from datetime import datetime, timezone, timedelta
import aiofiles


from backend.models import Log
from backend.database import get_db


os.makedirs("audio_logs", exist_ok=True)
logger = logging.getLogger(__name__)

router = APIRouter()

class LogRequest(BaseModel):
    text: str

@router.post('/log', summary='Create a new log entry')
async def create_log(log_request: LogRequest, db: AsyncSession = Depends(get_db)):
    # Create a new log instance with the provided text
    new_log = Log(text=log_request.text)
    db.add(new_log) 
    await db.commit()
    await db.refresh(new_log)
    return {'message': "Log saved", 'id':new_log.id}

@router.get('/log', summary='Get all log entries')
def get_logs(db: AsyncSession = Depends(get_db)):
    logs = db.query(Log).all()
    return logs


# Define an endpoint to upload an audio file and create a new log entry
# Post a file to the /log/audio endpoint to create a new log entry with an audio file
# The file parameter is an UploadFile object that represents the uploaded file
# The process_audio_log function processes the audio file and returns the transcription
# The transcription is saved in the database along with the audio file name
@router.post('/log/audio')
async def upload_audio(file: UploadFile = File(...), text: str = Form(...), db: AsyncSession = Depends(get_db)):
    logger.debug(f"Received db object: {db}")
    logger.info(f"Processing audio: {file.filename}")
    try:
        gmt_plus_7 = timezone(timedelta(hours=7))
        # Simpler timestamp format: HH-MM-SS-DD-MM-YYYY 
        timestamp = datetime.now(gmt_plus_7)
        filename = f"{timestamp.strftime("%H-%M-%S-%d-%m-%Y")}.wav"  
        file_path = os.path.join("audio_logs", filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        new_log = Log(audio_file=file_path, text=text, timestamp=timestamp)
        logger.info(f'Try to add {new_log} to the logs table')
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
        
        return {"message": "Audio and transcript saved", "file_name": filename, "id": new_log.id}
    except Exception as e:
        if db is not None:
            logger.debug(f"Rolling back with db: {db}")  # Debug before rollback
            await db.rollback()
        else:
            logger.error(f"db is None during rollback attempt")
        logger.error(f"Error saving audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving audio: {e}")
