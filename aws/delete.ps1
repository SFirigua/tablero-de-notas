<#
.SYNOPSIS
  Retira el stack AWS SAM del Tablero de Notas en Windows nativo.

.DESCRIPTION
  Ejecuta las mismas operaciones que aws/delete.sh:
    1. Vacía el bucket del frontend (CloudFormation no elimina buckets con objetos).
    2. `sam delete` (elimina Lambda, EC2, S3, CloudFront y recursos de apoyo).

  Uso (PowerShell):
    .\delete.ps1

  Si la política de ejecución bloquea el script:
    powershell -ExecutionPolicy Bypass -File .\delete.ps1

  Variables de entorno opcionales: STACK_NAME, AWS_REGION.
  Requiere: AWS CLI v2 configurada + AWS SAM CLI.
#>
[CmdletBinding()]
param(
    [string]$StackName = "tablero-notas",
    [string]$Region = $env:AWS_REGION
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

$bucket = aws cloudformation describe-stacks @regionArgs --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text 2>$null
$stackExists = ($LASTEXITCODE -eq 0)

if ($stackExists -and $bucket -and $bucket -ne "None") {
    Write-Host "== Vaciando bucket s3://$bucket =="
    aws s3 rm "s3://$bucket" --recursive @regionArgs
    if ($LASTEXITCODE -ne 0) { throw "No se pudo vaciar el bucket." }
} else {
    Write-Host "AVISO: no se encontró el bucket del frontend (¿stack ya eliminado?)."
}

Write-Host "== sam delete (stack: $StackName) =="
sam delete --stack-name $StackName --no-prompts @regionArgs
if ($LASTEXITCODE -ne 0) { throw "sam delete falló (código $LASTEXITCODE)." }

Write-Host "OK: recursos eliminados."
