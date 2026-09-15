"""
Lambda de ejemplo (Python 3.12) para eventos del tablero de notas.

Punto de entrada configurado en aws/template.yaml:
    Handler: src.handler.lambda_handler
"""
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALID_STATUSES = {"PENDING", "IN_PROGRESS", "DONE"}


def lambda_handler(event, context):
    logger.info("Evento recibido: %s", json.dumps(event, default=str))

    try:
        body = event.get("body")
        payload = json.loads(body) if isinstance(body, str) else (body or {})
        action = payload.get("action", "ping")

        if action == "validate_status":
            status = payload.get("status")
            valid = status in VALID_STATUSES
            return _response(200, {"status": status, "valid": valid})

        return _response(200, {"message": "pong", "stage": os.environ.get("STAGE", "dev")})
    except Exception:
        logger.exception("Error procesando evento")
        return _response(500, {"error": "Internal server error"})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
