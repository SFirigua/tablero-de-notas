# AGENTS.md — Tablero de Notas (Prueba Técnica)

Contexto obligatorio para agentes IA que trabajan en este repositorio.
Leer completo antes de crear o modificar cualquier archivo.

## REGLAS DE IMPLEMENTACIÓN:

- No cambies las tecnologías indicadas.
- No agregues frameworks o servicios no solicitados.
- No uses LocalStack.
- No uses ECS, App Runner ni servicios alternativos a EC2.
- No introduzcas patrones de arquitectura innecesarios.
- La arquitectura debe ser por capas, pero pragmática.
- Prioriza simplicidad y capacidad de demostración en una prueba con máximo 8 horas efectivas.
- Todo código generado debe ser ejecutable.
- No generes código ficticio, pseudocódigo ni placeholders donde se requiere implementación real.
- Antes de crear archivos, verifica que las decisiones sean compatibles entre sí.
- Mantén separación clara entre configuración local y configuración AWS.
- Todas las URLs, puertos, credenciales y secretos deben configurarse mediante variables de entorno cuando corresponda.

## STACK DEFINITIVO (no negociable)

| Capa       | Tecnología                                        | Notas                                    |
|------------|---------------------------------------------------|------------------------------------------|
| Frontend   | SvelteKit + TypeScript + TailwindCSS              | `@sveltejs/adapter-static`, modo SPA      |
| Backend    | Django 5 + Django REST Framework + SimpleJWT      | PostgreSQL 15 (`psycopg2-binary`)         |
| Serverless | AWS Lambda en Python 3.11                         | Handler: `app.lambda_handler`; `BACKEND_URL` configurable |
| IaC        | AWS SAM (`aws/template.yaml`)                     | Lambda+API GW, EC2, S3 y CloudFront (OAC) |
| Local infra| Docker Compose                                    | `db` + `backend` + `frontend`, red `tablero-net` |

## MAPA DEL REPOSITORIO

```
backend/    → API Django. apps `users` (Custom User + JWT) y `notes`; cada una con
              models/serializers/views/permissions/services/urls + management/commands
frontend/   → SvelteKit. Salida estática en ./build, servida por Nginx (nginx.conf)
lambda/     → app.py — Lambda de métricas (Python 3.11, solo stdlib; GET BACKEND_URL,
              calcula total y responde CORS configurable)
aws/        → Exclusivamente infra AWS: template.yaml (SAM), env.local.json y scripts
              deploy/delete en Bash (.sh) y PowerShell (.ps1).
docker-compose.yml → Exclusivamente infra local. NADA AWS aquí.
```

Convención de separación: lo que vive en `docker-compose.yml` es desarrollo local;
lo que vive en `aws/` es despliegue cloud. Nunca mezclar ambas configuraciones.

## COMANDOS ESENCIALES

Levantar todo (verificado):

```bash
docker compose up --build
docker compose exec backend python manage.py seed_data
```

Desarrollo local backend (sin Docker para el código):

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
docker compose up db -d
python manage.py migrate && python manage.py runserver 8000
```

Desarrollo local frontend:

```bash
cd frontend
npm install    # en Windows/PowerShell usar: npm.cmd install
npm run dev    # proxy /api -> http://localhost:8000 (vite.config.ts)
npm run build  # salida estática en ./build
```

Pruebas locales de la Lambda (requiere `docker compose up -d db backend` primero):

```bash
cd aws
sam build --use-container   # compila en la imagen oficial Lambda; no requiere Python 3.11 local
sam local start-api --docker-network tablero-net --env-vars env.local.json --port 3001
curl -i http://127.0.0.1:3001/metrics -H "Origin: http://localhost:3000"
```

Despliegue serverless (real, sobre AWS — no simuladores):

```bash
cd aws
./deploy.sh          # PowerShell nativo: .\deploy.ps1 (equivale a sam build --use-container + sam deploy)
# Tras el primer deploy: redesplegar con BACKEND_URL=http://<EC2-Dns>:8000/... y
# ALLOWED_ORIGIN=https://<CloudFrontDomain> (outputs del stack).
./delete.sh          # retirada: vacía FrontendBucket + sam delete
```

## PUERTOS Y URLS (inmutables)

| Servicio                     | URL                          |
|------------------------------|------------------------------|
| Frontend (Nginx)             | http://localhost:3000        |
| Backend API (DRF)            | http://localhost:8000/api/   |
| Django Admin                 | http://localhost:8000/django-admin/ |
| PostgreSQL                   | localhost:5432               |

Entre contenedores los servicios se resuelven por nombre: `db`, `backend`, `frontend`.

## CONFIGURACIÓN Y SECRETOS

- Variables del backend: definidas en `backend/config/settings.py` vía `os.environ`
  (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_TIME_ZONE`,
  `POSTGRES_*`, `CORS_ALLOWED_ORIGINS`). Defaults de referencia en `.env.example`.
- Prohibido hardcodear credenciales, hosts o puertos en código de aplicación.
- `POSTGRES_HOST` debe seguir siendo `db` en local (nombre de servicio compose).
- Los orígenes CORS nuevos se añaden a `CORS_ALLOWED_ORIGINS`/env, nunca en código.
- Lambda: `BACKEND_URL` (local: `http://backend:8000/api/internal/notes-status/`;
  AWS: parámetro `BackendUrl` apuntando al EC2 — el hostname `backend` NO existe en AWS)
  y `ALLOWED_ORIGIN` (CORS, CSV; `*` solo opt-in explícito, nunca default).
- Lambda -> backend: `/api/internal/notes-status/` acepta JWT de usuario activo o el
  token server-to-server en la cabecera `X-Internal-Token` (`INTERNAL_API_TOKEN`).
  Debe coincidir entre backend y Lambda: local `dev-internal-token`
  (docker-compose + `aws/env.local.json`); AWS parámetro `InternalApiToken`
  (deploy: env `INTERNAL_API_TOKEN`) y el `.env` del backend en EC2.

## CREDENCIALES DE DEMO (solo seed, no producción)

- Admin: `admin@ejemplo.com` / `Admin123!` (superusuario)
- Usuario: `user@ejemplo.com` / `User123!`
- El comando `seed_data` es idempotente: mantener esa propiedad al modificarlo.

## AUTENTICACIÓN Y ARQUITECTURA POR CAPAS

- Capas obligatorias en backend: **Views -> Serializers -> Services/Permissions -> Models**.
  Las views solo orquestan HTTP; reglas de negocio en `services.py`; control de
  acceso en `permissions.py`. No mover lógica de dominio a las views.
- Custom User (`users/models.py`): `email` como `USERNAME_FIELD` (único), `name`,
  `role` (ADMIN/USER), `is_active` (default True), `is_staff`. `AUTH_USER_MODEL = "users.User"`.
- JWT con `djangorestframework-simplejwt`: access **15 min**, refresh 7 días.
  `POST /api/auth/login/`, `POST /api/auth/refresh/`, `POST /api/auth/logout/`.
- Gate global `users.permissions.IsActiveUser` (DRF DEFAULT_PERMISSION_CLASSES):
  usuario autenticado e `is_active=True` en cada petición; inactivo -> **401**.
- `users` CRUD exclusivo de rol ADMIN (`IsAdminRole`); regla del **último admin
  activo** en `users/services.py` -> **400** al intentar desactivarlo o cambiarle el rol.
- Logout es **del lado cliente** (JWT sin estado): el frontend borra los tokens;
  el endpoint no revoca el access token (expira solo). No agregar blacklist sin pedirlo.
- Métricas `GET /api/internal/notes-status/` protegidas (cualquier usuario activo o
  token interno `X-Internal-Token`), formato exacto
  `{"pending": X, "in_progress": Y, "done": Z}`. El dashboard del frontend las
  consume vía `PUBLIC_METRICS_URL`; la Lambda las consulta con el token interno.

## MODELADO Y MIGRACIONES

- `Note` usa `pos_x`/`pos_y` (**integer**) y `status` con `TextChoices`:
  `PENDING`, `IN_PROGRESS`, `DONE`. Campos: `title`, `text`, `status`, timestamps.
  No tiene `color` ni `owner` (eliminados por alcance).
- Las migraciones `users/0001_initial.py` y `notes/0001_initial.py` están commiteadas
  y son consistentes con los modelos. Al cambiar un modelo: generar nueva migración
  (`makemigrations <app>`) y verificar con `makemigrations --check --dry-run`
  (debe decir "No changes detected").

## VERIFICACIÓN OBLIGATORIA ANTES DE DAR POR TERMINADO

Todo entregable debe ejecutarse de verdad. Checks ya usados y que deben seguir en verde:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend && npm run build && npm run check   # 0 errores
docker compose up --build                        # arranca sin errores
```

## HECHOS TÉCNICOS VERIFICADOS (no revertir)

- `frontend/package-lock.json` está commiteado: el `npm ci` del Dockerfile depende de ello.
- `adapter-static` requiere `export const prerender = true; export const ssr = false;`
  en `src/routes/+layout.ts` (modo SPA con fallback). El warning de "Overwriting
  build\index.html" es esperado e inofensivo.
- El `Dockerfile` del frontend es multietapa: Stage 1 Node 20 build, Stage 2 Nginx
  sirve `/usr/share/nginx/html` (copiado de `/app/build`) en el puerto 3000.
- `nginx.conf`: `try_files $uri $uri.html /index.html;` (SIN `$uri/`). El build genera
  `dashboard.html` y la carpeta `dashboard/` (sin index); con `$uri/` antes del fallback,
  recargar `/dashboard` daba 403. No volver a agregar `$uri/`.
- `CorsMiddleware` debe permanecer ANTES de `CommonMiddleware` en `MIDDLEWARE`.
- DRF: paginación activa (`PAGE_SIZE=50`); el frontend tolera `results` o array plano.
- La API completa fue verificada end-to-end con un harness SQLite temporal
  (40 comprobaciones en verde): login/refresh, CRUD notes, users solo-ADMIN,
  regla del último admin, inactivo -> 401, métricas y logout.
- Frontend: sesión en **sessionStorage** (claves `tablero.token` / `tablero.user`)
  con espejo en memoria (`src/lib/stores/auth.ts`); un 401 en cualquier llamada
  (fetch wrapper en `src/lib/api/client.ts`) limpia la sesión y redirige a `/login`.
- Frontend: rutas `/login`, `/dashboard` (métricas), `/dashboard/board` (canvas
  drag & drop con pointer events + edición inline) y `/dashboard/users` (solo ADMIN).
- `PUBLIC_METRICS_URL` es la ÚNICA variable para las métricas del dashboard: se lee
  con `$env/static/public` (se hornea en la build; `frontend/.env` local, ARG del
  Dockerfile y arg de compose). Local default: `http://localhost:3001/metrics`
  (SAM local). Prohibido hardcodear URLs de infraestructura en el código.
- La red de compose se llama **`tablero-net`** (fijada con `name:`) porque
  `sam local start-api --docker-network tablero-net` la referencia por ese nombre.
- `aws/template.yaml` define `MetricsFunction` (Lambda 3.11, GET/OPTIONS `/metrics`),
  `ApiInstance` (EC2 backend Docker), `FrontendBucket` (S3 privado) y
  `CloudFrontDistribution` (OAC), más apoyos (`FrontendOAC`, `FrontendBucketPolicy`,
  `ApiSecurityGroup`). Outputs: ApiEndpoint, CloudFrontUrl, FrontendBucketName, etc.
- Lambda verificada localmente con harness (13 checks en verde): total calculado,
  CORS por origen configurado, preflight OPTIONS, 403 origen no permitido, 502 si el
  backend cae, eventos v1 y v2.
- La Lambda envía `X-Internal-Token` en su GET al backend cuando `INTERNAL_API_TOKEN`
  está configurado (sin token no agrega la cabecera y el backend responde 401).
- `aws/deploy.sh|deploy.ps1|delete.sh|delete.ps1` deben permanecer consistentes con
  `template.yaml`: parámetros `BackendUrl`/`AllowedOrigin` (+ `EXTRA_OVERRIDES`),
  `STACK_NAME` (default `tablero-notas`), `--resolve-s3 --capabilities CAPABILITY_IAM`;
  delete usa el output `FrontendBucketName` y `sam delete --no-prompts`.
- La Lambda se compila SIEMPRE con `sam build --use-container` (imagen oficial
  `public.ecr.aws/sam/build-python3.11`): sin dependencia del Python del host. El runtime
  del template es `python3.11` (Globals.Function) y los scripts deploy usan ese flag.
- `aws/samconfig.toml` fija los defaults de SAM local: `use_container = true` (build en
  contenedor; evita el error `Binary validation failed for python` con hosts sin Python
  3.11), `docker_network = "tablero-net"`, `env_vars = "env.local.json"`, `port = 3001` y
  `warm_containers = "EAGER"` (contenedores Lambda calientes desde el arranque: sin esto
  SAM crea un contenedor nuevo por petición y /metrics tarda ~3-10 s).
  Por eso `sam build` y `sam local start-api` sin flags también funcionan (desde `aws/`).
- UI usuarios (`/dashboard/users`): crear (modal) + editar nombre/email (modal, PATCH
  existente) + rol/estado en tabla. No duplicar lógica de negocio del backend.
- Dashboard (`/dashboard`): al montar hace un ping autenticado a
  `/api/internal/notes-status/` con el wrapper común (la autoridad de `is_active` sigue
  siendo el backend; un 401 limpia sesión y redirige); las métricas se muestran SIEMPRE
  desde `PUBLIC_METRICS_URL` (Lambda). No implementar un segundo mecanismo de auth.
- `frontend/.env` NO se versiona: en un clon limpio, `npm run dev/build` fuera de Docker
  requiere `cp frontend/.env.example frontend/.env` (el flujo Docker lo provee vía ARG).
- Zona horaria: `TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "America/Bogota")` con
  `USE_TZ = True` (verificado: la DB guarda UTC y el Admin/serializers muestran la hora
  local configurada). No volver a dejar `TIME_ZONE = "UTC"`: causaba desfase -5 h en
  Django Admin.

## ALCANCE PENDIENTE (orden sugerido para las 8h)

1. Pruebas mínimas dentro del repo (backend: `TestCase` con pytest o Django tests;
   frontend: smoke).
2. Refresh automático del access token en el frontend (hoy: expira -> re-login).
3. Automatizar el bootstrap del backend en EC2 (hoy: copiar repo + `docker compose up` manual).

No ampliar el alcance con funciones no pedidas (realtime, colas, cachés, microservicios).

## ENTORNO DE DESARROLLO

- SO local: Windows / PowerShell 5.1. La ejecución de scripts puede estar bloqueada:
  ante errores de política, invocar `npm.cmd` en lugar de `npm`.
- Docker puede no estar disponible en la máquina del agente: validar entonces con los
  comandos de la sección anterior y dejar `docker compose up` para el evaluador.
