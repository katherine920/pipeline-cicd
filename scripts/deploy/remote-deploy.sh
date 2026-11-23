#!/usr/bin/env bash
# Se ejecuta en el runner de GitHub Actions: copia plantilla y ejecuta deploy.sh por SSH.
set -euo pipefail
: "${SSH_KEY:?}" "${HOST:?}" "${USER:?}" "${IMAGE:?}" "${TAG:?}" "${APP_ENV:?}" "${APP_PORT:?}"
IMAGE="${IMAGE,,}"
mkdir -p ~/.ssh
echo "$SSH_KEY" > ~/.ssh/deploy_key && chmod 600 ~/.ssh/deploy_key
ssh-keyscan -H "$HOST" >> ~/.ssh/known_hosts 2>/dev/null
OPTS="-i $HOME/.ssh/deploy_key"
ssh $OPTS "$USER@$HOST" "mkdir -p ~/tiendarapida/$APP_ENV"
scp $OPTS scripts/deploy/deploy.sh scripts/deploy/docker-compose.deploy.tpl.yml "$USER@$HOST:~/tiendarapida/$APP_ENV/"
ssh $OPTS "$USER@$HOST" "cd ~/tiendarapida/$APP_ENV && IMAGE=$IMAGE TAG=$TAG APP_ENV=$APP_ENV APP_PORT=$APP_PORT bash deploy.sh"
