
from datetime import datetime, timedelta
from typing import Any, Union
from fastapi import APIRouter, Body, Form, Depends,Security, Header, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from api.schemas.user import User
from api.schemas.file import BaseFile, FileInDBBase, ShareUrlInDB, UserFiles, FileInDB, DownloadRecord, ShareUrl
from api.database import db
from api.config import settings
import os
from fastapi.security import HTTPAuthorizationCredentials
from api.auth.deps import get_current_user, get_user_access_token, CustomHTTPBearer
import uuid
from shutil import copyfileobj
from functools import reduce

router = APIRouter()
security = CustomHTTPBearer()

def update_current_quota(user_id: str):
    # Filter for valid (recent) downloads
    valid_downloads = [download for download in db["users"][user_id]["last_downloads"] if lambda element: element.timestamp >=
                       datetime.now() - timedelta(minutes=settings.DOWNLOAD_QUOTA_MINUTES)]
    db["users"][user_id]["last_downloads"] = valid_downloads

    # Calculate currente allowance
    download_traffic_quota = settings.DOWNLOAD_QUOTA_TRAFFIC - \
        sum([download.size for download in valid_downloads])

    db["users"][user_id]["quotas"]["by_download_traffic"] = download_traffic_quota
    return download_traffic_quota


def add_file_to_db(user_id: str, file: FileInDB):
    # Validate that the current limit of files is less that the demo limit
    if len(db["users"][user_id]["files"]) == settings.USER_MAX_FILES:
        # Remove first file if the quota of files is maxed out
        os.remove(db["users"][user_id]["files"][0].route)
        del db["users"][user_id]["files"][0]
    db["users"][user_id]["files"].append(file)


@router.get("/me", response_model=UserFiles)
async def get_user_files(
    token: HTTPAuthorizationCredentials = Security(security),
    user_id: User = Depends(get_current_user)
):
    """
    Returns all files on the user space.
    """
    return UserFiles(user=user_id, files=[BaseFile(**dict(file_data)) for file_data in db["users"][user_id]["files"]])


@router.post("/me", response_model=BaseFile)
def upload_user_file(
    user_id: User = Depends(get_current_user),
    file: UploadFile = File(...),
    token: HTTPAuthorizationCredentials = Security(security),
):
    """
    Receives a file and stores in the user space, file is overwritten if exists.
    """
    # Verify if the file already exists for that user
    file_name = file.filename

    file_found = False
    file_found_idx = None
    for idx, file_data in enumerate(db["users"][user_id]["files"]):
        if file_data.name == file_name:
            file_found = file_data
            file_found_idx = idx
            break
    
    # If the file is found (check by filename), overwrite the existing file
    if file_found:
        # Delete the existing file
        os.remove(file_found.route)
        
        with open(file_found.route, "wb") as buffer:
            copyfileobj(file.file, buffer)

        # Update file size and media_type
        file_size = os.path.getsize(file_found.route)
        db["users"][user_id]["files"][file_found_idx].size = file_size
        db["users"][user_id]["files"][file_found_idx].media_type = file.content_type
        return BaseFile(name=file_name, url=file_found.url)
        
    # Generate file metadata
    file_id = str(uuid.uuid4())[:8]
    file_url = f"/f/{file_id}"
    file_route = f"./files/{user_id}/{file_id}"

    # For security reasons, we don't use the input filename in filesystem
    if not os.path.exists(os.path.dirname(file_route)):
        try:
            os.makedirs(os.path.dirname(file_route))
        except OSError: # Guard against race condition
            raise HTTPException(status_code=500)

    with open(file_route, "wb") as buffer:
        copyfileobj(file.file, buffer)

    # To measure the size of the files, we first save them and then get the size.
    # We could use a different approach, like chunking and adding up each chunk
    # But as the demo doc says, "File upload could be simple, no need to handle file chunks,
    # resumed uploads or improved upload tricks"
    file_size = os.path.getsize(file_route)

    add_file_to_db(user_id, FileInDB(
        name=file_name,
        url=file_url,
        route=file_route,
        id=file_id,
        media_type=file.content_type,
        size=file_size
    ))
    return BaseFile(name=file_name, url=file_url)


@router.get("/f/{file_id}")
def download_user_file(
    file_id: str,
    user_id: User = Depends(get_current_user),
    token: HTTPAuthorizationCredentials = Security(security),
):
    """
    Downloads a file from the user.
    """
    # Find the user file
    file_found = False
    for file_data in db["users"][user_id]["files"]:
        if file_data.id == file_id:
            file_found = file_data
            break

    if not file_found:
        raise HTTPException(status_code=404, detail="Not found")

    # As described in the doc spec, the first download that surpases the quota limit, is accepted.
    # For that reasom, we check the last quota, to determine if we need to update it.
    # Lazy approach, reducing the number of times that we update current quota from 2 to less that 2 per request
    if not db["users"][user_id]["quotas"]["by_download_traffic"] > 0:
        update_current_quota(user_id)

    # If we keep being limited by the quota, return an error
    if not db["users"][user_id]["quotas"]["by_download_traffic"] > 0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Add a record to the last downloads and update the user quota
    db["users"][user_id]["last_downloads"].append(
        DownloadRecord(timestamp=datetime.now(), size=file_found.size, file_id=file_found.id))
    update_current_quota(user_id)

    return FileResponse(path=file_found.route, filename=file_found.name, media_type=file_found.media_type)

@router.get("/f/{file_id}/share", response_model=ShareUrl)
def generate_user_file_share_url(
    file_id: str,
    user_id: User = Depends(get_current_user),
    token: HTTPAuthorizationCredentials = Security(security),
):
    """
    Generates a shareable url to download a file from the user.
    """
    # Find the user file
    file_found = False
    for file_data in db["users"][user_id]["files"]:
        if file_data.id == file_id:
            file_found = file_data
            break

    if not file_found:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Generate a new shareable link
    share_id= str(uuid.uuid4())[:6]
    share_url = f"/s/{share_id}"

    db["share_links"][share_id] = ShareUrlInDB(
        share_url = share_url,
        id = share_id,
        file = FileInDBBase(**dict(file_found)),
        owner = user_id
    )

    return ShareUrl(share_url=share_url)

@router.get("/s/{share_id}")
def download_share_url_file(
    share_id: str
):
    """
    Downloads a file from the a sharing url.
    """

    # Find the requested share_id data
    share_link_data = db["share_links"].get(share_id)
    if not share_link_data:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if the share link has been used
    if not share_link_data.valid:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Mark the share link as used
    share_link_data.valid = False
    db["share_links"][share_id] = share_link_data

    # Return the file
    return FileResponse(path=share_link_data.file.route, filename=share_link_data.file.name, media_type=share_link_data.file.media_type)