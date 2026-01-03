# ⚡ Быстрая загрузка на GitHub

## 🚀 Команды для выполнения (по порядку)

### 1. Инициализация Git
```bash
cd "C:\Users\user\Desktop\Cliner finance"
git init
```

### 2. Настройка Git (если ещё не настроено)
```bash
git config --global user.name "Ваше Имя"
git config --global user.email "your.email@example.com"
```

### 3. Добавление файлов
```bash
git add .
```

### 4. Проверка что будет закоммичено
```bash
git status
```
**Убедитесь что НЕТ:**
- ❌ `.env`
- ❌ `.venv/` или `venv/`
- ❌ `.idea/`
- ❌ `credit_ai.db`

### 5. Первый коммит
```bash
git commit -m "Initial commit: CreditAI system for credit report processing"
```

### 6. Создайте репозиторий на GitHub
1. Откройте https://github.com
2. Нажмите **"+"** → **"New repository"**
3. Имя: `credit-ai` (или другое)
4. Выберите **Private** (рекомендуется)
5. **НЕ отмечайте** README, .gitignore, license
6. Нажмите **"Create repository"**

### 7. Подключение и загрузка
```bash
# Замените YOUR_USERNAME на ваш GitHub username
git remote add origin https://github.com/YOUR_USERNAME/credit-ai.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Загрузите на GitHub
git push -u origin main
```

**При запросе авторизации:**
- Username: ваш GitHub username
- Password: используйте **Personal Access Token** (не пароль!)

---

## 🔑 Создание Personal Access Token

1. GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token (classic)
4. Выберите `repo` (полный доступ к репозиториям)
5. Скопируйте токен (показывается только один раз!)
6. Используйте токен как пароль при `git push`

---

## ✅ Всё готово!

После выполнения команд ваш проект будет на GitHub!

**Подробная инструкция:** см. `GITHUB_SETUP.md`

