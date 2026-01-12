"""
FastAPI приложение
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
from pathlib import Path

from config.settings import settings
from api.endpoints import router

app = FastAPI(
    title=settings.APP_NAME,
    description="Система автоматической обработки кредитных отчётов",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    from core.ai_processor import AIProcessor
    
    ai_processor = AIProcessor()
    ollama_available = ai_processor.check_ollama_connection()
    
    return {
        "status": "healthy" if ollama_available else "degraded",
        "ollama": "available" if ollama_available else "unavailable"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)








