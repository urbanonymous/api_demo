
from typing import List
from datetime import datetime
from pydantic import BaseModel
from api.schemas.user import User

class BaseFile(BaseModel):
    name: str
    url: str

class FileInDBBase(BaseFile):
    route: str
    id: str
    media_type: str

class FileInDB(FileInDBBase):
    size: int

class UserFiles(BaseModel):
    user: str
    files: List[BaseFile]


class DownloadRecord(BaseModel):
    timestamp: datetime
    size: int
    file_id: str

class ShareUrl(BaseModel):
    share_url: str

class ShareUrlInDB(ShareUrl):
    id: str
    valid: bool = True
    file: FileInDBBase
    owner: str
