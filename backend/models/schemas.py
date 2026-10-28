"""Pydantic 모델 — 요청/응답 데이터 검증"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ── 데이터 (시계열) ──────────────────────────────────
class DataCreate(BaseModel):
    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2024-01-15"])
    value: float = Field(..., description="값 (예: BTC 가격 USD)", examples=[42500.0])
    memo: str = Field("", description="메모", examples=["급등세"])


class DataUpdate(BaseModel):
    date: Optional[str] = None
    value: Optional[float] = None
    memo: Optional[str] = None


class DataResponse(BaseModel):
    id: str
    date: str
    value: float
    memo: str


# ── 채팅 ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="사용자 메시지")
    conversation_id: Optional[str] = Field(None, description="기존 대화 ID (없으면 새 대화)")


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


# ── 대화 기록 ────────────────────────────────────────
class MessageItem(BaseModel):
    role: str
    content: str


class ConversationCreate(BaseModel):
    title: str = Field("새 대화", description="대화 제목")
    messages: list[MessageItem] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    message_count: int
