from typing import Any, Union, Optional
from fastapi import APIRouter, Body, Form, Depends, HTTPException
from api.schemas.token import Token, TokenInDB
from pydantic import BaseModel
from api.auth.deps import generate_access_token
from api.database import db
from api.config import settings
import uuid

router = APIRouter()

@router.post("/auth", response_model=Token)
def auth(
    user_id: str = Form(...),
    password: str = Form(...)
):
    """
    Custom auth endpoint to generate access token.

    It doesn't follow OAuth2 password grant_flow spec
    https://tools.ietf.org/html/rfc6749#section-4.3.2
    """

    # Validate user credentials
    # This demo requires a hardcoded user
    if not user_id == settings.DEMO_USER_ID or not password == settings.DEMO_USER_PASSWORD:
        raise HTTPException(
            status_code=400, detail="Incorrect user_id or password")
    return Token(token = generate_access_token(user_id))
