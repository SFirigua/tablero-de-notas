#!/usr/bin/env bash
#
# Retira el stack AWS SAM del Tablero de Notas:
#   1. Vacía el bucket del frontend (CloudFormation no elimina buckets con objetos).
#   2. Ejecuta `sam delete` (elimina Lambda, EC2, S3, CloudFront y recursos de apoyo).
#
# Uso (Linux/macOS, o Windows con Git Bash / WSL):
#   ./delete.sh
#
# Variables de entorno opcionales:
#   STACK_NAME   nombre del stack  (default: tablero-notas)
#   AWS_REGION   región de AWS     (default: la configurada en la CLI)
#
# Requiere: AWS CLI v2 configurada + AWS SAM CLI.
set -euo pipefail
cd "$(dirname "$0")"

STACK_NAME="${STACK_NAME:-tablero-notas}"

command -v sam >/dev/null 2>&1 || { echo "ERROR: falta AWS SAM CLI (sam)."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "ERROR: falta AWS CLI (aws)."; exit 1; }

REGION_ARGS=()
if [[ -n "${AWS_REGION:-}" ]]; then
  REGION_ARGS=(--region "$AWS_REGION")
fi

BUCKET="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  ${REGION_ARGS[@]+"${REGION_ARGS[@]}"} \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text 2>/dev/null || true)"

if [[ -n "${BUCKET:-}" && "$BUCKET" != "None" ]]; then
  echo "== Vaciando bucket s3://$BUCKET =="
  aws s3 rm "s3://$BUCKET" --recursive ${REGION_ARGS[@]+"${REGION_ARGS[@]}"}
else
  echo "AVISO: no se encontró el bucket del frontend (¿stack ya eliminado?)."
fi

echo "== sam delete (stack: $STACK_NAME) =="
sam delete --stack-name "$STACK_NAME" --no-prompts ${REGION_ARGS[@]+"${REGION_ARGS[@]}"}

echo "OK: recursos eliminados."
