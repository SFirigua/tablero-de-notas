# Tablero de Notas (Monorepo)

Prueba técnica fullstack:

- **Frontend:** SvelteKit + TypeScript + TailwindCSS con `@sveltejs/adapter-static` (build estática servida por Nginx).
- **Backend:** Django + Django REST Framework + SimpleJWT + PostgreSQL.
- **Serverless:** AWS Lambda en Python.
- **IaC:** AWS SAM (`aws/template.yaml`).

## Estructura

```
/
├── backend/            # API Django + DRF
│   ├── Dockerfile
│   ├── manage.py
│   ├── config/         # settings, urls, wsgi/asgi
│   ├── users/          # Custom User (email), auth JWT, gestión de usuarios (ADMIN)
│   └── notes/          # notas + comando seed_data + métricas internas
├── frontend/           # SvelteKit + Tailwind (adapter-static -> /build)
│   ├── Dockerfile      # multietapa: Node build -> Nginx
│   ├── nginx.conf
│   ├── svelte.config.js
│   └── src/
│       ├── lib/        # api (fetch wrapper JWT), stores de sesión, componentes (PostIt, Modal)
│       └── routes/     # /login, /dashboard, /dashboard/board, /dashboard/users
├── lambda/             # código Python de la Lambda
│   └── src/handler.py
├── aws/
│   └── template.yaml   # plantilla AWS SAM
├── docker-compose.yml  # db + backend + frontend
└── README.md
```

Arquitectura backend por capas pragmática:

```
Views -> Serializers -> Services/Permissions -> Models
```

Las views solo orquestan HTTP; las reglas de negocio viven en `services.py`;
el control de acceso en `permissions.py`.

## Requisitos

- Docker y Docker Compose v2
- Node 20+ (solo para desarrollo local del frontend)
- Python 3.12+ (solo para desarrollo local del backend)
- AWS CLI + SAM CLI (solo para desplegar la capa serverless)

## Puesta en marcha

```bash
cp .env.example .env        # opcional: ajusta secretos
docker compose up --build
```

| Servicio | URL              |
|----------|------------------|
| Frontend (Nginx + build SvelteKit) | http://localhost:3000 |
| Backend API (DRF)                  | http://localhost:8000/api/ |
| Django Admin (`/django-admin/`)     | http://localhost:8000/django-admin/ |
| PostgreSQL                           | localhost:5432 |

Los contenedores se comunican por nombre de servicio (`db`, `backend`, `frontend`) dentro de la red `tablero-net`.

## Seed de datos

```bash
docker compose exec backend python manage.py seed_data
```

Crea (idempotente):

- Admin: `admin@ejemplo.com` / `Admin123!` (rol ADMIN, superusuario)
- Usuario: `user@ejemplo.com` / `User123!` (rol USER)
- 3 notas en distintas posiciones (`pos_x`, `pos_y`) y estados (`PENDING`, `IN_PROGRESS`, `DONE`).

## Autenticación (JWT)

| Método | Endpoint             | Acceso       | Descripción |
|--------|----------------------|--------------|-------------|
| POST   | `/api/auth/login/`   | Público      | Body `{email, password}` -> `{access, refresh, user}` |
| POST   | `/api/auth/refresh/` | Público      | Body `{refresh}` -> nuevo `{access}` |
| POST   | `/api/auth/logout/`  | Autenticado  | Ver nota de logout abajo |

- El **access token dura 15 minutos** (`SIMPLE_JWT.ACCESS_TOKEN_LIFETIME`); el refresh, 7 días.
- Cada petición autenticada valida que el usuario exista y tenga `is_active=True`.
  Si el usuario fue desactivado, la respuesta es **401 Unauthorized** inmediato.
- **Logout:** con JWT sin estado, el logout es **del lado cliente**: el frontend elimina
  los tokens almacenados y deja de enviarlos. El endpoint `POST /api/auth/logout/` existe
  para cerrar el ciclo (respuesta 200 informativa) y **no invalida** el access token ya
  emitido, que expira solo en 15 minutos. Para revocación server-side real se usaría
  `rest_framework_simplejwt.token_blacklist` (fuera de alcance por diseño).

## API

Todas las rutas (salvo login/refresh) requieren `Authorization: Bearer <access>`.

| Método | Endpoint                    | Rol requerido       | Descripción |
|--------|-----------------------------|---------------------|-------------|
| GET    | `/api/notes/`               | ADMIN o USER activos | Lista paginada |
| POST   | `/api/notes/`               | ADMIN o USER activos | Crear nota |
| GET    | `/api/notes/<id>/`          | ADMIN o USER activos | Detalle |
| PATCH  | `/api/notes/<id>/`          | ADMIN o USER activos | Parcial (`title`, `text`, `status`, `pos_x`, `pos_y`) |
| DELETE | `/api/notes/<id>/`          | ADMIN o USER activos | Eliminar |
| GET    | `/api/users/`               | ADMIN               | Lista de usuarios |
| POST   | `/api/users/`               | ADMIN               | Alta con contraseña inicial (login inmediato) |
| GET    | `/api/users/<id>/`          | ADMIN               | Detalle |
| PATCH  | `/api/users/<id>/`          | ADMIN               | Parcial (`email`, `name`, `role`, `is_active`) |
| GET    | `/api/internal/notes-status/` | Usuario activo    | `{"pending": X, "in_progress": Y, "done": Z}` |

Regla de negocio (`users/services.py`): no se puede **desactivar** ni **cambiar de rol**
al **último administrador activo** del sistema; en ese caso la API responde **400**.
`PUT` está deshabilitado en notas y usuarios: la edición es siempre parcial vía `PATCH`.

## Frontend (rutas y sesión)

| Ruta               | Acceso         | Descripción |
|--------------------|----------------|-------------|
| `/login`           | Público        | Login + botones de **Acceso Rápido** (Admin Demo / User Demo) que autocompletan credenciales |
| `/dashboard`       | Usuario activo | Tarjetas de métricas: Total, Pendientes, En curso, Hechas |
| `/dashboard/board` | Usuario activo | Lienzo libre con post-its arrastrables (pointer events) y edición inline |
| `/dashboard/users` | Solo ADMIN     | Tabla de usuarios + modal de alta + switch Activo/Inactivo + cambio de rol |

- El access token se guarda en **sessionStorage** (`tablero.token`) con espejo en memoria
  (`src/lib/stores/auth.ts`) y se envía vía `Authorization: Bearer <token>`.
- El fetch wrapper (`src/lib/api/client.ts`) intercepta **HTTP 401**: limpia la sesión y
  redirige a `/login`.
- **Métricas:** el dashboard consume exclusivamente la variable `PUBLIC_METRICS_URL`
  (nada hardcodeado en el código). Local: `http://localhost:3001/metrics`;
  AWS: `<URL_API_GATEWAY>/metrics`. Por defecto el compose apunta al endpoint de Django
  (`http://localhost:8000/api/internal/notes-status/`) para que la demo funcione sin
  servicios extra; se sobreescribe con la variable de entorno del mismo nombre.

## Desarrollo local

**Backend**

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
docker compose up db -d                            # solo la base de datos
python manage.py migrate
python manage.py runserver 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev        # proxy /api -> http://localhost:8000
npm run build      # salida estática en ./build (adapter-static)
```

## Serverless (AWS SAM)

```bash
cd aws
sam build
sam deploy --guided
```

`template.yaml` define la función `NotesProcessor` (Python 3.12, código en `../lambda/`) expuesta vía HTTP API en `POST /notes/validate`.

## Variables de entorno (backend)

| Variable               | Default                          | Descripción                       |
|------------------------|----------------------------------|-----------------------------------|
| `DJANGO_SECRET_KEY`    | —                                | Clave secreta de Django           |
| `DJANGO_DEBUG`         | `False`                          | Modo debug                        |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`            | Hosts permitidos (CSV)            |
| `POSTGRES_DB`          | `tablero`                        | Nombre de la base                 |
| `POSTGRES_USER`        | `postgres`                       | Usuario de PostgreSQL             |
| `POSTGRES_PASSWORD`    | `postgres`                       | Password de PostgreSQL            |
| `POSTGRES_HOST`        | `db`                             | Host (nombre del servicio compose)|
| `POSTGRES_PORT`        | `5432`                           | Puerto de PostgreSQL              |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000`          | Orígenes CORS permitidos (CSV)    |

## Variables de entorno (frontend)

| Variable             | Default                                            | Descripción |
|----------------------|----------------------------------------------------|-------------|
| `PUBLIC_METRICS_URL` | `http://localhost:8000/api/internal/notes-status/` | URL del servicio de métricas que consume `/dashboard` (se hornea en la build estática) |
