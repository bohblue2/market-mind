from fastapi import APIRouter, Body, Depends

from mm_backend.constant import LATEST_INDEX
from mm_backend.schemas import ChatCompletionResponse, ChatRequest, RoleEnum
from mm_llm.generator import GeneratorService, get_generator_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post(
    "/completion", 
    response_model=ChatCompletionResponse
)
async def chat_completion(
    generator_service: GeneratorService  = Depends(get_generator_service),    
    request: ChatRequest = Body(
        ...,
        example={
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, how are you?"
                },
                {
                    "role": "assistant",
                    "content": "I'm fine, thank you."
                }
            ]
        }
    )
):
    last_message = request.messages[LATEST_INDEX].content
    response_text = generator_service.generate_answer(content=last_message)
    if response_text == "" or response_text is None:
        response_text = "I'm sorry, I don't have an answer to that question."
    return ChatCompletionResponse(role=RoleEnum.assistant, content=response_text)

