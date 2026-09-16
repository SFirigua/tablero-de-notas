#!/usr/bin/env bash
#
# Despliega el stack AWS SAM del Tablero de Notas (aws/template.yaml).
#
# Uso (Linux/macOS, o Windows con Git Bash / WSL):
#   ./deploy.sh                                     # 1ª pasada (defaults del template)
#   BACKEND_URL="http://<EC2-Dns>:8000/api/internal/notes-status/" \
#   ALLOWED_ORIGIN="https://<CloudFrontDomain>" ./deploy.sh   # 2ª pasada con valores reales
#
# Variables de entorno opcionales:
#   STACK_NAME       nombre del stack            (default: tablero-notas)
#   AWS_REGION       región de AWS              (default: la configurada en la CLI)
#   BACKEND_URL      -> parámetro BackendUrl       (URL de la API en EC2; en AWS NUNCA usar "backend")
#   ALLOWED_ORIGIN   -> parámetro AllowedOrigin    (CORS de la Lambda; CSV; usar la URL de CloudFront)
#   INTERNAL_API_TOKEN -> parámetro InternalApiToken (token Lambda -> backend; debe coincidir con el
#                                                    INTERNAL_API_TOKEN del .env del backend en EC2)
#   EXTRA_OVERRIDES  parámetros SAM adicionales (p. ej. "InstanceType=t3.large KeyName=mi-clave")
#
# Compila con `sam build --use-container` (imagen oficial de AWS Lambda): no requiere
# tener Python 3.11 instalado en la máquina, solo Docker en marcha.
#
# Requiere: AWS CLI v2 configurada (aws configure) + AWS SAM CLI + Docker.
set -euo pipefail
cd "$(dirname "$0")"

STACK_NAME="${STACK_NAME:-tablero-notas}"
EXTRA_OVERRIDES="${EXTRA_OVERRIDES:-}"

command -v sam >/dev/null 2>&1 || { echo "ERROR: falta AWS SAM CLI (sam)."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "ERROR: falta AWS CLI (aws)."; exit 1; }

REGION_ARGS=()
if [[ -n "${AWS_REGION:-}" ]]; then
  REGION_ARGS=(--region "$AWS_REGION")
fi

OVERRIDES=()
if [[ -n "${BACKEND_URL:-}" ]]; then
  OVERRIDES+=("BackendUrl=$BACKEND_URL")
fi
if [[ -n "${ALLOWED_ORIGIN:-}" ]]; then
  OVERRIDES+=("AllowedOrigin=$ALLOWED_ORIGIN")
fi
if [[ -n "${INTERNAL_API_TOKEN:-}" ]]; then
  OVERRIDES+=("InternalApiToken=$INTERNAL_API_TOKEN")
fi
if [[ -n "$EXTRA_OVERRIDES" ]]; then
  # shellcheck disable=SC2206
  OVERRIDES+=($EXTRA_OVERRIDES)
fi

PARAM_ARGS=()
if (( ${#OVERRIDES[@]} > 0 )); then
  PARAM_ARGS=(--parameter-overrides "${OVERRIDES[@]}")
fi

echo "== sam build --use-container =="
sam build --use-container

echo "== sam deploy (stack: $STACK_NAME) =="
sam deploy \
  --stack-name "$STACK_NAME" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --no-confirm-changeset \
  ${REGION_ARGS[@]+"${REGION_ARGS[@]}"} \
  ${PARAM_ARGS[@]+"${PARAM_ARGS[@]}"}

echo
echo "== Outputs del stack =="
echo "   (usa BackendUrlForLambda y CloudFrontUrl para la 2ª pasada de deploy.sh)"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  ${REGION_ARGS[@]+"${REGION_ARGS[@]}"} \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" \
  --output table
