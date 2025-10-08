from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils.config import settings

# Import Modules
from llm.chat_engine import ChatEngine
from predictors.forecast_model import ForecastModel
from predictors.pattern_model import PatternModel


app = FastAPI(
    title="QuantForge AI Engine",
    version="1.0.0",
    description="AI microservices for chat, predictions, and pattern analysis.",
)


# Initialize models/services
try:
    chat_engine = ChatEngine()
    print("[INFO] Chat engine initialized successfully.")
except Exception as e:
    chat_engine = None
    print(f"[WARN] Chat not initialized yet: {e}")

try:
    forecast_model = ForecastModel()
    print("[INFO] Forecast model loaded successfully.")
except Exception as e:
    forecast_model = None
    print(f"[WARN] Forecast model initialized failed: {e}")

try:
    pattern_model = PatternModel()
    print("[INFO] Pattern model loaded successfully.")
except Exception as e:
    pattern_model = None
    print(f"[WARN] Pattern model initialization failed: {e}")


@app.get("/")
def root():
    return {"status": "QuantForge AI Engine is running"}


# ============= Data Models =============
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
        response = chat_engine.chat(request.prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict")
def predict_endpoint(request: PredictRequest):
    if not forecast_model:
        raise HTTPException(status_code=503, detail="Forecast model not initialized")

    try:
        result = forecast_model.predict(request.data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patterns")
def pattern_endpoint(request: PatternRequest):
    if not pattern_model:
        raise HTTPException(status_code=503, detail="Pattern model not initialized")

    try:
        result = pattern_model.detect(request.data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

