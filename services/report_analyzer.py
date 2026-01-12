"""
Модуль анализа кредитных отчётов по ТЗ
Формирует структурированный анализ с рекомендациями тарифов
"""

from typing import Dict, List, Optional
from datetime import datetime


class ReportAnalyzer:
    """Анализатор кредитных отчётов по техническому заданию"""
    
    def __init__(self):
        self.tariff_recommendations = {
            'premium': 'Премиум',
            'optimum': 'Оптимум',
            'analysis': 'Детальный анализ портрета клиента'
        }
    
    def analyze_nbki_report(self, extracted_data: Dict) -> Dict:
        """
        Анализ отчёта НБКИ по ТЗ
        
        Args:
            extracted_data: Извлечённые данные из PDF
            
        Returns:
            Структурированный анализ с рекомендациями
        """
        analysis = {
            'bki_type': 'НБКИ',
            'report_date': extracted_data.get('report_date', datetime.now().strftime('%d.%m.%Y')),
            'client_name': extracted_data.get('client_name', 'ФИО клиента'),
            'sections': {}
        }
        
        # Раздел 1: Кредитный рейтинг
        analysis['sections']['rating'] = {
            'title': 'Текущий кредитный рейтинг',
            'value': extracted_data.get('credit_score', 0),
            'has_image': True  # Нужно будет извлечь картинку из PDF
        }
        
        # Раздел 2: Текущие кредиты
        active_credits = self._extract_active_credits_nbki(extracted_data)
        analysis['sections']['active_credits'] = {
            'title': 'Текущие кредиты',
            'has_credits': len(active_credits) > 0,
            'credits': active_credits
        }
        
        # Раздел 3: Закрытые кредиты
        closed_credits = self._extract_closed_credits_nbki(extracted_data)
        analysis['sections']['closed_credits'] = {
            'title': 'Закрытые кредиты',
            'has_credits': len(closed_credits) > 0,
            'credits': closed_credits
        }
        
        # Раздел 4: Кредитная нагрузка
        analysis['sections']['credit_load'] = {
            'title': 'Кредитная нагрузка',
            'current_debt': extracted_data.get('total_debt', 0),
            'overdue_debt': extracted_data.get('overdue_debt', 0),
            'monthly_payment': extracted_data.get('monthly_payment', 0)
        }
        
        # Раздел 5: Рекомендации
        analysis['sections']['recommendations'] = self._generate_recommendations(
            rating=analysis['sections']['rating']['value'],
            overdue_debt=analysis['sections']['credit_load']['overdue_debt'],
            active_credits=active_credits,
            closed_credits=closed_credits,
            current_debt=analysis['sections']['credit_load']['current_debt']
        )
        
        return analysis
    
    def analyze_okb_report(self, extracted_data: Dict) -> Dict:
        """Анализ отчёта ОКБ по ТЗ"""
        analysis = {
            'bki_type': 'ОКБ',
            'report_date': extracted_data.get('report_date', datetime.now().strftime('%d.%m.%Y')),
            'client_name': extracted_data.get('client_name', 'ФИО клиента'),
            'sections': {}
        }
        
        # Раздел 1: Кредитный рейтинг
        analysis['sections']['rating'] = {
            'title': 'Текущий кредитный рейтинг',
            'value': extracted_data.get('credit_score', 0),
            'has_image': True
        }
        
        # Раздел 2: Признак банкротства
        analysis['sections']['bankruptcy'] = {
            'title': 'Признак банкротства',
            'has_bankruptcy': extracted_data.get('has_bankruptcy', False)
        }
        
        # Раздел 3-6: Аналогично НБКИ
        active_credits = self._extract_active_credits_okb(extracted_data)
        closed_credits = self._extract_closed_credits_okb(extracted_data)
        
        analysis['sections']['active_credits'] = {
            'title': 'Текущие кредиты',
            'has_credits': len(active_credits) > 0,
            'credits': active_credits
        }
        
        analysis['sections']['closed_credits'] = {
            'title': 'Закрытые кредиты',
            'has_credits': len(closed_credits) > 0,
            'credits': closed_credits
        }
        
        analysis['sections']['credit_load'] = {
            'title': 'Кредитная нагрузка',
            'current_debt': extracted_data.get('total_debt', 0),
            'overdue_debt': extracted_data.get('overdue_debt', 0)
        }
        
        analysis['sections']['recommendations'] = self._generate_recommendations(
            rating=analysis['sections']['rating']['value'],
            overdue_debt=analysis['sections']['credit_load']['overdue_debt'],
            active_credits=active_credits,
            closed_credits=closed_credits,
            current_debt=analysis['sections']['credit_load']['current_debt']
        )
        
        return analysis
    
    def analyze_scoring_bureau_report(self, extracted_data: Dict) -> Dict:
        """Анализ отчёта СкорингБюро по ТЗ"""
        # Определяем форму отчёта (старая/новая)
        is_new_form = extracted_data.get('form_type') == 'new'
        
        analysis = {
            'bki_type': 'СкорингБюро' + (' (новая форма)' if is_new_form else ''),
            'report_date': extracted_data.get('report_date', datetime.now().strftime('%d.%m.%Y')),
            'client_name': extracted_data.get('client_name', 'ФИО клиента'),
            'sections': {}
        }
        
        # Структура аналогична ОКБ
        analysis['sections']['rating'] = {
            'title': 'Текущий кредитный рейтинг',
            'value': extracted_data.get('credit_score', 0),
            'has_image': False  # В новой форме нет картинки
        }
        
        analysis['sections']['bankruptcy'] = {
            'title': 'Признак банкротства',
            'has_bankruptcy': extracted_data.get('has_bankruptcy', False)
        }
        
        if is_new_form:
            active_credits = self._extract_active_credits_scoring_new(extracted_data)
            closed_credits = self._extract_closed_credits_scoring_new(extracted_data)
        else:
            active_credits = self._extract_active_credits_scoring_old(extracted_data)
            closed_credits = self._extract_closed_credits_scoring_old(extracted_data)
        
        analysis['sections']['active_credits'] = {
            'title': 'Текущие кредиты',
            'has_credits': len(active_credits) > 0,
            'credits': active_credits
        }
        
        analysis['sections']['closed_credits'] = {
            'title': 'Закрытые кредиты',
            'has_credits': len(closed_credits) > 0,
            'credits': closed_credits
        }
        
        analysis['sections']['credit_load'] = {
            'title': 'Кредитная нагрузка',
            'current_debt': extracted_data.get('total_debt', 0),
            'overdue_debt': extracted_data.get('overdue_debt', 0)
        }
        
        analysis['sections']['recommendations'] = self._generate_recommendations(
            rating=analysis['sections']['rating']['value'],
            overdue_debt=analysis['sections']['credit_load']['overdue_debt'],
            active_credits=active_credits,
            closed_credits=closed_credits,
            current_debt=analysis['sections']['credit_load']['current_debt']
        )
        
        return analysis
    
    def _extract_active_credits_nbki(self, data: Dict) -> List[Dict]:
        """Извлечение активных кредитов из НБКИ"""
        credits = []
        
        # Ищем в извлечённых данных кредиты без даты закрытия
        accounts = data.get('credit_accounts', [])
        
        for account in accounts:
            # Проверяем что кредит активный
            if not account.get('close_date') and account.get('status') != 'закрыт':
                credit = {
                    'creditor': account.get('creditor_name', 'Неизвестно'),
                    'type': account.get('product_type', 'Неизвестно'),
                    'amount': account.get('credit_limit', 0),
                    'open_date': account.get('open_date', 'Неизвестно'),
                    'payment': self._calculate_payment(account),
                    'balance': account.get('current_balance', 0),
                    'has_overdue': account.get('delinquency_days', 0) > 0,
                    'max_overdue_days': account.get('max_delinquency_days', 0),
                    'current_overdue': account.get('delinquency_days', 0) > 0,
                    'current_overdue_days': account.get('delinquency_days', 0),
                    'current_overdue_amount': account.get('overdue_amount', 0)
                }
                credits.append(credit)
        
        return credits
    
    def _extract_closed_credits_nbki(self, data: Dict) -> List[Dict]:
        """Извлечение закрытых кредитов из НБКИ"""
        credits = []
        
        accounts = data.get('credit_accounts', [])
        
        for account in accounts:
            # Проверяем что кредит закрыт
            if account.get('close_date') or account.get('status') == 'закрыт':
                credit = {
                    'creditor': account.get('creditor_name', 'Неизвестно'),
                    'type': account.get('product_type', 'Неизвестно'),
                    'amount': account.get('credit_limit', 0),
                    'open_date': account.get('open_date', 'Неизвестно'),
                    'has_overdue': account.get('had_overdue', False),
                    'max_overdue_days': account.get('max_delinquency_days', 0)
                }
                credits.append(credit)
        
        return credits
    
    def _extract_active_credits_okb(self, data: Dict) -> List[Dict]:
        """Извлечение активных кредитов из ОКБ"""
        # Аналогично НБКИ, но с учётом специфики ОКБ
        return self._extract_active_credits_nbki(data)
    
    def _extract_closed_credits_okb(self, data: Dict) -> List[Dict]:
        """Извлечение закрытых кредитов из ОКБ"""
        return self._extract_closed_credits_nbki(data)
    
    def _extract_active_credits_scoring_old(self, data: Dict) -> List[Dict]:
        """Извлечение активных кредитов из СкорингБюро (старая форма)"""
        return self._extract_active_credits_nbki(data)
    
    def _extract_closed_credits_scoring_old(self, data: Dict) -> List[Dict]:
        """Извлечение закрытых кредитов из СкорингБюро (старая форма)"""
        return self._extract_closed_credits_nbki(data)
    
    def _extract_active_credits_scoring_new(self, data: Dict) -> List[Dict]:
        """Извлечение активных кредитов из СкорингБюро (новая форма)"""
        return self._extract_active_credits_nbki(data)
    
    def _extract_closed_credits_scoring_new(self, data: Dict) -> List[Dict]:
        """Извлечение закрытых кредитов из СкорингБюро (новая форма)"""
        return self._extract_closed_credits_nbki(data)
    
    def _calculate_payment(self, account: Dict) -> float:
        """Расчёт ежемесячного платежа"""
        # Для кредитных карт - 1/10 от лимита
        if 'карта' in account.get('product_type', '').lower():
            return account.get('credit_limit', 0) / 10
        
        # Иначе берём из данных
        return account.get('monthly_payment', 0)
    
    def _generate_recommendations(self, rating: float, overdue_debt: float, 
                                 active_credits: List[Dict], closed_credits: List[Dict],
                                 current_debt: float) -> Dict:
        """
        Генерация рекомендаций по ТЗ
        
        Логика:
        1. Если есть просроченная задолженность -> Премиум
        2. Если рейтинг <700 -> Оптимум
        3. Если были просрочки -> Оптимум
        4. Если нет кредитов -> Детальный анализ
        5. Дополнительные предупреждения о микрозаймах, количестве кредитов
        """
        recommendations = []
        recommended_tariff = None
        
        # Проверка 1: Просроченная задолженность
        if overdue_debt > 0:
            recommendations.append({
                'type': 'critical',
                'text': 'Имеется текущая просрочка, требующая ее закрытия. Любая просроченная задолженность снижает показатель кредитного рейтинга. Для увеличения кредитного рейтинга рекомендуем воспользоваться тарифным планом из линейки «Премиум»'
            })
            recommended_tariff = 'premium'
        
        # Проверка 2: Низкий рейтинг
        elif rating > 0 and rating < 700:
            recommendations.append({
                'type': 'warning',
                'text': 'Имеется низкий кредитный рейтинг. Для увеличения кредитного рейтинга рекомендуем воспользоваться тарифом «Оптимум»'
            })
            recommended_tariff = 'optimum'
        
        # Проверка 3: Были просрочки (но нет текущих)
        elif any(credit.get('has_overdue') for credit in active_credits + closed_credits):
            recommendations.append({
                'type': 'warning',
                'text': 'Допускается возникновение просрочек, которые негативно отражаются на показателе кредитного рейтинга. Рекомендуем воспользоваться тарифом «Оптимум».'
            })
            recommended_tariff = 'optimum'
        
        # Проверка 4: Нет кредитов
        elif len(active_credits) == 0 and len(closed_credits) == 0:
            recommendations.append({
                'type': 'info',
                'text': 'На основании предоставленных отчетов кредитная история не сформирована. Рекомендуем осуществить детальный анализ портрета клиента.'
            })
            recommended_tariff = 'analysis'
        
        # Проверка 5: Микрозаймы
        has_microloan = any('микро' in credit.get('type', '').lower() 
                           for credit in active_credits)
        if has_microloan:
            recommendations.append({
                'type': 'warning',
                'text': 'Вы пользуетесь микрозаймами. Заявки на микрозайм говорят банкам о низкой финансовой грамотности заемщика, либо о финансовых трудностях, что в свою очередь ухудшает Вашу кредитную историю.'
            })
        
        # Проверка 6: Много кредитов
        if len(active_credits) >= 5:
            recommendations.append({
                'type': 'warning',
                'text': 'Банки негативно относятся к большому количеству активных договоров. Получение нового кредитного продукта при пяти и более активных договорах затруднено. Рекомендуем закрыть кредиты с наименьшей текущей задолженностью, либо (при наличии) кредитные карты, которыми вы не пользуетесь, чтобы количество активных договоров было не более 4. Чем меньше активных договоров, тем проще одобрить новый кредитный продукт.'
            })
        
        # Проверка 7: Высокая задолженность
        if current_debt > 1_000_000:
            recommendations.append({
                'type': 'warning',
                'text': 'У клиента высокая кредитная нагрузка. Рекомендуем снизить нагрузку.'
            })
        
        # Если ничего не найдено
        if not recommendations:
            recommendations.append({
                'type': 'success',
                'text': 'Критичные отклонения в кредитном отчете отсутствуют. Рекомендуем осуществить детальный анализ портрета клиента.'
            })
            recommended_tariff = 'analysis'
        
        return {
            'items': recommendations,
            'recommended_tariff': recommended_tariff,
            'tariff_name': self.tariff_recommendations.get(recommended_tariff, 'Не определён')
        }



