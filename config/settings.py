import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Сервер
    APP_NAME: str = "CreditAI"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # База данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./credit_ai.db"  # Для MVP используем SQLite
    )
    
    # ИИ (Ollama)
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_MODEL_TEXTS: str = os.getenv("OLLAMA_MODEL_TEXTS", "saiga3:8b")
    
    # Битрикс24
    BITRIX_WEBHOOK_URL: str = os.getenv("BITRIX_WEBHOOK_URL", "")
    BITRIX_CLIENT_ID: str = os.getenv("BITRIX_CLIENT_ID", "")
    BITRIX_CLIENT_SECRET: str = os.getenv("BITRIX_CLIENT_SECRET", "")
    
    # Очередь задач
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    
    # Безопасность
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-in-production")
    API_KEY_HEADER: str = "X-API-Key"
    
    # Пути
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    OUTPUT_FOLDER: str = os.getenv("OUTPUT_FOLDER", "./output")
    TEMPLATES_FOLDER: str = os.getenv("TEMPLATES_FOLDER", "./templates")
    
    # Лимиты
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    PROCESSING_TIMEOUT: int = 300  # 5 минут
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()



