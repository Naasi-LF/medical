"""Pydantic request / response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=30)
    password: str = Field(min_length=4, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


# ---------- Chat ----------
class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: str | None = None
    think_mode: bool = True
    top_k: int = 8


class RenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=50)


class ConversationOut(BaseModel):
    id: str
    title: str
    updated_at: str


class MessageOut(BaseModel):
    role: str
    content: str
    thinking: str = ""
    sources: list[str] = []
    references: list[dict] = []
    created_at: str = ""


# ---------- Memory ----------
class MemoryEntityOut(BaseModel):
    id: str
    entity_type: str
    entity_name: str
    properties: dict


class MemoryRelationOut(BaseModel):
    id: str
    source: str
    relation: str
    target: str


class MemoryInfoRequest(BaseModel):
    text: str = Field(min_length=1)
