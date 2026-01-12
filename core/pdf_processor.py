"""
Модуль обработки PDF файлов
"""
import pdfplumber
from typing import Dict, List, Optional
import json
from pathlib import Path
from core.bki_detector import BKIDetector


class PDFProcessor:
    """Обработчик PDF файлов для извлечения текста и таблиц"""
    
    def __init__(self):
        self.bki_detector = BKIDetector()
    
    def extract_text_with_coordinates(self, pdf_path: str) -> List[Dict]:
        """
        Извлекает текст с координатами из PDF
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Список словарей с текстом и координатами по страницам
        """
        pages_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    words = page.extract_words()
                    
                    page_data = {
                        'page': page_num,
                        'text': page.extract_text() or '',
                        'words': [
                            {
                                'text': word.get('text', ''),
                                'x0': word.get('x0', 0),
                                'y0': word.get('y0', 0),
                                'x1': word.get('x1', 0),
                                'y1': word.get('y1', 0)
                            }
                            for word in words if isinstance(word, dict)
                        ],
                        'width': page.width,
                        'height': page.height
                    }
                    pages_data.append(page_data)
        
        except Exception as e:
            raise Exception(f"Ошибка при извлечении текста из PDF: {str(e)}")
        
        return pages_data
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Извлекает таблицы из PDF
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Список таблиц с метаданными
        """
        tables_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    
                    for table_num, table in enumerate(tables, start=1):
                        if table:  # Проверяем, что таблица не пустая
                            table_data = {
                                'page': page_num,
                                'table_number': table_num,
                                'data': table,
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0
                            }
                            tables_data.append(table_data)
        
        except Exception as e:
            # Если не удалось извлечь таблицы, возвращаем пустой список
            # Это не критичная ошибка
            pass
        
        return tables_data
    
    def extract_full_text(self, pdf_path: str) -> str:
        """
        Извлекает весь текст из PDF
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Полный текст документа
        """
        full_text = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
        
        except Exception as e:
            raise Exception(f"Ошибка при извлечении текста: {str(e)}")
        
        return '\n\n'.join(full_text)
    
    def detect_bki_type(self, pdf_path: str) -> str:
        """
        Определяет тип БКИ по содержимому PDF
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Название БКИ
        """
        text = self.extract_full_text(pdf_path)
        return self.bki_detector.detect(text)
    
    def detect_bki_type_with_confidence(self, pdf_path: str) -> Dict:
        """
        Определяет тип БКИ с уровнем уверенности
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Словарь с типом БКИ и уверенностью
        """
        text = self.extract_full_text(pdf_path)
        return self.bki_detector.detect_with_confidence(text)
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Полная обработка PDF: извлечение текста, таблиц и определение БКИ
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Словарь с результатами обработки
        """
        result = {
            'text_pages': self.extract_text_with_coordinates(pdf_path),
            'tables': self.extract_tables(pdf_path),
            'full_text': self.extract_full_text(pdf_path),
            'bki_detection': self.detect_bki_type_with_confidence(pdf_path)
        }
        
        return result






