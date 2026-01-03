"""
Модуль валидации извлечённых данных
"""
from typing import Dict, List, Optional
from datetime import datetime
import re


class DataValidator:
    """Валидатор для проверки корректности извлечённых данных"""
    
    @staticmethod
    def validate_date(date_str: Optional[str]) -> bool:
        """Проверяет корректность даты в формате YYYY-MM-DD"""
        if not date_str:
            return False
        
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_passport(series: Optional[str], number: Optional[str]) -> bool:
        """Проверяет формат паспорта (серия 4 цифры, номер 6 цифр)"""
        if not series or not number:
            return False
        
        series_pattern = r'^\d{4}$'
        number_pattern = r'^\d{6}$'
        
        return bool(re.match(series_pattern, series) and re.match(number_pattern, number))
    
    @staticmethod
    def validate_amount(amount: any) -> bool:
        """Проверяет, что сумма - это число"""
        if amount is None:
            return True  # None допустим
        
        try:
            float(amount)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_account_dates(open_date: Optional[str], close_date: Optional[str]) -> List[str]:
        """
        Проверяет корректность дат счёта
        
        Returns:
            Список ошибок (пустой если всё ок)
        """
        errors = []
        
        if open_date and not DataValidator.validate_date(open_date):
            errors.append(f"Некорректная дата открытия: {open_date}")
        
        if close_date and not DataValidator.validate_date(close_date):
            errors.append(f"Некорректная дата закрытия: {close_date}")
        
        if open_date and close_date and DataValidator.validate_date(open_date) and DataValidator.validate_date(close_date):
            open_dt = datetime.strptime(open_date, '%Y-%m-%d')
            close_dt = datetime.strptime(close_date, '%Y-%m-%d')
            
            if close_dt < open_dt:
                errors.append(f"Дата закрытия ({close_date}) раньше даты открытия ({open_date})")
        
        return errors
    
    @staticmethod
    def validate_account_amounts(limit: Optional[float], balance: Optional[float]) -> List[str]:
        """
        Проверяет корректность сумм счёта
        
        Returns:
            Список ошибок
        """
        errors = []
        
        if limit is not None and not DataValidator.validate_amount(limit):
            errors.append(f"Некорректный лимит: {limit}")
        
        if balance is not None and not DataValidator.validate_amount(balance):
            errors.append(f"Некорректный остаток: {balance}")
        
        if limit is not None and balance is not None:
            limit_val = float(limit)
            balance_val = float(balance)
            
            # Остаток не должен быть больше лимита (если лимит положительный)
            if limit_val > 0 and balance_val > limit_val:
                errors.append(f"Остаток ({balance_val}) превышает лимит ({limit_val})")
        
        return errors
    
    @staticmethod
    def validate_extracted_data(data: Dict) -> Dict:
        """
        Валидирует полный набор извлечённых данных
        
        Returns:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        # Проверка метаданных
        if 'metadata' not in data:
            errors.append("Отсутствует секция metadata")
        else:
            metadata = data['metadata']
            if 'bki_type' not in metadata:
                warnings.append("Не указан тип БКИ")
        
        # Проверка данных субъекта
        if 'subject' not in data:
            errors.append("Отсутствует секция subject")
        else:
            subject = data['subject']
            
            # Проверка ФИО
            if 'full_name' in subject:
                full_name = subject['full_name']
                if 'value' not in full_name or not full_name['value']:
                    warnings.append("Не указано ФИО")
            
            # Проверка даты рождения
            if 'birth_date' in subject:
                birth_date = subject['birth_date']
                if 'value' in birth_date:
                    if not DataValidator.validate_date(birth_date['value']):
                        errors.append(f"Некорректная дата рождения: {birth_date['value']}")
            
            # Проверка паспорта
            if 'passport' in subject:
                passport = subject['passport']
                series = passport.get('series')
                number = passport.get('number')
                if series or number:
                    if not DataValidator.validate_passport(series, number):
                        errors.append(f"Некорректный формат паспорта: {series} {number}")
        
        # Проверка счетов
        if 'accounts' in data:
            for idx, account in enumerate(data['accounts']):
                # Проверка дат
                if 'dates' in account:
                    dates = account['dates']
                    date_errors = DataValidator.validate_account_dates(
                        dates.get('open'),
                        dates.get('close')
                    )
                    errors.extend([f"Счёт {idx}: {err}" for err in date_errors])
                
                # Проверка сумм
                if 'amounts' in account:
                    amounts = account['amounts']
                    amount_errors = DataValidator.validate_account_amounts(
                        amounts.get('limit'),
                        amounts.get('current_balance')
                    )
                    errors.extend([f"Счёт {idx}: {err}" for err in amount_errors])
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }



