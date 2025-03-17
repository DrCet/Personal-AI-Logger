#backnend/api/routes/log.py
#this module defines the API endpoints for the logs table
from unittest import result
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import os
import logging
from datetime import datetime, timezone, timedelta
import aiofiles
import pathlib
from backend.config import PROJECT_ROOT


from backend.models import Log
from backend.database import get_db


os.makedirs("audio_logs", exist_ok=True)
logger = logging.getLogger(__name__)

router = APIRouter()

class LogRequest(BaseModel):
    text: str

# Retrieve all logs in the logs table
@router.get('/logs/data', summary='Get all log entries')
async def get_logs(db: AsyncSession = Depends(get_db), limit: int = Query(10, ge=1, le=100, description="Number of logs to retrieve")):
    logger.debug("Entered get_logs endpoint")
    try:

        '''
        result = select(Log).order_by(Log.timestamp.desc()).limit(limit)
        logs = result.scalars().all()
        This is incorrect because result is a Select object, not a Result object. 
        We need to execute the query with await db.execute() to fix this.'''
        # Define the query
        query = select(Log).order_by(Log.timestamp.desc()).limit(limit)
        # Execute the query with the database session
        result = await db.execute(query)
        # Fetch the results
        logs = result.scalars().all()
        if not logs:
            logger.info("No logs found in database")
            return []

        # Convert logs to JSON-serializable format
        logs_list = [
            {
                "id": log.id,
                "text": log.text,
                "audio_file": log.audio_file,
                "timestamp": log.timestamp.isoformat()  # Convert datetime to string
            }
            for log in logs
        ]
        logger.info(f"Retrieved {len(logs_list)} logs from database")
        return logs_list
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {e}")

@router.get('/audio/{filename}', summary='Retrieve an audio file by filename')
async def get_audio(filename: str):
    logger.debug(f"Entered get_audio endpoint for filename: {filename}")
    try:
        # Construct the full file path
        audio_logs_path = os.path.join(os.path.dirname(__file__), "..", "..", '..', "audio_logs")
        file_path = os.path.join(audio_logs_path, filename)

        # Ensure the resolved path is within audio_logs directory
        resolved_path = pathlib.Path(file_path).resolve()
        audio_logs_resolved = pathlib.Path(audio_logs_path).resolve()
        if not str(resolved_path).startswith(str(audio_logs_resolved)):
            logger.warning(f"Path traversal attempt: {filename}")
            raise HTTPException(status_code=400, detail="Invalid file path")

        # Check if the file exists on disk
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found on disk: {file_path}")
            raise HTTPException(status_code=404, detail="Audio file not found on server")

        logger.info(f"Serving audio file: {file_path}")
        return FileResponse(file_path, media_type="audio/wav")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving audio file: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving audio file: {e}")


# Define an endpoint to upload an audio file and create a new log entry
# Post a file to the /log/audio endpoint to create a new log entry with an audio file
# The file parameter is an UploadFile object that represents the uploaded file
# The process_audio_log function processes the audio file and returns the transcription
# The transcription is saved in the database along with the audio file name
@router.post('/logs/audio')
async def upload_audio(file: UploadFile = File(...), text: str = Form(...), db: AsyncSession = Depends(get_db)):
    logger.debug(f"Received db object: {db}")
    logger.info(f"Processing audio: {file.filename}")
    try:
        gmt_plus_7 = timezone(timedelta(hours=7))
        # Timezone-aware object
        timestamp = datetime.now(gmt_plus_7)
        # Simpler timestamp format: HH-MM-SS-DD-MM-YYYY 
        filename = f"{timestamp.strftime("%H-%M-%S-%d-%m-%Y")}.wav"  
        file_path = os.path.join("audio_logs", filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        # Need to convert the timestamp to timezone-naive to match the table datatype
        new_log = Log(audio_file=filename, text=text, timestamp=timestamp.replace(tzinfo=None))
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


@router.delete('/logs/delete/{log_id}')
async def delete_log(log_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Find the log
        log = await db.get(Log, log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

        # Delete the associated audio file
        audio_logs_path = os.path.join(PROJECT_ROOT, "audio_logs")
        file_path = os.path.join(audio_logs_path, log.audio_file)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete the log from the database
        await db.delete(log)
        await db.commit()

        return {"message": "Log deleted successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting log: {e}")