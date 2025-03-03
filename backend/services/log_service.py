from backend.intergrations.vosk_integration import transcribe_audio
from backend.models import Log
from sqlalchemy.orm import Session


async def process_audio_log(file, db: Session):
    print(file.filename)
    file_path = f"audio_logs/{file.filename}"
    with open(file_path, 'wb') as f:
        f.write(file.file.read())  # Save the file
    
    text = await transcribe_audio(file_path) 
    print(f'Transcription: {text}') # Call without await
    db_log = Log(text=text)

    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return {'message': 'Log saved', 'id': db_log.id}