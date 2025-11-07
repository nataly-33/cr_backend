# Script para ejecutar Celery Flower (Monitor UI) en Windows (PowerShell)
# Uso: .\run_celery_flower.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Iniciando Celery Flower (Monitor)..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Accede a: http://localhost:5555" -ForegroundColor Green
Write-Host ""

# Activar entorno virtual si no está activado
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Información
Write-Host "Funcionalidades de Flower:" -ForegroundColor Cyan
Write-Host "  - Monitor de workers"
Write-Host "  - Historial de tareas"
Write-Host "  - Estadísticas en tiempo real"
Write-Host "  - Pool inspector"
Write-Host "  - Configuración de workers"
Write-Host ""

# Ejecutar flower
celery -A config flower `
    --broker=redis://localhost:6379/0 `
    --port=5555 `
    --loglevel=info
