from datetime import datetime 
from fastapi import Body, FastAPI, Depends, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from language_backend.schemas import ChatCompletionResponse, ChatRequest, HealthCheck, RoleEnum
from language_backend.service.llm import LlmService

LATEST_INDEX = -1

def get_app() -> FastAPI:
    app = FastAPI()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app  

def get_llm_service():
    service = LlmService()
    try:
        yield service
    finally:
        service.close()


app = get_app()

@app.get(
    "/health", 
    response_model=HealthCheck,
    summary="서버 상태 확인",
    description="서버의 현재 상태와 타임스탬프를 반환합니다.",
    responses={
        200: {
            "description": "서버가 정상적으로 동작 중",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-01T00:00:00"
                    }
                }
            }
        }
    }
)
async def health_check() -> HealthCheck:
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now()
    )

@app.post(
    "/api/chat/completion", 
    response_model=ChatCompletionResponse
)
async def chat_completion(
    llm_service: LlmService = Depends(get_llm_service),    
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
    response_text = llm_service.generate_answer(content=last_message)
    return ChatCompletionResponse(role=RoleEnum.assistant, content=response_text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)