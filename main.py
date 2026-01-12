"""
Точка входа в приложение
"""
import uvicorn
from config.settings import settings
from database.repository import DatabaseRepository

# Инициализация базы данных
db_repo = DatabaseRepository()
db_repo.init_db()

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )








