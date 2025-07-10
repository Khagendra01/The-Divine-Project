import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://minimind:minimind123@localhost:5432/minimind"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Application
    APP_NAME: str = "MiniMind"
    DEBUG: bool = True
    
    # Agent Settings
    MAX_TASK_DURATION: int = 300  # 5 minutes
    MAX_SUBTASKS: int = 10
    
    class Config:
        env_file = ".env"


settings = Settings() 