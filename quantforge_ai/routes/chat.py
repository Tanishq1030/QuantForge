from fastapi import APIRouter

from ..services.llm_service import get_llm_response

router = APIRouter()


@router.post("/")
async def chat(request: dict):
	"""LLM-based conversational and analytical endpoint,"""
	user_input = request.get("message", "")
	response = get_llm_response(user_input)
	return {"input": user_input, "response": response}
