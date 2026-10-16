# ДЗ: JSON-логи Locals в VictoriaLogs и оба бонуса

Все команды выполняются из корня репозитория. Приложение из первого ДЗ должно
быть развёрнуто по [инструкции Minikube](../README.md). Основная часть —
шаги 1–7; оба бонуса — шаг 8. Cert-manager и Ingress не требуются.

## Что готово и что ещё необходимо

| Требование | Подготовлено в проекте | Проверка 16.10.2026 |
| --- | --- | --- |
| VictoriaLogs single-node | Chart `0.13.10`, одна реплика, PVC 10 GiB, retention 7 дней | Ready, Bound, vmui доступен |
| JSON в stdout | Formatter FastAPI с `service.name`, JSON access-логи Nginx | Записи работающего приложения проверены |
| Доставка логов | Chart collector `0.3.8`, DaemonSet vlagent, внутренний адрес VictoriaLogs | Новые записи найдены в VictoriaLogs |
| Четыре LogsQL-запроса | Запросы ниже и отчёт | Выполнены; четыре скриншота приложены |
| Артефакты | Values, инструкция, отчёт и восемь скриншотов | Подготовлены; отправка выполняется отдельно |
| Бонус Grafana | Chart `14.0.0`, плагин `0.32.0`, datasource и dashboard | Datasource OK, панели возвращают данные |
| Бонус vmalert | Chart `0.51.0`, правило LogsQL и Alertmanager | Firing и приём Alertmanager подтверждены |

При проверке **16.10.2026** существующий профиль Minikube запущен с
сохранёнными данными; оба бонуса развёрнуты и проверены в работающем кластере.
Скриншоты и результаты относятся к этому запуску. Для новой демонстрации
повтори тестовые HTTP-запросы, чтобы они попали в выбранное временное окно.

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
- [Отчёт.md](Отчёт.md): запросы, объяснения и реальные скриншоты.
- [grafana-values.yaml](grafana-values.yaml) и [grafana-dashboard.yaml](grafana-dashboard.yaml):
  Grafana, официальный плагин, datasource и готовый dashboard Locals.
- [vmalert-values.yaml](vmalert-values.yaml): vmalert, правило и Alertmanager.
- [deploy-bonuses.sh](deploy-bonuses.sh): установка обоих бонусов в `monitoring`.

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

1. Основные скриншоты `01-raw.png`, `02-filter.png`, `03-stats.png`,
   `04-top.png` уже находятся в `k8s/logging/screenshots/`.
2. В [Отчёт.md](Отчёт.md) приложены изображения и отмечены выполненные
   проверки. При повторной демонстрации обнови скриншоты и дату по результатам.
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

## 8. Оба бонуса: Grafana и vmalert

### Установка

После основной части выполни:

```bash
./k8s/logging/deploy-bonuses.sh
```

Скрипт проверяет готовность VictoriaLogs, создаёт namespace `monitoring`,
применяет ConfigMap dashboard и устанавливает два Helm release:

| Release | Chart | Версия | Что запускается |
| --- | --- | --- | --- |
| `grafana` | `grafana` из grafana-community | `14.0.0` | Grafana с PVC 1 GiB |
| `locals-alerts` | `victoria-metrics-alert` | `0.51.0` | vmalert и Alertmanager с PVC 128 MiB |

Используются HTTPS-репозитории Helm. Это также позволяет не зависеть от
OCI credential helper Docker Desktop при загрузке chart. Повторный запуск
обновляет существующие release. Пароль администратора Grafana генерирует
chart и хранит в Secret; в values пароля нет. Для скачивания образов и
плагина нужен доступ к Интернету.

Проверка:

```bash
helm list -n monitoring
kubectl -n monitoring get pods,services,pvc
kubectl -n monitoring logs deployment/vmalert --tail=20
```

### Grafana и официальный плагин

В отдельном терминале:

```bash
kubectl -n monitoring port-forward service/grafana 13000:80
```

Открой <http://localhost:13000>. Логин `admin`. Пароль посмотри локально:

```bash
kubectl -n monitoring get secret grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

Не включай пароль и Secret в отчёт или скриншоты.

Плагин `victoriametrics-logs-datasource` версии `0.32.0` устанавливается
синхронно перед запуском Grafana. Datasource **VictoriaLogs** с постоянным
UID `locals-victorialogs` создаётся автоматически через provisioning.
Его URL — внутренний Service VictoriaLogs, а не localhost браузера.

В Connections → Data sources → VictoriaLogs нажми **Test**
(в других версиях интерфейса — **Save & test**).
Затем открой Dashboards → Locals → **Locals — VictoriaLogs**, либо:
<http://localhost:13000/d/locals-logs>.

Dashboard содержит свежие HTTP-логи, число 404 за пять минут, p95 в
миллисекундах и количество записей по сервису/уровню. В Explore можно
выполнять запросы из основной части отчёта с этим datasource.
Скриншоты для бонуса: datasource с успешной проверкой и dashboard с данными.

### vmalert: правило и проверка срабатывания

Правило **LocalsTooMany404** использует дополнительный запрос из отчёта:

```text
_time:5m kubernetes.pod_namespace:="locals" logger:="APP.http" status:="404"
| stats count() as not_found
| filter not_found:>2
```

Тип группы — `vlogs`: это LogsQL, не PromQL. Проверка выполняется каждые
15 секунд, окно — пять минут. При трёх или более 404 условие должно
оставаться истинным 30 секунд: сначала Pending, затем Firing.
Считаются только записи FastAPI, поэтому Nginx не удваивает счётчик.
Метка сервиса постоянная: значения счётчика и request ID не включаются
в labels и не сбрасывают таймер `for` при каждом запросе.

В двух отдельных терминалах:

```bash
kubectl -n monitoring port-forward service/vmalert 18880:8880
```

```bash
kubectl -n monitoring port-forward service/alertmanager 19093:9093
```

Открой <http://localhost:18880/vmalert/> и <http://localhost:19093>.
При работающем frontend port-forward создай события:

```bash
for attempt in 1 2 3; do
  curl -sS -o /dev/null -w '%{http_code}\n' \
    http://localhost:8080/api/v1/logs-demo-missing
done
```

Примерно в течение минуты после доставки записей алерт должен перейти
в Firing и появиться в Alertmanager. Проверь и через API:

```bash
curl -fsS http://localhost:18880/api/v1/alerts
curl -fsS http://localhost:19093/api/v2/alerts
```

После прекращения таких запросов условие исчезнет, когда 404 выйдут из
пятиминутного окна; на следующей оценке алерт будет разрешён. Для отправки
resolved-состояния и обновления UI также требуется немного времени.

Alertmanager принимает алерт и показывает его в UI. Receiver `local-ui`
не отправляет сообщения в почту, Telegram или другие внешние системы.
Отдельная VictoriaMetrics для метрик здесь не нужна: recording rules не
используются, состояние таймера vmalert хранится в памяти и после его
перезапуска начинается заново. PVC Alertmanager сохраняет его собственное
состояние, но не таймер `for` vmalert.

Это учебный алерт по 404 с безопасным способом воспроизведения. Для
эксплуатации полезно отдельно настроить пороги по 5xx и задержкам.
Сохрани реальные скриншоты vmalert с Firing и Alertmanager с этим алертом.

### Обновление dashboard и правил

После изменения файлов повтори `deploy-bonuses.sh`. Чтобы Grafana перечитала
изменённый ConfigMap dashboard, явно перезапусти её:

```bash
kubectl -n monitoring rollout restart deployment/grafana
kubectl -n monitoring rollout status deployment/grafana --timeout=180s
```

Параметры и правило vmalert обновляются Helm chart. В отчёт и архив включи
все values, namespace, dashboard ConfigMap, скрипт и скриншоты из этой папки.

## Источники

- [VictoriaLogs single Helm chart](https://docs.victoriametrics.com/helm/victoria-logs-single/)
- [Collector Helm chart](https://docs.victoriametrics.com/helm/victoria-logs-collector/)
- [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/)
- [vmui](https://docs.victoriametrics.com/victorialogs/querying/#web-ui)
- [Официальный VictoriaLogs datasource](https://docs.victoriametrics.com/victorialogs/integrations/grafana/)
- [Grafana Helm chart](https://grafana.com/docs/grafana/latest/setup-grafana/installation/helm/)
- [Алерты LogsQL через vmalert](https://docs.victoriametrics.com/victorialogs/vmalert/)
