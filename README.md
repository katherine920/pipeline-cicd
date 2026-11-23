# TiendaRápida – Pipeline CI/CD

Caso de estudio de liberación y despliegue continuo con **GitHub Actions + Docker + Prometheus/Grafana**.
Documentación completa: [`docs/DOCUMENTO_CICD.md`](docs/DOCUMENTO_CICD.md).

## Uso rápido (local)

```bash
# 1. Pruebas unitarias
pip install -r app/requirements-dev.txt
python -m pytest app/tests

# 2. Construir imagen y levantar el entorno de liberación
docker build -f app/Dockerfile -t tiendarapida:latest .
./scripts/env/setup-env.sh

# 3. Pruebas en el entorno de liberación
./scripts/tests/smoke_test.sh http://localhost:8000
python scripts/tests/integration_test.py http://localhost:8000
python scripts/tests/slo_check.py http://localhost:8000

# 4. Destruir entorno
./scripts/env/teardown-env.sh
```

Servicios locales: API `:8000` · Prometheus `:9090` · Grafana `:3000` (admin/admin).

## Vincular el pipeline al entorno de despliegue

1. Sube el repositorio a GitHub (rama `main`).
2. *Settings → Environments*: crea `staging` y `production` (en `production`, activa *Required reviewers*).
3. En cada entorno agrega:
   - **Secret** `DEPLOY_SSH_KEY`: llave privada SSH de despliegue.
   - **Variables** `DEPLOY_HOST`, `DEPLOY_USER`, `APP_URL` (ej. `http://IP:8000`).
4. En el servidor: instalar Docker, `gettext-base` (envsubst), agregar la llave pública a `authorized_keys` y el usuario al grupo `docker`.
5. *Settings → Actions → General → Workflow permissions*: "Read and write permissions".
6. Haz `git push` a `main`: corre **CI** → publica imagen en GHCR → **CD** despliega a staging → espera aprobación → producción.

Despliegue manual de una versión concreta: *Actions → CD → Run workflow* e indicar el `tag`.

## Rollback

Automático si el healthcheck falla tras desplegar. Manual en el servidor:

```bash
IMAGE=ghcr.io/usuario/repo APP_ENV=production APP_PORT=8080 ./rollback.sh <tag_anterior>
```
