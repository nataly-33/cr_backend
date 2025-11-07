# Script para ejecutar Celery Beat en Windows (PowerShell)
# Uso: .\run_celery_beat.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Iniciando Celery Beat (Scheduler)..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Asegúrate de tener Redis ejecutándose en puerto 6379" -ForegroundColor Yellow
Write-Host "Asegúrate de tener ejecutando Celery Worker en otra terminal" -ForegroundColor Yellow
Write-Host ""

# Activar entorno virtual si no está activado
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Información
Write-Host "Configuración:" -ForegroundColor Cyan
Write-Host "  - Scheduler: Celery Beat"
Write-Host "  - Broker: redis://localhost:6379/0"
Write-Host "  - Tareas programadas:"
Write-Host "    * backup-sistema-diario (2:00 AM)"
Write-Host "    * limpiar-backups-vencidos (Domingo 3:00 AM)"
Write-Host "    * reintentar-notificaciones-fallidas (cada 6 horas)"
Write-Host "    * limpiar-notificaciones-antiguas (Domingo 4:00 AM)"
Write-Host ""

# Ejecutar beat
celery -A config beat `
    --loglevel=info `
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
