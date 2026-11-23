# Liberación y Despliegue Continuo – Caso de estudio TiendaRápida

> **Nota:** el caso de estudio usado es una *API de pedidos para una tienda en línea* (TiendaRápida). Si tu caso es otro, ajusta el nombre del sistema, los SLA y las métricas; la estructura del pipeline se mantiene.

## 1. Descripción del caso

TiendaRápida es una pequeña empresa de comercio electrónico que expone una API REST (consulta de productos y registro de pedidos) consumida por su sitio web y app móvil. El equipo (4 desarrolladores) realizaba despliegues manuales, con los siguientes problemas:

- Despliegues lentos (≈ 2 h) y propensos a error humano.
- Diferencias entre el entorno de desarrollo y el de producción.
- Errores detectados tarde, ya en producción.
- Sin monitoreo ni forma rápida de revertir.

**Objetivo:** automatizar la integración, liberación y despliegue para entregar cambios pequeños, frecuentes y seguros.

## 2. Justificación del flujo de trabajo (pipeline)

### 2.1 Herramientas elegidas y por qué

| Herramienta | Uso | Justificación |
|---|---|---|
| **Git + GitHub** | Control de versiones | El código ya vive en GitHub; un solo lugar para código y automatización. |
| **GitHub Actions** | CI/CD | Sin servidor propio que mantener, gratuito para repos pequeños, soporta *Environments* con aprobaciones y secretos por entorno. |
| **Docker / Docker Compose** | Empaquetado y entornos | Garantiza que lo probado es exactamente lo desplegado (inmutabilidad) y elimina el "en mi máquina funciona". |
| **GHCR** | Registro de imágenes | Integrado con GitHub, autenticación con `GITHUB_TOKEN`. |
| **Prometheus + Grafana** | Monitoreo | Estándar de facto, open source, ligero. |
| **Bash + Python (stdlib)** | Scripts | Sin dependencias adicionales en los runners/servidores. |

### 2.2 Etapas del pipeline

```
 commit/PR ─► [1] Lint + pruebas unitarias ─► [2] Build imagen Docker
          ─► [3] Entorno de liberación efímero ─► [4] Pruebas de humo, integración y SLO
          ─► [5] Publicar imagen (solo main) ─► [6] Deploy STAGING (auto)
          ─► [7] Pruebas post-despliegue ─► [8] Aprobación manual ─► [9] Deploy PRODUCCIÓN
          ─► [10] Verificación + monitoreo (rollback automático si falla)
```

| # | Etapa | Propósito | Criterio de paso |
|---|---|---|---|
| 1 | Lint y pruebas unitarias | Detectar errores de estilo y lógica en segundos | flake8 sin errores; pytest 100 % verde |
| 2 | Build | Crear artefacto inmutable etiquetado con el SHA del commit | Imagen construida |
| 3 | Entorno de liberación | Levantar un entorno idéntico al real (app + monitoreo) en el runner | Healthcheck OK |
| 4 | Pruebas en el entorno | Verificar el comportamiento real del contenedor | Humo, integración y SLO aprobados |
| 5 | Publicación | Versionar el artefacto aprobado | Solo en `main` |
| 6–7 | Staging | Ensayo general con la misma imagen | Humo e integración aprobados |
| 8 | Aprobación | Control humano antes de producción (*Required reviewers*) | Aprobado por responsable |
| 9–10 | Producción | Despliegue y verificación | `/health` OK; si no, **rollback automático** |

### 2.3 Justificación de las decisiones

1. **Integración continua en cada push/PR:** los errores se detectan minutos después de introducirse, cuando son baratos de corregir.
2. **Construir una sola vez (*build once, deploy many*):** la misma imagen (mismo SHA) pasa por liberación, staging y producción; así se elimina la variabilidad entre entornos.
3. **Entorno de liberación efímero:** se crea y destruye en cada ejecución, evitando contaminación entre pruebas y asegurando reproducibilidad (infraestructura como código).
4. **Pruebas en capas (pirámide):** unitarias (rápidas) → humo (¿arrancó?) → integración (¿el flujo funciona?) → SLO (¿rinde lo acordado?).
5. **Despliegue continuo a staging, entrega continua a producción con aprobación:** equilibra velocidad y riesgo; el negocio decide cuándo exponer el cambio.
6. **Rollback automático:** si la verificación de salud falla, se restaura la versión previa, reduciendo el tiempo de indisponibilidad.
7. **Monitoreo desde el primer día:** sin métricas no se puede demostrar que el despliegue fue exitoso ni cumplir los SLA.

### 2.4 Beneficios esperados

| Indicador (DORA) | Antes | Meta con el pipeline |
|---|---|---|
| Frecuencia de despliegue | 1 al mes | Varias por semana |
| Tiempo de entrega de un cambio | Días | < 1 hora |
| Tasa de fallos de cambios | ~25 % | < 10 % |
| Tiempo de recuperación (MTTR) | Horas | < 15 min |

## 3. Entorno requerido para la liberación y despliegue continuo

### 3.1 Entornos

| Entorno | Propósito | Dónde corre | Puerto app |
|---|---|---|---|
| Desarrollo | Trabajo local del desarrollador | Laptop (Docker) | 8000 |
| **Liberación (release)** | Pruebas automáticas efímeras | Runner de GitHub Actions (`ubuntu-latest`) | 8000 |
| Staging | Ensayo previo a producción | Servidor Linux (VM) | 8000 |
| Producción | Usuarios reales | Servidor Linux (VM) | 8080 |

### 3.2 Requerimientos de software

| Componente | Versión | Dónde |
|---|---|---|
| Python | 3.12 | Desarrollo/CI |
| Docker Engine + Compose v2 | ≥ 24 | Runner, staging y producción |
| Git | ≥ 2.40 | Todos |
| curl, envsubst (gettext), OpenSSH | — | Servidores y runner |
| Prometheus / Grafana | 2.53 / 11.1 | Entorno de liberación (y producción) |

### 3.3 Requerimientos de hardware (por servidor de despliegue)

| Recurso | Mínimo | Recomendado |
|---|---|---|
| CPU | 2 vCPU | 2–4 vCPU |
| RAM | 2 GB | 4 GB |
| Disco | 20 GB | 40 GB |
| Red | Puertos 22 (SSH), 8000/8080 (app), 3000/9090 (monitoreo, restringidos) | — |

### 3.4 Vinculación de la herramienta de liberación con el entorno de despliegue

1. **GitHub → Settings → Environments:** crear `staging` y `production`.
2. En `production` activar **Required reviewers** (aprobación manual).
3. **Secrets** (por entorno): `DEPLOY_SSH_KEY` (llave privada SSH del usuario de despliegue).
4. **Variables** (por entorno): `DEPLOY_HOST`, `DEPLOY_USER`, `APP_URL`.
5. En el servidor: instalar Docker, agregar la llave pública a `~/.ssh/authorized_keys` y agregar al usuario al grupo `docker`.
6. **Settings → Actions → General → Workflow permissions:** "Read and write" para publicar en GHCR.
7. En los servidores, autenticarse en GHCR si el paquete es privado: `echo $PAT | docker login ghcr.io -u USUARIO --password-stdin`.

## 4. Niveles de servicio acordados

### 4.1 SLI, SLO y SLA

| Indicador (SLI) | Objetivo (SLO) | Acuerdo (SLA) con el negocio |
|---|---|---|
| Disponibilidad mensual | 99.9 % | ≥ 99.5 % |
| Latencia p95 de la API | < 500 ms | < 800 ms |
| Latencia p99 de la API | < 1 s | < 2 s |
| Tasa de errores 5xx | < 1 % | < 2 % |
| Tiempo de recuperación (MTTR) | < 15 min | < 1 h |
| Tiempo máximo de despliegue | < 10 min (merge → staging) | < 30 min |

### 4.2 Presupuesto de error

Con 99.9 % de disponibilidad se permiten ≈ **43 min de indisponibilidad al mes**. Si se agota, se congelan los despliegues de nuevas funcionalidades y se prioriza la estabilidad.

### 4.3 Ventanas y soporte

- Despliegues a producción: lunes a jueves, 9:00–16:00 (evitar viernes y horas pico).
- Soporte: horario laboral con guardia para alertas críticas.
- Respaldos de configuración: versionados en Git.

### 4.4 Verificación automática

El script `scripts/tests/slo_check.py` falla el pipeline si p95 > 500 ms o errores > 1 %, y las reglas de `monitoring/alerts.yml` vigilan los mismos umbrales en operación.

## 5. Métricas para el monitoreo de la aplicación

La aplicación expone `/metrics` en formato Prometheus; Prometheus las recolecta cada 15 s y Grafana las visualiza.

### 5.1 Métricas de la aplicación

| Métrica | Tipo | Descripción |
|---|---|---|
| `http_requests_total{method,path,status}` | Contador | Peticiones totales |
| `http_errors_total` | Contador | Respuestas 5xx |
| `http_request_duration_seconds` (bucket/sum/count) | Histograma | Latencia de peticiones |
| `app_uptime_seconds` | Gauge | Tiempo en línea |
| `up{job="tiendarapida"}` | Gauge (Prometheus) | 1 = app alcanzable |

### 5.2 Consultas PromQL clave

| Indicador | Consulta |
|---|---|
| Peticiones por segundo | `sum(rate(http_requests_total[5m]))` |
| Tasa de errores | `sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m]))` |
| Latencia p95 | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` |
| Disponibilidad | `avg_over_time(up{job="tiendarapida"}[30d])` |

### 5.3 Métricas del pipeline (DORA)

Frecuencia de despliegue, lead time, tasa de fallo de cambios y MTTR, obtenidas del historial de GitHub Actions.

### 5.4 Alertas configuradas

| Alerta | Condición | Severidad |
|---|---|---|
| AppCaida | `up == 0` por 1 min | Crítica |
| TasaErroresAlta | errores > 1 % por 5 min | Advertencia |
| LatenciaP95Alta | p95 > 500 ms por 5 min | Advertencia |

### 5.5 Métricas de infraestructura (recomendadas)

CPU, memoria y disco del contenedor y del host (cAdvisor / node_exporter como ampliación).

## 6. Parámetros de configuración de las herramientas utilizadas

### 6.1 GitHub Actions – `ci.yml`

| Parámetro | Valor | Motivo |
|---|---|---|
| `on.push.branches` | `main`, `develop` | Ejecutar en ramas principales |
| `on.pull_request.branches` | `main` | Validar antes de fusionar |
| `runs-on` | `ubuntu-latest` | Docker preinstalado |
| `python-version` | `3.12` | Versión del runtime |
| `permissions` | `contents: read`, `packages: write` | Mínimo privilegio para publicar en GHCR |
| `REGISTRY` / `IMAGE_NAME` | `ghcr.io` / `${{ github.repository }}` | Destino de imágenes |
| Etiqueta de imagen | SHA corto (8) + `latest` | Trazabilidad |
| Publicación | Solo `main` y evento `push` | No publicar PRs |

### 6.2 GitHub Actions – `cd.yml`

| Parámetro | Valor |
|---|---|
| Disparador | `workflow_run` (CI exitoso en `main`) y `workflow_dispatch` (manual, con `tag`) |
| `environment` | `staging` → `production` (con *Required reviewers*) |
| Secreto | `DEPLOY_SSH_KEY` |
| Variables | `DEPLOY_HOST`, `DEPLOY_USER`, `APP_URL` |
| Puertos | staging `8000`, producción `8080` |

### 6.3 Docker (`app/Dockerfile`)

| Parámetro | Valor |
|---|---|
| Imagen base | `python:3.12-slim` |
| Usuario | `appuser` (no root) |
| Servidor | `gunicorn -w 2 -b 0.0.0.0:8000` |
| `HEALTHCHECK` | cada 15 s, timeout 3 s, 3 reintentos |
| Puerto expuesto | 8000 |

### 6.4 Docker Compose (entorno de liberación)

| Servicio | Imagen | Puerto | Parámetros |
|---|---|---|---|
| app | `${IMAGE}:${TAG}` | 8000 | límites 0.5 CPU / 256 MB; healthcheck cada 10 s |
| prometheus | `prom/prometheus:v2.53.0` | 9090 | `prometheus.yml` y `alerts.yml` montados |
| grafana | `grafana/grafana:11.1.0` | 3000 | datasource Prometheus provisionado; contraseña por `GRAFANA_PASSWORD` |

### 6.5 Prometheus

| Parámetro | Valor |
|---|---|
| `scrape_interval` | 15 s |
| `evaluation_interval` | 15 s |
| Job | `tiendarapida`, `/metrics`, destino `app:8000` |
| Reglas | `/etc/prometheus/alerts.yml` |

### 6.6 Servidor de despliegue (SSH)

| Parámetro | Valor |
|---|---|
| Autenticación | Llave SSH sin contraseña, exclusiva para despliegue |
| Directorio | `~/tiendarapida/<entorno>` |
| Registro de versión | `.current_tag` (para rollback) |
| Espera de salud | 20 intentos × 3 s |

### 6.7 Calidad de código

| Herramienta | Parámetro |
|---|---|
| flake8 | `max-line-length = 120` |
| pytest | pruebas en `app/tests` |

## 7. Estructura del repositorio y scripts entregados

```
.
├── app/                         # Aplicación, Dockerfile y pruebas unitarias
├── .github/workflows/
│   ├── ci.yml                   # Pipeline de integración y liberación
│   └── cd.yml                   # Pipeline de despliegue (staging → producción)
├── scripts/
│   ├── env/                     # Generación del entorno de liberación
│   │   ├── docker-compose.release.yml
│   │   ├── setup-env.sh
│   │   └── teardown-env.sh
│   ├── tests/                   # Pruebas en el entorno de liberación
│   │   ├── smoke_test.sh
│   │   ├── integration_test.py
│   │   └── slo_check.py
│   └── deploy/                  # Generación y ejecución del despliegue
│       ├── docker-compose.deploy.tpl.yml
│       ├── generate-deployment.sh
│       ├── deploy.sh
│       ├── remote-deploy.sh
│       └── rollback.sh
├── monitoring/                  # prometheus.yml, alerts.yml, Grafana
└── docs/DOCUMENTO_CICD.md       # Este documento
```

## 8. Evidencia de ejecución (completar tras la primera corrida)

| Evidencia | Dónde obtenerla |
|---|---|
| Ejecución exitosa de CI | Pestaña *Actions* → captura del workflow verde |
| Aprobación de producción | Pestaña *Actions* → job `deploy-production` |
| Dashboard de métricas | Grafana `http://<host>:3000` |
| Entorno vinculado | *Settings → Environments* |

## 9. Riesgos y mejoras futuras

| Riesgo | Mitigación |
|---|---|
| Fallo de un despliegue | Rollback automático + `rollback.sh` |
| Secretos expuestos | Secrets por entorno, llave exclusiva, rotación periódica |
| Vulnerabilidades en la imagen | Agregar escaneo con Trivy al CI |
| Despliegue con indisponibilidad breve | Evolucionar a *blue-green* o *canary* |
| Un solo servidor | Migrar a Kubernetes o balanceador con réplicas |
