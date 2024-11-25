from datetime import datetime

from fastapi import APIRouter

from mm_backend.schemas import HealthCheck

router = APIRouter(
    prefix="",
    tags=["root"]
)

@router.get(
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
