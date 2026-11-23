#!/usr/bin/env bash
# Uso (en el servidor): IMAGE=... APP_ENV=... APP_PORT=... ./rollback.sh <tag_anterior>
set -euo pipefail
export TAG="${1:?Indica el tag anterior}"
bash "$(dirname "$0")/deploy.sh"
