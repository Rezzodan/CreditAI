"""
Репозиторий для работы с базой данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import json

from database.models import (
    Base, CreditReport, ExtractedData, CreditAccount,
    CreditInquiry, ReportDispute, GeneratedDocument,
    ProcessingStats, ProcessingLog
)
from config.settings import settings


class DatabaseRepository:
    """Репозиторий для CRUD операций"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=settings.DEBUG)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Инициализирует базу данных (создаёт таблицы)"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Возвращает сессию БД"""
        return self.SessionLocal()
    
    # ========== CreditReport методы ==========
    
    def create_report(self, filename: str, file_size: int, 
                     bitrix_deal_id: Optional[int] = None) -> CreditReport:
        """Создаёт новую запись об отчёте"""
        session = self.get_session()
        try:
            report = CreditReport(
                original_filename=filename,
                file_size=file_size,
                bitrix_deal_id=bitrix_deal_id,
                processing_status='pending',
                processing_start=datetime.utcnow()
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def update_report(self, report_id: str, **kwargs) -> Optional[CreditReport]:
        """Обновляет отчёт"""
        session = self.get_session()
        try:
            report = session.query(CreditReport).filter(CreditReport.id == report_id).first()
            if report:
                for key, value in kwargs.items():
                    setattr(report, key, value)
                session.commit()
                session.refresh(report)
            return report
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_report(self, report_id: str) -> Optional[CreditReport]:
        """Получает отчёт по ID"""
        session = self.get_session()
        try:
            return session.query(CreditReport).filter(CreditReport.id == report_id).first()
        finally:
            session.close()
    
    def get_reports_by_deal(self, deal_id: int) -> List[CreditReport]:
        """Получает все отчёты по ID сделки"""
        session = self.get_session()
        try:
            return session.query(CreditReport).filter(
                CreditReport.bitrix_deal_id == deal_id
            ).order_by(CreditReport.upload_date.desc()).all()
        finally:
            session.close()
    
    # ========== ExtractedData методы ==========
    
    def save_extracted_data(self, report_id: str, json_data: Dict) -> ExtractedData:
        """Сохраняет извлечённые данные"""
        session = self.get_session()
        try:
            subject = json_data.get('subject', {})
            summary = json_data.get('summary', {})
            
            # Парсим дату рождения
            birth_date = None
            if 'birth_date' in subject and subject['birth_date'].get('value'):
                try:
                    birth_date = datetime.strptime(
                        subject['birth_date']['value'], 
                        '%Y-%m-%d'
                    ).date()
                except:
                    pass
            
            extracted = ExtractedData(
                report_id=report_id,
                client_name=subject.get('full_name', {}).get('value'),
                birth_date=birth_date,
                passport_series=subject.get('passport', {}).get('series'),
                passport_number=subject.get('passport', {}).get('number'),
                total_debt=summary.get('total_debt'),
                active_accounts=summary.get('active_accounts'),
                max_delinquency_days=summary.get('max_delinquency_days'),
                credit_score=summary.get('credit_score'),
                json_data=json_data
            )
            session.add(extracted)
            session.commit()
            session.refresh(extracted)
            return extracted
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ========== CreditAccount методы ==========
    
    def save_credit_accounts(self, report_id: str, accounts: List[Dict]) -> List[CreditAccount]:
        """Сохраняет кредитные счета"""
        session = self.get_session()
        try:
            saved_accounts = []
            for account_data in accounts:
                dates = account_data.get('dates', {})
                amounts = account_data.get('amounts', {})
                status = account_data.get('status', {})
                creditor = account_data.get('creditor', {})
                
                # Парсим даты
                open_date = None
                close_date = None
                if dates.get('open'):
                    try:
                        open_date = datetime.strptime(dates['open'], '%Y-%m-%d').date()
                    except:
                        pass
                if dates.get('close'):
                    try:
                        close_date = datetime.strptime(dates['close'], '%Y-%m-%d').date()
                    except:
                        pass
                
                account = CreditAccount(
                    report_id=report_id,
                    creditor_name=creditor.get('name'),
                    product_type=account_data.get('product_type'),
                    account_number=account_data.get('account_number'),
                    open_date=open_date,
                    close_date=close_date,
                    credit_limit=amounts.get('limit'),
                    current_balance=amounts.get('current_balance'),
                    status=status.get('general'),
                    delinquency_days=status.get('delinquency_days'),
                    monthly_payment=amounts.get('monthly_payment'),
                    currency=amounts.get('currency', 'RUB')
                )
                session.add(account)
                saved_accounts.append(account)
            
            session.commit()
            for account in saved_accounts:
                session.refresh(account)
            return saved_accounts
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ========== GeneratedDocument методы ==========
    
    def save_document(self, report_id: str, document_type: str, 
                    filename: str, file_path: str, file_size: int) -> GeneratedDocument:
        """Сохраняет информацию о сгенерированном документе"""
        session = self.get_session()
        try:
            document = GeneratedDocument(
                report_id=report_id,
                document_type=document_type,
                filename=filename,
                file_path=file_path,
                file_size=file_size
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            return document
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ========== ProcessingLog методы ==========
    
    def add_log(self, report_id: Optional[str], log_level: str, 
               module: str, message: str, details: Optional[Dict] = None):
        """Добавляет лог"""
        session = self.get_session()
        try:
            log = ProcessingLog(
                report_id=report_id,
                log_level=log_level,
                module=module,
                message=message,
                details=details
            )
            session.add(log)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ========== Статистика ==========
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Возвращает статистику обработки"""
        session = self.get_session()
        try:
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Получаем базовую статистику
            stats = session.query(
                CreditReport.bki_type,
                func.count(CreditReport.id).label('total'),
                func.avg(CreditReport.confidence_score).label('avg_confidence')
            ).filter(
                CreditReport.processing_status == 'completed',
                CreditReport.upload_date >= cutoff_date
            ).group_by(CreditReport.bki_type).all()
            
            # Вычисляем среднее время обработки отдельно (для совместимости с SQLite)
            result = []
            for stat in stats:
                # Получаем все отчёты этого типа БКИ
                reports = session.query(CreditReport).filter(
                    CreditReport.bki_type == stat.bki_type,
                    CreditReport.processing_status == 'completed',
                    CreditReport.upload_date >= cutoff_date,
                    CreditReport.processing_start.isnot(None),
                    CreditReport.processing_end.isnot(None)
                ).all()
                
                # Вычисляем среднее время
                avg_time = 0.0
                if reports:
                    times = []
                    for report in reports:
                        if report.processing_start and report.processing_end:
                            delta = report.processing_end - report.processing_start
                            times.append(delta.total_seconds())
                    if times:
                        avg_time = sum(times) / len(times)
                
                result.append({
                    'bki_type': stat.bki_type,
                    'total': stat.total,
                    'avg_confidence': float(stat.avg_confidence or 0),
                    'avg_time_seconds': avg_time
                })
            
            return {'by_bki': result}
        finally:
            session.close()

