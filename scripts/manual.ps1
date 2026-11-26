param(
    [ValidateSet("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc")]
    [string]$Versao,
    [switch]$Manter
)

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$todas = @("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc")

if (-not $Versao) {
    Write-Host "Escolha a versao:"
    for ($i = 0; $i -lt $todas.Count; $i++) {
        Write-Host ("  {0}) {1}" -f ($i + 1), $todas[$i])
    }
    $escolha = [int](Read-Host "Numero")
    if ($escolha -lt 1 -or $escolha -gt $todas.Count) {
        Write-Host "Opcao invalida."
        exit 1
    }
    $Versao = $todas[$escolha - 1]
}

$api = $Versao.Split("-")[1]

foreach ($v in $todas) {
    docker compose --profile $v rm -sf $v 2>&1 | Out-Null
}

docker compose up -d --wait db
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker compose --profile $Versao up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$fim = (Get-Date).AddSeconds(120)
$pronto = $false
while ((Get-Date) -lt $fim) {
    try {
        $cliente = New-Object System.Net.Sockets.TcpClient
        $cliente.Connect("localhost", 8080)
        $cliente.Close()
        $pronto = $true
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $pronto) {
    Write-Host "A versao $Versao nao subiu em 120 segundos."
    docker compose --profile $Versao logs --tail 40 $Versao
    exit 1
}
Start-Sleep -Seconds 3

Write-Host "Servico $Versao disponivel em http://localhost:8080"
docker compose --profile loadtest run --rm --entrypoint python locust manual.py --api $api --host "http://${Versao}:8080" --versao $Versao

if (-not $Manter) {
    docker compose --profile $Versao rm -sf $Versao 2>&1 | Out-Null
    Write-Host "Servico $Versao encerrado."
} else {
    Write-Host "Servico $Versao mantido em http://localhost:8080 (pare com .\scripts\api-parar.ps1 -Perfil $Versao)."
}