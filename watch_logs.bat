@echo off
REM Script para monitorear logs del backend en tiempo real

echo ========================================
echo Django Logs Monitor
echo ========================================
echo.
echo Monitoreando logs en tiempo real...
echo.

cd /d "d:\Universidad\Prácticos\Séptimo Semestre\Sistemas de Información II\Proyecto Rework\cr_backend"

echo Logs de Django:
echo.

:loop
if exist logs\django.log (
    powershell -Command "Get-Content 'logs\django.log' -Tail 20 -Wait"
) else (
    echo Esperando archivo de logs...
    timeout /t 2
    goto loop
)
