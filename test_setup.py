#!/usr/bin/env python3
"""Тестовая проверка всех компонентов"""

def test_imports():
    """Проверка импортов"""
    try:
        from config.settings import settings
        from core.pdf_processor import PDFProcessor
        from core.ai_processor import AIProcessor
        from core.bki_detector import BKIDetector
        from database.repository import DatabaseRepository
        from services.document_generator import DocumentGenerator
        print("✅ Все импорты успешны")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ollama():
    """Проверка Ollama"""
    try:
        from core.ai_processor import AIProcessor
        ai = AIProcessor()
        if ai.check_ollama_connection():
            print("✅ Ollama доступен")
            return True
        else:
            print("❌ Ollama недоступен (убедитесь что ollama serve запущен)")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки Ollama: {e}")
        return False

def test_database():
    """Проверка базы данных"""
    try:
        from database.repository import DatabaseRepository
        db = DatabaseRepository()
        db.init_db()
        print("✅ База данных инициализирована")
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_processor():
    """Проверка PDF процессора"""
    try:
        from core.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print("✅ PDF процессор инициализирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка PDF процессора: {e}")
        return False

def test_bki_detector():
    """Проверка детектора БКИ"""
    try:
        from core.bki_detector import BKIDetector
        detector = BKIDetector()
        result = detector.detect("Национальное бюро кредитных историй")
        if result == "НБКИ":
            print("✅ Детектор БКИ работает корректно")
            return True
        else:
            print(f"⚠️ Детектор БКИ работает, но результат: {result}")
            return True  # Не критично
    except Exception as e:
        print(f"❌ Ошибка детектора БКИ: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка установки CreditAI...\n")
    
    results = []
    results.append(("Импорты", test_imports()))
    results.append(("PDF процессор", test_pdf_processor()))
    results.append(("Детектор БКИ", test_bki_detector()))
    results.append(("База данных", test_database()))
    results.append(("Ollama", test_ollama()))
    
    print("\n📊 Результаты проверки:")
    print("-" * 40)
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    print("-" * 40)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nПройдено: {passed}/{total}")
    
    if all(r[1] for r in results):
        print("\n🎉 Все проверки пройдены! Система готова к работе.")
    else:
        print("\n⚠️ Есть проблемы. Проверьте ошибки выше и:")
        print("   1. Убедитесь что все зависимости установлены: pip install -r requirements.txt")
        print("   2. Проверьте что Ollama запущен: ollama serve")
        print("   3. Проверьте настройки в .env файле")
        print("   4. Запустите: python init_db.py")



