#!/usr/bin/env bash
# Se ejecuta EN el servidor de despliegue. Despliega, verifica salud y hace rollback si falla.
set -euo pipefail
: "${IMAGE:?}" "${TAG:?}" "${APP_ENV:?}" "${APP_PORT:?}"
DIR="$HOME/tiendarapida/$APP_ENV"
mkdir -p "$DIR"; cd "$DIR"
PREV=$(cat .current_tag 2>/dev/null || echo "")
export IMAGE TAG APP_ENV APP_PORT
envsubst < docker-compose.deploy.tpl.yml > docker-compose.deploy.yml
docker pull "$IMAGE:$TAG"
docker compose -f docker-compose.deploy.yml up -d
for i in $(seq 1 20); do
  if curl -fs "http://localhost:$APP_PORT/health" >/dev/null; then
    echo "$TAG" > .current_tag
    echo ">> Despliegue exitoso: $TAG en $APP_ENV"; exit 0
  fi
  sleep 3
done
echo "ERROR: despliegue fallido"
if [ -n "$PREV" ]; then
  echo ">> Rollback a $PREV"
  TAG="$PREV" envsubst < docker-compose.deploy.tpl.yml > docker-compose.deploy.yml
  TAG="$PREV" docker compose -f docker-compose.deploy.yml up -d
fi
exit 1
