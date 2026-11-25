param(
    [ValidateSet("rapido", "completo")]
    [string]$Modo = "rapido",
    [switch]$Retomar
)

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$raiz = Get-Location

Add-Type -Namespace Energia -Name Janela -MemberDefinition '[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint estado);'
[Energia.Janela]::SetThreadExecutionState(0x80000001) | Out-Null

$inicio = Get-Date
Start-Transcript -Path (Join-Path $raiz "analysis\rodar-tudo.log") -Append | Out-Null
Write-Host "Inicio: $inicio  modo: $Modo  retomar: $Retomar"

if (-not $Retomar) {
    $carimbo = Get-Date -Format "yyyyMMdd-HHmmss"
    $arquivo = Join-Path $raiz "analysis\results\anteriores\$carimbo"
    foreach ($fase in "consultas", "crud") {
        $origem = Join-Path $raiz "analysis\results\$fase"
        if (Test-Path $origem) {
            New-Item -ItemType Directory -Force (Join-Path $arquivo $fase) | Out-Null
            Move-Item (Join-Path $origem "*") (Join-Path $arquivo $fase) -Force
        }
    }
}

foreach ($fase in "consultas", "crud") {
    for ($tentativa = 1; $tentativa -le 3; $tentativa++) {
        Write-Host ""
        Write-Host "##### fase $fase, tentativa $tentativa #####"
        python -u loadtest\orquestrador.py --versoes todas --fase $fase --modo $Modo
        if ($LASTEXITCODE -eq 0) { break }
        Write-Host "falhou com codigo $LASTEXITCODE, tentando retomar em 30s"
        Start-Sleep -Seconds 30
    }
}

if (Test-Path (Join-Path $raiz "analysis\graficos.py")) {
    Write-Host ""
    Write-Host "##### graficos #####"
    python analysis\graficos.py
}

$minutos = [math]::Round(((Get-Date) - $inicio).TotalMinutes, 1)
Write-Host ""
Write-Host "TUDO CONCLUIDO em $minutos min"
[Energia.Janela]::SetThreadExecutionState(0x80000000) | Out-Null
Stop-Transcript | Out-Null