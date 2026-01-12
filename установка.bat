@echo off
chcp 65001 > nul
echo ════════════════════════════════════════════════════════════════
echo      CREDITAI - АВТОМАТИЧЕСКАЯ УСТАНОВКА
echo ════════════════════════════════════════════════════════════════
echo.

:: Проверка Python
echo [1/7] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ОШИБКА: Python не найден!
    echo Установите Python 3.10+ с https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo ✅ Python найден
echo.

:: Создание виртуального окружения
echo [2/7] Создание виртуального окружения...
if exist venv (
    echo ⚠️  Папка venv уже существует
    echo Хотите пересоздать? (файлы будут удалены^)
    set /p "recreate=Введите Y для пересоздания или N для продолжения: "
    if /i "%recreate%"=="Y" (
        echo Удаление старого venv...
        rmdir /s /q venv
        echo Создание нового venv...
        python -m venv venv
    )
) else (
    python -m venv venv
)
if %errorlevel% neq 0 (
    echo ❌ ОШИБКА: Не удалось создать venv
    pause
    exit /b 1
)
echo ✅ Виртуальное окружение создано
echo.

:: Активация виртуального окружения
echo [3/7] Активация виртуального окружения...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ ОШИБКА: Не удалось активировать venv
    pause
    exit /b 1
)
echo ✅ Виртуальное окружение активировано
echo.

:: Обновление pip
echo [4/7] Обновление pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo ⚠️  Предупреждение: Не удалось обновить pip
) else (
    echo ✅ Pip обновлен
)
echo.

:: Установка зависимостей
echo [5/7] Установка зависимостей (может занять 2-5 минут^)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ ОШИБКА: Не удалось установить зависимости
    echo Проверьте интернет-соединение и попробуйте снова
    pause
    exit /b 1
)
echo ✅ Зависимости установлены
echo.

:: Создание .env файла
echo [6/7] Создание конфигурации...
if not exist .env (
    if exist env.example (
        copy env.example .env >nul
        echo ✅ Файл .env создан из шаблона
        echo ⚠️  ВАЖНО: Проверьте настройки в файле .env
    ) else (
        echo ⚠️  Файл env.example не найден
    )
) else (
    echo ℹ️  Файл .env уже существует
)
echo.

:: Инициализация базы данных
echo [7/7] Инициализация базы данных...
if exist credit_ai.db (
    echo ℹ️  База данных уже существует
    set /p "recreatedb=Пересоздать базу данных? (Y/N): "
    if /i "%recreatedb%"=="Y" (
        del credit_ai.db
        python init_db.py
    )
) else (
    python init_db.py
)
if %errorlevel% neq 0 (
    echo ⚠️  Предупреждение: Не удалось инициализировать БД
) else (
    echo ✅ База данных готова
)
echo.

:: Проверка Ollama
echo ════════════════════════════════════════════════════════════════
echo      ПРОВЕРКА OLLAMA
echo ════════════════════════════════════════════════════════════════
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  ВНИМАНИЕ: Ollama не найден!
    echo.
    echo Для работы AI необходимо:
    echo 1. Установить Ollama с https://ollama.com
    echo 2. Загрузить модель: ollama pull qwen2.5:3b
    echo.
) else (
    ollama --version
    echo ✅ Ollama установлен
    echo.
    echo Проверка модели qwen2.5:3b...
    ollama list | findstr "qwen2.5:3b" >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  Модель qwen2.5:3b не найдена
        echo.
        set /p "pullmodel=Загрузить модель сейчас? (Y/N): "
        if /i "%pullmodel%"=="Y" (
            echo Загрузка модели (может занять несколько минут^)...
            ollama pull qwen2.5:3b
        ) else (
            echo Загрузите модель позже: ollama pull qwen2.5:3b
        )
    ) else (
        echo ✅ Модель qwen2.5:3b установлена
    )
)
echo.

:: Итоги
echo ════════════════════════════════════════════════════════════════
echo      ✅ УСТАНОВКА ЗАВЕРШЕНА!
echo ════════════════════════════════════════════════════════════════
echo.
echo Проверка установки:
pip list | findstr "fastapi pdfplumber sqlalchemy" >nul
if %errorlevel% equ 0 (
    echo ✅ Основные библиотеки установлены
) else (
    echo ⚠️  Некоторые библиотеки могут отсутствовать
)
echo.

:: Список установленных пакетов
echo Установленные пакеты:
pip list
echo.

:: Следующие шаги
echo ════════════════════════════════════════════════════════════════
echo      СЛЕДУЮЩИЕ ШАГИ:
echo ════════════════════════════════════════════════════════════════
echo.
echo 1. Проверьте настройки в файле .env
echo 2. Запустите сервер: python main.py
echo 3. Откройте в браузере: http://localhost:8000/docs
echo.
echo Для запуска проекта в будущем:
echo    venv\Scripts\activate
echo    python main.py
echo.
echo ════════════════════════════════════════════════════════════════
echo.
set /p "runserver=Запустить сервер сейчас? (Y/N): "
if /i "%runserver%"=="Y" (
    echo.
    echo Запуск сервера...
    echo Для остановки нажмите Ctrl+C
    echo.
    python main.py
) else (
    echo.
    echo Для запуска сервера выполните:
    echo    venv\Scripts\activate
    echo    python main.py
    echo.
    pause
)


