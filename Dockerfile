FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание папок
RUN mkdir -p uploads output templates

# Порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]








