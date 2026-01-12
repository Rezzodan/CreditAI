# Полное руководство по развёртыванию CreditAI

## 📋 Содержание

1. [Локальная установка и тестирование](#локальная-установка)
2. [Подготовка к продакшену](#подготовка-к-продакшену)
3. [Развёртывание на сервере](#развёртывание-на-сервере)
4. [Настройка инфраструктуры](#настройка-инфраструктуры)
5. [Мониторинг и обслуживание](#мониторинг)
6. [Решение проблем](#решение-проблем)

---

## 🖥️ Локальная установка

### Шаг 1: Установка Python и зависимостей

#### Windows:
```powershell
# Проверка версии Python (нужна 3.10+)
python --version

# Если Python не установлен, скачайте с python.org

# Создание виртуального окружения
python -m venv venv

# Активация
venv\Scripts\activate

# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
```

#### Linux/Mac:
```bash
# Установка Python 3.10+ (если нет)
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Mac (через Homebrew):
brew install python@3.10

# Создание виртуального окружения
python3 -m venv venv

# Активация
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 2: Установка и настройка Ollama

#### Windows:
1. Скачайте установщик с https://ollama.ai/download
2. Установите и запустите Ollama
3. Откройте PowerShell/CMD и выполните:

```powershell
# Проверка работы
ollama --version

# Запуск сервера (обычно запускается автоматически)
ollama serve

# В другом терминале загрузите модели:
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b

# Проверка загрузки
ollama list
```

#### Linux:
```bash
# Установка через скрипт
curl -fsSL https://ollama.ai/install.sh | sh

# Или через пакетный менеджер (Ubuntu/Debian)
# Добавьте репозиторий и установите

# Запуск сервиса
sudo systemctl enable ollama
sudo systemctl start ollama

# Загрузка моделей
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b
```

#### Mac:
```bash
# Установка через Homebrew
brew install ollama

# Запуск
brew services start ollama

# Загрузка моделей
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b
```

### Шаг 3: Настройка базы данных

#### Вариант A: SQLite (для разработки/MVP)

Ничего дополнительного не требуется. SQLite работает из коробки.

```bash
# Инициализация БД
python init_db.py
```

#### Вариант B: PostgreSQL (для продакшена)

**Windows:**
1. Скачайте PostgreSQL с https://www.postgresql.org/download/windows/
2. Установите с настройками по умолчанию
3. Запомните пароль для пользователя postgres

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Запуск сервиса
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание базы данных
sudo -u postgres psql
```

В psql выполните:
```sql
CREATE DATABASE credit_ai;
CREATE USER credit_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE credit_ai TO credit_user;
\q
```

**Mac:**
```bash
brew install postgresql
brew services start postgresql

# Создание БД
createdb credit_ai
```

### Шаг 4: Настройка Redis (для Celery)

#### Windows:
1. Скачайте Redis для Windows: https://github.com/microsoftarchive/redis/releases
2. Или используйте WSL2 с Linux версией Redis
3. Или используйте Docker (рекомендуется)

#### Linux:
```bash
# Ubuntu/Debian
sudo apt install redis-server

# Запуск
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка
redis-cli ping
# Должен ответить: PONG
```

#### Mac:
```bash
brew install redis
brew services start redis
```

### Шаг 5: Настройка конфигурации

```bash
# Скопируйте пример конфигурации
# Windows:
copy env.example .env

# Linux/Mac:
cp env.example .env
```

Отредактируйте `.env` файл:

```env
# Для локальной разработки (SQLite)
DATABASE_URL=sqlite:///./credit_ai.db

# Для продакшена (PostgreSQL)
# DATABASE_URL=postgresql://credit_user:password@localhost/credit_ai

# Ollama (обычно не нужно менять)
OLLAMA_HOST=http://localhost:11434

# Битрикс24 (заполните при необходимости)
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/webhook_code/

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Шаг 6: Инициализация и запуск

```bash
# Инициализация БД
python init_db.py

# Запуск сервера
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

### Шаг 7: Проверка работы

1. Откройте http://localhost:8000/docs - должна открыться документация API
2. Проверьте здоровье: http://localhost:8000/health
3. Попробуйте загрузить тестовый PDF через API

---

## 🚀 Подготовка к продакшену

### 1. Обновление зависимостей

```bash
# Обновите requirements.txt с точными версиями
pip freeze > requirements.txt

# Проверьте на уязвимости
pip install safety
safety check
```

### 2. Настройка безопасности

#### Обновите `.env` для продакшена:

```env
# КРИТИЧНО: Измените секретный ключ!
SECRET_KEY=your-very-secure-random-string-here

# Отключите debug
DEBUG=False

# Используйте PostgreSQL
DATABASE_URL=postgresql://credit_user:secure_password@localhost/credit_ai

# Настройте CORS (укажите конкретные домены)
# В api/main.py измените allow_origins
```

#### Создайте файл `.env.production`:

```env
APP_NAME=CreditAI
DEBUG=False
HOST=0.0.0.0
PORT=8000

DATABASE_URL=postgresql://credit_user:password@localhost/credit_ai
OLLAMA_HOST=http://localhost:11434

BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/webhook_code/

SECRET_KEY=generate-strong-random-key-here

UPLOAD_FOLDER=/var/credit_ai/uploads
OUTPUT_FOLDER=/var/credit_ai/output
TEMPLATES_FOLDER=/var/credit_ai/templates
```

### 3. Настройка файловой системы

```bash
# Создайте директории для файлов
sudo mkdir -p /var/credit_ai/{uploads,output,templates}
sudo chown -R $USER:$USER /var/credit_ai
sudo chmod -R 755 /var/credit_ai
```

---

## 🖥️ Развёртывание на сервере

### Вариант 1: Развёртывание без Docker (VPS/Выделенный сервер)

#### Требования к серверу:
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Минимум 4GB RAM (рекомендуется 8GB+)
- 50GB+ свободного места
- Python 3.10+
- Доступ по SSH

#### Шаг 1: Подготовка сервера

```bash
# Подключитесь к серверу
ssh user@your-server-ip

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых инструментов
sudo apt install -y git curl wget build-essential
```

#### Шаг 2: Установка Python и зависимостей

```bash
# Установка Python 3.10+
sudo apt install -y python3.10 python3.10-venv python3-pip

# Установка системных зависимостей для PDF
sudo apt install -y \
    libpq-dev \
    python3-dev \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev
```

#### Шаг 3: Установка PostgreSQL

```bash
# Установка PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Настройка
sudo -u postgres psql
```

В psql:
```sql
CREATE DATABASE credit_ai;
CREATE USER credit_user WITH PASSWORD 'your_secure_password';
ALTER ROLE credit_user SET client_encoding TO 'utf8';
ALTER ROLE credit_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE credit_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE credit_ai TO credit_user;
\q
```

#### Шаг 4: Установка Redis

```bash
sudo apt install -y redis-server

# Настройка Redis
sudo nano /etc/redis/redis.conf
# Найдите и раскомментируйте:
# bind 127.0.0.1
# requirepass your_redis_password

# Перезапуск
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

#### Шаг 5: Установка Ollama

```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск как сервис
sudo systemctl enable ollama
sudo systemctl start ollama

# Загрузка моделей
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b
```

#### Шаг 6: Развёртывание приложения

```bash
# Создание пользователя для приложения
sudo useradd -m -s /bin/bash credit_ai
sudo su - credit_ai

# Клонирование проекта (или загрузка файлов)
cd ~
git clone <your-repo-url> credit_ai
# ИЛИ загрузите файлы через scp/sftp

cd credit_ai

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Настройка конфигурации
cp env.example .env
nano .env  # Отредактируйте настройки

# Инициализация БД
python init_db.py

# Создание директорий
mkdir -p uploads output templates
```

#### Шаг 7: Настройка systemd сервисов

Создайте файл `/etc/systemd/system/credit-ai.service`:

```ini
[Unit]
Description=CreditAI FastAPI Application
After=network.target postgresql.service redis.service ollama.service

[Service]
Type=simple
User=credit_ai
WorkingDirectory=/home/credit_ai/credit_ai
Environment="PATH=/home/credit_ai/credit_ai/venv/bin"
ExecStart=/home/credit_ai/credit_ai/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Создайте файл `/etc/systemd/system/credit-ai-celery.service`:

```ini
[Unit]
Description=CreditAI Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=credit_ai
WorkingDirectory=/home/credit_ai/credit_ai
Environment="PATH=/home/credit_ai/credit_ai/venv/bin"
ExecStart=/home/credit_ai/credit_ai/venv/bin/celery -A integration.celery_tasks worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервисов:

```bash
sudo systemctl daemon-reload
sudo systemctl enable credit-ai
sudo systemctl enable credit-ai-celery
sudo systemctl start credit-ai
sudo systemctl start credit-ai-celery

# Проверка статуса
sudo systemctl status credit-ai
sudo systemctl status credit-ai-celery
```

#### Шаг 8: Настройка Nginx (реверс-прокси)

```bash
# Установка Nginx
sudo apt install -y nginx

# Создание конфигурации
sudo nano /etc/nginx/sites-available/credit-ai
```

Содержимое файла:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/credit-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Шаг 9: Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

---

### Вариант 2: Развёртывание с Docker

#### Шаг 1: Установка Docker и Docker Compose

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка (или перелогин)
```

#### Шаг 2: Подготовка файлов

```bash
# Загрузите проект на сервер
cd /opt
git clone <your-repo> credit_ai
cd credit_ai

# Создайте .env файл
cp env.example .env
nano .env  # Отредактируйте настройки
```

#### Шаг 3: Запуск через Docker Compose

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps
```

#### Шаг 4: Настройка Nginx (аналогично варианту 1)

---

## 🔧 Настройка инфраструктуры

### Резервное копирование базы данных

Создайте скрипт `/home/credit_ai/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/credit_ai"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# PostgreSQL
pg_dump -U credit_user credit_ai > $BACKUP_DIR/credit_ai_$DATE.sql

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

Добавьте в crontab:

```bash
crontab -e
# Ежедневный бэкап в 2:00
0 2 * * * /home/credit_ai/backup_db.sh
```

### Мониторинг логов

```bash
# Просмотр логов приложения
sudo journalctl -u credit-ai -f

# Просмотр логов Celery
sudo journalctl -u credit-ai-celery -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Настройка автоматического обновления

Создайте скрипт `/home/credit_ai/update.sh`:

```bash
#!/bin/bash
cd /home/credit_ai/credit_ai
source venv/bin/activate
git pull
pip install -r requirements.txt
sudo systemctl restart credit-ai
sudo systemctl restart credit-ai-celery
```

---

## 📊 Мониторинг

### Проверка здоровья системы

```bash
# Проверка API
curl http://localhost:8000/health

# Проверка Ollama
curl http://localhost:11434/api/tags

# Проверка Redis
redis-cli ping

# Проверка PostgreSQL
sudo -u postgres psql -c "SELECT version();"
```

### Метрики для мониторинга

1. **Производительность API**: время ответа, количество запросов
2. **Обработка PDF**: успешность, время обработки
3. **База данных**: размер, количество записей, время запросов
4. **Ollama**: использование памяти, время ответа
5. **Дисковое пространство**: размер uploads и output

---

## 🐛 Решение проблем

### Проблема: Ollama не отвечает

```bash
# Проверка статуса
systemctl status ollama

# Перезапуск
sudo systemctl restart ollama

# Проверка порта
netstat -tulpn | grep 11434
```

### Проблема: Ошибки базы данных

```bash
# Проверка подключения
psql -U credit_user -d credit_ai -c "SELECT 1;"

# Проверка логов PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Проблема: Celery не работает

```bash
# Проверка Redis
redis-cli ping

# Перезапуск Celery
sudo systemctl restart credit-ai-celery

# Просмотр логов
sudo journalctl -u credit-ai-celery -n 50
```

### Проблема: Недостаточно памяти

```bash
# Проверка использования
free -h
df -h

# Очистка старых файлов
find /var/credit_ai/uploads -type f -mtime +30 -delete
find /var/credit_ai/output -type f -mtime +30 -delete
```

---

## ✅ Чеклист развёртывания

- [ ] Python 3.10+ установлен
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Ollama установлен и модели загружены
- [ ] База данных настроена (PostgreSQL или SQLite)
- [ ] Redis установлен и запущен
- [ ] Конфигурация (.env) заполнена
- [ ] База данных инициализирована
- [ ] Приложение запускается локально
- [ ] Systemd сервисы созданы (для продакшена)
- [ ] Nginx настроен (для продакшена)
- [ ] SSL сертификат установлен (для продакшена)
- [ ] Резервное копирование настроено
- [ ] Мониторинг настроен
- [ ] Тестирование API прошло успешно

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u credit-ai -n 100`
2. Проверьте документацию API: http://your-domain/docs
3. Проверьте статус всех сервисов
4. Обратитесь к разработчикам с логами ошибок








