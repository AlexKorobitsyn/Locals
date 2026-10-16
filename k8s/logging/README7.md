# Повторение демонстрации: vmui, Grafana и алерт 404

Это сценарий повторения восьми скриншотов из [отчёта](Отчёт.md).
Он использует уже установленные сервисы. Установка и обновление описаны
в [README6.md](README6.md).

Порядок: проверить кластер → открыть пять туннелей → проверить Grafana →
вызвать три HTTP 404 → увидеть Firing и Alertmanager → выполнить четыре
запроса vmui → дождаться автоматического снятия алерта.

## 1. Проверить готовность

В рабочем терминале перейди в проект:

```bash
cd /home/switch2001/network/sre/Locals
docker version
minikube status
kubectl config use-context minikube
```

Если профиль остановлен, запусти существующий:

```bash
minikube start -p minikube
```

Проверь сервисы:

```bash
kubectl -n locals get pods,services
kubectl -n victoria-logs get pods,services,pvc
kubectl -n victoria-logs-collector get daemonsets,pods
kubectl -n monitoring get deployments,pods,services,pvc
helm list -A
```

Ожидается:

- FastAPI `app`, Nginx `frontend`, PostgreSQL `db` и MinIO `storage` работают.
- VictoriaLogs Ready; её PVC имеет статус `Bound`.
- У collector в Minikube `DESIRED=1` и `READY=1`.
- В `monitoring` работают `grafana`, `vmalert`, `alertmanager`, их Pod Ready.
- Job `migrate` и `storage-init` могут быть `Completed` — это нормально.

После запуска Minikube дай DNS и приложениям восстановиться. Готовность
бонусных сервисов можно дождаться командами:

```bash
kubectl -n monitoring rollout status deployment/grafana --timeout=180s
kubectl -n monitoring rollout status deployment/vmalert --timeout=180s
kubectl -n monitoring rollout status deployment/alertmanager --timeout=180s
```

Если бонусные release ещё не установлены, при работающем VictoriaLogs выполни:

```bash
./k8s/logging/deploy-bonuses.sh
```

При `connection refused` от Kubernetes сначала восстанови Minikube.
Если `docker version` не показывает Server, запусти Docker Desktop и проверь
WSL Integration для своей Linux-системы.

## 2. Открыть доступ из браузера

Оставь пять команд работающими, **каждую в отдельной вкладке терминала**.
Ещё один терминал понадобится для `curl` и остальных команд.

**Терминал 1 — приложение:**

```bash
kubectl -n locals port-forward service/frontend 8080:80
```

**Терминал 2 — VictoriaLogs и vmui:**

```bash
kubectl -n victoria-logs port-forward service/victoria-logs-single-server 19428:9428
```

**Терминал 3 — Grafana:**

```bash
kubectl -n monitoring port-forward service/grafana 13000:80
```

**Терминал 4 — vmalert:**

```bash
kubectl -n monitoring port-forward service/vmalert 18880:8880
```

**Терминал 5 — Alertmanager:**

```bash
kubectl -n monitoring port-forward service/alertmanager 19093:9093
```

| Что открыть | URL |
| --- | --- |
| Приложение | <http://localhost:8080> |
| vmui | <http://localhost:19428/select/vmui/> |
| Вход в Grafana | <http://localhost:13000> |
| Dashboard Locals | <http://localhost:13000/d/locals-logs> |
| Правила vmalert | <http://localhost:18880/vmalert/groups> |
| Активные алерты vmalert | <http://localhost:18880/vmalert/alerts> |
| Alertmanager | <http://localhost:19093> |

Port-forward должен показывать `Forwarding from ...`. При закрытии
терминала туннель прекращает работать. После пересоздания Pod туннель
также может потребовать повторного запуска.

Если порт занят, проверь, не работает ли уже прежний port-forward.
Дополнительный проброс MinIO нужен для медиа приложения, но в этом сценарии
проверяются HTTP-запросы и логи, поэтому он не требуется.

## 3. Войти в Grafana и повторить скриншот datasource

Открой <http://localhost:13000>. Логин — **admin**.
В рабочем терминале получи пароль:

```bash
kubectl -n monitoring get secret grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

Скопируй только пароль, без приглашения терминала. Это отдельная учётная
запись Grafana; пароль от аккаунта администратора музыкального сервиса
здесь не используется. Пароль и вывод Secret не включай в скриншоты.

После входа:

1. Открой **Connections → Data sources → VictoriaLogs**.
2. Убедись, что указан тип **VictoriaLogs**, версия плагина `0.32.0`.
3. Внизу нажми **Test**. В других версиях кнопка может называться Save & test.
4. Дождись зелёного сообщения **Data source is working**.
5. Сделай скриншот, как [05-grafana-datasource.png](screenshots/05-grafana-datasource.png).

Сообщение **Provisioned data source** нормально: источник создан из
`grafana-values.yaml`, его настройки управляются конфигурацией.

## 4. Посмотреть dashboard Grafana

Открой **Dashboards → Locals → Locals — VictoriaLogs** или прямой адрес:
<http://localhost:13000/d/locals-logs>.

Выбери **Last 15 minutes** и нажми **Refresh**. Есть четыре панели:

| Панель | Что показывает |
| --- | --- |
| HTTP-запросы FastAPI | Записи `APP.http` из VictoriaLogs |
| Ответы 404 за пять минут | Число записей с `status=404`; порог алерта — 3 |
| p95 времени HTTP-ответа | 95-й перцентиль `duration_ms`, в миллисекундах |
| Количество записей по сервису и уровню | Распределение записей backend/frontend |

До теста счётчик 404 может быть **0**, а алерт — **Inactive**. Это здоровое
исходное состояние. Если ты недавно уже вызывал 404, счётчик может быть
больше нуля; для чистого повторения дождись пяти минут после последнего
такого запроса. Значения на dashboard меняются вместе с временным окном.

Ниже создадим 404, после чего вернёмся сюда для скриншота dashboard.

## 5. Вызвать три настоящих HTTP 404

Сначала проверь успешный запрос:

```bash
curl -i http://localhost:8080/api/v1/health/version
```

Ожидается `200 OK` и заголовок `X-Request-ID`.

Затем выполни:

```bash
for attempt in 1 2 3; do
  curl -sS -o /dev/null -w '%{http_code}\n' \
    http://localhost:8080/api/v1/logs-demo-missing
done
```

Ожидаемый вывод:

```text
404
404
404
```

Маршрута `/api/v1/logs-demo-missing` в FastAPI нет. Nginx проксирует запрос,
FastAPI возвращает 404, middleware пишет JSON с `logger=APP.http` и
`status=404`. Collector отправляет запись в VictoriaLogs. Эти GET-запросы
не создают данные в БД.

Именно API-префикс здесь важен: произвольная страница frontend может
возвращать `index.html` со статусом 200 из-за настройки SPA.

Проверь stdout:

```bash
kubectl -n locals logs deployment/app --tail=20
```

У соответствующих HTTP-записей должны быть `status: 404`, `request_id`,
`path`, `duration_ms`. В VictoriaLogs значения этих полей могут
отображаться строками — например, `"status":"404"`.

## 6. Увидеть Pending → Firing и получение алерта

Открой <http://localhost:18880/vmalert/groups>.
Нажми **Expand All**, чтобы раскрыть группу `locals-log-alerts` и правило
**LocalsTooMany404**. Состояние проверки должно быть здоровым, без last error.

Для наблюдения за активным алертом открой:
<http://localhost:18880/vmalert/alerts> и также нажми **Expand All**.
Обновляй страницу примерно каждые 10–15 секунд.

Правило выполняет запрос:

```text
_time:5m kubernetes.pod_namespace:="locals" logger:="APP.http" status:="404"
| stats count() as not_found
| filter not_found:>2
```

Последовательность:

1. В пятиминутном окне появляются минимум три записи 404.
2. На очередной оценке правило становится **Pending**.
3. Если условие сохраняется 30 секунд, правило становится **Firing**.
4. vmalert отправляет алерт в Alertmanager.

Оценка идёт каждые 15 секунд с задержкой данных 5 секунд. Ожидай примерно
минуту после доставки логов; переход может произойти чуть позже из-за
времени сбора и обработки. Pending можно пропустить между обновлениями
страницы — Firing после него является ожидаемым результатом.

На странице активного алерта должны быть:

- имя `LocalsTooMany404`;
- состояние `firing`;
- значение не меньше 3;
- метки `service=locals-backend`, `severity=warning`.

Сделай скриншот, как [07-vmalert-firing.png](screenshots/07-vmalert-firing.png).

Теперь открой <http://localhost:19093>. Обнови страницу и при необходимости
нажми **Expand all groups**. Должен появиться `LocalsTooMany404` у receiver
`local-ui`, с меткой `service="locals-backend"`.
Сделай скриншот, как [08-alertmanager.png](screenshots/08-alertmanager.png).

Это подтверждение доставки алерта в Alertmanager. Receiver не отправляет
письма и сообщения в мессенджеры: уведомление видно в локальном UI.

При необходимости проверь состояние через API:

```bash
curl -fsS http://localhost:18880/api/v1/rules | python3 -m json.tool
curl -fsS http://localhost:18880/api/v1/alerts | python3 -m json.tool
curl -fsS http://localhost:19093/api/v2/alerts | python3 -m json.tool
```

В первом ответе проверяй `health: "ok"` и пустой `lastError`.
Во втором у активного алерта будет `state: "firing"`, в третьем —
`status.state: "active"`.

Вернись в dashboard Grafana и нажми **Refresh**. Счётчик 404 должен быть
не меньше 3. Сделай скриншот, как
[06-grafana-dashboard.png](screenshots/06-grafana-dashboard.png).

## 7. Повторить четыре скриншота vmui

Открой <http://localhost:19428/select/vmui/>. У этой установки рабочий
путь именно `/select/vmui/`.

Для каждого запроса:

1. Вставь запрос в поле **Query**.
2. Нажми **Execute** и дождись результата.
3. Выбери вкладку **JSON** под графиком: на скриншотах использовалась она.
4. Сохрани кадр, где видны запрос, диапазон и результаты.

Запросы содержат `_time:15m`. Уведомление **Time range overridden by query
filter** ожидаемо: время задаётся самим запросом. Если используешь ручной
выбор диапазона, выбери Last 15 minutes.

### Скриншот 01 — сырые записи

```text
_time:15m kubernetes.pod_namespace:="locals" kubernetes.container_name:="backend"
```

Ожидаются JSON-записи с `_time`, `_msg`, `level`, `service.name` и
Kubernetes-метаданными. У записей `APP.http` есть HTTP-поля.
Пример: [01-raw.png](screenshots/01-raw.png).

### Скриншот 02 — фильтр по статусу

```text
_time:15m kubernetes.pod_namespace:="locals" kubernetes.container_name:="backend" status:="404"
```

Ожидаются записи запросов к `/api/v1/logs-demo-missing`.
Пример: [02-filter.png](screenshots/02-filter.png).

### Скриншот 03 — группировка и count

```text
_time:15m kubernetes.pod_namespace:="locals" kubernetes.container_name:in(backend,nginx)
| stats by (service.name, level) count() as logs_count
```

Ожидаются строки с сервисом, уровнем и `logs_count`. Строка без имени
сервиса возможна для служебных текстовых startup-логов Nginx.
Пример: [03-stats.png](screenshots/03-stats.png).

### Скриншот 04 — top путей

```text
_time:15m kubernetes.pod_namespace:="locals" logger:="APP.http"
| top 5 by (path)
```

Ожидаются пути и число записей `hits`. Проверки `/health/ready` и
`/health/live` часто лидируют: их вызывает Kubernetes.
Пример: [04-top.png](screenshots/04-top.png).

У агрегированных результатов может не быть `_time` и `_msg` — там
вычисленные поля. Во вкладке Group это иногда выглядит как `timestamp
missing` или пустое сообщение; переключись на JSON, чтобы увидеть значения.

Если цифры отличаются от сохранённых скриншотов, это нормально: данные
живые, probes выполняются постоянно. Повторный запуск цикла `curl` добавляет
ещё три записи, а не обнуляет предыдущие.

## 8. Проверить автоматическое снятие алерта

Прекрати запросы, создающие 404. Обычные health checks и успешные
обращения к приложению можно продолжать.

Дождись чуть больше пяти минут после **последнего** тестового 404:

1. Старые 404 выйдут из окна `_time:5m`.
2. Условие `not_found > 2` станет ложным.
3. На очередной оценке vmalert вернётся в **Inactive**.
4. После обработки resolved-состояния алерт исчезнет из активных
   в Alertmanager. Обнови страницу и фильтры, если отображается старый результат.
5. Счётчик 404 за пять минут в Grafana станет 0 после обновления.

На `/vmalert/alerts` список может стать пустым; само правило останется
на `/vmalert/groups`. В API `/api/v1/rules` ожидается `state: "inactive"`
и `health: "ok"`.

Сырые записи при этом ещё видны в запросе `_time:15m`. Это нормально:
пятиминутное окно алерта и пятнадцатиминутное окно просмотра различаются.

## 9. Если результат не совпал

| Симптом | Что проверить |
| --- | --- |
| Сайт не открывается | Frontend Pod Ready, терминал с `8080:80` работает |
| Вместо 404 получился 502/503 | Готовность backend и PostgreSQL; логи `app` и `frontend` |
| В vmui нет свежих записей | Временное окно, stdout backend и логи collector |
| В логах нет `status` или `APP.http` | Запущен ли backend-образ с новым middleware; обновление описано в README6 |
| Grafana сообщает об ошибке datasource | Доступность VictoriaLogs и внутренний URL в datasource |
| Dashboard пустой | Last 15 minutes, Refresh, свежие запросы и правильный datasource |
| Правило имеет error вместо Pending | `/api/v1/rules`, `lastError` и логи vmalert |
| Firing есть, а Alertmanager пустой | Подожди отправку, проверь фильтры UI и логи обоих сервисов |
| Счётчик больше 3 | В окне сохранились предыдущие или чужие HTTP 404 |
| После перезапуска Grafana браузер завис | Заново запусти её port-forward и обнови страницу |

Команды диагностики:

```bash
kubectl -n locals logs deployment/app --tail=30
kubectl -n locals logs deployment/frontend --tail=30
kubectl -n victoria-logs-collector logs daemonset/victoria-logs-collector --tail=30
kubectl -n monitoring logs deployment/vmalert --tail=30
kubectl -n monitoring logs deployment/alertmanager --tail=30
kubectl -n monitoring logs deployment/grafana --tail=30
```

При пустом результате агрегирующего запроса с `| filter not_found:>2`
причиной может быть просто отсутствие трёх 404. Для проверки самого
счётчика временно убери последний `filter` в поле Query vmui.

## 10. Завершить демонстрацию

Останови port-forward через **Ctrl+C** в пяти терминалах.
Pod, настройки и данные останутся в Minikube. Для остановки самого
профиля после работы:

```bash
minikube stop -p minikube
```

При обновлении материалов сохраняй скриншоты в `screenshots/` и проверь
ссылки в [Отчёт.md](Отчёт.md). Скриншоты не обязаны иметь те же числа,
но должны показывать нужный запрос или состояние системы.
