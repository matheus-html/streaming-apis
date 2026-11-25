param(
    [string[]]$Versoes = @("java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc"),
    [int]$Usuarios = 10,
    [int]$Segundos = 15
)

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$pasta = Join-Path (Get-Location) "analysis\results\tmp"
New-Item -ItemType Directory -Force $pasta | Out-Null

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

function Parar-Tudo {
    foreach ($v in "java-rest", "java-soap", "java-graphql", "java-grpc", "python-rest", "python-soap", "python-graphql", "python-grpc") {
        docker compose --profile $v rm -sf $v 2>&1 | Out-Null
    }
}

$resumo = @()
foreach ($versao in $Versoes) {
    $api = $versao.Split("-")[1]
    Write-Host "== $versao =="
    Parar-Tudo
    docker compose --profile $versao up -d --build 2>&1 | Out-Null
    if (-not (Esperar-Porta)) {
        $resumo += "{0,-15} nao subiu" -f $versao
        Write-Host $resumo[-1]
        continue
    }
    Start-Sleep -Seconds 5
    foreach ($fase in "consultas", "crud") {
        Remove-Item (Join-Path $pasta "rapido_*") -ErrorAction SilentlyContinue
        $saida = docker compose --profile loadtest run --rm -T locust -f "/app/${api}_${fase}.py" --host "http://${versao}:8080" --headless -u $Usuarios -r $Usuarios -t "${Segundos}s" --only-summary --csv /results/tmp/rapido 2>&1 | Out-String
        $arquivo = Join-Path $pasta "rapido_stats.csv"
        if (Test-Path $arquivo) {
            $total = Import-Csv $arquivo | Where-Object { $_.Name -eq "Aggregated" } | Select-Object -First 1
            $falhas = [int]$total."Failure Count"
            $status = if ($falhas -eq 0) { "OK    " } else { "FALHAS" }
            $linha = "{0,-15} {1,-9} {2} {3} req, {4} falhas, {5} req/s, mediana {6} ms" -f $versao, $fase, $status, $total."Request Count", $falhas, ([math]::Round([double]$total."Requests/s", 1)), $total."Median Response Time"
        } else {
            $linha = "{0,-15} {1,-9} SEM DADOS" -f $versao, $fase
            $saida -split "`n" | Select-Object -Last 15 | ForEach-Object { Write-Host "   $_" }
        }
        $resumo += $linha
        Write-Host $linha
    }
}
Parar-Tudo
Remove-Item (Join-Path $pasta "rapido_*") -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "===== RESUMO ====="
$resumo | ForEach-Object { Write-Host $_ }