from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import shutil
import os

# Create app
app = FastAPI()

#Directory to store audio logs
os.makedirs("audio_logs", exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Personal AI Logger API new"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)