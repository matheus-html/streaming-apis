param(
    [string]$Url = "http://python-rest:8080",
    [int[]]$Usuarios = @(25, 50, 100, 200, 400),
    [int]$Duracao = 40
)

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

foreach ($n in $Usuarios) {
    Write-Host "== $n usuarios =="
    $tempo = Measure-Command {
        docker compose --profile loadtest run --rm locust -f /app/rest_consultas.py --host $Url --headless -u $n -r $n -t "$($Duracao)s" --reset-stats --only-summary --csv "/results/piloto-$n" | Out-Host
    }
    Write-Host ("tempo total do nivel: {0:n1}s" -f $tempo.TotalSeconds)
}