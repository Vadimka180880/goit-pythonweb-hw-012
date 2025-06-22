import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.src.config.config import settings
from typing import Optional
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# Ініціалізація Cloudinary
cloudinary.config(
    cloud_name=settings.cloud_name,
    api_key=settings.cloud_api_key,
    api_secret=settings.cloud_api_secret,
    secure=True
)

async def upload_avatar(file: UploadFile, user_email: str) -> str:
    """
    Завантажує аватар на Cloudinary з обробкою помилок та перевірками.
    
    Args:
        file: Файл аватара (UploadFile)
        user_email: Email користувача для унікального імені файла
        
    Returns:
        URL завантаженого аватара
        
    Raises:
        HTTPException: У разі помилки завантаження
    """
    try:
        # Читаємо вміст файлу
        contents = await file.read()
        
        # Перевірка, чи файл не порожній
        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Файл порожній"
            )
        
        # Створюємо BytesIO з вмістом файлу
        file_bytes = BytesIO(contents)
        
        # Генеруємо унікальне public_id
        public_id = f"avatars/{user_email.replace('@', '_at_').replace('.', '_dot_')}"
        
        # Завантаження на Cloudinary
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
            allowed_formats=["jpg", "png", "jpeg"],
            format="jpg"  # Конвертуємо всі зображення в JPG для уніфікації
        )
        
        if not result.get('secure_url'):
            raise HTTPException(
                status_code=500,
                detail="Не вдалося отримати URL аватара"
            )
            
        return result['secure_url']
    
    except cloudinary.exceptions.Error as e:
        logger.error(f"Cloudinary error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Помилка Cloudinary: {str(e)}"
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Внутрішня помилка сервера при завантаженні аватара"
        )