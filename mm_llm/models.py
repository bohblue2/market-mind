
from typing import Dict, List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]]

