"""Auth routes: register + login."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ..auth import create_access_token, hash_password, verify_password
from ..database import users_col
from ..models import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    col = users_col()
    if col.find_one({"username": req.username}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    doc = {
        "username": req.username,
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = col.insert_one(doc)
    user_id = str(result.inserted_id)
    token = create_access_token(user_id)
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        username=req.username,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    col = users_col()
    user = col.find_one({"username": req.username})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    user_id = str(user["_id"])
    token = create_access_token(user_id)
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        username=req.username,
    )
