#!/usr/bin/env bash
# Genera el entorno de liberacion y espera a que la app este saludable.
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "Docker no esta instalado"; exit 1; }
export IMAGE="${IMAGE:-tiendarapida}" TAG="${TAG:-latest}"
echo ">> Levantando entorno de liberacion ($IMAGE:$TAG)"
docker compose -f docker-compose.release.yml up -d
echo ">> Esperando salud de la aplicacion..."
for i in $(seq 1 30); do
  if curl -fs http://localhost:8000/health >/dev/null; then
    echo ">> Entorno listo"; exit 0
  fi
  sleep 2
done
echo "ERROR: la aplicacion no respondio a tiempo"
docker compose -f docker-compose.release.yml logs
exit 1
