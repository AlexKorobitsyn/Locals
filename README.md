# Locals

Музыкальный сервис для независимой местной сцены(Я в Екб плотно общаюсь с многими площадками и музыкантами): публикация и прослушивание музыки,
оценки звёздами от 1 до 5 с шагом 0,5, рецензии, рекомендации и плейлисты.
Есть события и площадки на карте, подписки, опыт участников и модерация.

**Backkend:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL 16, Alembic;
аудио и изображения хранятся в MinIO/S3, авторизация — JWT и HttpOnly cookie.
**Frontend:** React, TypeScript, Vite; отдельный контейнер Nginx проксирует API.

## Первый запуск backend

.env
# Заполнить случайным секретом минимум 32 символа.
JWT_SECRET_KEY=

# Задать пароль PostgreSQL.
POSTGRES_PASSWORD=

# Собрать URL с этим паролем:
# postgresql+asyncpg://<POSTGRES_USER>:<пароль>@db:5432/<POSTGRES_DB>
DATABASE_URL=

# Заполнить учётными данными своего хранилища.
S3_ACCESS_KEY=
S3_SECRET_KEY=
MINIO_ROOT_PASSWORD=

Нужны Docker с Compose и работающий Docker Desktop/Engine. Команды — из корня проекта.
Скопируйте `.env.example` в `.env`, если его ещё нет. В `.env` задайте
`JWT_SECRET_KEY` (случайный секрет от 32 символов), оставьте `COMPOSE_PROFILES=local`.
Пароли `MINIO_ROOT_PASSWORD` и `S3_SECRET_KEY` должны совпадать.
Настройки локальных адресов и cookie уже есть в примере.

```bash
docker compose build app storage
docker compose up -d --wait db storage
docker compose run --rm migrate
docker compose run --rm storage-init
docker compose up -d --no-build app
```

API станет доступно: http://localhost:8000/api/v1/docs. Порт меняется через `PORT` в `.env`.

## Первый запуск frontend

После запуска backend, из того же корня:

```bash
docker compose -f compose.yaml -f compose.frontend.yaml build frontend
docker compose -f compose.yaml -f compose.frontend.yaml up -d --no-build frontend
```

Сайт: http://localhost:8080. Порт меняется через `FRONTEND_PORT` в `.env`.
При смене порта сайта обновите `BROWSER_ALLOWED_ORIGINS` и CORS MinIO/S3.
Зарегистрируйтесь на сайте; музыку можно добавлять через «Студию».

Для доступа к администрированию и заполнения справочников:

```bash
docker compose run --rm app python -m APP.create_admin --email admin@example.com --display-name "Администратор"
```

Пароль вводится в терминале. После входа этим аккаунтом доступен раздел «Администрирование».

## Повторный запуск готовых образов

После первого запуска, с прежним `.env` и сохранёнными данными:

```bash
docker compose -f compose.yaml -f compose.frontend.yaml up -d --no-build db storage app frontend
```

Остановка без удаления данных:

```bash
docker compose -f compose.yaml -f compose.frontend.yaml down
```

Данные БД и файлов остаются в Docker volumes. `down -v` удаляет их.
