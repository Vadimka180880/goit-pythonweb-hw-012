.
# Домашнє завдання 12: Production-ready FastAPI REST API

## Опис проєкту
Цей проєкт — повноцінний REST API для керування контактами та користувачами з ролями, JWT, кешуванням, скиданням пароля, контейнеризацією та деплоєм у хмару.

### Основні можливості
- CRUD для контактів
- Реєстрація, логін, email-верифікація
- JWT (access/refresh), ротація та відкликання refresh_token через Redis
- Ролі користувачів: user/admin, захист endpoint-ів
- Скидання пароля через email
- Кешування користувача через Redis
- Оновлення аватара (Cloudinary)
- Документація Swagger/OpenAPI
- Контейнеризація Docker + Docker Compose
- Alembic міграції
- Sphinx-документація
- Покриття тестами >75% (pytest, pytest-cov)

### Технології
- Python 3.12+
- FastAPI, SQLAlchemy, Alembic
- PostgreSQL, Redis
- Docker, Docker Compose
- Cloudinary, Mailtrap
- Pytest, httpx, coverage

## Швидкий старт

### 1. Клонування та запуск у Docker
```bash
git clone https://github.com/Vadimka180880/goit-pythonweb-hw-012.git
cd goit-pythonweb-hw-012
docker-compose up --build
```

### 2. Локальний запуск
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Міграції
```bash
docker-compose exec app alembic upgrade head
# або локально:
alembic upgrade head
```

### 4. Тести
```bash
pytest --cov=app
```

## .env (приклад)
```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
REDIS_URL=redis://default:password@host:6379
JWT_SECRET=your_jwt_secret
MAIL_USERNAME=your@mail.com
MAIL_PASSWORD=your_mail_password
MAIL_FROM=your@mail.com
MAIL_PORT=2525
MAIL_SERVER=smtp.mailtrap.io
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
```

## Деплой на Render
1. Створіть PostgreSQL та Redis сервіси на Render, скопіюйте URL.
2. Додайте Web Service з GitHub-репозиторію.
3. Додайте змінні середовища у Render Dashboard.
4. Після деплою застосунок буде доступний за посиланням Render.

## Документація
- Swagger: `/docs`
- Sphinx: у папці `docs/` (збірка: `make html`)

---
**Автор:** Смірнов Вадим

**Посилання на репозиторій:** https://github.com/Vadimka180880/goit-pythonweb-hw-012

