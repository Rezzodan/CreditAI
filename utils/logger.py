"""
Модуль логирования
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "credit_ai", log_file: str = None) -> logging.Logger:
    """
    Настраивает логгер
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов (опционально)
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый handler (если указан)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Глобальный логгер
logger = setup_logger()



