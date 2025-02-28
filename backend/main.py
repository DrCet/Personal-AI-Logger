from sys import prefix
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import shutil
import os
from backend.api.routes import log, search

# Create app
app = FastAPI()

#Directory to store audio logs
os.makedirs("audio_logs", exist_ok=True)
@app.get("/")
def read_root():
    return {"message": "Personal AI Logger API new"}

app.include_router(log.router, prefix="/api")
app.include_router(search.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)