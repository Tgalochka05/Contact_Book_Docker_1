# Contact_Book_Docker

Приложение для хранение контактов.

## Функциональность

- Добавление контактов по БД и по XML
- Возможность поиска
- Docker контейнеризация
- PostgreSQL база данных

## Установка и запуск

1. Клонируйте репозиторий

2. Создайте файл .env, взяв информацию из .env.example:

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

3. Запустите приложение:
```bash
docker-compose up --build
```
4. Выполните миграции (в новом терминале):

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```
5. Откройте в браузере: http://localhost:8000
