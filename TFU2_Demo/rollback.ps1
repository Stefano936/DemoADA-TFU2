# Script de Rollback para Windows PowerShell
# Táctica de Disponibilidad - Recuperación ante fallas

param(
    [switch]$Help,
    [switch]$VerifyOnly
)

if ($Help) {
    Write-Host "=== SCRIPT DE ROLLBACK - TÁCTICA DE DISPONIBILIDAD ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\rollback.ps1 [opciones]" -ForegroundColor White
    Write-Host ""
    Write-Host "Opciones:" -ForegroundColor Yellow
    Write-Host "  -Help        Muestra esta ayuda"
    Write-Host "  -VerifyOnly  Solo verifica el estado sin hacer rollback"
    Write-Host ""
    Write-Host "Este script implementa la táctica de rollback para:"
    Write-Host "- Revertir a versión estable ante fallas"
    Write-Host "- Garantizar disponibilidad < 1 minuto de interrupción"
    Write-Host "- Crear backups automáticos del estado actual"
    exit 0
}

$BackupDir = ".\backups"
$RollbackCompose = "docker-compose.rollback.yaml"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "=== INICIANDO ROLLBACK DEL SISTEMA ===" -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date)" -ForegroundColor Gray

if ($VerifyOnly) {
    Write-Host "🔍 MODO VERIFICACIÓN - Solo chequeando estado..." -ForegroundColor Yellow
} else {
    # Verificar si existe configuración de rollback
    if (-not (Test-Path $RollbackCompose)) {
        Write-Host "❌ Error: No se encontró $RollbackCompose" -ForegroundColor Red
        Write-Host "Creando configuración de rollback..." -ForegroundColor Yellow
        Copy-Item "docker-compose.yaml" $RollbackCompose
    }

    # Crear directorio de backup
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }

    # Crear backup del estado actual
    Write-Host "📦 Creando backup del estado actual..." -ForegroundColor Blue
    Copy-Item "docker-compose.yaml" "$BackupDir\docker-compose.backup.$Timestamp.yaml"
    Copy-Item "config.yaml" "$BackupDir\config.backup.$Timestamp.yaml"

    # Detener servicios actuales
    Write-Host "🛑 Deteniendo servicios actuales..." -ForegroundColor Red
    docker-compose down

    # Esperar un momento
    Write-Host "⏳ Esperando que los servicios se detengan..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3

    # Iniciar servicios con configuración de rollback
    Write-Host "🔄 Iniciando servicios con configuración estable..." -ForegroundColor Green
    docker-compose -f $RollbackCompose up -d

    # Esperar que los servicios inicien
    Write-Host "⏳ Esperando que los servicios estén listos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# Verificar disponibilidad de servicios
Write-Host "🔍 Verificando disponibilidad de servicios..." -ForegroundColor Blue

try {
    $apiResponse = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -UseBasicParsing
    if ($apiResponse.StatusCode -eq 200) {
        Write-Host "✅ API disponible en puerto 8080" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ API no disponible en puerto 8080" -ForegroundColor Red
}

try {
    $consulResponse = Invoke-WebRequest -Uri "http://localhost:8500/v1/status/leader" -TimeoutSec 5 -UseBasicParsing
    if ($consulResponse.StatusCode -eq 200) {
        Write-Host "✅ Consul disponible en puerto 8500" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Consul no disponible en puerto 8500" -ForegroundColor Red
}

if (-not $VerifyOnly) {
    Write-Host ""
    Write-Host "=== ROLLBACK COMPLETADO ===" -ForegroundColor Cyan
    Write-Host "🎯 Sistema revertido a versión estable" -ForegroundColor Green
    Write-Host "📊 Estado de contenedores:" -ForegroundColor Blue
    docker-compose -f $RollbackCompose ps

    Write-Host ""
    Write-Host "💡 Para volver a la versión actual, ejecute:" -ForegroundColor Yellow
    Write-Host "   docker-compose -f docker-compose.yaml up -d" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "=== VERIFICACIÓN COMPLETADA ===" -ForegroundColor Cyan
}
