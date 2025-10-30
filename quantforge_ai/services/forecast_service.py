import numpy as np


def forecast_asset(symbol: str, data: list):
	"""Mock forecast logic - replace with ARIMA/LSTM later"""
	if not data:
		return {"error": "No data provided"}
	avg = np.mean(data)
	trend = "bullish" if data[-1] > avg else "bearish"
	return {"trend": trend, "average": avg, "confidence": 0.85}
