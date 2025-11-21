#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script para verificar la configuración de AWS Bedrock para Reportes AI
.DESCRIPTION
    Ejecuta validaciones completas de configuración y conexión a Bedrock
.EXAMPLE
    .\verify_bedrock_quick.ps1
#>

Write-Host "`n" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🔍 VERIFICACIÓN RÁPIDA AWS BEDROCK" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Verificar si estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Ejecuta este script desde cr_backend/" -ForegroundColor Red
    exit 1
}

# Verificar Python
Write-Host "1️⃣  Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar Django
Write-Host "`n2️⃣  Verificando Django y dependencias..." -ForegroundColor Yellow
$requirements = @("boto3", "django", "rest_framework")
foreach ($pkg in $requirements) {
    $result = python -c "import $pkg; print($pkg)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $pkg NO INSTALADO" -ForegroundColor Red
    }
}

# Verificar .env
Write-Host "`n3️⃣  Verificando archivo .env..." -ForegroundColor Yellow
if (Test-Path ".env.production") {
    $hasBedrockEnabled = Select-String -Path ".env.production" -Pattern "BEDROCK_ENABLED=True" -Quiet
    if ($hasBedrockEnabled) {
        Write-Host "   ✅ .env.production contiene BEDROCK_ENABLED=True" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  .env.production existe pero BEDROCK_ENABLED no está True" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  .env.production no encontrado (usando .env)" -ForegroundColor Yellow
}

# Ejecutar verificación Python
Write-Host "`n4️⃣  Ejecutando verificación de Bedrock..." -ForegroundColor Yellow
Write-Host "   (esto puede tardar 10-30 segundos)..." -ForegroundColor Gray

$pythonScript = @"
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

# Ejecutar verificación
try:
    exec(open('scripts/verify_bedrock_config.py').read())
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
"@

python -c $pythonScript

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host "✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Green
    Write-Host "`n🎉 Tu sistema está listo para usar AWS Bedrock`n" -ForegroundColor Green
} else {
    Write-Host "`n" -ForegroundColor Red
    Write-Host "=" * 70 -ForegroundColor Red
    Write-Host "❌ VERIFICACIÓN FALLÓ" -ForegroundColor Red
    Write-Host "=" * 70 -ForegroundColor Red
    Write-Host "`nRevisa los errores arriba y consulta:" -ForegroundColor Yellow
    Write-Host "  📖 GUIA_BEDROCK_REPORTES_AI.md`n" -ForegroundColor Yellow
    exit 1
}
