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
├── aws/                # template.yaml (SAM), env.local.json (pruebas locales)
├── docker-compose.yml  # infra local: db + backend + frontend (red tablero-net)
└── README.md
```

---

## 3. Requisitos previos

- Docker Engine + Docker Compose v2
- Node.js 20+ (solo desarrollo local del frontend)
- Python 3.12+ (solo desarrollo local del backend)
- AWS CLI v2 y AWS SAM CLI (para la capa serverless: `sam build`, `sam local`, `sam deploy`)
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
| GET    | `/api/internal/notes-status/` | Usuario activo      | `{"pending": X, "in_progress": Y, "done": Z}` |

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

**Métricas**: única variable de configuración `PUBLIC_METRICS_URL` (sin URLs hardcodeadas
en el código). Local: `http://localhost:3001/metrics` (SAM local). AWS:
`https://<API_GATEWAY>/Prod/metrics`. Requiere que la Lambda esté levantada (ver sección 9);
alternativa sin SAM: `http://localhost:8000/api/internal/notes-status/` (Django directo).

---

## 9. Probar la Lambda localmente con SAM

Requiere el backend en marcha (`docker compose up -d db backend`) y la red `tablero-net`
creada por compose. `aws/env.local.json` inyecta la configuración local de la función:

```json
{
  "MetricsFunction": {
    "BACKEND_URL": "http://backend:8000/api/internal/notes-status/",
    "ALLOWED_ORIGIN": "http://localhost:3000"
  }
}
```

Ejecución:

```bash
cd aws
sam build
sam local start-api --docker-network tablero-net --env-vars env.local.json --port 3001
```

Prueba (en otra terminal):

```bash
curl -i http://127.0.0.1:3001/metrics -H "Origin: http://localhost:3000"
# → {"total": 3, "pending": 1, "in_progress": 1, "done": 1} + cabeceras CORS
```

- `<nombre_red_docker>` = **`tablero-net`** (nombre fijo declarado en `docker-compose.yml`
  con `name:`, para que no dependa del nombre del proyecto).
- La Lambda llama a `BACKEND_URL` (`http://backend:8000/...`), resoluble **solo** dentro de
  la red Docker; en AWS ese hostname no existe y se usa el parámetro `BackendUrl`.

---

## 10. Despliegue y retirada en AWS

### 10.1 Infraestructura (SAM)

```bash
cd aws
sam build
sam deploy --guided
# Stack: tablero-notas | Región: p.ej. us-east-1
# Parámetros: BackendUrl (dejar default en el primer deploy), AllowedOrigin,
#             InstanceType, KeyName, SshCidr
```

Tras el primer deploy, tomar de los **Outputs**:

- `BackendUrlForLambda` (DNS público del EC2) y `CloudFrontUrl`.

Y redesplegar con la configuración real (segunda pasada):

```bash
sam deploy --parameter-overrides \
  BackendUrl=http://<ApiInstancePublicDns>:8000/api/internal/notes-status/ \
  AllowedOrigin=https://<CloudFrontDomain> \
  --no-confirm-changeset
```

> En AWS, `BackendUrl` apunta a la API desplegada en EC2. El hostname `backend` de Docker
> **nunca** se usa en la nube.

### 10.2 Backend en EC2

La instancia nace con Docker y el plugin de Compose instalados (UserData). Copiar el
proyecto y levantar los contenedores:

```bash
scp -i <clave.pem> -r ./backend ./docker-compose.yml ec2-user@<ApiInstancePublicDns>:~
ssh -i <clave.pem> ec2-user@<ApiInstancePublicDns>
# En la instancia:
cp backend/.env.example backend/.env   # ajustar DJANGO_ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS
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
# El bucket debe vaciarse antes de eliminar el stack:
aws s3 rm s3://<FrontendBucketName> --recursive
cd aws
sam delete --stack-name tablero-notas
```

---

## 11. Configuración local vs AWS

| Aspecto               | Local (docker compose / SAM local)                              | AWS (SAM template)                                         |
|-----------------------|-----------------------------------------------------------------|------------------------------------------------------------|
| `BACKEND_URL`         | `http://backend:8000/api/internal/notes-status/` (red `tablero-net`) | `http://<EC2-PublicDns>:8000/api/internal/notes-status/` (parámetro `BackendUrl`) |
| CORS de la Lambda     | `ALLOWED_ORIGIN=http://localhost:3000`                          | `AllowedOrigin=https://<CloudFrontDomain>` (parámetro, CSV) |
| `PUBLIC_METRICS_URL`  | `http://localhost:3001/metrics` (SAM local)                     | `https://<API_GATEWAY>/Prod/metrics`                       |
| Frontend              | Nginx sirviendo `./build` en `:3000`                            | S3 + CloudFront (OAC)                                      |
| Base de datos         | Contenedor `db` + volumen `postgres_data`                       | PostgreSQL en Docker sobre la instancia EC2                |
| Hostnames             | `db`, `backend`, `frontend`, `tablero-net` (DNS de Docker)      | DNS públicos de EC2/CloudFront/API Gateway (nunca `backend`) |

**CORS**: la Lambda permite configurar los orígenes por parámetro/variable
(`ALLOWED_ORIGIN`, lista separada por comas) y responde con `Vary: Origin`. Enviar
`Access-Control-Allow-Origin: *` es posible pero **opt-in** (`AllowedOrigin="*"`), nunca
la única configuración; los orígenes no permitidos reciben 403.

---

## 12. Registro de tiempo estimado (≈7 horas efectivas)

| Fase                                                        | Tiempo |
|-------------------------------------------------------------|--------|
| Backend: custom user, JWT, permisos, capas, reglas, seed    | 2.5 h  |
| Frontend: login, tablero drag & drop, dashboard, usuarios   | 2.0 h  |
| Lambda + plantilla SAM (S3/CloudFront/OAC, EC2)             | 1.0 h  |
| Docker/infra local, documentación y scripts                 | 1.0 h  |
| Verificación end-to-end (API 40 checks, Lambda 13 checks)   | 0.5 h  |
| **Total**                                                   | **≈7 h** |

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
