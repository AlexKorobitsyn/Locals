#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo_root"

# Нужен уже работающий VictoriaLogs из основной части задания.
kubectl -n victoria-logs get service victoria-logs-single-server
kubectl -n victoria-logs rollout status statefulset/victoria-logs-single-server --timeout=180s

kubectl apply -f k8s/logging/bonuses-namespace.yaml
kubectl apply -f k8s/logging/grafana-dashboard.yaml

helm upgrade --install grafana grafana \
  --repo https://grafana-community.github.io/helm-charts \
  --version 14.0.0 \
  --namespace monitoring \
  -f k8s/logging/grafana-values.yaml \
  --wait --timeout 5m

helm upgrade --install locals-alerts victoria-metrics-alert \
  --repo https://victoriametrics.github.io/helm-charts/ \
  --version 0.51.0 \
  --namespace monitoring \
  -f k8s/logging/vmalert-values.yaml \
  --wait --timeout 5m

kubectl -n monitoring get pods,services,pvc
