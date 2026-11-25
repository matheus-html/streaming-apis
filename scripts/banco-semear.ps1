$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

docker compose up -d --wait db
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker compose run --rm seed
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }