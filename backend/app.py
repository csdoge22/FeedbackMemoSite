from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def index():
    data = {"response": "Welcome to the Feedback API"}
    return JSONResponse(data, status_code=200)