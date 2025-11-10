# Script para ejecutar Celery Worker en Windows (PowerShell)
# Uso: .\run_celery_worker.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Iniciando Celery Worker..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Asegúrate de tener Redis ejecutándose en puerto 6379" -ForegroundColor Yellow
Write-Host "Si no está corriendo, abre otra terminal y ejecuta:" -ForegroundColor Yellow
Write-Host "  redis-server" -ForegroundColor Magenta
Write-Host ""

# Activar entorno virtual si no está activado
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Información
Write-Host "Configuración:" -ForegroundColor Cyan
Write-Host "  - Broker: redis://localhost:6379/0"
Write-Host "  - Backend: redis://localhost:6379/0"
Write-Host "  - Colas: celery, backups, notifications"
Write-Host "  - Workers: 4"
Write-Host ""

# Ejecutar worker
celery -A config worker `
    --loglevel=info `
    --concurrency=4 `
    --queues=celery,backups,notifications `
    --time-limit=3600 `
    --soft-time-limit=3000
