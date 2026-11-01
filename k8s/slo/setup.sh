set -euo pipefail
slo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$slo_root"
export PATH="$HOME/.local/bin:$PATH"
for slo_tool in docker minikube kubectl helm python3; do
  command -v "$slo_tool" >/dev/null || { echo "Не найден $slo_tool. См. README.md"; exit 1; }
done
docker info >/dev/null
slo_profile=${SLO_PROFILE:-minikube}
minikube start -p "$slo_profile" --driver=docker --container-runtime=docker --cpus=2 --memory=4096
kubectl config use-context "$slo_profile"
eval "$(minikube -p "$slo_profile" docker-env --shell bash)"
docker build -t locals-backend:k8s .
docker build -t locals-frontend:k8s frontend
docker build -f docker/minio.Dockerfile -t locals-minio:k8s .
docker build -f docker/prober.Dockerfile -t locals-prober:k8s .
eval "$(minikube -p "$slo_profile" docker-env --unset --shell bash)"
python3 k8s/create_secret.py
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml -f k8s/02-secret.yaml
kubectl apply -f k8s/03-postgres.yaml -f k8s/04-storage.yaml
kubectl -n locals rollout status statefulset/db --timeout=300s
kubectl -n locals rollout status statefulset/storage --timeout=300s
kubectl -n locals delete job migrate storage-init --ignore-not-found
kubectl apply -f k8s/05-jobs.yaml
kubectl -n locals wait --for=condition=complete job/migrate job/storage-init --timeout=300s
kubectl apply -f k8s/06-backend.yaml -f k8s/07-frontend.yaml
kubectl -n locals rollout restart deployment/app deployment/frontend
kubectl -n locals rollout status deployment/app --timeout=300s
kubectl -n locals rollout status deployment/frontend --timeout=300s
helm upgrade --install vmsingle victoria-metrics-single --repo https://victoriametrics.github.io/helm-charts --version 0.49.0 -n default -f guide-vmsingle-values.yaml --wait --timeout 10m
kubectl apply -f k8s/logging/bonuses-namespace.yaml
kubectl apply -f k8s/slo/grafana-dashboard.yaml
helm upgrade --install grafana grafana --repo https://grafana-community.github.io/helm-charts --version 14.0.0 -n monitoring -f k8s/slo/grafana-values.yaml --wait --timeout 10m
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check prometheus-client==0.26.0
mkdir -p data
slo_forward_pid=''
slo_cleanup() {
  if [[ -n "$slo_forward_pid" ]]; then
    kill "$slo_forward_pid" 2>/dev/null || true
    wait "$slo_forward_pid" 2>/dev/null || true
  fi
}
trap slo_cleanup EXIT
kubectl -n locals port-forward --address=127.0.0.1 svc/frontend 18081:80 > data/prepare-forward.log 2>&1 &
slo_forward_pid=$!
python3 - <<'PY'
import time
import urllib.error
import urllib.request
for attempt in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:18081/api/v1/health/live', timeout=2) as response:
            if response.status == 200:
                break
    except (OSError, urllib.error.URLError):
        pass
    time.sleep(1)
else:
    raise SystemExit('API недоступен. См. data/prepare-forward.log')
PY
.venv/bin/python scripts/prober.py --prepare --api http://127.0.0.1:18081 --state data/prober.json
kubectl -n locals create secret generic locals-prober --from-file=config.json=data/prober.json --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/slo/prober.yaml
kubectl -n locals rollout restart deployment/prober
kubectl -n locals rollout status deployment/prober --timeout=300s
kubectl -n locals logs deployment/prober --tail=6
printf '%s\n' 'Готово. Доступ к Grafana и демонстрация описаны в README.md'
