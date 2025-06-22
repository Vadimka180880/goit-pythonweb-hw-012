from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    sync_database_url: str
    async_database_url: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email
    mail_server: str
    mail_port: int
    mail_username: str
    mail_password: str
    mail_from: str
    mail_starttls: bool
    mail_ssl_tls: bool

    # Cloudinary
    cloud_name: str
    cloud_api_key: str
    cloud_api_secret: str

    # Redis
    redis_url: str

    # CORS
    allowed_origins: str = "*"

    # Frontend URL
    frontend_url: str = ""

    mail_test_mode: bool = False
    mail_test_recipient: str = "test@example.com"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    class Config:
        env_file = ".env"  
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()