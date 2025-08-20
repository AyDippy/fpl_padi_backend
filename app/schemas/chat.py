from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(ChatRequest):
    user_id: str
    response: str
    timestamp: str
