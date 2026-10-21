# Locals в minikube

## Установка и сборка

В моём окружении уже установлены minikube и kubectl. В вашем не знаю, но на всякий случай:
Значения средние, думаю у вас минимум 8гб есть
скрипт для создания секретов также прилагается 
```bash
mkdir -p "$HOME/.local/bin"
curl -fL https://storage.googleapis.com/minikube/releases/v1.39.0/minikube-linux-amd64 -o "$HOME/.local/bin/minikube"
curl -fL https://dl.k8s.io/release/v1.37.1/bin/linux/amd64/kubectl -o "$HOME/.local/bin/kubectl"
chmod +x "$HOME/.local/bin/minikube" "$HOME/.local/bin/kubectl"
export PATH="$HOME/.local/bin:$PATH"
docker version
minikube start --driver=docker --container-runtime=docker --cpus=2 --memory=4096 --nodes=1
kubectl config use-context minikube
kubectl get nodes
eval "$(minikube docker-env)"
docker build -t locals-backend:k8s .
docker build -t locals-frontend:k8s frontend
docker build -f docker/minio.Dockerfile -t locals-minio:k8s .
docker save locals-backend:k8s locals-frontend:k8s locals-minio:k8s -o /tmp/locals-k8s-images.tar
minikube image load /tmp/locals-k8s-images.tar
eval "$(minikube docker-env -u)"
```

## Первый запуск приложения
поэтапно

```bash
python3 k8s/create_secret.py
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml -f k8s/02-secret.yaml
kubectl apply -f k8s/03-postgres.yaml -f k8s/04-storage.yaml
kubectl -n locals rollout status statefulset/db --timeout=180s
kubectl -n locals rollout status statefulset/storage --timeout=180s
kubectl apply -f k8s/05-jobs.yaml
kubectl -n locals wait --for=condition=complete job/migrate job/storage-init --timeout=180s
kubectl apply -f k8s/06-backend.yaml -f k8s/07-frontend.yaml
kubectl -n locals rollout status deployment/app --timeout=180s
kubectl -n locals rollout status deployment/frontend --timeout=180s
kubectl -n locals get pods,services,pvc,jobs
```

В двух терминалах оставьте работающими:

```bash
kubectl -n locals port-forward service/frontend 8080:80
```

```bash
kubectl -n locals port-forward service/storage 9000:9000
```

Сайт: http://localhost:8080. API: http://localhost:8080/api/v1/docs. Второй туннель нужен для изображений и аудио(9000).

Зарегистрируйтесь в UI. Администратор создаётся отдельно:

```bash
kubectl -n locals exec -it deployment/app -- python -m APP.create_admin --email admin@example.com --display-name "Администратор"
```
Введите пароль(придумайте). После входа администратором можно заполнить города и жанры. Музыку публиковать может любой человек став артистом.

## Масштабирование

```bash
kubectl -n locals scale deployment/app --replicas=3
kubectl -n locals scale deployment/frontend --replicas=2
kubectl -n locals rollout status deployment/app --timeout=180s
kubectl -n locals rollout status deployment/frontend --timeout=180s
kubectl -n locals get deployments,pods
kubectl -n locals get endpointslices -l kubernetes.io/service-name=app
```
## Удаление для вас
если вам не нужны данные(музыка и т.д.), (они вам не нужны) удалить
```bash
kubectl delete namespace locals
```
остановка
```bash
kubectl -n locals scale deployment/app deployment/frontend --replicas=0
kubectl -n locals scale statefulset/db statefulset/storage --replicas=0

```


..................................................
## Что делает каждый файл

### `00-namespace.yaml`

Создаёт Namespace `locals`, отделяет Locals от системных подов и других проектов. Все остальные манифесты ссылаются на неё. 

### `01-configmap.yaml`

Создаёт ConfigMap `locals-config` с несекретными параметрами. 

### `02-secret.yaml.example` и `create_secret.py`

Шаблон описывает Secret `locals-secret`. Python-скрипт создаёт `02-secret.yaml` со случайными значениями.

### `03-postgres.yaml`

 Service `db` и StatefulSet PostgreSQL с одной репликой. Headless Service clusterIP: None даёт DNS наименование для обращения. `data-db-0` на 5 GiB.

### `04-storage.yaml`

Содержит Service `storage` с портами S3 9000 и консоли 9001, StatefulSet MinIO и PVC `data-storage-0` на 5 GiB.

### `05-jobs.yaml`

Создаёт два Job из backend-образа. "migrate" выполняет `alembic upgrade head`, `storage-init` - `python -m APP.storage_init`, создавая bucket и CORS где нужно.

### `06-backend.yaml`

Создаёт Service app с постоянным ClusterIP и Deployment FastAPI. Контейнер слушает 8000, конфигурация и секреты передаются через envFrom.

### `07-frontend.yaml`

Создаёт Service frontend на порту 80 и Deployment Nginx на порту 8080. Nginc проксирует к /api/ к service app, адрес backend пода не обязателен для браузера, ConfigMap задаёт адрес API, лимиты загрузки и параметры /config.json без пересборки frontend.



