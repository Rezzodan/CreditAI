# Чеклист установки и проверки

## ✅ Проверка кода на ошибки

### 1. Синтаксические ошибки
```bash
# Проверка всех Python файлов
python -m py_compile config/*.py
python -m py_compile core/*.py
python -m py_compile database/*.py
python -m py_compile services/*.py
python -m py_compile api/*.py
python -m py_compile integration/*.py
python -m py_compile utils/*.py
python -m py_compile main.py
python -m py_compile init_db.py
```

### 2. Проверка импортов
```bash
# Создайте тестовый скрипт test_imports.py
python test_imports.py
```

### 3. Проверка зависимостей
```bash
# Установка зависимостей
pip install -r requirements.txt

# Проверка отсутствующих модулей
python -c "import fastapi, uvicorn, sqlalchemy, pdfplumber, docx, celery, redis, requests, pydantic; print('Все зависимости установлены')"
```

---

## 📋 Пошаговая установка (локально)

### Шаг 1: Подготовка окружения
- [ ] Python 3.10+ установлен (`python --version`)
- [ ] Виртуальное окружение создано
- [ ] Виртуальное окружение активировано
- [ ] pip обновлён до последней версии

### Шаг 2: Установка зависимостей
- [ ] `pip install -r requirements.txt` выполнен успешно
- [ ] Все зависимости установлены без ошибок

### Шаг 3: Установка Ollama
- [ ] Ollama скачан и установлен
- [ ] Ollama запущен (`ollama serve`)
- [ ] Модель `qwen2.5-coder:7b` загружена
- [ ] Модель `saiga3:8b` загружена
- [ ] Проверка: `ollama list` показывает обе модели

### Шаг 4: Настройка базы данных
- [ ] Файл `.env` создан из `env.example`
- [ ] `DATABASE_URL` настроен (SQLite для теста)
- [ ] `python init_db.py` выполнен успешно
- [ ] База данных создана (проверить наличие `credit_ai.db`)

### Шаг 5: Первый запуск
- [ ] `python main.py` запускается без ошибок
- [ ] Сервер отвечает на http://localhost:8000
- [ ] Документация доступна на http://localhost:8000/docs
- [ ] Health check работает: http://localhost:8000/health

### Шаг 6: Тестирование API
- [ ] POST `/api/process` принимает файл
- [ ] GET `/api/status/{task_id}` возвращает статус
- [ ] GET `/api/statistics` возвращает статистику
- [ ] GET `/api/reports` возвращает список отчётов

---

## 🐛 Известные проблемы и решения

### Проблема 1: Ошибка импорта UUID из postgresql
**Решение**: Исправлено в models.py - используется String для ID, что работает с SQLite и PostgreSQL

### Проблема 2: Ollama не отвечает
**Решение**: 
```bash
# Проверка
curl http://localhost:11434/api/tags

# Перезапуск
ollama serve
```

### Проблема 3: Ошибки при установке зависимостей
**Решение**:
```bash
# Для Windows может потребоваться:
pip install --upgrade pip setuptools wheel

# Для Linux может потребоваться:
sudo apt install python3-dev libpq-dev
```

### Проблема 4: Ошибки с pdfplumber
**Решение**:
```bash
# Установка системных зависимостей
# Ubuntu/Debian:
sudo apt install python3-tk

# Windows: обычно работает из коробки
```

### Проблема 5: Ошибки с camelot-py
**Решение**:
```bash
# Установка зависимостей
# Ubuntu/Debian:
sudo apt install ghostscript python3-tk

# Windows:
# Скачайте и установите Ghostscript с https://www.ghostscript.com/
```

---

## 🔍 Детальная проверка компонентов

### Проверка PDF процессора
```python
from core.pdf_processor import PDFProcessor
processor = PDFProcessor()
# Должно работать без ошибок
```

### Проверка детектора БКИ
```python
from core.bki_detector import BKIDetector
detector = BKIDetector()
result = detector.detect("НБКИ текст")
# Должен вернуть 'НБКИ'
```

### Проверка ИИ процессора
```python
from core.ai_processor import AIProcessor
ai = AIProcessor()
available = ai.check_ollama_connection()
# Должно вернуть True если Ollama работает
```

### Проверка базы данных
```python
from database.repository import DatabaseRepository
db = DatabaseRepository()
db.init_db()
# Должно создать таблицы без ошибок
```

### Проверка генератора документов
```python
from services.document_generator import DocumentGenerator
generator = DocumentGenerator()
# Должно работать без ошибок
```

---

## 📝 Тестовый скрипт для проверки

Создайте файл `test_setup.py`:

```python
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
            print("❌ Ollama недоступен")
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
        return False

if __name__ == "__main__":
    print("🔍 Проверка установки...\n")
    
    results = []
    results.append(("Импорты", test_imports()))
    results.append(("Ollama", test_ollama()))
    results.append(("База данных", test_database()))
    
    print("\n📊 Результаты:")
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    if all(r[1] for r in results):
        print("\n🎉 Все проверки пройдены!")
    else:
        print("\n⚠️ Есть проблемы, проверьте выше")
```

Запуск:
```bash
python test_setup.py
```

---

## 🚀 Готовность к продакшену

### Перед деплоем проверьте:

- [ ] Все тесты пройдены
- [ ] `.env` файл настроен для продакшена
- [ ] `SECRET_KEY` изменён на случайный
- [ ] `DEBUG=False` в настройках
- [ ] PostgreSQL настроен (не SQLite)
- [ ] Резервное копирование настроено
- [ ] Мониторинг настроен
- [ ] SSL сертификат установлен
- [ ] Firewall настроен
- [ ] Логирование настроено
- [ ] Документация обновлена

---

## 📞 Контакты для поддержки

При возникновении проблем:
1. Проверьте логи приложения
2. Проверьте этот чеклист
3. Проверьте DEPLOYMENT_GUIDE.md
4. Обратитесь к разработчикам с:
   - Описанием проблемы
   - Логами ошибок
   - Версией Python
   - Операционной системой



