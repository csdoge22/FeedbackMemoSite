from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Feedback API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}