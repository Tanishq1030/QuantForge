from fastapi import APIRouter

from ..services.forecast_service import forecast_asset

router = APIRouter()


@router.post("/")
async def predict(payload: dict):
	"""Predict asset movement based on provided time-series data."""
	symbol = payload.get("symbol")
	data = payload.get("data", [])
	forecast = forecast_asset(symbol, data)
	return {"symbol": symbol, "forecast": forecast}
