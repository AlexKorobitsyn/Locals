# ДЗ: JSON-логи Locals в VictoriaLogs — без бонусов

Все команды выполняются из корня репозитория. Приложение из первого ДЗ должно
быть развёрнуто по [инструкции Minikube](../README.md). Grafana, vmalert,
cert-manager и Ingress для этой работы не требуются.

## Что готово и что ещё необходимо

| Требование | Подготовлено в проекте | Что подтвердить перед сдачей |
| --- | --- | --- |
| VictoriaLogs single-node | Chart `0.13.10`, одна реплика, PVC 10 GiB, retention 7 дней | Pod Ready, PVC Bound, доступ к vmui |
| JSON в stdout | Formatter FastAPI с `service.name`, JSON access-логи Nginx | Пересобрать образы и проверить реальные записи |
| Доставка логов | Chart collector `0.3.8`, DaemonSet vlagent, внутренний адрес VictoriaLogs | Найти новую запись приложения в VictoriaLogs |
| Четыре LogsQL-запроса | Готовые запросы ниже и черновик отчёта | Выполнить в vmui, приложить четыре скриншота |
| Артефакты | Values, инструкция, черновик `Отчёт.md` | Добавить скриншоты и отправить архив либо ссылку на коммит |

При проверке **15.10.2026** API Minikube был недоступен, а Docker Desktop
сообщал об отключённой интеграции с WSL. Поэтому текущие образы и доставку
после последних изменений подтвердить не удалось. Успешный Helm render
или локальный тест не заменяет проверку работающего кластера.

## Файлы и схема доставки

- [victoria-logs-single-values.yaml](victoria-logs-single-values.yaml):
  StatefulSet VictoriaLogs, Service и постоянное хранилище.
- [victorialogs-collector-values.yaml](victorialogs-collector-values.yaml):
  адрес получателя, поля сообщения, ресурсы и ограничение буфера до 1 GB.
- [logging.py](../../APP/core/logging.py): JSON formatter и stdout handler.
- [request_logging.py](../../APP/core/request_logging.py): HTTP-поля,
  длительность, request ID и изоляция контекста параллельных запросов.
- [__main__.py](../../APP/__main__.py): подключение HTTP middleware.
- [default.conf.template](../../frontend/nginx/default.conf.template):
  JSON access-логи Nginx и передача `X-Request-ID` в FastAPI.
- [Отчёт.md](Отчёт.md): черновик с запросами и местами для скриншотов.

```text
FastAPI / Nginx → stdout контейнера → файлы логов узла
  → vlagent (DaemonSet) → Service VictoriaLogs:9428 → PVC
                                             ↘ vmui через port-forward
```

DaemonSet запускает collector на каждом узле; в однонодовом Minikube это один
Pod. Он читает файлы контейнеров, разбирает JSON, добавляет Kubernetes-поля
и отправляет данные через native endpoint `/insert/native`. При временной
недоступности получателя использует дисковый буфер. База логов хранится на PVC,
а буфер collector — на узле: это разные хранилища.

FastAPI пишет `timestamp`, `level`, `message`, `service.name`, `logger`.
HTTP-записи дополнительно содержат `request_id`, `method`, `path`, `status`,
`duration_ms`, `response_completed`. Nginx пишет access-логи в JSON с
`duration_sec` **в секундах**, FastAPI — с `duration_ms` **в миллисекундах**.
Служебные startup/error-сообщения Nginx могут оставаться текстовыми;
JSON-настройка `log_format` относится к access-логам.

В VictoriaLogs `timestamp` используется как `_time`, `message` — как `_msg`.
Их отсутствие под исходными именами в результатах не означает потерю данных.

## 1. Восстановить доступ к кластеру

```bash
docker version
minikube status
kubectl config use-context minikube
kubectl get nodes
```

Если Docker выводит сообщение о WSL integration: запусти Docker Desktop
в Windows, включи Settings → Resources → WSL Integration для своей Linux
системы и заново открой терминал. Продолжай, когда `docker version`
показывает Client и Server.

Если Minikube остановлен, запусти существующий профиль:

```bash
minikube start -p minikube
kubectl get nodes
kubectl -n locals get pods,services
```

Если приложение ещё не развёрнуто, сначала выполни первый запуск из
`k8s/README.md`. Удаление кластера или namespace для продолжения не нужно.

## 2. Обновить образы с новым логированием

Для существующего Minikube с Docker runtime:

```bash
eval "$(minikube docker-env)"
docker build -t locals-backend:k8s .
docker build -t locals-frontend:k8s frontend
eval "$(minikube docker-env -u)"

kubectl apply -f k8s/01-configmap.yaml
kubectl -n locals rollout restart deployment/app deployment/frontend
kubectl -n locals rollout status deployment/app --timeout=180s
kubectl -n locals rollout status deployment/frontend --timeout=180s
```

Сборка идёт непосредственно в Docker Minikube; дополнительный image load
для этих образов не нужен. Deployment используют `imagePullPolicy: Never`.
Повторная сборка с прежним тегом требует restart: уже запущенные контейнеры
сами не обновятся. PostgreSQL, MinIO и миграции ради изменения логов
пересобирать или повторно запускать не требуется.

## 3. Установить или обновить VictoriaLogs и collector

```bash
helm upgrade --install victoria-logs-single \
  oci://ghcr.io/victoriametrics/helm-charts/victoria-logs-single \
  --version 0.13.10 \
  --namespace victoria-logs --create-namespace \
  -f k8s/logging/victoria-logs-single-values.yaml \
  --wait --timeout 5m

helm upgrade --install victoria-logs-collector \
  oci://ghcr.io/victoriametrics/helm-charts/victoria-logs-collector \
  --version 0.3.8 \
  --namespace victoria-logs-collector --create-namespace \
  -f k8s/logging/victorialogs-collector-values.yaml \
  --wait --timeout 5m

helm list -A
kubectl -n victoria-logs get pods,services,pvc
kubectl -n victoria-logs-collector get daemonsets,pods
kubectl -n victoria-logs-collector logs daemonset/victoria-logs-collector --tail=30
```

Ожидается: сервер VictoriaLogs Ready, PVC Bound, у collector Desired=Ready=1.
Если Pod Pending, смотри `kubectl describe pod ...` в его namespace:
возможны нехватка ресурсов или невыделенный PVC. При ошибках доставки
проверь Service `victoria-logs-single-server` в namespace `victoria-logs`.

## 4. Открыть приложение и vmui

В первом терминале:

```bash
kubectl -n locals port-forward service/frontend 8080:80
```

Во втором терминале:

```bash
kubectl -n victoria-logs port-forward service/victoria-logs-single-server 19428:9428
```

- Приложение: <http://localhost:8080>.
- vmui: <http://localhost:19428/select/vmui/>.

У VictoriaLogs v1.53.0 UI расположен на `/select/vmui/`; адрес `/vmui/`
из формулировки задания в проверенной ранее установке возвращал 400.
Для отображения аудио и изображений приложения дополнительно потребуется
проброс MinIO из инструкции первого ДЗ; для демонстрации логов он не нужен.

## 5. Создать свежие записи и проверить JSON

В третьем терминале:

```bash
curl -i http://localhost:8080/api/v1/health/version

for attempt in 1 2 3; do
  curl -sS -o /dev/null -w '%{http_code}\n' \
    http://localhost:8080/api/v1/logs-demo-missing
done

kubectl -n locals logs deployment/app --tail=15
kubectl -n locals logs deployment/frontend --tail=15
```

Первый запрос должен вернуть 200 и `X-Request-ID`; остальные — 404.
Ожидаются JSON access-записи обоих сервисов, одинаковый `request_id`
для соответствующего проксированного запроса, числовые `status` и длительность.
Не ищи `duration_ms` в nginx: там поле называется `duration_sec`.

## 6. Выполнить четыре запроса в vmui

Выбери временной диапазон **Last 15 minutes**. Для каждого запроса нажми
Execute Query и сделай отдельный скриншот: текст запроса, диапазон и результат
должны быть видны. Новые поля появятся только у записей из обновлённых образов.

### А. Сырые записи за 15 минут

```text
_time:15m kubernetes.pod_namespace:="locals" kubernetes.container_name:="backend"
```

Показывает записи FastAPI. Раскрой одну строку: `_time`, `_msg`, `level`,
`service.name`, HTTP-поля и Kubernetes-метаданные должны быть видны.

### Б. Фильтр по конкретному полю

```text
_time:15m kubernetes.pod_namespace:="locals" kubernetes.container_name:="backend" status:="404"
```

Показывает ответы 404, созданные на шаге 5. Фильтрация идёт по полю `status`,
а не по наличию числа в тексте сообщения.

### В. Stats с группировкой

```text
_time:15m kubernetes.pod_namespace:="locals" kubernetes.container_name:in(backend,nginx)
| stats by (service.name, level) count() as logs_count
```

Считает записи по сервисам и уровням. Здесь считаются записи логов, а не
уникальные пользовательские запросы: один запрос проходит через оба сервиса.

### Г. Агрегирующий запрос top

```text
_time:15m kubernetes.pod_namespace:="locals" logger:="APP.http"
| top 5 by (path)
```

Показывает пять путей с наибольшим количеством access-записей FastAPI.
Health checks тоже входят в статистику — их регулярно выполняет Kubernetes.

Дополнительно, после появления новых HTTP-полей, можно проверить p95:

```text
_time:15m kubernetes.pod_namespace:="locals" logger:="APP.http" response_completed:="true"
| stats quantile(0.95, duration_ms) as p95_ms
```

Если результатов нет: повтори запросы шага 5, проверь выбранный диапазон,
stdout приложения и логи collector. Если нет `APP.http`, сначала проверь,
что backend действительно пересоздан из нового образа.

## 7. Подготовить сдачу

1. Создай `k8s/logging/screenshots/` и сохрани реальные скриншоты:
   `01-raw.png`, `02-filter.png`, `03-stats.png`, `04-top.png`.
2. В [Отчёт.md](Отчёт.md) добавь ссылки на эти изображения и отметь проверки.
   Замени статус черновика только после фактического выполнения.
3. Приложи эту папку с values и отчётом либо отправь ссылку на коммит/ветку.
   Изменения Python/Nginx также должны быть доступны в исходном коде.
4. Проверь, что в сдачу не попали `.env` и реальные Kubernetes Secrets.

Перед отправкой удобно проверить файлы:

```bash
git status --short
git diff --check
```

README без четырёх реальных скриншотов не заменяет обязательный отчёт.
Видео для этого задания в приведённых требованиях не требуется.

## Источники

- [VictoriaLogs single Helm chart](https://docs.victoriametrics.com/helm/victoria-logs-single/)
- [Collector Helm chart](https://docs.victoriametrics.com/helm/victoria-logs-collector/)
- [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/)
- [vmui](https://docs.victoriametrics.com/victorialogs/querying/#web-ui)
