# CreditAI - Система автоматической обработки кредитных отчётов

Система для автоматической обработки PDF кредитных отчётов с генерацией аналитических документов и писем в БКИ.

## Возможности

- ✅ Поддержка множественных форматов БКИ (НБКИ, ОКБ, Скоринг Бюро, Эквифакс, КБ Киви, Русский Стандарт БКИ)
- ✅ Автоматическое определение типа БКИ
- ✅ Извлечение структурированных данных через ИИ (Ollama)
- ✅ Генерация аналитических отчётов (Word)
- ✅ Генерация писем в БКИ для оспаривания ошибок
- ✅ База данных для хранения истории обработки
- ✅ REST API для интеграции
- ✅ Интеграция с Битрикс24

## Установка

### 1. Клонирование и установка зависимостей

```bash
cd "C:\Users\user\Desktop\Cliner finance"
python -m venv venv
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Установка Ollama

Скачайте и установите Ollama с [ollama.ai](https://ollama.ai)

Запустите Ollama и загрузите модели:

```bash
ollama serve
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b
```

### 3. Настройка базы данных

#### Для MVP (SQLite):
Ничего дополнительного не требуется, SQLite работает из коробки.

#### Для продакшена (PostgreSQL):
```bash
# Установка PostgreSQL
# Создание базы данных
createdb credit_ai

# В settings.py укажите:
DATABASE_URL=postgresql://user:password@localhost/credit_ai
```

### 4. Настройка окружения

Скопируйте `.env.example` в `.env` и заполните настройки:

```bash
cp .env.example .env
# Отредактируйте .env файл
```

### 5. Инициализация базы данных

```bash
python main.py
# При первом запуске БД создастся автоматически
```

## Запуск

### Запуск сервера

```bash
python main.py
```

Или напрямую через uvicorn:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: http://localhost:8000

### Запуск Celery worker (опционально)

```bash
celery -A integration.celery_tasks worker --loglevel=info
```

## API Документация

После запуска сервера доступна автоматическая документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Основные эндпоинты

### POST /api/process
Загрузка и обработка PDF файла

```bash
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@report.pdf" \
  -F "deal_id=12345"
```

### GET /api/status/{task_id}
Получить статус обработки

```bash
curl "http://localhost:8000/api/status/{task_id}"
```

### GET /api/download/{document_id}
Скачать сгенерированный документ

### GET /api/statistics
Получить статистику обработки

## Структура проекта

```
credit_ai/
├── main.py                    # Точка входа
├── requirements.txt           # Зависимости
├── config/
│   ├── settings.py           # Настройки
│   └── prompts.py            # Промпты для ИИ
├── core/
│   ├── pdf_processor.py      # Обработка PDF
│   ├── ai_processor.py       # Работа с Ollama
│   ├── data_validator.py     # Валидация данных
│   └── bki_detector.py       # Детекция типа БКИ
├── database/
│   ├── models.py             # SQLAlchemy модели
│   └── repository.py         # CRUD операции
├── services/
│   └── document_generator.py # Генерация Word
├── integration/
│   ├── bitrix_client.py      # Битрикс24 API
│   └── celery_tasks.py       # Фоновые задачи
├── api/
│   ├── main.py               # FastAPI приложение
│   └── endpoints.py          # Эндпоинты
└── utils/
    └── logger.py             # Логирование
```

## Использование

### Пример обработки отчёта

```python
from core.pdf_processor import PDFProcessor
from core.ai_processor import AIProcessor
from services.document_generator import DocumentGenerator

# Обработка PDF
processor = PDFProcessor()
pdf_data = processor.process_pdf("report.pdf")

# Определение типа БКИ
bki_type = pdf_data['bki_detection']['bki_type']

# Извлечение данных через ИИ
ai = AIProcessor()
extracted_data = ai.extract_structured_data(
    pdf_data['full_text'],
    bki_type
)

# Генерация отчёта
generator = DocumentGenerator()
report_path = generator.generate_analysis_report(
    extracted_data,
    "report_id"
)
```

## Разработка

### Тестирование

```bash
pytest tests/
```

### Логирование

Логи сохраняются в консоль и (опционально) в файл.

## Лицензия

Proprietary

## Поддержка

Для вопросов и поддержки обращайтесь к разработчикам.



