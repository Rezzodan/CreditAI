"""
Celery задачи для фоновой обработки
"""
from celery import Celery
from config.settings import settings

# Создание Celery приложения
celery_app = Celery(
    'credit_ai',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name='process_pdf_task')
def process_pdf_task(file_path: str, deal_id: int = None, callback_url: str = None):
    """
    Фоновая задача обработки PDF
    
    Args:
        file_path: Путь к PDF файлу
        deal_id: ID сделки в Битрикс24
        callback_url: URL для уведомления
        
    Returns:
        Результат обработки
    """
    # Импортируем здесь чтобы избежать циклических зависимостей
    from core.pdf_processor import PDFProcessor
    from core.ai_processor import AIProcessor
    from core.data_validator import DataValidator
    from services.document_generator import DocumentGenerator
    from database.repository import DatabaseRepository
    from datetime import datetime
    from pathlib import Path
    
    pdf_processor = PDFProcessor()
    ai_processor = AIProcessor()
    validator = DataValidator()
    document_generator = DocumentGenerator(settings.OUTPUT_FOLDER)
    db_repo = DatabaseRepository()
    
    # Логика обработки (аналогично process_pdf_sync из endpoints.py)
    # Можно вынести в отдельный сервис для переиспользования
    pass








