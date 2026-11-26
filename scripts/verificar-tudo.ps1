param(
    [string[]]$Versoes = @("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc")
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location (Split-Path $PSScriptRoot -Parent)

$todas = @("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc")

function Esperar-Porta {
    $fim = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $fim) {
        try {
            $cliente = New-Object System.Net.Sockets.TcpClient
            $cliente.Connect("localhost", 8080)
            $cliente.Close()
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

docker compose up -d --wait db 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "O banco nao subiu."
    exit 1
}

$resumo = @()
$falhou = $false
foreach ($versao in $Versoes) {
    $api = $versao.Split("-")[1]
    Write-Host "== $versao =="
    foreach ($v in $todas) {
        docker compose --profile $v rm -sf $v 2>&1 | Out-Null
    }
    & (Join-Path $PSScriptRoot "banco-resetar.ps1") 2>&1 | Out-Null
    docker compose --profile $versao up -d --build 2>&1 | Out-Null
    if (-not (Esperar-Porta)) {
        $resumo += "{0,-15} NAO SUBIU" -f $versao
        Write-Host $resumo[-1]
        $falhou = $true
        continue
    }
    Start-Sleep -Seconds 3
    $saida = docker compose --profile loadtest run --rm -T --entrypoint python locust verificar.py --api $api --host "http://${versao}:8080" --versao $versao 2>&1 | Out-String
    $codigo = $LASTEXITCODE
    $linhaFinal = ($saida -split "`r?`n" | Where-Object { $_ -like "RESULTADO*" } | Select-Object -Last 1)
    if ($codigo -ne 0 -or -not $linhaFinal) {
        $falhou = $true
        Write-Host $saida
        if (-not $linhaFinal) { $linhaFinal = "RESULTADO ${versao}: SEM RESPOSTA" }
    }
    $resumo += $linhaFinal
    Write-Host $linhaFinal
}

foreach ($v in $todas) {
    docker compose --profile $v rm -sf $v 2>&1 | Out-Null
}

Write-Host ""
Write-Host "RESUMO"
$resumo | ForEach-Object { Write-Host $_ }
if ($falhou) { exit 1 }
exit 0