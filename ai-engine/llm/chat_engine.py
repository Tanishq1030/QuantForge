import os
from llama_cpp import Llama
from utils.config import settings


class ChatEngine:
    def __init__(self, model_name="mistral-7b-instruct.gguf"):
        model_path = os.path.join(settings.MODEL_PATH, model_name)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        self.llm = Llama(model_path=model_path, n_threads=8, n_ctx=4096)

    def generate(self, prompt: str):
        response = self.llm(prompt, max_tokens=256, temperature=0.7)
        return response["choices"][0]["text"].strip()
