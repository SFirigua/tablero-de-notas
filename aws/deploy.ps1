<#
.SYNOPSIS
  Despliega el stack AWS SAM del Tablero de Notas (aws/template.yaml) en Windows nativo.

.DESCRIPTION
  Ejecuta las mismas operaciones que aws/deploy.sh:
  `sam build --use-container` y `sam deploy` (--resolve-s3, CAPABILITY_IAM, sin
  confirmación interactiva), y al final muestra los Outputs del stack.

  `--use-container` compila dentro de la imagen oficial de AWS Lambda, así no hace
  falta tener Python 3.11 instalado en la máquina: solo Docker en marcha.

  Uso (PowerShell):
    .\deploy.ps1
    $env:BACKEND_URL  = "http://<EC2-Dns>:8000/api/internal/notes-status/"; .\deploy.ps1
    $env:ALLOWED_ORIGIN = "https://<CloudFrontDomain>"; .\deploy.ps1

  Si la política de ejecución bloquea el script:
    powershell -ExecutionPolicy Bypass -File .\deploy.ps1

  Variables de entorno opcionales: STACK_NAME, AWS_REGION, BACKEND_URL, ALLOWED_ORIGIN,
  INTERNAL_API_TOKEN (token Lambda -> backend; debe coincidir con el del backend en EC2),
  EXTRA_OVERRIDES (p. ej. "InstanceType=t3.large KeyName=mi-clave").
  Requiere: AWS CLI v2 configurada + AWS SAM CLI.
#>
[CmdletBinding()]
param(
    [string]$StackName = "tablero-notas",
    [string]$Region = $env:AWS_REGION,
    [string]$BackendUrl = $env:BACKEND_URL,
    [string]$AllowedOrigin = $env:ALLOWED_ORIGIN,
    [string]$InternalApiToken = $env:INTERNAL_API_TOKEN,
    [string]$ExtraOverrides = $env:EXTRA_OVERRIDES
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if ($env:STACK_NAME) { $StackName = $env:STACK_NAME }

foreach ($tool in @("sam", "aws")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "ERROR: falta '$tool' en el PATH."
    }
}

$regionArgs = @()
if ($Region) { $regionArgs += @("--region", $Region) }

$overrides = @()
if ($BackendUrl) { $overrides += "BackendUrl=$BackendUrl" }
if ($AllowedOrigin) { $overrides += "AllowedOrigin=$AllowedOrigin" }
if ($InternalApiToken) { $overrides += "InternalApiToken=$InternalApiToken" }
if ($ExtraOverrides) {
    $overrides += $ExtraOverrides.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
}

$paramArgs = @()
if ($overrides.Count -gt 0) { $paramArgs = @("--parameter-overrides") + $overrides }

Write-Host "== sam build --use-container =="
sam build --use-container
if ($LASTEXITCODE -ne 0) { throw "sam build falló (código $LASTEXITCODE)." }

Write-Host "== sam deploy (stack: $StackName) =="
sam deploy @regionArgs @paramArgs --stack-name $StackName --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset
if ($LASTEXITCODE -ne 0) { throw "sam deploy falló (código $LASTEXITCODE)." }

Write-Host "`n== Outputs del stack =="
Write-Host "   (usa BackendUrlForLambda y CloudFrontUrl para la 2ª pasada de deploy.ps1)"
aws cloudformation describe-stacks @regionArgs --stack-name $StackName --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
