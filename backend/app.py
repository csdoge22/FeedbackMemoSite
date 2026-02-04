from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from model_utils import load_models, predict_with_priority, bucket_priority
app = FastAPI()

class Priority(BaseModel):
    text: str

@app.get("/")
def index():
    data = {"response": "Welcome to the Feedback API"}
    return JSONResponse(data, status_code=200)

@app.post("/priority")
def get_priority(priority_obj: Priority):
    models = load_models()
    predictions = predict_with_priority(models, priority_obj.text)
    data = {"text": priority_obj.text, "priority": predictions}
    return JSONResponse(data, status_code=200)