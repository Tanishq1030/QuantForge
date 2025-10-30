import numpy as np


def detect_patterns(data: list):
	"""Simple pattern detection = spike, dips, or trends."""
	if not data:
		return {"error": "No data provided"}
	diffs = np.diff(data)
	spikes = np.where(np.abs(diffs) > np.std(diffs) * 2)[0].tolist()
	return {"spikes_detected": len(spikes), "spike_positions": spikes}
