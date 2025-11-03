# Script para monitorear logs del backend en tiempo real
# Uso: .\watch_logs.ps1

$logDir = "d:\Universidad\Prácticos\Séptimo Semestre\Sistemas de Información II\Proyecto Rework\cr_backend\logs"
$djangoLog = Join-Path $logDir "django.log"
$requestsLog = Join-Path $logDir "requests.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Django Logs Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoreando logs en tiempo real..." -ForegroundColor Green
Write-Host ""
Write-Host "Django Log: $djangoLog" -ForegroundColor Yellow
Write-Host "Requests Log: $requestsLog" -ForegroundColor Yellow
Write-Host ""

# Esperar a que exista el archivo
while (-not (Test-Path $djangoLog)) {
    Write-Host "Esperando archivo de logs..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

# Monitorear los logs
Write-Host "Logs comenzando a partir de ahora:" -ForegroundColor Green
Write-Host ""

Get-Content -Path $djangoLog -Wait -Tail 50

