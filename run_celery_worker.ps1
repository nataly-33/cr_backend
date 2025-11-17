# Script para ejecutar Celery Worker en Windows (PowerShell)
# Uso: .\run_celery_worker.ps1

# Cambiar a la carpeta del script (importante para que Python encuentre el módulo 'config')
if ($PSScriptRoot) {
    Set-Location $PSScriptRoot
} else {
    Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

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

# Variables de entorno ya se cargan desde config/celery.py con python-dotenv
Write-Host "Variables de entorno se cargan desde .env via python-dotenv" -ForegroundColor Yellow

# Información
Write-Host "Configuración:" -ForegroundColor Cyan
Write-Host "  - Broker: redis://localhost:6379/0"
Write-Host "  - Backend: redis://localhost:6379/0"
Write-Host "  - Colas: celery, backups, notifications"
Write-Host "  - Pool: solo (optimizado para Windows)"
Write-Host ""

# Ejecutar worker con pool 'solo' para Windows (evita errores de multiprocessing)
celery -A config worker `
    --loglevel=info `
    --pool=solo `
    --queues=celery,backups,notifications `
    --time-limit=3600 `
    --soft-time-limit=3000
