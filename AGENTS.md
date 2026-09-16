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
| Serverless | AWS Lambda en Python 3.12                         | Handler: `src.handler.lambda_handler`     |
| IaC        | AWS SAM (`aws/template.yaml`)                     | Solo servicios serverless permitidos      |
| Local infra| Docker Compose                                    | `db` + `backend` + `frontend`             |

## MAPA DEL REPOSITORIO

```
backend/    → API Django. apps `users` (Custom User + JWT) y `notes`; cada una con
              models/serializers/views/permissions/services/urls + management/commands
frontend/   → SvelteKit. Salida estática en ./build, servida por Nginx (nginx.conf)
lambda/     → Código Python de Lambdas (src/handler.py)
aws/        → Exclusivamente infra AWS (template.yaml). NADA local aquí.
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

Despliegue serverless (real, sobre AWS — no simuladores):

```bash
cd aws
sam build
sam deploy --guided
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
  (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `POSTGRES_*`,
  `CORS_ALLOWED_ORIGINS`). Defaults de referencia en `.env.example`.
- Prohibido hardcodear credenciales, hosts o puertos en código de aplicación.
- `POSTGRES_HOST` debe seguir siendo `db` en local (nombre de servicio compose).
- Los orígenes CORS nuevos se añaden a `CORS_ALLOWED_ORIGINS`/env, nunca en código.

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
- Métricas `GET /api/internal/notes-status/` protegidas (cualquier usuario activo),
  formato exacto `{"pending": X, "in_progress": Y, "done": Z}`. El dashboard del
  frontend las consume vía `PUBLIC_METRICS_URL`.

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
  Dockerfile y arg de compose). Prohibido hardcodear URLs de infraestructura en el código.

## ALCANCE PENDIENTE (orden sugerido para las 8h)

1. Pruebas mínimas (backend: `TestCase` con pytest o Django tests; frontend: smoke).
2. Rol de la Lambda en un flujo real (p. ej. validación/notificación de cambios de estado).
3. Refresh automático del access token en el frontend (hoy: expira -> re-login).

No ampliar el alcance con funciones no pedidas (realtime, colas, cachés, microservicios).

## ENTORNO DE DESARROLLO

- SO local: Windows / PowerShell 5.1. La ejecución de scripts puede estar bloqueada:
  ante errores de política, invocar `npm.cmd` en lugar de `npm`.
- Docker puede no estar disponible en la máquina del agente: validar entonces con los
  comandos de la sección anterior y dejar `docker compose up` para el evaluador.
