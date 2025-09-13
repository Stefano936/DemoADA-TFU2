# TÁCTICA: Rollback para Disponibilidad (Recuperación ante fallas)
# Garantiza disponibilidad < 1 minuto de interrupción

param(
    [switch]$Help,
    [switch]$VerifyOnly
)

if ($Help) {
    Write-Host "=== TÁCTICA: ROLLBACK PARA DISPONIBILIDAD ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\rollback.ps1 [opciones]" -ForegroundColor White
    Write-Host ""
    Write-Host "Opciones:" -ForegroundColor Yellow
    Write-Host "  -Help        Muestra esta ayuda"
    Write-Host "  -VerifyOnly  Solo verifica el estado sin hacer rollback"
    Write-Host ""
    Write-Host "Esta táctica implementa:"
    Write-Host "- Revertir a versión estable ante fallas"
    Write-Host "- Garantizar disponibilidad < 1 minuto de interrupción"
    Write-Host "- Crear backups automáticos del estado actual"
    exit 0
}

$BackupDir = ".\backups"
$RollbackCompose = "docker-compose.rollback.yaml"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "=== TÁCTICA: ROLLBACK PARA DISPONIBILIDAD ===" -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date)" -ForegroundColor Gray

if ($VerifyOnly) {
    Write-Host "🔍 MODO VERIFICACIÓN - Solo chequeando estado..." -ForegroundColor Yellow
} else {
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
    $notifResponse = Invoke-WebRequest -Uri "http://localhost:8081" -TimeoutSec 5 -UseBasicParsing
    if ($notifResponse.StatusCode -eq 200) {
        Write-Host "✅ Servicio de notificaciones disponible en puerto 8081" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Servicio de notificaciones no disponible en puerto 8081" -ForegroundColor Red
}

if (-not $VerifyOnly) {
    Write-Host ""
    Write-Host "=== ROLLBACK COMPLETADO ===" -ForegroundColor Cyan
    Write-Host "🎯 Sistema revertido a versión estable" -ForegroundColor Green
    Write-Host "📊 Estado de contenedores:" -ForegroundColor Blue
    docker-compose -f $RollbackCompose ps

    Write-Host ""
    Write-Host "💡 Para volver a la versión actual, ejecute:" -ForegroundColor Yellow
    Write-Host "   docker-compose up -d" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "=== VERIFICACIÓN COMPLETADA ===" -ForegroundColor Cyan
}
