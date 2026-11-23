#!/usr/bin/env bash
# Genera docker-compose.deploy.yml desde la plantilla. Requiere IMAGE, TAG, APP_ENV, APP_PORT.
set -euo pipefail
: "${IMAGE:?}" "${TAG:?}" "${APP_ENV:?}" "${APP_PORT:?}"
export IMAGE TAG APP_ENV APP_PORT
cd "$(dirname "$0")"
envsubst < docker-compose.deploy.tpl.yml > docker-compose.deploy.yml
echo ">> Manifiesto generado para $APP_ENV ($IMAGE:$TAG, puerto $APP_PORT)"
