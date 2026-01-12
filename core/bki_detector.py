"""
Модуль детекции типа БКИ по содержимому PDF
"""
import re
from typing import Dict, List, Optional


class BKIDetector:
    """Определяет тип БКИ по содержимому PDF"""
    
    def __init__(self):
        self.bki_patterns = {
            'НБКИ': [
                r'Национальное бюро кредитных историй',
                r'ООО\s*["\']?НБКИ["\']?',
                r'www\.nbki\.ru',
                r'НБКИ',
                r'Национальное\s+бюро'
            ],
            'ОКБ': [
                r'Объединенное кредитное бюро',
                r'ООО\s*["\']?ОКБ["\']?',
                r'www\.bki-okb\.ru',
                r'ОКБ',
                r'Объединенное\s+кредитное'
            ],
            'Скоринг Бюро': [
                r'Скоринг Бюро',
                r'ООО\s*["\']?Скоринг Бюро["\']?',
                r'sb\.bki\.ru',
                r'Скоринг\s+Бюро'
            ],
            'Эквифакс': [
                r'Equifax',
                r'Эквифакс',
                r'www\.equifax\.ru',
                r'Equifax\s+Credit'
            ],
            'КБ Киви': [
                r'КБ Киви',
                r'Киви БКИ',
                r'kbc\.k\.ru',
                r'КБ\s+Киви'
            ],
            'Русский Стандарт БКИ': [
                r'Русский Стандарт БКИ',
                r'РС БКИ',
                r'rsbki\.ru',
                r'Русский\s+Стандарт\s+БКИ'
            ]
        }
    
    def detect(self, pdf_text: str) -> str:
        """
        Определяет тип БКИ по содержимому PDF
        
        Args:
            pdf_text: Текст извлечённый из PDF
            
        Returns:
            Название БКИ или 'Неизвестно'
        """
        if not pdf_text:
            return 'Неизвестно'
        
        # Нормализуем текст
        text = pdf_text.replace('\n', ' ').replace('\r', ' ')
        
        detected_type = 'Неизвестно'
        max_matches = 0
        match_scores = {}
        
        for bki_name, patterns in self.bki_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
            
            match_scores[bki_name] = matches
            
            if matches > max_matches:
                max_matches = matches
                detected_type = bki_name
        
        # Если нет совпадений, возвращаем неизвестно
        if max_matches == 0:
            return 'Неизвестно'
        
        return detected_type
    
    def detect_with_confidence(self, pdf_text: str) -> Dict[str, any]:
        """
        Определяет тип БКИ с уровнем уверенности
        
        Returns:
            {
                'bki_type': str,
                'confidence': float,
                'matches': dict
            }
        """
        if not pdf_text:
            return {
                'bki_type': 'Неизвестно',
                'confidence': 0.0,
                'matches': {}
            }
        
        text = pdf_text.replace('\n', ' ').replace('\r', ' ')
        
        match_scores = {}
        total_patterns = 0
        
        for bki_name, patterns in self.bki_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
            match_scores[bki_name] = matches
            total_patterns += len(patterns)
        
        if not match_scores or max(match_scores.values()) == 0:
            return {
                'bki_type': 'Неизвестно',
                'confidence': 0.0,
                'matches': match_scores
            }
        
        detected_type = max(match_scores, key=match_scores.values)
        max_matches = match_scores[detected_type]
        
        # Уверенность = количество совпадений / общее количество паттернов для этого БКИ
        confidence = min(max_matches / len(self.bki_patterns[detected_type]), 1.0)
        
        return {
            'bki_type': detected_type,
            'confidence': confidence,
            'matches': match_scores
        }








