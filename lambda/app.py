"""
Lambda `MetricsFunction` del Tablero de Notas.

Flujo:
  1. API Gateway (GET /metrics) invoca este handler.
  2. Consulta el backend Django por HTTP GET (`BACKEND_URL`) y recibe
     {"pending": X, "in_progress": Y, "done": Z}.
  3. Calcula `total = pending + in_progress + done` y responde
     {"total": total, "pending": X, "in_progress": Y, "done": Z}.
  4. Agrega cabeceras CORS configurables (`ALLOWED_ORIGIN`, CSV). Con
     ALLOWED_ORIGIN="*" se emite `Access-Control-Allow-Origin: *` (opt-in);
     el default es un origen concreto, nunca el comodín.

Configuración (variables de entorno, definidas en aws/template.yaml):
  BACKEND_URL     URL del endpoint de métricas del backend.
                  Local: http://backend:8000/api/internal/notes-status/
                  AWS:   http://<EC2-PublicDns>:8000/api/internal/notes-status/
                         (el hostname `backend` NO existe en AWS)
  ALLOWED_ORIGIN  Origen(es) permitido(s) para CORS, separados por coma.

Despliegue: aws/template.yaml (AWS SAM). Pruebas locales: ver README.
"""
import json
import logging
import os
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_BACKEND_URL = "http://backend:8000/api/internal/notes-status/"
DEFAULT_ALLOWED_ORIGIN = "http://localhost:3000"
REQUEST_TIMEOUT_SECONDS = 5.0

CORS_BASE_HEADERS = {
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "600",
}


class BackendError(Exception):
    """El backend no respondió o devolvió un payload inválido."""


def lambda_handler(event, context):
    """Handler de API Gateway (proxy integration)."""
    cors_headers = _cors_headers(event)
    if cors_headers is None:
        _log(event, "Origen no permitido por ALLOWED_ORIGIN.")
        return _response(403, {"detail": "Origen no permitido."}, {})

    method = _get_method(event)

    if method == "OPTIONS":  # preflight CORS
        return _response(204, None, cors_headers)

    if method != "GET":
        return _response(405, {"detail": "Método no permitido. Usa GET /metrics."}, cors_headers)

    try:
        metrics = _fetch_metrics()
    except BackendError as exc:
        logger.warning("Error consultando el backend: %s", exc)
        return _response(502, {"detail": str(exc)}, cors_headers)

    total = metrics["pending"] + metrics["in_progress"] + metrics["done"]
    result = {
        "total": total,
        "pending": metrics["pending"],
        "in_progress": metrics["in_progress"],
        "done": metrics["done"],
    }
    _log(event, f"Métricas OK: {result}")
    return _response(200, result, cors_headers)


# --------------------------------------------------------------------- #
# Internos                                                              #
# --------------------------------------------------------------------- #
def _fetch_metrics():
    """GET al backend Django y validación del payload de métricas."""
    url = os.environ.get("BACKEND_URL", DEFAULT_BACKEND_URL)
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (ValueError, OSError) as exc:
        raise BackendError(f"No se pudo consultar el backend ({url}): {exc}") from exc

    try:
        return {
            "pending": int(payload["pending"]),
            "in_progress": int(payload["in_progress"]),
            "done": int(payload["done"]),
        }
    except (TypeError, KeyError, ValueError) as exc:
        raise BackendError(
            "Respuesta inválida del backend; se esperaba "
            '{"pending": X, "in_progress": Y, "done": Z}.'
        ) from exc


def _cors_headers(event):
    """
    Cabeceras CORS según ALLOWED_ORIGIN (CSV).

    Devuelve None si la petición trae un Origin no permitido (403).
    Sin cabecera Origin (server-to-server/curl) responde con el primer
    origen permitido; nunca emite "*" salvo configuración explícita.
    """
    allowed = [
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGIN", DEFAULT_ALLOWED_ORIGIN).split(",")
        if origin.strip()
    ]
    if not allowed:
        allowed = [DEFAULT_ALLOWED_ORIGIN]

    if "*" in allowed:
        return dict(CORS_BASE_HEADERS, **{"Access-Control-Allow-Origin": "*"})

    request_origin = _get_header(event, "origin")
    if not request_origin:
        return dict(CORS_BASE_HEADERS, **{"Access-Control-Allow-Origin": allowed[0]})
    if request_origin in allowed:
        return dict(
            CORS_BASE_HEADERS,
            **{"Access-Control-Allow-Origin": request_origin, "Vary": "Origin"},
        )
    return None


def _response(status_code, body, extra_headers):
    headers = {"Content-Type": "application/json"}
    headers.update(extra_headers or {})
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": "" if body is None else json.dumps(body),
        "isBase64Encoded": False,
    }


def _get_method(event):
    """Soporta API Gateway REST (v1) y HTTP API (v2)."""
    method = event.get("httpMethod")
    if not method:
        method = (event.get("requestContext", {}).get("http", {}) or {}).get("method")
    return (method or "GET").upper()


def _get_header(event, name):
    headers = event.get("headers") or {}
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return None


def _log(event, message):
    request_id = (event.get("requestContext") or {}).get("requestId", "-")
    logger.info("[%s] %s", request_id, message)
