"""Avatar upload integration with Cloudinary."""

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from src.conf.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


class CloudinaryService:
    """Upload user avatars to Cloudinary and return a URL."""

    def upload_avatar(self, file: UploadFile, user_id: int) -> str:
        """Upload the incoming file and return the secure URL."""

        if not settings.cloudinary_cloud_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cloudinary is not configured')
        result = cloudinary.uploader.upload(file.file, folder='contacts_api', public_id=f'user_{user_id}_avatar', overwrite=True)
        return result['secure_url']


cloudinary_service = CloudinaryService()
