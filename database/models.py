"""
SQLAlchemy модели для базы данных
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Float, 
    Text, Boolean, Date, ForeignKey, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# UUID поддержка для разных БД
try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    USE_PG_UUID = True
except ImportError:
    USE_PG_UUID = False

Base = declarative_base()


class CreditReport(Base):
    """Таблица: Обработка отчётов"""
    __tablename__ = 'credit_reports'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bitrix_deal_id = Column(Integer, nullable=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    bki_type = Column(String(50))
    upload_date = Column(DateTime, default=datetime.utcnow)
    processing_start = Column(DateTime)
    processing_end = Column(DateTime)
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    confidence_score = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    extracted_data = relationship("ExtractedData", back_populates="report", cascade="all, delete-orphan")
    credit_accounts = relationship("CreditAccount", back_populates="report", cascade="all, delete-orphan")
    credit_inquiries = relationship("CreditInquiry", back_populates="report", cascade="all, delete-orphan")
    disputes = relationship("ReportDispute", back_populates="report", cascade="all, delete-orphan")
    documents = relationship("GeneratedDocument", back_populates="report", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="report", cascade="all, delete-orphan")


class ExtractedData(Base):
    """Таблица: Извлечённые данные"""
    __tablename__ = 'extracted_data'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('credit_reports.id', ondelete='CASCADE'), nullable=False)
    client_name = Column(String(255))
    birth_date = Column(Date)
    passport_series = Column(String(10))
    passport_number = Column(String(10))
    total_debt = Column(Float)
    active_accounts = Column(Integer)
    max_delinquency_days = Column(Integer)
    credit_score = Column(Integer)
    json_data = Column(JSON)  # Полные структурированные данные
    extraction_date = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    report = relationship("CreditReport", back_populates="extracted_data")


class CreditAccount(Base):
    """Таблица: Кредиты/займы"""
    __tablename__ = 'credit_accounts'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('credit_reports.id', ondelete='CASCADE'), nullable=False)
    creditor_name = Column(String(255))
    product_type = Column(String(100))
    account_number = Column(String(100))
    open_date = Column(Date)
    close_date = Column(Date)
    credit_limit = Column(Float)
    current_balance = Column(Float)
    status = Column(String(50))
    delinquency_days = Column(Integer)
    monthly_payment = Column(Float)
    currency = Column(String(3), default='RUB')
    
    # Связи
    report = relationship("CreditReport", back_populates="credit_accounts")


class CreditInquiry(Base):
    """Таблица: Запросы в БКИ"""
    __tablename__ = 'credit_inquiries'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('credit_reports.id', ondelete='CASCADE'), nullable=False)
    inquiry_date = Column(Date)
    creditor_name = Column(String(255))
    inquiry_type = Column(String(100))
    purpose = Column(String(255))
    
    # Связи
    report = relationship("CreditReport", back_populates="credit_inquiries")


class ReportDispute(Base):
    """Таблица: Ошибки/диспуты"""
    __tablename__ = 'report_disputes'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('credit_reports.id', ondelete='CASCADE'), nullable=False)
    dispute_type = Column(String(50))  # incorrect_data, duplicate, outdated
    field_name = Column(String(100))
    incorrect_value = Column(Text)
    correct_value = Column(Text)
    evidence_page = Column(Integer)
    evidence_text = Column(Text)
    status = Column(String(20), default='pending')  # pending, in_progress, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Связи
    report = relationship("CreditReport", back_populates="disputes")


class GeneratedDocument(Base):
    """Таблица: Сгенерированные документы"""
    __tablename__ = 'generated_documents'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('credit_reports.id', ondelete='CASCADE'), nullable=False)
    document_type = Column(String(50))  # analysis_report, bki_letter, summary
    filename = Column(String(255))
    file_path = Column(Text)
    file_size = Column(Integer)
    generation_date = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=0)
    
    # Связи
    report = relationship("CreditReport", back_populates="documents")


class ProcessingStats(Base):
    """Таблица: Статистика обработки"""
    __tablename__ = 'processing_stats'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    bki_type = Column(String(50), nullable=False)
    total_reports = Column(Integer, default=0)
    successful_reports = Column(Integer, default=0)
    failed_reports = Column(Integer, default=0)
    avg_processing_time = Column(Float)
    avg_confidence = Column(Float)
    common_errors = Column(JSON)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('date', 'bki_type', name='_date_bki_uc'),
    )


class SystemUser(Base):
    """Таблица: Пользователи системы"""
    __tablename__ = 'system_users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bitrix_user_id = Column(Integer)
    username = Column(String(100))
    email = Column(String(255))
    role = Column(String(50), default='user')  # admin, manager, user
    permissions = Column(JSON)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessingLog(Base):
    """Таблица: Логи обработки"""
    __tablename__ = 'processing_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey('credit_reports.id', ondelete='SET NULL'), nullable=True)
    log_level = Column(String(20))  # INFO, WARNING, ERROR
    module = Column(String(100))  # pdf_parser, ai_processor, etc.
    message = Column(Text)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    report = relationship("CreditReport", back_populates="logs")

