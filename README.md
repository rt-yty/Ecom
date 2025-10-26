## Ecom
Это REST API на базе FastAPI и асинхронного SQLAlchemy. Приложение реализует базовый функционал интернет-магазина: пользователи, роли (админ, поставщик, покупатель), категории, товары, отзывы, рейтинг и права доступа. В проекте используется JWT-аутентификация и Alembic для миграций базы данных.
### Структура проекта
``` 
app/
├── main.py                 # Создаёт экземпляр FastAPI и подключает маршруты
├── requirements.txt
├── Dockerfile
├── Dockerfile.prod
├── backend/
│   ├── db.py               # Настройка асинхронного движка SQLAlchemy и Base
│   └── db_depends.py       # Зависимость FastAPI для выдачи AsyncSession
├── models/
│   ├── __init__.py
│   ├── user.py             # Модель пользователя со статусами admin/supplier/customer
│   ├── products.py         # Модель товара с полями id, name, slug, price, stock и рейтинг
│   ├── category.py         # Модель категории с древовидной связью parent_id
│   └── review.py           # Модель отзыва: оценка 1–5, комментарий, дата
├── schemas.py              # Pydantic-схемы для валидации входных данных
├── routers/
│   ├── auth.py             # Регистрация, получение токена и текущего пользователя
│   ├── products.py         # CRUD для товаров и выборка по категориям/slug
│   ├── category.py         # CRUD для категорий
│   ├── review.py           # CRUD для отзывов и пересчёт рейтинга
│   └── permission.py       # Операции админа: смена ролей и удаление пользователей
└── migrations/
    ├── env.py
    └── versions/           
alembic.ini
```

### Настройка и запуск
1. Клонируйте репозиторий и создайте файл в корне. В нём должны быть переменные: `.env`
``` dotenv
    DATABASE_URL=postgresql+asyncpg://user:password@host:port/db_name
    SECRET_KEY=ваш_секретный_ключ
    ALGORITHM=HS256
```
1. Установите зависимости:
``` bash
    python -m venv venv
    source venv/bin/activate
    pip install -r app/requirements.txt
```
1. Запустите миграции, чтобы создать таблицы в БД:
``` bash
    alembic upgrade head
```
1. Запустите сервер:
``` bash
    uvicorn app.main:app --reload
```
Сервис будет доступен на `http://localhost:8000`. Документация Swagger доступна по адресу `http://localhost:8000/docs`.
#### (Опционально) Docker
Для локального запуска в контейнере соберите образ:
``` bash
docker build -f app/Dockerfile -t ecom-dev .
docker run -p 8000:8000 --env-file .env ecom-dev
```
### Как пользоваться API
Все защищённые маршруты требуют передачи заголовка `Authorization: Bearer <token>`.
#### Регистрация и авторизация (`/auth`)
- **`POST /auth/`**: Создать пользователя.
- **`POST /auth/token`**: Получить JWT-токен, указав `username` и `password` в форме.

#### Категории (`/category`)
- **`GET /category/`**: Список всех активных категорий.
- **`POST /category/`**: Создание категории (только админ).
- **`PUT /category/{slug}`**: Обновить категорию (только админ).
- **`DELETE /category/{slug}`**: Логическое удаление категории (только админ).

#### Товары (`/products`)
- **`GET /products/`**: Получить все активные товары, привязанные к активным категориям.
- **`POST /products/`**: Создать товар (поставщик или админ).
- **`GET /products/{category_slug}`**: Товары выбранной категории и её подкатегорий.
- **`GET /products/details/{product_slug}`**: Подробная информация о товаре.
- **`PUT /products/{product_slug}`**: Обновить товар (только поставщик-владелец).
- **`DELETE /products/{product_slug}`**: Скрыть товар (поставщик-владелец).

#### Отзывы (`/review`)
- **`GET /review/`**: Список отзывов для всех активных товаров.
- **`POST /review/`**: Добавить отзыв, указывая `id` товара, оценку (1–5) и комментарий. Рейтинг товара пересчитывается.
- **`GET /review/{user_id}`**: Отзывы конкретного пользователя.
- **`GET /review/{product_slug}`**: Отзывы для товара.
- **`PUT /review/{review_id}`**: Обновить отзыв (автор или админ).
- **`DELETE /review/{review_id}`**: Скрыть отзыв (автор или админ).

#### Управление ролями (`/permission`)
- **`PATCH /permission/`**: Админ может включить/выключить статус поставщика у пользователя.
- **`DELETE /permission/delete`**: Админ может деактивировать пользователя (кроме админов).
