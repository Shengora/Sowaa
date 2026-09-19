from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    bot_token: str = "test_token"
    admin_ids: str = "123456789"
    encryption_key: str = Fernet.generate_key().decode()
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite+aiosqlite:///:memory:"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def parsed_admin_ids(self) -> List[int]:
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

config = Settings()