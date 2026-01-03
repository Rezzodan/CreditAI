# Пошаговая инструкция по установке и развёртыванию

## 🎯 Краткий обзор

Этот документ содержит пошаговые инструкции для:
1. Локальной установки и тестирования
2. Подготовки к продакшену
3. Развёртывания на сервере

---

## 📦 Часть 1: Локальная установка (для разработки/тестирования)

### Шаг 1.1: Установка Python

**Windows:**
1. Скачайте Python 3.10+ с https://www.python.org/downloads/
2. При установке отметьте "Add Python to PATH"
3. Проверьте: `python --version` (должно быть 3.10 или выше)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
python3 --version
```

**Mac:**
```bash
brew install python@3.10
python3 --version
```

### Шаг 1.2: Создание виртуального окружения

```bash
# Перейдите в папку проекта
cd "C:\Users\user\Desktop\Cliner finance"

# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate
```

### Шаг 1.3: Установка зависимостей Python

```bash
# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
```

**Если возникают ошибки:**
- Windows: может потребоваться Visual C++ Build Tools
- Linux: `sudo apt install python3-dev libpq-dev gcc g++`
- Mac: `xcode-select --install`

### Шаг 1.4: Установка Ollama

**Windows:**
1. Скачайте с https://ollama.ai/download
2. Установите и запустите
3. Откройте новый терминал и выполните:

```powershell
# Проверка
ollama --version

# Загрузка моделей (это займёт время, ~7GB каждая)
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b

# Проверка
ollama list
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve  # В фоне или через systemd
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b
```

**Mac:**
```bash
brew install ollama
brew services start ollama
ollama pull qwen2.5-coder:7b
ollama pull saiga3:8b
```

### Шаг 1.5: Настройка конфигурации

```bash
# Создание .env файла
# Windows:
copy env.example .env

# Linux/Mac:
cp env.example .env
```

Откройте `.env` и проверьте настройки (для локальной разработки можно оставить по умолчанию).

### Шаг 1.6: Инициализация базы данных

```bash
# Инициализация БД (создаст SQLite файл)
python init_db.py
```

Должен появиться файл `credit_ai.db`.

### Шаг 1.7: Запуск приложения

```bash
# Запуск сервера
python main.py
```

Откройте браузер:
- API документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Шаг 1.8: Проверка работы

```bash
# В другом терминале запустите тест
python test_setup.py
```

Все проверки должны пройти успешно.

---

## 🏭 Часть 2: Подготовка к продакшену

### Шаг 2.1: Установка PostgreSQL

**Windows:**
1. Скачайте с https://www.postgresql.org/download/windows/
2. Установите, запомните пароль для postgres

**Linux:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Создание базы данных:**
```bash
sudo -u postgres psql
```

В psql:
```sql
CREATE DATABASE credit_ai;
CREATE USER credit_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE credit_ai TO credit_user;
ALTER USER credit_user CREATEDB;
\q
```

### Шаг 2.2: Установка Redis

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping  # Должен ответить PONG
```

**Windows:** Используйте Docker или WSL2

### Шаг 2.3: Обновление конфигурации

Обновите `.env` для продакшена:

```env
DEBUG=False
DATABASE_URL=postgresql://credit_user:your_password@localhost/credit_ai
SECRET_KEY=generate-very-secure-random-key-here
REDIS_URL=redis://localhost:6379/0
```

**Генерация SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Шаг 2.4: Инициализация продакшен БД

```bash
# Убедитесь что DATABASE_URL указывает на PostgreSQL
python init_db.py
```

---

## 🚀 Часть 3: Развёртывание на сервере

### Вариант A: Без Docker (VPS/Выделенный сервер)

#### Шаг 3.1: Подключение к серверу

```bash
ssh user@your-server-ip
```

#### Шаг 3.2: Установка системных зависимостей

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых инструментов
sudo apt install -y git curl wget build-essential

# Установка Python
sudo apt install -y python3.10 python3.10-venv python3-pip

# Системные зависимости для Python пакетов
sudo apt install -y \
    libpq-dev \
    python3-dev \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    ghostscript \
    python3-tk
```

#### Шаг 3.3: Установка PostgreSQL, Redis, Ollama

См. шаги 2.1, 2.2 и 1.4 выше.

#### Шаг 3.4: Развёртывание приложения

```bash
# Создание пользователя
sudo useradd -m -s /bin/bash credit_ai
sudo su - credit_ai

# Создание директории
mkdir -p ~/credit_ai
cd ~/credit_ai

# Загрузка проекта (через git или scp)
# Если через git:
git clone <your-repo-url> .

# Если через scp (с локальной машины):
# scp -r "C:\Users\user\Desktop\Cliner finance\*" user@server:~/credit_ai/

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

#### Шаг 3.5: Настройка systemd сервисов

Выйдите из пользователя credit_ai и создайте сервисы:

```bash
exit  # Выход из пользователя credit_ai
sudo nano /etc/systemd/system/credit-ai.service
```

Содержимое:
```ini
[Unit]
Description=CreditAI FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=credit_ai
WorkingDirectory=/home/credit_ai/credit_ai
Environment="PATH=/home/credit_ai/credit_ai/venv/bin"
EnvironmentFile=/home/credit_ai/credit_ai/.env
ExecStart=/home/credit_ai/credit_ai/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Создайте Celery сервис:
```bash
sudo nano /etc/systemd/system/credit-ai-celery.service
```

Содержимое:
```ini
[Unit]
Description=CreditAI Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=credit_ai
WorkingDirectory=/home/credit_ai/credit_ai
Environment="PATH=/home/credit_ai/credit_ai/venv/bin"
EnvironmentFile=/home/credit_ai/credit_ai/.env
ExecStart=/home/credit_ai/credit_ai/venv/bin/celery -A integration.celery_tasks worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable credit-ai
sudo systemctl enable credit-ai-celery
sudo systemctl start credit-ai
sudo systemctl start credit-ai-celery

# Проверка
sudo systemctl status credit-ai
```

#### Шаг 3.6: Настройка Nginx

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/credit-ai
```

Содержимое:
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

#### Шаг 3.7: Настройка SSL

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Вариант B: С Docker

#### Шаг 3.1: Установка Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### Шаг 3.2: Установка Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Шаг 3.3: Развёртывание

```bash
# Загрузка проекта
cd /opt
git clone <your-repo> credit_ai
cd credit_ai

# Настройка .env
cp env.example .env
nano .env

# Запуск
docker-compose up -d

# Проверка
docker-compose ps
docker-compose logs -f
```

---

## ✅ Финальная проверка

После развёртывания проверьте:

1. **API доступен:**
   ```bash
   curl http://your-domain.com/health
   ```

2. **Документация работает:**
   Откройте http://your-domain.com/docs

3. **Все сервисы запущены:**
   ```bash
   sudo systemctl status credit-ai
   sudo systemctl status credit-ai-celery
   sudo systemctl status postgresql
   sudo systemctl status redis
   sudo systemctl status ollama
   ```

4. **Тест загрузки файла:**
   ```bash
   curl -X POST "http://your-domain.com/api/process" \
     -F "file=@test.pdf"
   ```

---

## 📚 Дополнительные ресурсы

- `DEPLOYMENT_GUIDE.md` - подробное руководство по развёртыванию
- `CHECKLIST.md` - чеклист проверки
- `README.md` - общая документация
- `QUICKSTART.md` - быстрый старт

---

## 🆘 Поддержка

При проблемах:
1. Проверьте логи: `sudo journalctl -u credit-ai -n 100`
2. Запустите тест: `python test_setup.py`
3. Проверьте все сервисы: `sudo systemctl status <service-name>`



