from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	PROJECT_NAME: str = "QuantForge AI Engine"
	VERSION: str = "0.1.0"
	ENVIRONMENT: str = "development"
	DEBUG: bool = True
	
	# API keys
	HF_API_KEY: str | None = None
	OPENAI_API_KEY: str | None = None
	
	# Model config
	MODEL_NAME: str = "mistralai/Mistral-7B-Instruct-v0.2"
	
	class Config:
		env_file = ".env"
		extra = "ignore"


@lru_cache()
def get_settings():
	return Settings()


settings = get_settings()
