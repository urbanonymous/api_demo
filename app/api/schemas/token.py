from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    token: str

class TokenInDB(BaseModel):
    id: str
    expires_at: datetime
    available_calls: int
    expired: bool = False
