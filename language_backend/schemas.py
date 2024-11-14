from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime

class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

# 메시지 구조 정의
class Message(BaseModel):
    role: RoleEnum  # Enum으로 역할 지정
    content: str

# 요청 형식 정의
class ChatRequest(BaseModel):
    model: str
    messages: List[Message] = list()
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7

# 응답 형식 정의
class ChatCompletionResponse(BaseModel):
    role: RoleEnum
    content: str
