from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils.config import settings

# Import Modules
from llm.chat_engine import ChatEngine
from predictors.forecasr_model import ForecastModel
from predictors.pattern_model import PatternModel


app = FastAPI(
    title="QuantForge AI Engine",
    version="1.0.0",
    description="AI microservices for chat, predections, and pattern analysis.",
)

# Initialize models/services

try:
    chat_engine = ChatEngine()
except Exception as e:
    chat_engine = None
    print(f"[WARN] chat engine not initialized yet: {e}")

forecast_model = ForecastModel()
pattern_model = PatternModel()


@app.get("/")
def root():
    return {"status": "QuantForge AI Engine is running"}


class ChatRequest(BaseModel):
    prompt: str


class PredictRequest(BaseModel):
    data: list


class PatternRequest(BaseModel):
    data: list


# ============= Endpoints =============


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    if not chat_engine:
        raise HTTPException(status_code=503, detail="Chat engine not initialized")
    try:
        response = chat_engine.generate(request.prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict")
def predict_endpoint(request: PredictRequest):
    try:
        result = forecast_model.predict(request.data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patterns")
def pattern_endpoint(request: PatternRequest):
    try:
        result = pattern_model.detect(request.data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
