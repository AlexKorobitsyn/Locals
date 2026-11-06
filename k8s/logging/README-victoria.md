# Логи Locals в minikube

Я настроил JSON-логи FastAPI и Nginx, сбор через collector в VictoriaLogs, Grafana и алерт через vmalert с Alertmanager. Команды выполнял из корня проекта в Ubuntu WSL. Docker Desktop должен быть включён, minikube и kubectl установлены по [инструкции](../README.md).

## Подготовка

```bash
export PATH="$HOME/.local/bin:$PATH"
docker version
minikube start -p minikube --driver=docker --container-runtime=docker --cpus=2 --memory=4096
kubectl config use-context minikube
kubectl get nodes
```

Helm установил в домашний каталог. Если уже установлен, этот блок можно пропустит:

```bash
mkdir -p "$HOME/.local/bin"
curl -fL --retry 5 --retry-all-errors https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 -o /tmp/locals-get-helm.sh &&
HELM_INSTALL_DIR="$HOME/.local/bin" bash /tmp/locals-get-helm.sh --version v4.3.1 --no-sudo
helm version --short
```

## Приложение

Собрал образы с JSON-логами и развернул Locals.

```bash
eval "$(minikube docker-env)"
docker build -t locals-backend:k8s .
docker build -t locals-frontend:k8s frontend
docker build -f docker/minio.Dockerfile -t locals-minio:k8s .
eval "$(minikube docker-env -u)"
python3 k8s/create_secret.py
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml -f k8s/02-secret.yaml
kubectl apply -f k8s/03-postgres.yaml -f k8s/04-storage.yaml
kubectl -n locals rollout status statefulset/db --timeout=180s
kubectl -n locals rollout status statefulset/storage --timeout=180s
kubectl apply -f k8s/05-jobs.yaml
kubectl -n locals wait --for=condition=complete job/migrate job/storage-init --timeout=180s
kubectl apply -f k8s/06-backend.yaml -f k8s/07-frontend.yaml
kubectl -n locals rollout restart deployment/app deployment/frontend
kubectl -n locals rollout status deployment/app --timeout=180s
kubectl -n locals rollout status deployment/frontend --timeout=180s
```

## VictoriaLogs, collector, Grafana и vmalert

```bash
helm upgrade --install victoria-logs-single victoria-logs-single \
  --repo https://victoriametrics.github.io/helm-charts/ --version 0.13.10 \
  --namespace victoria-logs --create-namespace -f k8s/logging/victoria-logs-single-values.yaml --wait --timeout 5m
helm upgrade --install victoria-logs-collector victoria-logs-collector \
  --repo https://victoriametrics.github.io/helm-charts/ --version 0.3.8 \
  --namespace victoria-logs-collector --create-namespace -f k8s/logging/victorialogs-collector-values.yaml --wait --timeout 5m
bash k8s/logging/deploy-bonuses.sh
helm list -A
kubectl -n locals get pods,services
kubectl -n victoria-logs get pods,services,pvc
kubectl -n victoria-logs-collector get daemonsets,pods
kubectl -n monitoring get deployments,pods,services,pvc
```

Скрипт устанавливает Grafana с datasource и dashboard, vmalert и Alertmanager. Ожидаю Ready у подов, Bound у PVC; Job приложения могут быть Completed.

## Доступ из браузера

Каждую команду оставил работать в отдельном терминале.

```bash
kubectl -n locals port-forward service/frontend 8080:80
```

```bash
kubectl -n locals port-forward service/storage 9000:9000
```

```bash
kubectl -n victoria-logs port-forward service/victoria-logs-single-server 19428:9428
```

```bash
kubectl -n monitoring port-forward service/grafana 13000:80
```

```bash
kubectl -n monitoring port-forward service/vmalert 18880:8880
```

```bash
kubectl -n monitoring port-forward service/alertmanager 19093:9093
```

| Сервис | Адрес |
| Locals | http://localhost:8080 |
| VictoriaLogs, vmui | http://localhost:19428/select/vmui/ |
| Grafana, dashboard | http://localhost:13000/d/locals-logs |
| vmalert, правила | http://localhost:18880/vmalert/groups |
| vmalert, алерты | http://localhost:18880/vmalert/alerts |
| Alertmanager | http://localhost:19093 |

В Grafana логин `admin`, пароль получить можно командой:

```bash
kubectl -n monitoring get secret grafana -o jsonpath='{.data.admin-password}' | base64 --decode
```

## Проверка логов и алерта

Создал успешный запрос и три ответа 404:

```bash
curl -i http://localhost:8080/api/v1/health/version
for attempt in 1 2 3; do
  curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:8080/api/v1/logs-demo-missing
done
kubectl -n locals logs deployment/app --tail=15
kubectl -n locals logs deployment/frontend --tail=15
```

В vmui выполнил четыре запроса из отчёта диапазон Last 15 minutes. Алерт `LocalsTooMany404` срабатывает при трёх 404 за 5 минут.

```bash
curl -fsS http://localhost:18880/api/v1/alerts
curl -fsS http://localhost:19093/api/v2/alerts
```

VictoriaMetrics:

```bash
helm upgrade --install vmsingle victoria-metrics-single --repo https://victoriametrics.github.io/helm-charts/ --version 0.49.0 -n monitoring --create-namespace -f guide-vmsingle-values.yaml --wait
```

```bash
kubectl -n monitoring port-forward svc/vmsingle-victoria-metrics-single-server 8428:8428
```

Как проверить?:

```bash
python3 scripts/check_metrics.py
```

VictoriaMetrics работает в `monitoring`, приложение и PostgreSQL — в `locals`. Адрес datasource Grafana: `http://vmsingle-victoria-metrics-single-server.monitoring.svc.cluster.local:8428`. После переноса VictoriaMetrics 06.11.2026 собирается новая история; прежняя история не импортируется. Старый port-forward нужно остановить и запустить приведённую выше команду заново.

В `guide-vmsingle-values.yaml` оставлен фильтр `default;kubernetes;https`: он выбирает сервис Kubernetes API, который находится в namespace `default`, и не задаёт namespace VictoriaMetrics.
