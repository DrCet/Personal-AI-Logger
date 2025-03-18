from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from backend.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import os

router = APIRouter()

# Set up templates (assuming templates are in the 'frontend' directory)
templates = Jinja2Templates(directory="frontend")

# List of predefined sentences (for now; can be replaced with AI-generated sentences)

# Serve the audio_context_record.html page
@router.get("/context-audio-recording", response_class=HTMLResponse)
async def get_audio_context_record(request: Request):
    return templates.TemplateResponse("audio_context_record.html", {"request": request})

@router.get('/context-audio-recording/sentences')
async def get_sentences(db: AsyncSession = Depends(get_db)):
    # Path to the private sentences file (adjust based on your project structure)
    file_path = os.path.join(os.path.dirname(__file__), '..','..','/integrations/sentences.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sentences = f.read().splitlines()  # Split by lines, remove empty lines
            return {"sentences": [s.strip() for s in sentences if s.strip()]}
    except FileNotFoundError:
        return {"error": "Sentences file not found", "sentences": []}
    except Exception as e:
        return {"error": f"Error reading sentences: {str(e)}", "sentences": []}

