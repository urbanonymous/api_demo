""" Settings singleton that gets autocompleted from env vars """
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "99files.com"
    PROJECT_DESCRIPTION: str = "Upload and download files using our API!"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    ACCESS_TOKEN_EXPIRE_QUOTA: int = 5

    USER_MAX_FILES: int = 99
    
    DEMO_USER_ID: str = "username"
    DEMO_USER_PASSWORD: str = "password"
    
    
    DOWNLOAD_QUOTA_TRAFFIC: int = 1024 ** 2 # 1 Megabyte in bytes
    DOWNLOAD_QUOTA_MINUTES: int = 5

    class Config:
        case_sensitive = True


settings = Settings()