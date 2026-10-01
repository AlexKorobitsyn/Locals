#!/usr/bin/env bash
set -euo pipefail

# БД и хранилище уже доступны; миграции выполняются тем же образом.
deploy_env_file="${1:-.env}"
deploy_image="${2:?Usage: scripts/deploy.sh ENV_FILE REGISTRY_IMAGE@sha256:DIGEST}"
if [[ ! -f "$deploy_env_file" ]]; then
  printf 'Environment file does not exist\n' >&2
  exit 1
fi
if [[ ! "$deploy_image" =~ @sha256:[a-f0-9]{64}$ ]]; then
  printf 'Deploy requires an immutable image digest\n' >&2
  exit 1
fi
export APP_IMAGE="$deploy_image"
deploy_compose=(docker compose --env-file "$deploy_env_file")
"${deploy_compose[@]}" config --quiet
"${deploy_compose[@]}" pull app migrate
"${deploy_compose[@]}" run --rm --no-deps migrate
"${deploy_compose[@]}" up --detach --no-build --no-deps --wait app
"${deploy_compose[@]}" exec -T app python -c 'import json, logging, os, urllib.request; logging.basicConfig(level=logging.INFO); response = urllib.request.urlopen("http://127.0.0.1:" + os.environ["PORT"] + "/api/v1/health/version", timeout=5); result = json.load(response); assert result["release_id"] == os.environ["RELEASE_ID"]; logging.info("Running release: %s", result["release_id"])'
