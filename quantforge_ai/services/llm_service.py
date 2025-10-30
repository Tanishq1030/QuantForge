from huggingface_hub import InferenceClient

from ..app.config import settings

client = InferenceClient(api_key=settings.HF_API_KEY)


def get_llm_response(prompt: str):
	try:
		response = client.text_generation(
			model=settings.MODEL_NAME,
			prompt=prompt,
			max_new_tokens=150,
		)
		return response
	except Exception as e:
		return f"Eror: {str(e)}"
