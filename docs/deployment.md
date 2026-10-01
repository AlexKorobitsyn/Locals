# CI, релизы и развёртывание

## Что проверяется автоматически

Workflow `.github/workflows/backend.yml` запускается для PR, push и вручную:

1. Python 3.12, установка закреплённых зависимостей, `pip check`, Ruff и форматирование.
2. Проверка единственной Alembic head и полный цикл `upgrade → check → downgrade →
   upgrade → check` в новой временной схеме PostgreSQL 16.
3. Весь pytest, включая реальные PostgreSQL/S3, конкурентные изменения и каскады.
   MinIO собирается из фиксированного исходного релиза, bucket приватен.
4. Однократная сборка backend-образа; миграции отдельным контейнером из этого образа,
   проверка готовности HTTP, версии, OpenAPI и рекомендаций.
5. Сохранение `image.tar` и `release.json` как GitHub artifact на 7 дней.

GitHub Actions закреплены по SHA проверенных официальных релизов.
PR не публикует образ. Для push тега `vMAJOR.MINOR.PATCH` отдельный job с правом
`packages: write` загружает уже проверенный artifact и публикует его в GHCR
без повторной сборки. Push обычной ветки и ручной запуск выполняют проверки и
сборку. Workflow не подключается к серверу и не выполняет деплой автоматически.

Для репозитория `AlexKorobitsyn/Locals` образ будет расположен в
`ghcr.io/alexkorobitsyn/locals`. Нужны включённые Actions и разрешение публиковать
пакеты через `GITHUB_TOKEN`. Доступность пакета и политики Actions настраиваются
в GitHub при первом запуске. Workflow подготовлен в репозитории; реальное
удалённое выполнение требует коммита и push.

Источники:
[публикация Docker-образов в GitHub](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images),
[Docker Build в GitHub Actions](https://docs.docker.com/build/ci/github-actions/).

## Идентификатор артефакта

```text
sha-<полный git sha>-<github run id>-<run attempt>
```

Повтор CI получает отдельный ID. Docker labels содержат версию, revision и source;
`RELEASE_ID` встроен в образ. `GET /api/v1/health/version` показывает именно ID
запущенной сборки. Build принимает только метаданные `RELEASE_ID`, `VCS_REF`,
`VCS_URL`; пароли и ключи передаются при запуске.

`release.json` сохраняет ID, commit и имя образа. Опубликованный тег включает
этот ID, а digest виден при `docker push`. Для staging/prod использовать
`APP_IMAGE=ghcr.io/alexkorobitsyn/locals@sha256:<digest>`: digest однозначно
фиксирует содержимое, независимо от будущего состояния тега.
Один и тот же digest переносится из staging в production, без пересборки.

Локальная сборка с известным commit:

```bash
RELEASE_ID="sha-$(git rev-parse HEAD)-local" \
VCS_REF="$(git rev-parse HEAD)" \
APP_IMAGE=music-service:local-release docker compose build app
```

Если рабочее дерево изменено, такой локальный ID не утверждает, что содержимое
равно чистому commit. CI собирает checkout указанной ревизии и включает run ID.

## Одна схема Compose для разных окружений

В `.env.example` описаны переменные. `COMPOSE_PROFILES=local` включает локальные
PostgreSQL и MinIO. `COMPOSE_PROFILES=` оставляет их выключенными: приложение
использует внешние `DATABASE_URL` и `S3_*`. Необязательные зависимости Compose
позволяют запускать тот же шаблон с внешними сервисами.

`APP_BIND_HOST` и `MINIO_BIND_HOST` по умолчанию `127.0.0.1`. Для публичного
HTTPS поставить reverse proxy на том же сервере и направить API к локальному
порту приложения. Управление TLS и доменом — конфигурация выбранного proxy.
MinIO console не является публичным пользовательским API. Для браузера
`S3_PUBLIC_ENDPOINT_URL` должен указывать на доступный HTTPS-адрес объекта,
а не на внутреннее имя `storage`. За proxy сохранять host и URI подписанной ссылки.

Для локального MinIO внутренний адрес — `http://storage:9000`, для внешнего S3 —
адрес провайдера. `CORS_ORIGINS` задаётся JSON-массивом точных frontend origins,
например `["https://music.example.com"]`; по умолчанию кросс-доменные обращения
не разрешены. На одном origin с `/api/v1` через proxy CORS не нужен.
S3 и MinIO имеют свои отдельные CORS-настройки для браузерного `Range`.

Frontend добавляется вторым Compose-файлом:
`docker compose -f compose.yaml -f compose.frontend.yaml up -d --build app frontend`.
Nginx отдаёт SPA и проксирует `/api` в отдельный контейнер app. Внешний порт
задаётся `FRONTEND_PORT` (по умолчанию 8080), образ — `FRONTEND_IMAGE`.
Для публичного HTTPS направьте TLS reverse proxy на frontend.

`BROWSER_ALLOWED_ORIGINS` задаёт JSON-массив точных origins сайта для браузерных
login/refresh/logout. Это отдельная проверка CSRF, необходимая и при одном origin.
В production `BROWSER_COOKIE_SECURE=true` (значение по умолчанию), для локального
HTTP — false. Refresh хранится в HttpOnly SameSite=Lax cookie; JSON API сохранён.
После изменения backend-авторизации нужен новый образ app, миграции не добавлены.
Origins сайта также добавляются в настройки S3/MinIO для воспроизведения медиа.

Frontend получает лимиты `IMAGE_MAX_BYTES`/`AUDIO_MAX_BYTES` через `/config.json`
при запуске контейнера. `UPLOAD_MAX_BODY_SIZE` и `API_READ_TIMEOUT` регулируют
ограничение multipart и ожидание backend в Nginx. Эти значения не требуют
пересборки SPA; `frontend/README.md` содержит инструкции и проверки.

Долгоживущие контейнеры используют `RESTART_POLICY`, Docker ограничивает объём
собираемых stdout-логов через `LOG_MAX_SIZE` и `LOG_MAX_FILE`. Параметры БД,
JWT, лимиты файлов и коэффициенты рекомендаций также задаются env.
Runtime `RELEASE_ID` Compose не подменяет: это метаданные подготовленного образа.
Для standalone `python -m APP` его можно задать в окружении.

## Первый запуск сервера

Выбрать один сервер/VPS, настроить HTTPS и постоянное хранилище конфигурации
вне Git. У пользователя deploy должны быть доступ к Docker и право скачивать
приватный GHCR package, если он приватен. Для `docker login ghcr.io` использовать
учётные данные с правом чтения пакета. Серверу нужны Compose с поддержкой
`depends_on.required` и доступ к PostgreSQL/S3.

1. Скопировать `.env.example` в защищённый файл вне репозитория, задать реальные
   секреты, адреса, origins и опубликованный `APP_IMAGE` по digest.
2. При `COMPOSE_PROFILES=local` собрать MinIO один раз и запустить backing services:

   ```bash
   docker compose --env-file /srv/music/runtime.env build storage
   docker compose --env-file /srv/music/runtime.env up -d --wait db storage
   ```

3. Если bucket создаёт приложение, инициализировать его отдельным процессом:

   ```bash
   docker compose --env-file /srv/music/runtime.env pull app storage-init
   docker compose --env-file /srv/music/runtime.env run --rm --no-deps storage-init
   ```

   При внешнем S3 bucket можно подготовить средствами провайдера и ограничить
   доступ приложения чтением/записью объектов. Тогда `storage-init` не запускать.
4. Развернуть опубликованный образ:

   ```bash
   scripts/deploy.sh /srv/music/runtime.env ghcr.io/alexkorobitsyn/locals@sha256:<digest>
   ```

   Вместо `<digest>` подставить реальное значение. Скрипт скачивает образ,
   запускает Alembic отдельным процессом, поднимает приложение без сборки,
   ждёт readiness и проверяет версию внутри работающего контейнера.
5. Проверить публичный HTTPS `/api/v1/health/ready`, login/logout, каталог,
   рекомендации, upload и браузерное воспроизведение через S3. Затем открыть трафик.

Команды с placeholders — шаблоны, а не готовые идентификаторы релиза.
Переменные не передаются через shell `source`, Compose читает env-файл сам.
Скрипт не меняет env-файл и требует digest; фиксировать выбранный `APP_IMAGE`
в конфигурации релиза нужно отдельно, чтобы последующие ручные команды также
использовали эту версию.

## Обновление и восстановление

Перед изменением схемы иметь проверенную резервную копию PostgreSQL и план
восстановления объектов S3/MinIO. На первом небольшом развёртывании обеспечить
окно обслуживания, если миграция несовместима с работающей версией.
Сначала проверить миграцию на staging с копией структуры/реалистичных данных,
затем применить на production тот же digest через `scripts/deploy.sh`.

Скрипт останавливается при ошибке миграции, новый API не запускается. При
неуспешной readiness старый образ можно развернуть повторно **только** если
схема совместима с ним. Автоматический `alembic downgrade` на production
не выполнять: он может удалить данные. Несовместимую миграцию исправлять
последующей миграцией или восстанавливать БД согласно заранее проверенному плану.

`docker compose down` сохраняет volumes; `down -v` удаляет их.
Бэкапы хранить вне этих volumes и проверять восстановление.
Readiness сейчас проверяет PostgreSQL. Доступность S3 контролировать отдельно
реальными upload/playback и мониторингом провайдера: отказ S3 влияет на медиа,
но не должен останавливать чтение музыкального каталога.

## Проверки локально

```bash
python -m pip install -r requirements-dev.txt
python -m pip check
ruff check --isolated --select E4,E7,E9,F,I APP alembic scripts tests
ruff format --check APP alembic scripts tests
python -m scripts.check_migrations
python -m pytest -q --strict-markers
```

Для последних двух команд задать `TEST_DATABASE_URL`. Проверка миграций
создаёт и удаляет только собственную схему со случайным именем; приложение
и production schema не затрагиваются. Для проверки настоящего S3 также задать
`TEST_S3_ENDPOINT_URL`, `TEST_S3_ACCESS_KEY`, `TEST_S3_SECRET_KEY`, `TEST_S3_BUCKET`.
В CI эти ресурсы одноразовые и полный набор integration-проверок обязателен.

Кэш результатов рекомендаций и workers в этой версии не добавлены. Конкретное
основание для следующего шага — измеренное время SQL, долгие операции обработки
аудио или объём повторных запросов; критерии обсуждаются в recommendations.md.
