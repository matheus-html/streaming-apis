$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

docker compose exec -T db psql -U streaming -d postgres -c "DROP DATABASE IF EXISTS streaming WITH (FORCE)"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker compose exec -T db psql -U streaming -d postgres -c "CREATE DATABASE streaming TEMPLATE streaming_base"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }