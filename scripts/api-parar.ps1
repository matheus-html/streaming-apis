param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc")]
    [string]$Perfil
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

docker compose --profile $Perfil rm -sf $Perfil
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }