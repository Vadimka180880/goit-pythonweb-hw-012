from typing import Optional
from pydantic_settings import BaseSettings
import os

if os.environ.get("TEST_USE_SQLITE", "0") == "1":
    os.environ["ASYNC_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

class Settings(BaseSettings):
    # Database
    database_url: Optional[str] = None
    sync_database_url: Optional[str] = None
    async_database_url: Optional[str] = "sqlite+aiosqlite:///./test.db"

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

    @property
    def effective_async_database_url(self):
        # Use SQLite for local tests if TEST_USE_SQLITE=1 or if db host is unreachable
        if os.environ.get("TEST_USE_SQLITE", "0") == "1":
            return "sqlite+aiosqlite:///./test.db"
        # Use local Postgres if TEST_DB_URL is set
        if os.environ.get("TEST_DB_URL"):
            return os.environ["TEST_DB_URL"]
        # Default: use .env async_database_url
        if self.async_database_url:
            return self.async_database_url
        raise RuntimeError("No async database URL configured. Set TEST_USE_SQLITE=1 for local tests or provide ASYNC_DATABASE_URL in .env.")

    @property
    def effective_redis_url(self):
        if os.environ.get("TEST_USE_FAKE_REDIS", "0") == "1":
            return "redis://localhost:6379/0"
        if os.environ.get("TEST_REDIS_URL"):
            return os.environ["TEST_REDIS_URL"]
        return self.redis_url

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Patch async_database_url for test mode
        if os.environ.get("TEST_USE_SQLITE", "0") == "1":
            self.async_database_url = "sqlite+aiosqlite:///./test.db"

    class Config:
        env_file = ".env"  
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()