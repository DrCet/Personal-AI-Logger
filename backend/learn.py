from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Personal AI Logger API new"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)