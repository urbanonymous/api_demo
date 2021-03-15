
from datetime import datetime, timedelta
from typing import Any, Union
from pydantic import BaseModel
from fastapi import APIRouter, Body, Form, Depends, HTTPException
from api.schemas.token import Token, TokenInDB
from api.schemas.user import User
from api.database import db
from api.config import settings
import uuid

from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from typing import List, Optional

from fastapi.exceptions import HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.security.http import HTTPBase

class HTTPAuthorizationCredentials(BaseModel):
    scheme: str
    credentials: str

def get_token(request: Request) -> Optional[str]:
    authorization: str = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return param

def get_datetime_now():
    """ This function allows to mock the current time at testing """
    return datetime.now()

def get_user_access_token(token: str = Depends(get_token), datetime_now = Depends(get_datetime_now)) -> Optional[TokenInDB]:
    """Returns the token information from db of a token.

    As this demo doesn't follow OAuth2, and the token doesn't have any data inside
    we asume that the owner of the token is the demo user.

    Ideally here we would decode the signed jwt to extract information about the token owner.
    Args:
        token (str, optional) 
        datetime_now
    """

    # Check that the token exists
    token_data = db["users"][settings.DEMO_USER_ID]["access_tokens"].get(token)
    if not token_data:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="invalid token"
        )

    # Validate the expiration date
    if datetime_now >= token_data.expires_at:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="token expired"
        )

    # Validate that the token that the user is using has available_calls quota
    if token_data.available_calls <= 0:
        raise HTTPException(
            status_code=401,
            detail="token expired"
        )

    # Update number of available calls for the token
    token_data.available_calls = token_data.available_calls - 1
    db["users"][settings.DEMO_USER_ID]["access_tokens"][token_data.id] = token_data

    return token_data

def get_current_user(token: str = Depends(get_token), token_data: TokenInDB = Depends(get_user_access_token)) -> str:
    """Returns the user_id from a token

    As this demo doesn't follow OAuth2, and the token doesn't have any data inside
    we asume that the owner of the token is the demo user.

    Ideally here we would decode the signed jwt to extract information about the token owner.
    Args:
        token (str, optional): 
    """
    return settings.DEMO_USER_ID

def generate_access_token(user_id: str) -> str:
    """Creates a new access token for the given user.

    Args:
        user_id (str): The user id to which the access token will be generated.

    Returns:
        token (str): Random access token (uuid4) created for the user, doesn't follow OAuth2 spec.
    """
    # Generate a new access token and save it in the database
    token_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    db["users"][user_id]["access_tokens"][token_id] = TokenInDB(
        id=token_id,
        expires_at=expires_at,
        available_calls=settings.ACCESS_TOKEN_EXPIRE_QUOTA
    )

    return token_id

# Required class to override the default 403 error into 401 as required in the doc spec
class CustomHTTPBearer(HTTPBase):
    def __init__(
        self,
        *,
        bearerFormat: Optional[str] = None,
        scheme_name: Optional[str] = None,
        auto_error: bool = True,
    ):
        self.model = HTTPBearerModel(bearerFormat=bearerFormat)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        authorization: str = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)