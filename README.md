# Tablero de Notas — Prueba Técnica Fullstack

Sistema de tablero de notas compartido (post-its arrastrables con posición libre y estados
tipo kanban), con autenticación JWT, gestión de usuarios por roles, métricas internas y
una capa serverless sobre AWS.

| Capa              | Tecnología                                                        |
|-------------------|-------------------------------------------------------------------|
| Frontend          | SvelteKit + TypeScript + TailwindCSS (`adapter-static`, modo SPA)  |
| Servidor estático | Nginx (local) / S3 + CloudFront con OAC (AWS)                     |
| Backend           | Django 5 + Django REST Framework + SimpleJWT (JWT, access 15 min) |
| Base de datos     | PostgreSQL 15 (volumen Docker persistente)                        |
| Serverless        | AWS Lambda Python 3.11 (métricas) + API Gateway GET `/metrics`    |
| IaC               | AWS SAM (`aws/template.yaml`)                                     |
| Infra local       | Docker Compose (`db` + `backend` + `frontend`, red `tablero-net`) |

---

## Quickstart (instalación rápida)

> Todo el flujo local funciona **sin cuenta AWS**. Con Docker en marcha es suficiente;
> para las métricas del dashboard se agrega la Lambda local con **AWS SAM CLI**
> (también sin cuenta AWS). El detalle de cada paso está en las secciones 4 y 9.

### 0. Requisitos

| Herramienta                        | Uso                                              | ¿Obligatorio? |
|------------------------------------|--------------------------------------------------|---------------|
| Docker Engine + Docker Compose v2  | `db` + `backend` + `frontend` (y build de la Lambda) | Sí |
| AWS SAM CLI                        | Lambda de métricas en local (`sam local`)        | Sí, para ver `/dashboard` con métricas |
| AWS CLI v2                         | Despliegue real en AWS                           | Solo para deploy |
| Node.js 20+ / Python 3.12+         | Desarrollo fuera de Docker (sección 4.1)         | Opcional |

### 1. Levantar la aplicación (3 comandos)

```bash
cp .env.example .env          # opcional: ajustar secretos
docker compose up -d --build  # levanta db + backend + frontend
docker compose exec backend python manage.py seed_data
```

> Si el `seed_data` falla porque el backend aún está migrando, espera unos segundos y
> repítelo (el comando es idempotente).

| Servicio          | URL                                 |
|-------------------|-------------------------------------|
| Frontend          | http://localhost:3000               |
| Backend API (DRF) | http://localhost:8000/api/          |
| Django Admin      | http://localhost:8000/django-admin/ |
| PostgreSQL        | localhost:5432                      |

### 2. Levantar la Lambda local con SAM (necesario para el dashboard)

Con el paso 1 en marcha (la red `tablero-net` ya existe):

```bash
cd aws
sam build --use-container
sam local start-api --docker-network tablero-net --env-vars env.local.json --port 3001
```

Verificación (en otra terminal):

```bash
curl -i http://127.0.0.1:3001/metrics -H "Origin: http://localhost:3000"
# → {"total": 3, "pending": 1, "in_progress": 1, "done": 1} + cabeceras CORS
```

`aws/samconfig.toml` ya fija `--use-container`, la red, el archivo de env y el puerto,
así que desde `aws/` también bastan `sam build` y `sam local start-api` a secas.

### 3. Iniciar sesión

| Cuenta     | Email               | Contraseña  | Rol   |
|------------|---------------------|-------------|-------|
| Admin Demo | `admin@ejemplo.com` | `Admin123!` | ADMIN |
| User Demo  | `user@ejemplo.com`  | `User123!`  | USER  |

En `/login`, los botones de **Acceso Rápido** autocompletan estas credenciales.

### 4. Comandos útiles

```bash
docker compose logs -f backend                            # logs en vivo
docker compose down                                       # detener (los datos persisten)
docker compose down -v                                    # reset total (borra la base)
docker compose up -d --build                              # reconstruir y arrancar
docker compose exec backend python manage.py seed_data    # datos demo (idempotente)
```

- Desarrollo sin Docker (backend/frontend por separado) → sección **4.1**.
- Pruebas de la Lambda (build, CORS, cold start) → sección **9**.
- Despliegue y retirada en AWS → sección **10**.

---

## Versión entregada

- **Repositorio:** https://github.com/SFirigua/tablero-de-notas
- **Versión:** tag **`v1.0.0`**. La entrega corresponde al commit al que apunta el tag;
  puede resolverse con `git rev-parse v1.0.0` o inspeccionarse con `git show v1.0.0 --stat`.

---

## 1. Arquitectura general

### Local (docker compose + SAM local)

```
                              docker compose
   ┌─────────────────────────────── red: tablero-net ───────────────────────────────┐
   │                                                                                │
   │  frontend (Nginx :3000) ── /api/* ──▶ backend (Django :8000) ──▶ db (Postgres 15)│
   │       ▲                                    ▲                    │               │
   │       │ navegador                          │ GET /api/internal/notes-status/   │
   │       │                          MetricsFunction (Lambda local, :3001)          │
   │       └── PUBLIC_METRICS_URL ──▶ sam local start-api --docker-network tablero-net│
   └────────────────────────────────────────────────────────────────────────────────┘
```

- El navegador consume la API vía Nginx (`/api/*` → `backend:8000`), sin CORS en local
  para la API. El dashboard consulta **PUBLIC_METRICS_URL** (`http://localhost:3001/metrics`).
- La Lambda local se une a la red `tablero-net` y resuelve `backend` por nombre DNS de Docker.
- `sam local` sirve el API Gateway simulado en el puerto 3001.

### AWS (SAM: `aws/template.yaml`)

```
   Usuario ──▶ CloudFront (OAC) ──▶ S3 FrontendBucket        [frontend estático]
   Usuario ──▶ API Gateway ──▶ Lambda MetricsFunction ──▶ BACKEND_URL
                                     │                http://<EC2-PublicDns>:8000/...
                                     │                (el hostname "backend" NO existe en AWS)
                                     ▼
                             EC2 ApiInstance (Docker: Django + PostgreSQL)
```

Recursos del template: `MetricsFunction` (Lambda 3.11 + GET/OPTIONS `/metrics`),
`ApiInstance` (EC2 para los contenedores Docker), `FrontendBucket` (S3 privado) y
`CloudFrontDistribution` (con OAC + política de bucket); más los recursos de apoyo
necesarios (`FrontendOAC`, `FrontendBucketPolicy`, `ApiSecurityGroup`).

---

## 2. Estructura del repositorio

```
/
├── backend/            # API Django + DRF (apps `users` y `notes`, capas View→Service→Model)
├── frontend/           # SvelteKit + Tailwind (build estática en ./build, servida por Nginx)
├── lambda/             # app.py — Lambda de métricas (Python 3.11)
├── aws/                # template.yaml (SAM), env.local.json y scripts deploy/delete (.sh y .ps1)
├── docker-compose.yml  # infra local: db + backend + frontend (red tablero-net)
└── README.md
```

---

## 3. Requisitos previos

- Docker Engine + Docker Compose v2
- Node.js 20+ (solo desarrollo local del frontend)
- Python 3.12+ (solo desarrollo local del backend)
- AWS CLI v2 y AWS SAM CLI (para la capa serverless: `sam build`, `sam local`, `sam deploy`)
- Docker en marcha para `sam build --use-container` (compila la Lambda en el contenedor
  oficial de AWS; **no** hace falta tener Python 3.11 instalado en el host)
- Credenciales AWS configuradas (`aws configure`) para el despliegue

---

## 4. Arranque local

```bash
cp .env.example .env          # opcional: ajustar secretos
docker compose up -d --build  # levanta db + backend + frontend
docker compose exec backend python manage.py seed_data
```

| Servicio                    | URL                                    |
|-----------------------------|----------------------------------------|
| Frontend                    | http://localhost:3000                  |
| Backend API (DRF)           | http://localhost:8000/api/             |
| Django Admin                | http://localhost:8000/django-admin/    |
| PostgreSQL                  | localhost:5432                         |
| Lambda de métricas (SAM local, opcional) | http://localhost:3001/metrics |

El comando de seed es **idempotente**: se puede ejecutar varias veces sin duplicar datos.

> **Métricas del dashboard en local:** `/dashboard` consume la **Lambda local** en
> `PUBLIC_METRICS_URL` (`http://localhost:3001/metrics`). Requiere ejecutar SAM local
> (sección 9) con el backend en marcha; sin SAM, el dashboard muestra un error de
> conexión (existe una alternativa sin SAM en la sección 8, pero **no sustituye** a la
> Lambda exigida por la prueba).

### 4.1 Desarrollo sin Docker (backend y frontend por separado)

Backend:

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
docker compose up db -d                            # solo PostgreSQL
python manage.py migrate && python manage.py runserver 8000
```

Frontend (en un clon limpio hay que crear el `.env` local a partir del ejemplo;
**los `.env` reales no se versionan**):

```bash
cd frontend
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
npm install                   # Windows/PowerShell: npm.cmd install
npm run dev                   # proxy /api -> http://localhost:8000 (vite.config.ts)
npm run build                 # salida estática en ./build
```

`PUBLIC_METRICS_URL` se resuelve así según el flujo: **Docker** la hornea desde el build
arg de `docker-compose.yml`/`Dockerfile` (no necesita `.env`); **`npm run dev`/`npm run
build` locales** la leen de `frontend/.env` (por eso el `cp` es obligatorio en un clon
nuevo).

---

## 5. Credenciales de demostración

| Cuenta     | Email                | Contraseña  | Rol   |
|------------|----------------------|-------------|-------|
| Admin Demo | `admin@ejemplo.com`  | `Admin123!` | ADMIN |
| User Demo  | `user@ejemplo.com`   | `User123!`  | USER  |

La pantalla de `/login` incluye botones de **Acceso Rápido** que autocompletan estas
credenciales. Los usuarios creados desde `/dashboard/users` (solo ADMIN) reciben una
contraseña inicial y pueden iniciar sesión de inmediato.

---

## 6. Persistencia (PostgreSQL + volumen Docker)

- El servicio `db` usa la imagen `postgres:15-alpine` y guarda sus datos en el volumen
  nombrado **`postgres_data`** (`/var/lib/postgresql/data`), definido en `docker-compose.yml`.
- Los datos **sobreviven** a `docker compose down`, reinicios y reconstrucciones.
- Para reiniciar la base desde cero: `docker compose down -v` (elimina el volumen) y
  volver a ejecutar `docker compose up -d --build` + `seed_data`.
- El backend aplica migraciones automáticamente al arrancar
  (`python manage.py migrate && runserver` en el `command` del compose).

---

## 7. API y autenticación

JWT (`djangorestframework-simplejwt`): access de **15 minutos**, refresh de 7 días.
El access token se envía en `Authorization: Bearer <token>` y se guarda en `sessionStorage`.

| Método | Endpoint                      | Acceso              | Descripción |
|--------|-------------------------------|---------------------|-------------|
| POST   | `/api/auth/login/`            | Público             | `{email, password}` → `{access, refresh, user}` |
| POST   | `/api/auth/refresh/`          | Público             | `{refresh}` → nuevo access |
| POST   | `/api/auth/logout/`           | Autenticado         | Ver nota de logout |
| GET/POST/PATCH/DELETE | `/api/notes/…`    | ADMIN y USER activos | CRUD de notas (`title`, `text`, `status`, `pos_x`, `pos_y`) |
| GET/POST/PATCH | `/api/users/…`        | Solo ADMIN          | CRUD de usuarios; la contraseña inicial es obligatoria al crear |
| GET    | `/api/internal/notes-status/` | Usuario activo o token interno (`X-Internal-Token`) | `{"pending": X, "in_progress": Y, "done": Z}` |

- Usuario con `is_active=False` → **401** inmediato en cada petición.
- Regla de negocio: no se puede desactivar ni cambiar de rol al **último administrador
  activo** (HTTP **400**, lógica en `users/services.py`).
- **Logout**: con JWT sin estado el cierre es **del lado cliente**; `POST /api/auth/logout/`
  responde 200 y el frontend elimina los tokens. El access token ya emitido expira solo
  (15 min); no hay revocación server-side (fuera de alcance a propósito).

---

## 8. Frontend (rutas y configuración)

| Ruta               | Acceso         | Descripción |
|--------------------|----------------|-------------|
| `/login`           | Público        | Login + Acceso Rápido |
| `/dashboard`       | Usuario activo | Métricas: Total, Pendientes, En curso, Hechas |
| `/dashboard/board` | Usuario activo | Lienzo libre: post-its con drag & drop (pointer events), edición inline, crear/eliminar |
| `/dashboard/users` | Solo ADMIN     | Tabla, alta por modal, switch Activo/Inactivo, cambio de rol |

**Métricas**: el dashboard consume el resultado de la **Lambda** de métricas; su URL sale
exclusivamente de la variable `PUBLIC_METRICS_URL` (nada hardcodeado en el código).
Local: `http://localhost:3001/metrics` (SAM local, sección 9). AWS:
`https://<API_GATEWAY>/Prod/metrics`. **La Lambda local debe estar disponible en esa URL**;
sin ella el dashboard muestra un error de conexión. La alternativa
`http://localhost:8000/api/internal/notes-status/` (Django directo) sirve solo para demos
sin SAM y **no reemplaza** el flujo con Lambda exigido por la prueba.

---

## 9. Probar la Lambda localmente con SAM

Requiere el backend en marcha (`docker compose up -d db backend`) y la red `tablero-net`
creada por compose. `aws/env.local.json` inyecta la configuración local de la función:

```json
{
  "MetricsFunction": {
    "BACKEND_URL": "http://backend:8000/api/internal/notes-status/",
    "ALLOWED_ORIGIN": "http://localhost:3000",
    "INTERNAL_API_TOKEN": "dev-internal-token"
  }
}
```

Paso a paso (3 comandos):

```bash
cd aws
sam build --use-container
sam local start-api --docker-network tablero-net --env-vars env.local.json --port 3001
```

> **¿Por qué `--use-container`?** Compila el código dentro de un contenedor oficial de
> AWS Lambda (`public.ecr.aws/sam/build-python3.11`), no con el Python del host: el
> artefacto es idéntico al runtime `python3.11` de AWS y el flujo es "frictionless" sin
> importar qué versión de Python tenga instalada la máquina (o si no tiene ninguna).
> Solo requiere Docker en marcha; la primera vez descarga la imagen (~1 min).

`aws/samconfig.toml` fija esos mismos defaults (`use_container = true`, red `tablero-net`,
`env.local.json`, puerto `3001` y `warm_containers = "EAGER"`), así que `sam build` y
`sam local start-api` a secas también funcionan. Si `sam build` falla con
`PythonPipBuilder:Validation - Binary validation failed for python`, se ejecutó sin
`--use-container` (o fuera de `aws/`): intenta compilar con el Python local (p. ej. 3.12)
en vez de con la imagen oficial de Python 3.11.

> **Latencia de `/metrics` en local:** sin `--warm-containers`, SAM levanta un contenedor
> Lambda NUEVO en cada petición (cold start de varios segundos). Con `EAGER` (fijado en
> `samconfig.toml`) los contenedores arrancan junto con `sam local start-api` y quedan
> calientes: cada petición baja a ~1 s en Windows/Docker Desktop.

Prueba (en otra terminal):

```bash
curl -i http://127.0.0.1:3001/metrics -H "Origin: http://localhost:3000"
# → {"total": 3, "pending": 1, "in_progress": 1, "done": 1} + cabeceras CORS
```

- `<nombre_red_docker>` = **`tablero-net`** (nombre fijo declarado en `docker-compose.yml`
  con `name:`, para que no dependa del nombre del proyecto).
- La Lambda llama a `BACKEND_URL` (`http://backend:8000/...`), resoluble **solo** dentro de
  la red Docker; en AWS ese hostname no existe y se usa el parámetro `BackendUrl`.
- `/api/internal/notes-status/` está protegido: acepta JWT de un usuario activo (dashboard)
  o el token server-to-server que envía la Lambda en la cabecera `X-Internal-Token`
  (`INTERNAL_API_TOKEN`). En local, `docker-compose.yml` y `env.local.json` comparten el
  mismo valor de demo (`dev-internal-token`); en AWS se controla con el parámetro
  `InternalApiToken` del stack (cambiar en entornos reales).

---

## 10. Despliegue y retirada en AWS

Scripts incluidos en `aws/` (equivalen a los comandos manuales; ejecutan
`sam build --use-container` + `sam deploy`/`sam delete` y muestran los Outputs):

| Entorno                                   | Despliegue   | Retirada     |
|-------------------------------------------|--------------|--------------|
| Linux / macOS (o Windows con Git Bash/WSL) | `./deploy.sh` | `./delete.sh` |
| Windows PowerShell nativo                  | `.\deploy.ps1` | `.\delete.ps1` |

> **Bash o PowerShell:** usa los `.sh` en Linux/macOS o en Windows dentro de Git Bash/WSL;
> usa los `.ps1` en PowerShell nativo. Si la política de ejecución bloquea los scripts,
> invócalos con `powershell -ExecutionPolicy Bypass -File .\deploy.ps1` (mismo caso para
> `delete.ps1`). Requieren AWS CLI v2 configurada (`aws configure`) y AWS SAM CLI en el PATH.

### 10.1 Infraestructura (SAM)

Primera pasada (defaults del template; los scripts son opcionales, también puede usarse
`sam build --use-container` + `sam deploy --guided` a mano):

```bash
cd aws
./deploy.sh          # PowerShell: .\deploy.ps1
# Parámetros del template: BackendUrl (default en la 1ª pasada), AllowedOrigin,
# InternalApiToken, InstanceType, KeyName, SshCidr
```

Tras el primer deploy, tomar de los **Outputs**:

- `BackendUrlForLambda` (DNS público del EC2) y `CloudFrontUrl`.

Y redesplegar con la configuración real (segunda pasada):

```bash
BACKEND_URL="http://<ApiInstancePublicDns>:8000/api/internal/notes-status/" \
ALLOWED_ORIGIN="https://<CloudFrontDomain>" \
INTERNAL_API_TOKEN="<token-propio>" \
./deploy.sh
# PowerShell:
#   $env:BACKEND_URL="http://<ApiInstancePublicDns>:8000/api/internal/notes-status/"
#   $env:ALLOWED_ORIGIN="https://<CloudFrontDomain>"
#   $env:INTERNAL_API_TOKEN="<token-propio>"
#   .\deploy.ps1
```

> En AWS, `BackendUrl` apunta a la API desplegada en EC2. El hostname `backend` de Docker
> **nunca** se usa en la nube. Para el resto de parámetros: `EXTRA_OVERRIDES` (p. ej.
> `EXTRA_OVERRIDES="InstanceType=t3.large KeyName=mi-clave"`).

### 10.2 Backend en EC2

La instancia nace con Docker y el plugin de Compose instalados (UserData). Copiar el
proyecto y levantar los contenedores:

```bash
scp -i <clave.pem> -r ./backend ./docker-compose.yml ec2-user@<ApiInstancePublicDns>:~
ssh -i <clave.pem> ec2-user@<ApiInstancePublicDns>
# En la instancia:
cp backend/.env.example backend/.env   # ajustar DJANGO_ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS
# INTERNAL_API_TOKEN debe coincidir con el parámetro InternalApiToken del stack SAM
docker compose up -d --build db backend
docker compose exec backend python manage.py seed_data
```

### 10.3 Frontend en S3 + CloudFront (OAC)

El bucket es privado: solo CloudFront (Origin Access Control) puede leerlo.

```bash
cd frontend
npm ci
# Hornea la URL de métricas de AWS en la build estática:
#   Linux/macOS:
PUBLIC_METRICS_URL=https://<api-id>.execute-api.<region>.amazonaws.com/Prod/metrics npm run build
#   Windows PowerShell:
#   $env:PUBLIC_METRICS_URL="https://<api-id>.execute-api.<region>.amazonaws.com/Prod/metrics"; npm run build

aws s3 sync build/ s3://<FrontendBucketName> --delete

# Invalidar la caché tras cada nueva versión:
aws cloudfront create-invalidation \
  --distribution-id <CloudFrontDistributionId> --paths "/*"
```

### 10.4 Retirada

```bash
cd aws
./delete.sh          # PowerShell: .\delete.ps1
```

Los scripts vacían `FrontendBucket` (CloudFormation no elimina buckets con objetos) y
ejecutan `sam delete`. Manualmente serían:
`aws s3 rm s3://<FrontendBucketName> --recursive` + `sam delete --stack-name tablero-notas`.

---

## 11. Configuración local vs AWS

| Aspecto               | Local (docker compose / SAM local)                              | AWS (SAM template)                                         |
|-----------------------|-----------------------------------------------------------------|------------------------------------------------------------|
| `BACKEND_URL`         | `http://backend:8000/api/internal/notes-status/` (red `tablero-net`) | `http://<EC2-PublicDns>:8000/api/internal/notes-status/` (parámetro `BackendUrl`) |
| CORS de la Lambda     | `ALLOWED_ORIGIN=http://localhost:3000`                          | `AllowedOrigin=https://<CloudFrontDomain>` (parámetro, CSV) |
| Token interno         | `dev-internal-token` (compose + `env.local.json`)               | parámetro `InternalApiToken` (debe coincidir con el `.env` del EC2) |
| `PUBLIC_METRICS_URL`  | `http://localhost:3001/metrics` (SAM local)                     | `https://<API_GATEWAY>/Prod/metrics`                       |
| Frontend              | Nginx sirviendo `./build` en `:3000`                            | S3 + CloudFront (OAC)                                      |
| Base de datos         | Contenedor `db` + volumen `postgres_data`                       | PostgreSQL en Docker sobre la instancia EC2                |
| Hostnames             | `db`, `backend`, `frontend`, `tablero-net` (DNS de Docker)      | DNS públicos de EC2/CloudFront/API Gateway (nunca `backend`) |

**CORS**: la Lambda permite configurar los orígenes por parámetro/variable
(`ALLOWED_ORIGIN`, lista separada por comas) y responde con `Vary: Origin`. Enviar
`Access-Control-Allow-Origin: *` es posible pero **opt-in** (`AllowedOrigin="*"`), nunca
la única configuración; los orígenes no permitidos reciben 403.

---

## 12. Registro de tiempo estimado (≈7.5 horas efectivas)

| Fase                                                          | Tiempo |
|---------------------------------------------------------------|--------|
| Backend: custom user, JWT, permisos, capas, reglas, seed      | 2.5 h  |
| Frontend: login, tablero drag & drop, dashboard, usuarios     | 2.0 h  |
| Lambda + plantilla SAM (S3/CloudFront/OAC, EC2)               | 1.0 h  |
| Docker/infra local, documentación y scripts                   | 1.0 h  |
| Verificación end-to-end (API 40 checks, Lambda 13 checks)     | 0.5 h  |
| Cierre: scripts AWS, edición de usuarios en UI, docs y re-check | 0.5 h |
| **Total**                                                     | **≈7.5 h** |

---

## 13. Limitaciones y pendientes conocidos

- **HTTP sin TLS en el backend EC2** (demo): en producción iría detrás de ALB + ACM o
  CloudFront con origen custom.
- **Bootstrap manual del backend en EC2** (copiar repo + `docker compose up`); no hay
  CI/CD ni user-data completo de la aplicación.
- **PostgreSQL en el mismo EC2** (pragmático para la prueba); en producción → RDS.
- **Sin tests automatizados dentro del repo** (se usaron harness de verificación externos);
  pendiente: `TestCase`/pytest en backend y smoke en frontend.
- **Refresh automático del access token en el frontend**: hoy, al expirar (15 min) el
  wrapper detecta 401, limpia la sesión y redirige a `/login`.
- **Bucket S3 sin versionado/logging** y **CloudFront sin dominio propio/ACM**.
- **SG de demo** con 8000 y 22 abiertos según parámetros (`SshCidr`); restringir en real.
- **Django `runserver`** en la demo (no gunicorn/uwsgi): adecuado para la prueba, no para
  producción.
