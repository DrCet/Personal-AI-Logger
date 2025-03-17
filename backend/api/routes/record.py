from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from backend.log import add_log, get_logs, delete_log  # Import predefined methods
from backend.database import get_db, Log  # Import database dependencies
from pathlib import Path
import uuid
import shutil
import os
import random

router = APIRouter()

# Set up templates (assuming templates are in the 'frontend' directory)
templates = Jinja2Templates(directory="frontend")

# List of predefined sentences (for now; can be replaced with AI-generated sentences)

# Serve the audio_context_record.html page
@router.get("/context-audio-recording", response_class=HTMLResponse)
async def get_audio_context_record(request: Request):
    return templates.TemplateResponse("audio_context_record.html", {"request": request})