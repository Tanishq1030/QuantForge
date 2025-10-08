import os
import requests
from dotenv import load_dotenv

load_dotenv()


class ChatEngine:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/mistral/Mistral-7B-Instruct-v0.2"
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
        print("[INFO] ChatEngine initialized using Hugging Face API.")


    def chat(self, prompt: str) -> str:
        payload = {
            "input":prompt,
            "parameters": {
                "max_new_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            }
        }

        response = requests.post(self.api_url, headers=self.headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"HuggingFace API Error: {response.status_code}, {response.text}")

        data = response.json()

        # Handle both possible API response formats
        if isinstance((data, list) and "generated_text" in data[0]):
            return data[0]["generated_text"].strip()
        elif "error" in data:
            raise Exception(f"API Error: {data['error']}")
        else:
            return str(data)


