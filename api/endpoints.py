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
    client_id: Optional[str] = Form(None),
    callback_url: Optional[str] = Form(None)
):
    """
    Запуск обработки PDF файла
    
    Args:
        file: PDF файл
        deal_id: ID сделки в Битрикс24
        client_id: ID клиента (для группировки отчётов)
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
            bitrix_deal_id=deal_id,
            client_id=client_id
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
    
    # Получаем документы отдельным запросом (чтобы избежать DetachedInstanceError)
    documents = []
    try:
        docs = db_repo.get_documents_by_report(task_id)
        if docs:
            documents = [
                {
                    'id': doc.id,
                    'type': doc.document_type,
                    'filename': doc.filename,
                    'download_url': f"/api/download/{doc.id}"
                }
                for doc in docs
            ]
    except Exception:
        pass  # Если не удалось получить документы, просто пропускаем
    
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


@router.post("/merge-reports")
async def merge_reports(client_id: str):
    """
    Объединяет все отчёты одного клиента от разных БКИ в один сводный отчёт
    
    Args:
        client_id: ID клиента
        
    Returns:
        Информация о сводном отчёте и путь к документу
    """
    from services.merger import merge_bki_reports, decide_merged_tariff, generate_tariff_explanation
    from services.merged_report_generator import generate_merged_word_report
    import os
    
    # Получаем все отчёты клиента
    reports = db_repo.get_reports_by_client(client_id)
    
    if not reports:
        raise HTTPException(
            status_code=404,
            detail=f"Не найдено отчётов для клиента {client_id}"
        )
    
    if len(reports) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Для объединения нужно минимум 2 отчёта, найдено: {len(reports)}"
        )
    
    # Проверяем что все отчёты обработаны
    incomplete = [r for r in reports if r.processing_status != 'completed']
    if incomplete:
        raise HTTPException(
            status_code=400,
            detail=f"Не все отчёты обработаны. Ожидают завершения: {len(incomplete)}"
        )
    
    try:
        # Объединяем данные
        merged_data = merge_bki_reports(reports)
        
        # Определяем тариф
        final_tariff = decide_merged_tariff(merged_data)
        
        # Генерируем объяснение
        explanation = generate_tariff_explanation(merged_data, final_tariff)
        
        # Создаём Word документ
        doc_path = generate_merged_word_report(merged_data, final_tariff, explanation)
        
        # Получаем размер файла
        file_size = os.path.getsize(doc_path)
        
        # Сохраняем в БД
        merged_report = db_repo.create_merged_report(
            client_id=client_id,
            client_name=merged_data["client_name"],
            source_report_ids=[r.id for r in reports],
            bki_types=merged_data["summary"]["bki_types"],
            avg_credit_score=merged_data["summary"]["avg_credit_score"],
            total_debt=merged_data["summary"]["total_debt"],
            total_active_accounts=merged_data["summary"]["total_active_accounts"],
            max_delinquency_days=merged_data["summary"]["max_delinquency_days"],
            final_tariff=final_tariff,
            document_path=doc_path,
            file_size=file_size,
            bitrix_deal_id=reports[0].bitrix_deal_id if reports else None
        )
        
        return {
            "status": "success",
            "merged_report_id": merged_report.id,
            "client_id": client_id,
            "client_name": merged_data["client_name"],
            "reports_merged": len(reports),
            "bki_types": merged_data["summary"]["bki_types"],
            "summary": {
                "avg_credit_score": merged_data["summary"]["avg_credit_score"],
                "total_debt": merged_data["summary"]["total_debt"],
                "total_active_accounts": merged_data["summary"]["total_active_accounts"],
                "max_delinquency_days": merged_data["summary"]["max_delinquency_days"]
            },
            "final_tariff": final_tariff,
            "document_path": doc_path,
            "download_url": f"/download/{merged_report.id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при объединении отчётов: {str(e)}"
        )


@router.get("/client/{client_id}/reports")
async def get_client_reports(client_id: str):
    """
    Получает все отчёты клиента
    
    Args:
        client_id: ID клиента
        
    Returns:
        Список всех отчётов клиента
    """
    reports = db_repo.get_reports_by_client(client_id)
    
    return {
        "client_id": client_id,
        "total_reports": len(reports),
        "reports": [
            {
                "id": r.id,
                "bki_type": r.bki_type,
                "status": r.processing_status,
                "upload_date": r.upload_date.isoformat() if r.upload_date else None,
                "credit_score": r.extracted_data[0].credit_score if r.extracted_data and len(r.extracted_data) > 0 else None,
                "total_debt": r.extracted_data[0].total_debt if r.extracted_data and len(r.extracted_data) > 0 else None
            }
            for r in reports
        ]
    }

