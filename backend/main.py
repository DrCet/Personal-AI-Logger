from sys import prefix
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
import shutil
import os
from backend.api.routes import log, search, transcribe
import uvicorn
import logging

# Create app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.debug("Registered routes:")
    for route in app.routes:
        logger.debug(f"{route.path} [{route.name}]")

# Mount the static files directory
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_file_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    try:
        with open(html_file_path, "r") as f:
            html_content = f.read()
        # Replace the direct scripts.js reference with the static path
        html_content = html_content.replace('src="scripts.js"', 'src="/static/scripts.js"')
        return html_content
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
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