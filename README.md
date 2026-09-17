# Tablero de Notas — Prueba Técnica

Sistema de tablero de notas compartido: post-its arrastrables con
posición libre y estados, autenticación JWT, gestión de usuarios por
roles, métricas internas y una capa serverless sobre AWS.

| Capa              | Tecnología                                                        |
|-------------------|-------------------------------------------------------------------|
| Frontend          | SvelteKit + TypeScript + TailwindCSS (`adapter-static`, modo SPA)  |
| Servidor estático | Nginx (local) / S3 + CloudFront con OAC (AWS)                      |
| Backend           | Django 5 + Django REST Framework + SimpleJWT (access 15 min)       |
| Base de datos     | PostgreSQL 15 (volumen Docker persistente)                         |
| Serverless        | AWS Lambda Python 3.11 (métricas) + API Gateway `GET /metrics`     |
| IaC               | AWS SAM (`aws/template.yaml`)                                      |
| Infra local       | Docker Compose (`db` + `backend` + `frontend`, red `tablero-net`)  |

**Versión entregada:** tag **`v1.0.0`** — repositorio:
https://github.com/SFirigua/tablero-de-notas

---

## Quickstart: de `git clone` a la aplicación funcionando

Todo el flujo local funciona **sin cuenta AWS**. Con Docker en marcha alcanza para la
aplicación; SAM CLI agrega la Lambda de métricas que consume el dashboard.

### Requisitos

| Herramienta                       | Para qué                                             |
|-----------------------------------|------------------------------------------------------|
| Docker Engine + Docker Compose v2 | `db` + `backend` + `frontend` y build de la Lambda   |
| AWS SAM CLI                       | Lambda de métricas en local (`sam build`, `sam local`) |
| AWS CLI v2                        | Despliegue real en AWS                               |
| Node.js 20+ / Python 3.12+        | Desarrollo fuera de Docker                           |

### 1. Clonar el repositorio

```bash
git clone https://github.com/SFirigua/tablero-de-notas.git
cd tablero-de-notas
```

### 2. Crear el `.env` (opcional)

```bash
cp .env.example .env          # Linux/macOS/Git Bash
Copy-Item .env.example .env   # Windows PowerShell
```

Sin este paso, Docker Compose arranca con los valores de demo por defecto. `.env.example`
documenta cada variable (secretos Django, PostgreSQL, CORS y `INTERNAL_API_TOKEN`).

### 3. Levantar la aplicación

```bash
docker compose up -d --build
```

Arranca `db` (PostgreSQL), `backend` (aplica migraciones y sirve la API en `:8000`) y
`frontend` (Nginx en `:3000`), conectados por la red `tablero-net`.

### 4. Cargar los datos de demostración

```bash
docker compose exec backend python manage.py seed_data
```

Es idempotente (puede repetirse sin duplicar datos). Si falla porque el backend todavía
está migrando, espera unos segundos y repítelo.

### 5. Levantar la Lambda de métricas (en una segunda terminal)

Requiere que el paso 3 esté en marcha (la red `tablero-net` ya existe):

```bash
cd aws
sam build --use-container   # compila con la imagen oficial de AWS; no requiere Python 3.11 local
sam local start-api         # samconfig.toml fija red, env, puerto 3001 y warm containers
```

El endpoint queda en `http://localhost:3001/metrics`. El dashboard (`/dashboard`) consume
esta Lambda a través de `PUBLIC_METRICS_URL`; **sin la Lambda en marcha el dashboard
muestra un error de conexión**. Los detalles técnicos (por qué bastan esos dos comandos,
CORS, token interno) están en **Detalles de la Lambda de métricas**.

### 6. Abrir la aplicación e iniciar sesión

| Servicio                     | URL                                    |
|------------------------------|----------------------------------------|
| Frontend                     | http://localhost:3000                  |
| Backend API (DRF)            | http://localhost:8000/api/             |
| Django Admin                 | http://localhost:8000/django-admin/    |
| Lambda de métricas (SAM local) | http://localhost:3001/metrics        |

Abre http://localhost:3000 y entra con las cuentas de demostración (sección siguiente) o
con los botones de **Acceso Rápido** de la pantalla de login.

### 7. Verificar el flujo completo (opcional)

```bash
curl -i http://127.0.0.1:3001/metrics -H "Origin: http://localhost:3000"
# → HTTP 200 con {"total": N, "pending": X, "in_progress": Y, "done": Z} y cabeceras CORS
```

> **Windows/PowerShell:** `curl` es un alias de `Invoke-WebRequest` y no acepta `-H`;
> usa `curl.exe`. Si la política de scripts bloquea `npm`, usa `npm.cmd`.

---

## Cuentas de demostración

| Cuenta     | Email                | Contraseña  | Rol                  |
|------------|----------------------|-------------|----------------------|
| Admin Demo | `admin@ejemplo.com`  | `Admin123!` | ADMIN                |
| User Demo  | `user@ejemplo.com`   | `User123!`  | USER                 |

La pantalla de `/login` incluye botones de **Acceso Rápido** que autocompletan estas
credenciales. Los usuarios creados desde `/dashboard/users` reciben una contraseña
inicial y pueden iniciar sesión de inmediato.

---

## Uso de la aplicación

| Ruta               | Acceso         | Descripción |
|--------------------|----------------|-------------|
| `/login`           | Público        | Login + Acceso Rápido |
| `/dashboard`       | Usuario activo | Métricas (Lambda): Total, Pendientes, En curso, Hechas |
| `/dashboard/board` | Usuario activo | Lienzo de post-its: drag & drop (pointer events), edición inline, crear/eliminar, cambiar estado |
| `/dashboard/users` | Solo ADMIN     | Tabla de usuarios: alta por modal, editar nombre/email, rol y estado activo/inactivo |

Recorrido sugerido: iniciar sesión → ver métricas en `/dashboard` → crear y arrastrar
notas en `/dashboard/board` → gestionar usuarios en `/dashboard/users` (solo ADMIN).

### Endpoints principales de la API

JWT con SimpleJWT: access de **15 minutos**, refresh de 7 días, enviado en
`Authorization: Bearer <token>`.

| Método | Endpoint                      | Acceso                        | Descripción |
|--------|-------------------------------|-------------------------------|-------------|
| POST   | `/api/auth/login/`            | Público                       | `{email, password}` → `{access, refresh, user}` |
| POST   | `/api/auth/refresh/`          | Público                       | `{refresh}` → nuevo access |
| POST   | `/api/auth/logout/`           | Autenticado                   | Responde 200; el logout es del lado cliente |
| GET/POST/PATCH/DELETE | `/api/notes/...` | ADMIN y USER activos          | CRUD de notas (`title`, `text`, `status`, `pos_x`, `pos_y`) |
| GET/POST/PATCH | `/api/users/...`     | Solo ADMIN                    | CRUD de usuarios; contraseña inicial obligatoria al crear |
| GET    | `/api/internal/notes-status/` | Usuario activo o token interno | `{"pending": X, "in_progress": Y, "done": Z}` |

- Usuario con `is_active=False` → **401** en cada petición.
- No se puede desactivar ni cambiar de rol al **último administrador activo** → **400**.
- El logout no revoca el access token (JWT sin estado): el frontend borra los tokens y
  el access expira solo.

---

## Persistencia

- PostgreSQL 15 corre en el contenedor `db` y guarda sus datos en el volumen nombrado
  **`postgres_data`** (`/var/lib/postgresql/data`, definido en `docker-compose.yml`).
- Los datos **sobreviven** a `docker compose down`, reinicios y reconstrucciones.
- El backend aplica las migraciones automáticamente al arrancar
  (`python manage.py migrate && runserver`).
- Reset total (borra la base): `docker compose down -v` y repetir los pasos 3 y 4 del
  Quickstart.

Comandos útiles de operación:

```bash
docker compose logs -f backend    # logs en vivo
docker compose down               # detener (los datos persisten)
docker compose down -v            # reset total (borra el volumen)
```

---

## Arquitectura

### Local (Docker Compose + SAM local)

```
navegador ─▶ frontend (Nginx :3000) ──/api/*──▶ backend (Django :8000) ─▶ db (PostgreSQL 15)
     │                                                ▲
     └── PUBLIC_METRICS_URL ─▶ Lambda local (:3001) ──┘        [red tablero-net]
```

- El dashboard pide `GET /metrics` a la Lambda; la Lambda consulta al backend por
  `BACKEND_URL` (`http://backend:8000/...`, DNS interno de Docker).
- El navegador no habla directo con Django: Nginx hace de proxy inverso de `/api/*`
  (sin CORS en local para la API).

### AWS (SAM: `aws/template.yaml`)

```
usuario ─▶ CloudFront (OAC) ─▶ S3 (frontend estático)
usuario ─▶ API Gateway ─▶ Lambda ─▶ EC2 (Docker: Django + PostgreSQL)
                                     (el hostname `backend` NO existe en AWS)
```

Recursos del template: `MetricsFunction` (Lambda 3.11 + `GET/OPTIONS /metrics`),
`ApiInstance` (EC2 para los contenedores Docker), `FrontendBucket` (S3 privado) y
`CloudFrontDistribution` (con OAC), más los recursos de apoyo necesarios
(`FrontendOAC`, `FrontendBucketPolicy`, `ApiSecurityGroup`).

---

## Desarrollo sin Docker (opcional)

Backend:

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
docker compose up db -d                            # solo PostgreSQL
python manage.py migrate && python manage.py runserver 8000
```

Frontend (en un clon limpio hay que crear el `.env` local; los `.env` reales no se
versionan):

```bash
cd frontend
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
npm install                   # Windows/PowerShell: npm.cmd install
npm run dev                   # Vite en :5173 con proxy /api -> http://localhost:8000
npm run build                 # salida estática en ./build
```

`PUBLIC_METRICS_URL` se resuelve así: **Docker** la hornea desde el build arg de
`docker-compose.yml`/`Dockerfile` (no necesita `.env`); **`npm run dev`/`npm run build`
locales** la leen de `frontend/.env`.

> Nota: `npm run dev` sirve el frontend en `http://localhost:5173`, pero la Lambda
> permite solo `http://localhost:3000`. Para ver el dashboard con métricas en ese modo,
> agrega `http://localhost:5173` al `ALLOWED_ORIGIN` de `aws/env.local.json`. Para el
> flujo completo, usa el Quickstart (Docker en `:3000`).

---

## Detalles de la Lambda de métricas

`aws/env.local.json` define la configuración local de la función:

```json
{
  "MetricsFunction": {
    "BACKEND_URL": "http://backend:8000/api/internal/notes-status/",
    "ALLOWED_ORIGIN": "http://localhost:3000",
    "INTERNAL_API_TOKEN": "dev-internal-token"
  }
}
```

- `BACKEND_URL` se resuelve solo dentro de la red Docker; por eso `sam local start-api`
  se une a `tablero-net`. En AWS el hostname `backend` no existe: se usa el parámetro
  `BackendUrl` (DNS público del EC2).
- `aws/samconfig.toml` fija los defaults del flujo local (`use_container = true`, red
  `tablero-net`, `env.local.json`, puerto `3001` y `warm_containers = "EAGER"`), así que
  desde `aws/` los comandos funcionan a secas.
  - `--use-container` compila con la imagen oficial `public.ecr.aws/sam/build-python3.11`:
    el artefacto es idéntico al runtime de AWS y no depende del Python del host. Sin él,
    `sam build` puede fallar con `Binary validation failed for python`.
  - `warm_containers = "EAGER"` arranca los contenedores junto con SAM y las peticiones
    responden en ~1 s; sin esto SAM crea un contenedor nuevo por petición (cold start de
    3-10 s).
- **CORS**: `ALLOWED_ORIGIN` acepta una lista separada por comas; un origen no permitido
  recibe **403**. El comodín `*` es opt-in explícito (`AllowedOrigin="*"` en el deploy),
  nunca el default. Sin cabecera `Origin` (server-to-server/curl) responde con el primer
  origen permitido.
- **Endpoint interno protegido**: `/api/internal/notes-status/` acepta el JWT de un
  usuario activo (lo usa el dashboard para validar la sesión) o el token
  server-to-server `X-Internal-Token` que envía la Lambda. Debe coincidir entre backend
  y Lambda: local `dev-internal-token` (compose + `env.local.json`); en AWS, parámetro
  `InternalApiToken` del stack y `.env` del EC2.
- La Lambda calcula `total = pending + in_progress + done` y responde
  `{"total": X, "pending": X, "in_progress": Y, "done": Z}`; si el backend no responde,
  devuelve **502**.

---

## Despliegue y retirada en AWS

Scripts en `aws/` (equivalen a `sam build --use-container` + `sam deploy`/`sam delete` y
muestran los Outputs):

| Entorno                                   | Despliegue     | Retirada       |
|-------------------------------------------|----------------|----------------|
| Linux/macOS (o Windows con Git Bash/WSL)  | `./deploy.sh`  | `./delete.sh`  |
| Windows PowerShell nativo                 | `.\deploy.ps1` | `.\delete.ps1` |

> Requieren AWS CLI v2 configurada (`aws configure`) y SAM CLI en el PATH. Si la política
> de ejecución bloquea los `.ps1`, invócalos con
> `powershell -ExecutionPolicy Bypass -File .\deploy.ps1`.

### 1) Infraestructura (SAM)

Primera pasada con los defaults del template:

```bash
cd aws
./deploy.sh          # PowerShell: .\deploy.ps1
```

Toma de los **Outputs** del stack `BackendUrlForLambda` (DNS público del EC2) y
`CloudFrontUrl`, y redesplega con la configuración real:

```bash
BACKEND_URL="http://<ApiInstancePublicDns>:8000/api/internal/notes-status/" \
ALLOWED_ORIGIN="https://<CloudFrontDomain>" \
INTERNAL_API_TOKEN="<token-propio>" \
./deploy.sh
```

En PowerShell:

```powershell
$env:BACKEND_URL="http://<ApiInstancePublicDns>:8000/api/internal/notes-status/"
$env:ALLOWED_ORIGIN="https://<CloudFrontDomain>"
$env:INTERNAL_API_TOKEN="<token-propio>"
.\deploy.ps1
```

Parámetros del template: `BackendUrl`, `AllowedOrigin`, `InternalApiToken`,
`InstanceType`, `KeyName`, `SshCidr` (+ `EXTRA_OVERRIDES`, p. ej.
`EXTRA_OVERRIDES="InstanceType=t3.large KeyName=mi-clave"`). El nombre del stack por
defecto es `tablero-notas` (`STACK_NAME`).

### 2) Backend en EC2

La instancia nace con Docker y el plugin de Compose instalados (UserData). Copia el
proyecto y levanta los contenedores:

```bash
scp -i <clave.pem> -r ./backend ./docker-compose.yml ./.env.example ec2-user@<ApiInstancePublicDns>:~
ssh -i <clave.pem> ec2-user@<ApiInstancePublicDns>
# En la instancia:
cp .env.example .env    # ajustar DJANGO_ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS e INTERNAL_API_TOKEN
docker compose up -d --build db backend
docker compose exec backend python manage.py seed_data
```

`INTERNAL_API_TOKEN` debe coincidir con el parámetro `InternalApiToken` del stack SAM.

### 3) Frontend en S3 + CloudFront (OAC)

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
aws cloudfront create-invalidation \
  --distribution-id <CloudFrontDistributionId> --paths "/*"
```

### 4) Retirada

```bash
cd aws
./delete.sh          # PowerShell: .\delete.ps1
```

Los scripts vacían `FrontendBucket` (CloudFormation no elimina buckets con objetos) y
ejecutan `sam delete`. Manualmente:
`aws s3 rm s3://<FrontendBucketName> --recursive` + `sam delete --stack-name tablero-notas`.

---

## Configuración local vs AWS

| Aspecto              | Local (Docker Compose / SAM local)                             | AWS (SAM template)                                         |
|----------------------|----------------------------------------------------------------|------------------------------------------------------------|
| `BACKEND_URL`        | `http://backend:8000/api/internal/notes-status/` (red `tablero-net`) | `http://<EC2-PublicDns>:8000/api/internal/notes-status/` (parámetro `BackendUrl`) |
| CORS de la Lambda    | `ALLOWED_ORIGIN=http://localhost:3000`                         | `AllowedOrigin=https://<CloudFrontDomain>` (parámetro, CSV) |
| Token interno        | `dev-internal-token` (compose + `env.local.json`)              | parámetro `InternalApiToken` (debe coincidir con el `.env` del EC2) |
| `PUBLIC_METRICS_URL` | `http://localhost:3001/metrics` (SAM local)                    | `https://<API_GATEWAY>/Prod/metrics`                       |
| Frontend             | Nginx sirviendo `./build` en `:3000`                           | S3 + CloudFront (OAC)                                      |
| Base de datos        | contenedor `db` + volumen `postgres_data`                      | PostgreSQL en Docker sobre la instancia EC2                |
| Hostnames            | `db`, `backend`, `frontend`, `tablero-net` (DNS de Docker)     | DNS públicos de EC2/CloudFront/API Gateway (nunca `backend`) |

---

## Tiempo empleado (≈7.5 horas efectivas)

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

## Limitaciones y pendientes conocidos

- **HTTP sin TLS en el backend EC2** (demo): en producción iría detrás de ALB + ACM o
  CloudFront con origen custom.
- **Bootstrap manual del backend en EC2** (copiar repo + `docker compose up`); no hay
  CI/CD ni user-data completo de la aplicación.
- **PostgreSQL en el mismo EC2** (pragmático para la prueba); en producción → RDS.
- **Sin tests automatizados dentro del repo** (se usaron harness de verificación
  externos); pendiente: `TestCase`/pytest en backend y smoke en frontend.
- **Refresh automático del access token en el frontend**: hoy, al expirar (15 min) el
  wrapper detecta 401, limpia la sesión y redirige a `/login`.
- **Bucket S3 sin versionado/logging** y **CloudFront sin dominio propio/ACM**.
- **Security Group de demo** con 8000 y 22 abiertos según parámetros (`SshCidr`);
  restringir en un entorno real.
- **Django `runserver`** en la demo (no gunicorn/uwsgi): adecuado para la prueba, no para
  producción.
- **`npm run dev` (Vite `:5173`) no está incluido en el CORS de la Lambda**: el dashboard
  con métricas requiere agregar ese origen a `ALLOWED_ORIGIN` o usar el flujo Docker.
