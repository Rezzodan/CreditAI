"""
API эндпоинты
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
from pathlib import Path
import shutil
from datetime import datetime

from config.settings import settings
from core.pdf_processor import PDFProcessor
from core.ai_processor import AIProcessor
from core.data_validator import DataValidator
from services.document_generator import DocumentGenerator
from database.repository import DatabaseRepository

router = APIRouter()

# Инициализация компонентов
pdf_processor = PDFProcessor()
ai_processor = AIProcessor()
document_generator = DocumentGenerator(settings.OUTPUT_FOLDER)
db_repo = DatabaseRepository()

# Создаём папки если их нет
Path(settings.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)


class ProcessRequest(BaseModel):
    """Модель запроса на обработку"""
    deal_id: Optional[int] = None
    callback_url: Optional[str] = None


class ProcessResponse(BaseModel):
    """Модель ответа на запрос обработки"""
    task_id: str
    status: str
    message: str


@router.post("/process", response_model=ProcessResponse)
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    deal_id: Optional[int] = Form(None),
    callback_url: Optional[str] = Form(None)
):
    """
    Запуск обработки PDF файла
    
    Args:
        file: PDF файл
        deal_id: ID сделки в Битрикс24
        callback_url: URL для уведомления о завершении
        
    Returns:
        task_id для отслеживания статуса
    """
    # Проверка размера файла
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой. Максимальный размер: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Проверка типа файла
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Поддерживаются только PDF файлы")
    
    # Сохранение файла
    task_id = str(uuid.uuid4())
    file_path = Path(settings.UPLOAD_FOLDER) / f"{task_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}")
    
    # Создание записи в БД
    try:
        report = db_repo.create_report(
            filename=file.filename,
            file_size=file.size or 0,
            bitrix_deal_id=deal_id
        )
        task_id = report.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании записи: {str(e)}")
    
    # Запуск обработки в фоне (можно использовать Celery)
    # Для простоты используем BackgroundTasks
    background_tasks.add_task(
        process_pdf_sync,
        task_id=task_id,
        file_path=str(file_path),
        deal_id=deal_id,
        callback_url=callback_url
    )
    
    return ProcessResponse(
        task_id=task_id,
        status="pending",
        message="Обработка запущена"
    )


async def process_pdf_sync(
    task_id: str,
    file_path: str,
    deal_id: Optional[int],
    callback_url: Optional[str]
):
    """Синхронная обработка PDF (вызывается в фоне)"""
    try:
        # Обновляем статус
        db_repo.update_report(task_id, processing_status='processing')
        db_repo.add_log(task_id, 'INFO', 'api', 'Начало обработки PDF')
        
        # Обработка PDF
        pdf_data = pdf_processor.process_pdf(file_path)
        bki_type = pdf_data['bki_detection']['bki_type']
        
        db_repo.update_report(
            task_id,
            bki_type=bki_type,
            processing_start=datetime.utcnow()
        )
        db_repo.add_log(task_id, 'INFO', 'pdf_processor', f'Тип БКИ определён: {bki_type}')
        
        # Извлечение данных через ИИ
        extracted_data = ai_processor.extract_structured_data(
            pdf_data['full_text'],
            bki_type
        )
        
        # Добавляем метаданные
        extracted_data['metadata'] = extracted_data.get('metadata', {})
        extracted_data['metadata']['processing_id'] = task_id
        extracted_data['metadata']['processed_at'] = datetime.utcnow().isoformat()
        extracted_data['metadata']['source_filename'] = Path(file_path).name
        extracted_data['metadata']['bki_type'] = bki_type
        
        # Валидация
        validator = DataValidator()
        validation_result = validator.validate_extracted_data(extracted_data)
        
        if not validation_result['is_valid']:
            db_repo.add_log(
                task_id,
                'WARNING',
                'validator',
                f"Обнаружены ошибки валидации: {', '.join(validation_result['errors'])}"
            )
        
        # Сохранение в БД
        db_repo.save_extracted_data(task_id, extracted_data)
        
        if 'accounts' in extracted_data:
            db_repo.save_credit_accounts(task_id, extracted_data['accounts'])
        
        # Детекция ошибок
        errors_data = ai_processor.detect_errors(extracted_data)
        errors = errors_data.get('errors', [])
        
        # Генерация рекомендаций
        recommendations = ai_processor.generate_recommendations(extracted_data)
        extracted_data['recommendations'] = recommendations
        
        # Генерация документов
        analysis_report_path = document_generator.generate_analysis_report(
            extracted_data,
            task_id
        )
        
        db_repo.save_document(
            task_id,
            'analysis_report',
            Path(analysis_report_path).name,
            analysis_report_path,
            Path(analysis_report_path).stat().st_size
        )
        
        # Генерация письма в БКИ если есть ошибки
        if errors and errors_data.get('requires_bki_letter', False):
            subject = extracted_data.get('subject', {})
            client_data = {
                'full_name': subject.get('full_name', {}).get('value', ''),
                'birth_date': subject.get('birth_date', {}).get('value', ''),
                'passport': subject.get('passport', {})
            }
            
            letter_path = document_generator.generate_bki_letter(
                bki_type,
                client_data,
                errors,
                task_id
            )
            
            db_repo.save_document(
                task_id,
                'bki_letter',
                Path(letter_path).name,
                letter_path,
                Path(letter_path).stat().st_size
            )
        
        # Обновление статуса
        confidence = extracted_data['metadata'].get('confidence_overall', 0.0)
        db_repo.update_report(
            task_id,
            processing_status='completed',
            processing_end=datetime.utcnow(),
            confidence_score=confidence
        )
        
        db_repo.add_log(task_id, 'INFO', 'api', 'Обработка завершена успешно')
        
        # Отправка в Битрикс24 (если указан deal_id)
        if deal_id:
            try:
                from integration.bitrix_client import BitrixClient
                bitrix = BitrixClient(settings.BITRIX_WEBHOOK_URL)
                bitrix.upload_document(deal_id, analysis_report_path, Path(analysis_report_path).name)
            except Exception as e:
                db_repo.add_log(task_id, 'ERROR', 'bitrix', f"Ошибка отправки в Битрикс: {str(e)}")
        
        # Callback (если указан)
        if callback_url:
            try:
                import requests
                requests.post(callback_url, json={
                    'task_id': task_id,
                    'status': 'completed',
                    'report_path': analysis_report_path
                }, timeout=10)
            except Exception as e:
                db_repo.add_log(task_id, 'WARNING', 'api', f"Ошибка callback: {str(e)}")
    
    except Exception as e:
        # Обработка ошибок
        db_repo.update_report(
            task_id,
            processing_status='failed',
            processing_end=datetime.utcnow(),
            error_message=str(e)
        )
        db_repo.add_log(task_id, 'ERROR', 'api', f"Ошибка обработки: {str(e)}")


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """Получить статус обработки"""
    report = db_repo.get_report(task_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    
    # Получаем документы
    documents = []
    if report.documents:
        documents = [
            {
                'id': doc.id,
                'type': doc.document_type,
                'filename': doc.filename,
                'download_url': f"/api/download/{doc.id}"
            }
            for doc in report.documents
        ]
    
    return {
        'task_id': task_id,
        'status': report.processing_status,
        'bki_type': report.bki_type,
        'confidence_score': report.confidence_score,
        'upload_date': report.upload_date.isoformat() if report.upload_date else None,
        'processing_start': report.processing_start.isoformat() if report.processing_start else None,
        'processing_end': report.processing_end.isoformat() if report.processing_end else None,
        'error_message': report.error_message,
        'documents': documents
    }


@router.get("/download/{document_id}")
async def download_document(document_id: str):
    """Скачать сгенерированный документ"""
    from database.models import GeneratedDocument
    from sqlalchemy.orm import Session
    
    session = db_repo.get_session()
    try:
        document = session.query(GeneratedDocument).filter(
            GeneratedDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        if not Path(document.file_path).exists():
            raise HTTPException(status_code=404, detail="Файл не найден на диске")
        
        # Увеличиваем счётчик скачиваний
        document.download_count += 1
        session.commit()
        
        return FileResponse(
            document.file_path,
            filename=document.filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    finally:
        session.close()


@router.get("/statistics")
async def get_statistics(days: int = 30):
    """Получить статистику обработки"""
    stats = db_repo.get_statistics(days)
    return stats


@router.get("/reports")
async def get_reports(deal_id: Optional[int] = None, limit: int = 50):
    """Получить список отчётов"""
    if deal_id:
        reports = db_repo.get_reports_by_deal(deal_id)
    else:
        # Получаем последние отчёты
        from database.models import CreditReport
        from sqlalchemy.orm import Session
        
        session = db_repo.get_session()
        try:
            reports = session.query(CreditReport).order_by(
                CreditReport.upload_date.desc()
            ).limit(limit).all()
        finally:
            session.close()
    
    return [
        {
            'id': report.id,
            'filename': report.original_filename,
            'bki_type': report.bki_type,
            'status': report.processing_status,
            'upload_date': report.upload_date.isoformat() if report.upload_date else None,
            'confidence_score': report.confidence_score
        }
        for report in reports
    ]

