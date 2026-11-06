# SLI/SLO/SLA Locals

Сначала настройка по [прошлыйReadme](../logging/README-victoria.md)

VictoriaMetrics и Grafana размещены в namespace `monitoring`, приложение и пробер — в `locals`. После переустановки VictoriaMetrics 06.11.2026 графики используют новую историю. Инструкции установки и проверки метрик: [ОтчётMetrics.md](../../ОтчётMetrics.md).

```bash
minikube start -p minikube
kubectl config use-context minikube
kubectl -n locals scale deployment/prober --replicas=1
kubectl -n locals rollout status deployment/prober --timeout=180s
```

В отдельном терминале:

```bash
kubectl -n monitoring port-forward svc/grafana 13000:80
```

[Grafana](http://localhost:13000/d/locals-slo), логин `admin`. Пароль:

```bash
kubectl -n monitoring get secret grafana -o jsonpath='{.data.admin-password}' | base64 --decode
```

Журнал пробера

```bash
kubectl -n locals logs -f deployment/prober --tail=6
```
Можете стопануть MinIO:

```bash
kubectl -n locals scale statefulset/storage --replicas=0
```

Восстановить:

```bash
kubectl -n locals scale statefulset/storage --replicas=1
kubectl -n locals rollout status statefulset/storage --timeout=180s
```
