from fastapi import APIRouter

from ..services.analyzer_service import detect_patterns

router = APIRouter()


@router.post("/")
async def analyze_patterns(payload: dict):
	"""Detect anomalies, correlations, and trends."""
	data = payload.get("data", [])
	patterns = detect_patterns(data)
	return {"patterns": patterns}
