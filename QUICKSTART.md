# Быстрый старт

## Шаг 1: Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка пакетов
pip install -r requirements.txt
```

## Шаг 2: Установка и настройка Ollama

1. Скачайте Ollama с https://ollama.ai
2. Установите и запустите:
   ```bash
   ollama serve
   ```

3. В другом терминале загрузите модели:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama pull saiga3:8b
   ```

## Шаг 3: Настройка окружения

Скопируйте `env.example` в `.env` и при необходимости отредактируйте:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

Для MVP можно оставить настройки по умолчанию (SQLite).

## Шаг 4: Инициализация базы данных

```bash
python init_db.py
```

## Шаг 5: Запуск сервера

```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

## Шаг 6: Проверка работы

Откройте в браузере:
- API документация: http://localhost:8000/docs
- Проверка здоровья: http://localhost:8000/health

## Тестирование API

### Загрузка PDF для обработки:

```bash
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@path/to/your/report.pdf" \
  -F "deal_id=12345"
```

Ответ:
```json
{
  "task_id": "uuid",
  "status": "pending",
  "message": "Обработка запущена"
}
```

### Проверка статуса:

```bash
curl "http://localhost:8000/api/status/{task_id}"
```

### Скачивание документа:

```bash
curl "http://localhost:8000/api/download/{document_id}" \
  --output report.docx
```

## Структура папок

После первого запуска создадутся папки:
- `uploads/` - загруженные PDF файлы
- `output/` - сгенерированные документы
- `credit_ai.db` - база данных SQLite (если используется)

## Решение проблем

### Ollama не доступен

Проверьте, что Ollama запущен:
```bash
curl http://localhost:11434/api/tags
```

### Ошибки при обработке PDF

- Убедитесь, что файл является валидным PDF
- Проверьте размер файла (максимум 50MB)
- Проверьте логи в консоли

### Проблемы с базой данных

Для SQLite убедитесь, что есть права на запись в текущую директорию.

Для PostgreSQL проверьте подключение и создайте базу данных:
```sql
CREATE DATABASE credit_ai;
```

## Следующие шаги

1. Настройте интеграцию с Битрикс24 (укажите `BITRIX_WEBHOOK_URL` в `.env`)
2. Настройте Celery для фоновой обработки (опционально)
3. Настройте мониторинг и логирование
4. Настройте резервное копирование базы данных



