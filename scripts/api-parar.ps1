param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc")]
    [string]$Perfil
)

Set-Location (Split-Path $PSScriptRoot -Parent)

$anterior = $ErrorActionPreference
$ErrorActionPreference = "Continue"
docker compose --profile $Perfil rm -sf $Perfil 2>&1 | Out-Null
$ErrorActionPreference = $anterior
exit 0