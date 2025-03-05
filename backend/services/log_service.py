from backend.integrations.fast_whisper_integration import transcribe_audio
from backend.models import Log
from sqlalchemy.orm import Session


def process_audio_log(file, db: Session):
    print(f'Audio: {file.filename}')
    file_path = f"audio_logs/{file.filename}"
    with open(file_path, 'wb') as f:
        f.write(file.file.read())  # Save the file
    
    text = transcribe_audio(file_path) 
    print(f'Transcription: {text}') 
    db_log = Log(text=text, audio_file=file.filename)

    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return text