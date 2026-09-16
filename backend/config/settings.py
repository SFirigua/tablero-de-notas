"""
Configuración de Django para el tablero de notas.

Toda la configuración sensible se lee desde variables de entorno
(inyectadas por docker-compose o el entorno de ejecución).
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------ #
# Seguridad                                                           #
# ------------------------------------------------------------------ #
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "insecure-dev-key-solo-para-desarrollo-local-cambiar-en-produccion",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]


# ------------------------------------------------------------------ #
# Apps y middleware                                                   #
# ------------------------------------------------------------------ #
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "corsheaders",
    # Locales
    "users",
    "notes",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # debe ir antes que CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ------------------------------------------------------------------ #
# Base de datos: PostgreSQL vía variables de entorno                  #
# ------------------------------------------------------------------ #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "tablero"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),  # nombre del servicio en docker-compose
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


# ------------------------------------------------------------------ #
# CORS: permitir peticiones desde el frontend                         #
# ------------------------------------------------------------------ #
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://frontend:3000",
    ).split(",")
    if o.strip()
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS


# ------------------------------------------------------------------ #
# API interna (consumo server-to-server: Lambda y dashboard)          #
# ------------------------------------------------------------------ #
# Token compartido que la Lambda envía en la cabecera X-Internal-Token
# al consultar GET /api/internal/notes-status/. Vacío = solo JWT de
# usuario activo (ver notes.permissions.IsActiveUserOrInternalToken).
INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")


# ------------------------------------------------------------------ #
# Usuario personalizado                                               #
# ------------------------------------------------------------------ #
AUTH_USER_MODEL = "users.User"


# ------------------------------------------------------------------ #
# DRF + JWT                                                           #
# ------------------------------------------------------------------ #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Gate global: toda petición requiere usuario autenticado y activo.
    # Si is_active == False -> 401 (ver users.permissions.IsActiveUser).
    "DEFAULT_PERMISSION_CLASSES": [
        "users.permissions.IsActiveUser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}


# ------------------------------------------------------------------ #
# Validación de passwords                                             #
# ------------------------------------------------------------------ #
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ------------------------------------------------------------------ #
# Internacionalización y estáticos                                    #
# ------------------------------------------------------------------ #
LANGUAGE_CODE = "es"
# Zona horaria de exibición (Admin y serializers). Con USE_TZ = True los
# timestamps se guardan SIEMPRE en UTC en PostgreSQL; Django convierte a esta
# zona al mostrar. Configurable por env (default: hora de Colombia, UTC-5).
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "America/Bogota")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
