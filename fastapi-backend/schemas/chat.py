from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 请求体
class ChatStartRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    story_id: Optional[int] = Field(None, ge=1)


class SendMessageRequest(BaseModel):
    session_id: int = Field(..., ge=1)
    content: str = Field(..., min_length=1, max_length=5000)


# 响应体
class MessageResponse(BaseModel):
    id: int
    sessionId: str
    role: str
    content: str
    metadata: Optional[dict] = None
    createdAt: datetime


class ChatSessionResponse(BaseModel):
    id: int
    sessionKey: str = Field(..., alias="session_key")
    title: str
    status: str
    currentStage: str = Field(..., alias="current_stage")
    progressPercentage: int = Field(..., alias="progress_percentage")   
    storyId: Optional[int] = Field(None, alias="story_id")
    contextData: Optional[dict] = Field(None, alias="context_data")     
    startedAt: datetime = Field(..., alias="started_at")                
    lastActive: datetime = Field(..., alias="last_active")