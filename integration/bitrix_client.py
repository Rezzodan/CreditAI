"""
Клиент для работы с Битрикс24 API
"""
import requests
from typing import Dict, Optional, List
from pathlib import Path
from config.settings import settings


class BitrixClient:
    """Клиент для интеграции с Битрикс24"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.BITRIX_WEBHOOK_URL
        
        if not self.webhook_url:
            raise ValueError("BITRIX_WEBHOOK_URL не указан в настройках")
    
    def _call_api(self, method: str, params: Dict = None) -> Dict:
        """
        Вызывает метод Битрикс24 API
        
        Args:
            method: Название метода API
            params: Параметры запроса
            
        Returns:
            Ответ API
        """
        url = f"{self.webhook_url}/{method}"
        params = params or {}
        
        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при вызове Битрикс24 API: {str(e)}")
    
    def upload_document(self, deal_id: int, file_path: str, filename: str) -> Dict:
        """
        Загружает документ в сделку
        
        Args:
            deal_id: ID сделки
            file_path: Путь к файлу
            filename: Имя файла
            
        Returns:
            Результат загрузки
        """
        # Сначала получаем URL для загрузки
        upload_result = self._call_api('disk.folder.uploadfile', {
            'id': 0,  # Корневая папка
            'data': {
                'NAME': filename
            },
            'fileContent': self._read_file_base64(file_path)
        })
        
        if 'result' not in upload_result:
            raise Exception("Не удалось загрузить файл")
        
        file_id = upload_result['result']['ID']
        
        # Прикрепляем файл к сделке
        attach_result = self._call_api('crm.deal.update', {
            'id': deal_id,
            'fields': {
                'UF_CRM_FILES': [file_id]  # Поле для файлов (может отличаться)
            }
        })
        
        return attach_result
    
    def _read_file_base64(self, file_path: str) -> str:
        """Читает файл и возвращает base64"""
        import base64
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def update_deal_fields(self, deal_id: int, fields: Dict) -> Dict:
        """
        Обновляет поля сделки
        
        Args:
            deal_id: ID сделки
            fields: Словарь полей для обновления
            
        Returns:
            Результат обновления
        """
        return self._call_api('crm.deal.update', {
            'id': deal_id,
            'fields': fields
        })
    
    def get_deal(self, deal_id: int) -> Dict:
        """
        Получает данные сделки
        
        Args:
            deal_id: ID сделки
            
        Returns:
            Данные сделки
        """
        return self._call_api('crm.deal.get', {
            'id': deal_id
        })
    
    def add_comment(self, deal_id: int, comment: str) -> Dict:
        """
        Добавляет комментарий к сделке
        
        Args:
            deal_id: ID сделки
            comment: Текст комментария
            
        Returns:
            Результат добавления
        """
        return self._call_api('crm.timeline.comment.add', {
            'fields': {
                'ENTITY_ID': deal_id,
                'ENTITY_TYPE': 'deal',
                'COMMENT': comment
            }
        })



