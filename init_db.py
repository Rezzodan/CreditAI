"""
Скрипт инициализации базы данных
"""
from database.repository import DatabaseRepository
from config.settings import settings

if __name__ == "__main__":
    print("Инициализация базы данных...")
    db_repo = DatabaseRepository()
    db_repo.init_db()
    print(f"База данных инициализирована: {settings.DATABASE_URL}")



