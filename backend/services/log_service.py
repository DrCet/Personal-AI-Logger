from backend.integrations.fast_whisper_integration import AudioProcessor
from backend.models import Log
from sqlalchemy.orm import Session
import aiofiles
import logging

logger = logging.getLogger(__name__)
audio_processor = AudioProcessor()

async def process_audio_log(file, db: Session):
    try:
        logger.info(f'Processing audio: {file.filename}')
        file_path = f"audio_logs/{file.filename}"
        
        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Transcribe file
        text = await audio_processor.transcribe_file(file_path)
        logger.info(f'Transcription complete: {text[:100]}...')
        
        # Save to database
        db_log = Log(text=text, audio_file=file.filename)
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        return text
    except Exception as e:
        logger.error(f"Error processing audio log: {e}")
        raise