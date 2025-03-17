from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend.database import AsyncSessionLocal

import os
from backend.api.routes import log, search, transcribe
import uvicorn
import logging
from backend.database import check_permissions

# Create app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.debug("Registered routes:")
    async with AsyncSessionLocal() as session:
        await check_permissions(db=session)
    for route in app.routes:
        logger.debug(f"{route.path} [{route.name}]")
        logger.info(f"{route.path} [{route.name}]")

# Mount the static files directory
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    try:
        with open(html_file_path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)

@app.get("/live-transcription", response_class=HTMLResponse)
def live_transcription():
    html_file_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "live_transcription.html")
    try:
        with open(html_file_path, "r") as f:
            html_content = f.read()
        # Replace the direct scripts.js reference with the static path
        html_content = html_content.replace('src="live_transcription.js"', 'src="/static/live_transcription.js"')
        return html_content
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)
    
# New context-audio-recording endpoints
@app.get("/context-audio-recording", response_class=HTMLResponse)
async def context_audio_recording():
    html_file_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "context_audio_recording.html")
    try:
        with open(html_file_path, "r") as f:
            html_content = f.read()
        # Replace the direct JS reference with the static path
        html_content = html_content.replace('src="/context_audio_recording.js"', 'src="/static/context_audio_recording.js"')
        return html_content
    except Exception as e:
        logger.error(f"Error reading audio_context_record.html: {e}")
        return HTMLResponse(content="Error loading page", status_code=500)

app.include_router(log.router, prefix='/api')
app.include_router(search.router, prefix='/api')
app.include_router(transcribe.router, prefix='/api')

if __name__ == "__main__":
    uvicorn.run("backend.main:app", 
                host="127.0.0.1", 
                port=8000, 
                reload=True,
                log_level="debug")