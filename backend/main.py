from sys import prefix
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
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

#Directory to store audio logs
os.makedirs("audio_logs", exist_ok=True)
@app.get("/")
def read_root():
    return {"message": "Personal AI Logger API new"}

app.include_router(log.router, prefix='/api')
app.include_router(search.router, prefix='/api')
app.include_router(transcribe.router, prefix='/api')

if __name__ == "__main__":
    uvicorn.run("backend.main:app", 
                host="127.0.0.1", 
                port=8000, 
                reload=True,
                log_level="debug")