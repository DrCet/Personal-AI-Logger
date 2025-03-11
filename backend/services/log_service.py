from backend.integrations.fast_whisper_integration import AudioProcessor
from backend.database import save_audio_file
from sqlalchemy.orm import Session
import aiofiles
import logging
from fastapi import File, UploadFile, Form
from datetime import datetime
import os

logger = logging.getLogger(__name__)
audio_processor = AudioProcessor()

async def process_audio_log(file, Log, db: Session, text:str = Form(...)):
    try:
        logger.info(f'Processing audio: {file.filename}')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        file_path = os.path.join("audio_logs", filename)
        
        # Save audio file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create log entry
        new_log = Log(
            text=text,
            audio_file=filename,
            created_at=datetime.now()
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        return {
            "message": "Audio and transcript saved",
            "file_name": filename,
            "id": new_log.id
        }
    except Exception as e:
        logger.error(f"Error saving audio: {e}")
        db.rollback()
        raise