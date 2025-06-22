"""
Service functions for uploading files to Cloudinary.
"""

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.src.config.config import settings
from typing import Optional
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# Initialize Cloudinary
cloudinary.config(
    cloud_name=settings.cloud_name,
    api_key=settings.cloud_api_key,
    api_secret=settings.cloud_api_secret,
    secure=True
)

async def upload_avatar(file: UploadFile, user_email: str) -> str:
    """
    Upload an avatar image to Cloudinary with error handling and validation.

    Args:
        file (UploadFile): The avatar file to upload.
        user_email (str): The user's email for unique file naming.

    Returns:
        str: URL of the uploaded avatar.

    Raises:
        HTTPException: If upload fails or file is empty.
    """
    try:
        # Read file contents
        contents = await file.read()
        
        # Check if file is not empty
        if not contents:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Create BytesIO from file contents
        file_bytes = BytesIO(contents)
        
        # Generate unique public_id
        public_id = f"avatars/{user_email.replace('@', '_at_').replace('.', '_dot_')}"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            folder="avatars",
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 250, "height": 250, "crop": "fill"},
                {"quality": "auto:good"}
            ],
        )
        
        return result["secure_url"]
    
    except Exception as e:
        logger.error(f"Cloudinary upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload avatar to Cloudinary")