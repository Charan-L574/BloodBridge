from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import computed_field
from urllib.parse import quote_plus


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MySQL Database Configuration
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "bloodbridge"
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Construct MySQL connection URL with URL-encoded password"""
        password = quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Optional external API keys (mock if not provided)
    OPENROUTESERVICE_API_KEY: Optional[str] = None
    GEOAPIFY_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()
