
Для экспорта HTTP-метрик используется promtheus-fastapi-instrumentator, для метрик Python и собственных счётчиков используется prometheus-client.

Реализованы четыре бизнес-метрики. locals_login_operations_total считает операции входа, locals_audio_uploads_total считает загрузки аудио, locals_playback_link_requests_total считает запросы на аудио(прослушивание, отображение), locals_review_submitted_total считает создание рецензий. Также есть встроенные метрики в Victoriametrics они отображают работает ли сервис в целом(кол-во 5** ошибок и прочее). Каждая метрика, считает success, error, rejected.

Запуск приложения и создание Secret описаны в [инструкции](./k8s/logging/README-victoria.md).. VictoriaMetrics устанавливается командой:

```bash
helm upgrade --install vmsingle victoria-metrics-single --repo https://victoriametrics.github.io/helm-charts/ --version 0.49.0 -n monitoring --create-namespace -f guide-vmsingle-values.yaml --wait
```

Каждый проброс портов запускается в отдельном терминале:

```bash
kubectl -n locals port-forward svc/app 18000:8000
kubectl -n locals port-forward svc/storage 9000:9000
kubectl -n monitoring port-forward svc/vmsingle-victoria-metrics-single-server 8428:8428
```

Для проверки pod-ов, сбора метрик и четырёх сценариев выполнить скрипт:

```bash
python3 scripts/check_metrics.py
```
Он создаёт аккаунт , заливает трек, рецензию, и проверяет как counter поменялся в VictoriaMetrics.

VictoriaMetrics размещена в namespace `monitoring` вместе с Grafana, vmalert и Alertmanager. Она обнаруживает Pod приложения и PostgreSQL в namespace `locals` по аннотациям. В Grafana используется адрес `http://vmsingle-victoria-metrics-single-server.monitoring.svc.cluster.local:8428`.

При переустановке 06.11.2026 история из прежнего namespace не переносится: VictoriaMetrics собирает новые значения в новый PVC. Счётчики экспортёров при этом не обнуляются, если сами экспортёры не перезапускались. Для `increase(...[5m])` нужно накопить несколько свежих измерений. Архив проверки от 24.10.2026 в `k8s/metrics/проверка.txt` и `проверка.json` относится к прежней установке.
