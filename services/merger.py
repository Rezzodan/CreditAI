"""
Объединение данных от разных БКИ
"""
from typing import List, Dict, Any
from database.models import CreditReport, ExtractedData, CreditAccount


def merge_bki_reports(reports: List[CreditReport]) -> Dict[str, Any]:
    """
    Объединяет данные от нескольких БКИ в один сводный результат
    
    Args:
        reports: Список отчётов от разных БКИ для одного клиента
        
    Returns:
        Словарь со сводными данными
    """
    if not reports:
        raise ValueError("Нет отчётов для объединения")
    
    merged_data = {
        "client_name": None,
        "client_id": reports[0].client_id,
        "bitrix_deal_id": reports[0].bitrix_deal_id,
        "bki_data": {},  # Данные по каждому БКИ отдельно
        "all_credits": [],  # Все кредиты со всех БКИ
        "summary": {
            "total_reports": len(reports),
            "bki_types": [],
            "avg_credit_score": 0,
            "total_debt": 0,
            "total_active_accounts": 0,
            "max_delinquency_days": 0,
            "has_overdue": False,
            "credit_scores": []
        }
    }
    
    # Собираем данные от каждого БКИ
    for report in reports:
        if not report.extracted_data or len(report.extracted_data) == 0:
            continue
            
        bki_type = report.bki_type or "Неизвестный БКИ"
        extracted = report.extracted_data[0]
        
        # Имя клиента берём из первого доступного отчёта
        if not merged_data["client_name"] and extracted.client_name:
            merged_data["client_name"] = extracted.client_name
        
        # Данные от конкретного БКИ
        merged_data["bki_data"][bki_type] = {
            "credit_score": extracted.credit_score or 0,
            "total_debt": extracted.total_debt or 0,
            "active_accounts": extracted.active_accounts or 0,
            "max_delinquency": extracted.max_delinquency_days or 0,
            "report_id": report.id,
            "upload_date": report.upload_date.isoformat() if report.upload_date else None
        }
        
        # Добавляем тип БКИ в список
        merged_data["summary"]["bki_types"].append(bki_type)
        
        # Добавляем кредиты от этого БКИ
        if report.credit_accounts:
            for account in report.credit_accounts:
                merged_data["all_credits"].append({
                    "bki_source": bki_type,
                    "creditor": account.creditor_name,
                    "product_type": account.product_type,
                    "balance": account.current_balance or 0,
                    "limit": account.credit_limit or 0,
                    "status": account.status,
                    "delinquency_days": account.delinquency_days or 0
                })
        
        # Суммируем показатели
        merged_data["summary"]["total_debt"] += extracted.total_debt or 0
        merged_data["summary"]["total_active_accounts"] += extracted.active_accounts or 0
        
        # Максимальная просрочка
        if extracted.max_delinquency_days and extracted.max_delinquency_days > merged_data["summary"]["max_delinquency_days"]:
            merged_data["summary"]["max_delinquency_days"] = extracted.max_delinquency_days
        
        # Собираем рейтинги для усреднения
        if extracted.credit_score:
            merged_data["summary"]["credit_scores"].append(extracted.credit_score)
    
    # Вычисляем средний кредитный рейтинг
    if merged_data["summary"]["credit_scores"]:
        merged_data["summary"]["avg_credit_score"] = sum(merged_data["summary"]["credit_scores"]) / len(merged_data["summary"]["credit_scores"])
    
    # Есть ли просрочки
    merged_data["summary"]["has_overdue"] = merged_data["summary"]["max_delinquency_days"] > 0
    
    return merged_data


def decide_merged_tariff(merged_data: Dict[str, Any]) -> str:
    """
    Определяет рекомендуемый тариф на основе сводных данных
    
    Args:
        merged_data: Сводные данные от merge_bki_reports
        
    Returns:
        "Premium" или "Optimum"
    """
    summary = merged_data["summary"]
    
    # Критерии для Premium:
    # 1. Средний кредитный рейтинг >= 700
    # 2. Максимальная просрочка <= 5 дней
    # 3. Общий долг < 2 000 000
    
    avg_score = summary["avg_credit_score"]
    max_delay = summary["max_delinquency_days"]
    total_debt = summary["total_debt"]
    
    # Premium - если клиент очень надёжный
    if avg_score >= 700 and max_delay <= 5 and total_debt < 2_000_000:
        return "Premium"
    
    # Optimum - если есть проблемы
    return "Optimum"


def generate_tariff_explanation(merged_data: Dict[str, Any], tariff: str) -> str:
    """
    Генерирует текстовое объяснение выбора тарифа
    
    Args:
        merged_data: Сводные данные
        tariff: Рекомендованный тариф
        
    Returns:
        Текст объяснения
    """
    summary = merged_data["summary"]
    
    if tariff == "Premium":
        return f"""
Клиент демонстрирует высокую платёжную дисциплину и может претендовать на наилучшие условия.

Обоснование:
• Высокий средний кредитный рейтинг: {summary['avg_credit_score']:.0f} баллов
• Данные подтверждены {summary['total_reports']} БКИ: {', '.join(summary['bki_types'])}
• Просрочки: {"минимальные ({} дней)".format(summary['max_delinquency_days']) if summary['max_delinquency_days'] > 0 else "отсутствуют"}
• Общая долговая нагрузка: {summary['total_debt']:,.0f} руб
• Активных кредитных продуктов: {summary['total_active_accounts']}

Клиент надёжный и может обслуживать кредит на лучших условиях.
        """.strip()
    else:
        reasons = []
        if summary['avg_credit_score'] < 700:
            reasons.append(f"• Средний кредитный рейтинг ниже порога: {summary['avg_credit_score']:.0f} баллов (норма: 700+)")
        if summary['max_delinquency_days'] > 5:
            reasons.append(f"• Имеются просрочки: {summary['max_delinquency_days']} дней")
        if summary['total_debt'] >= 2_000_000:
            reasons.append(f"• Высокая долговая нагрузка: {summary['total_debt']:,.0f} руб")
        
        reasons_text = "\n".join(reasons) if reasons else "• Требуется дополнительный анализ кредитной истории"
        
        return f"""
Рекомендуется тариф Optimum с повышенными гарантиями.

Обоснование:
{reasons_text}

Данные проверены в {summary['total_reports']} БКИ: {', '.join(summary['bki_types'])}
Активных кредитных продуктов: {summary['total_active_accounts']}

Клиенту требуются условия с учётом текущей кредитной нагрузки.
        """.strip()

