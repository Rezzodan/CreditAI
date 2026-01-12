"""
Модуль работы с ИИ через Ollama
"""
import requests
import json
from typing import Dict, Optional, Any, List
from config.settings import settings
from config.prompts import (
    get_base_extraction_prompt,
    get_error_detection_prompt,
    get_recommendations_prompt,
    get_letter_generation_prompt,
    get_bki_specific_prompt
)


class AIProcessor:
    """Обработчик для работы с Ollama API"""
    
    def __init__(self, host: Optional[str] = None):
        self.host = host or settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.model_texts = settings.OLLAMA_MODEL_TEXTS
    
    def _call_ollama(self, prompt: str, model: Optional[str] = None, 
                     temperature: float = 0.1) -> str:
        """
        Вызывает Ollama API
        
        Args:
            prompt: Промпт для модели
            model: Модель для использования (по умолчанию self.model)
            temperature: Температура генерации
            
        Returns:
            Ответ модели
        """
        model = model or self.model
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при вызове Ollama API: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        Парсит JSON из ответа модели
        
        Args:
            response: Ответ модели
            
        Returns:
            Распарсенный JSON
        """
        # Пытаемся найти JSON в ответе
        response = response.strip()
        
        # Удаляем markdown код блоки если есть
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Пытаемся найти JSON в тексте
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            raise Exception(f"Не удалось распарсить JSON из ответа: {str(e)}")
    
    def extract_structured_data(self, pdf_text: str, bki_type: str) -> Dict:
        """
        Извлекает структурированные данные из текста PDF
        
        Args:
            pdf_text: Текст из PDF
            bki_type: Тип БКИ
            
        Returns:
            Структурированные данные в формате JSON
        """
        # Добавляем специфичные инструкции для БКИ
        bki_specific = get_bki_specific_prompt(bki_type)
        full_prompt = f"""{bki_specific}

{get_base_extraction_prompt(bki_type, pdf_text)}"""
        
        response = self._call_ollama(full_prompt, model=self.model)
        return self._parse_json_response(response)
    
    def detect_errors(self, json_data: Dict) -> Dict:
        """
        Обнаруживает ошибки в извлечённых данных
        
        Args:
            json_data: Извлечённые данные
            
        Returns:
            Словарь с найденными ошибками
        """
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        prompt = get_error_detection_prompt(json_str)
        
        response = self._call_ollama(prompt, model=self.model)
        return self._parse_json_response(response)
    
    def generate_recommendations(self, json_data: Dict) -> Dict:
        """
        Генерирует рекомендации на основе данных
        
        Args:
            json_data: Извлечённые данные
            
        Returns:
            Словарь с рекомендациями
        """
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        prompt = get_recommendations_prompt(json_str)
        
        response = self._call_ollama(prompt, model=self.model_texts, temperature=0.3)
        return self._parse_json_response(response)
    
    def generate_bki_letter(self, bki_type: str, errors: List[Dict], 
                           client_data: Dict) -> str:
        """
        Генерирует письмо в БКИ
        
        Args:
            bki_type: Тип БКИ
            errors: Список ошибок
            client_data: Данные клиента
            
        Returns:
            Текст письма
        """
        prompt = get_letter_generation_prompt(bki_type, errors, client_data)
        response = self._call_ollama(prompt, model=self.model_texts, temperature=0.4)
        
        # Очищаем ответ от markdown если есть
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            response = '\n'.join(lines[1:-1])
        
        return response.strip()
    
    def check_ollama_connection(self) -> bool:
        """
        Проверяет доступность Ollama
        
        Returns:
            True если Ollama доступен
        """
        try:
            url = f"{self.host}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False






