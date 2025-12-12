from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./blood_bank.db"
    
    # Optional external API keys (mock if not provided)
    OPENROUTESERVICE_API_KEY: Optional[str] = None
    GEOAPIFY_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()
