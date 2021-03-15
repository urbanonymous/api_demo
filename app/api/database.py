""" Singleton dict as in memory db
Added the hardcoded demo user as we don't have any account creation endpoints
"""

from api.config import settings

db = {
    "users": {
        f"{settings.DEMO_USER_ID}": {
            "user_id": f"{settings.DEMO_USER_ID}",
            "access_tokens": {},
            "files": [],
            "quotas": {
                "by_download_traffic": settings.DOWNLOAD_QUOTA_TRAFFIC
            },
            "last_downloads": []
        },
    },
    "share_links":{}
}
