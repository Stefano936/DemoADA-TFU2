# Demo TFU2 - Tácticas Arquitectónicas

Esta demo implementa **3 tácticas arquitectónicas específicas**:

1. **ROLLBACK** para disponibilidad (recuperación ante fallas)
2. **BINDING EN TIEMPO DE CONFIGURACIÓN** para modificabilidad
3. **BINDING EN TIEMPO DE EJECUCIÓN** para modificabilidad

## 🚀 Inicio Rápido

### Paso 1: Ubicarse en el directorio
```powershell
cd C:\Users\stuff\Desktop\DemoADA-TFU2\TFU2_Demo
```

### Paso 2: Levantar el sistema
```powershell
docker-compose up --build
```

### Paso 3: Verificar funcionamiento
- **API principal**: http://localhost:8080
- **Servicio de notificaciones**: http://localhost:8081

## 🎯 Tácticas Implementadas

### 1. 🔄 TÁCTICA: Rollback para Disponibilidad

**Objetivo**: Recuperación rápida ante fallas (< 1 minuto de interrupción)

```powershell
# Hacer rollback completo a versión estable
.\rollback.ps1

# Solo verificar estado sin cambios
.\rollback.ps1 -VerifyOnly
```

**Qué hace**:
- Crea backup automático del estado actual
- Revierte a configuración estable (`docker-compose.rollback.yaml`)
- Verifica que servicios estén funcionando
- Garantiza disponibilidad continua

### 2. ⚙️ TÁCTICA: Binding en Tiempo de Configuración

**Objetivo**: Modificar comportamiento sin recompilar código

La aplicación lee configuración desde `config.yaml` al iniciar:

```yaml
# Ejemplo: Cambiar estas opciones en config.yaml
feature_flags:
  enable_notifications: false  # Deshabilitar notificaciones
  maintenance_mode: true       # Activar modo mantenimiento

api:
  port: 8080                   # Cambiar puerto

logging:
  level: "DEBUG"               # Cambiar nivel de logging
```

**Beneficio**: Diferentes configuraciones sin tocar código fuente.

### 3. 🔃 TÁCTICA: Binding en Tiempo de Ejecución

**Objetivo**: Cambiar configuración sin reiniciar servicios

```bash
# 1. Modificar config.yaml con cualquier editor
# 2. Recargar configuración en tiempo real:
curl -X POST http://localhost:8080/reload-config

# 3. Ver cambios aplicados inmediatamente:
curl http://localhost:8080
```

**Beneficio**: Cero downtime para cambios de configuración.

## 📋 Endpoints de la Demo

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Estado general (demuestra binding de configuración) |
| `/health` | GET | Health check básico |
| `/config` | GET | Ver configuración actual |
| `/reload-config` | POST | **TÁCTICA 3**: Recargar config sin reiniciar |

## 🧪 Casos de Prueba

### Probar Táctica 1: Rollback
```powershell
# Simular falla y recuperación
docker-compose down
docker-compose -f docker-compose.rollback.yaml up -d
# ✅ Sistema recuperado en < 1 minuto
```

### Probar Táctica 2: Binding de Configuración
```bash
# 1. Editar config.yaml (cambiar maintenance_mode: true)
# 2. Reiniciar servicios
docker-compose restart
# 3. Verificar cambio
curl http://localhost:8080
# ✅ Respuesta de mantenimiento sin tocar código
```

### Probar Táctica 3: Binding en Tiempo de Ejecución
```bash
# 1. Cambiar config.yaml (enable_notifications: false)
# 2. Recargar SIN reiniciar
curl -Method POST http://localhost:8080/reload-config
# 3. Verificar cambio inmediato
curl http://localhost:8080
# ✅ Configuración aplicada sin downtime
```

## 🛠️ Solución de Problemas

### Si los contenedores no inician:
```powershell
docker-compose logs
docker-compose down
docker-compose up --build
```

### Si hay problemas con PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🚫 Para Detener Todo
```powershell
docker-compose down
```

---

## 📚 Resumen de Tácticas

| Táctica | Categoría | Beneficio | Implementación |
|---------|-----------|-----------|----------------|
| **Rollback** | Disponibilidad | Recuperación < 1 min | Script PowerShell + docker-compose.rollback.yaml |
| **Config Binding** | Modificabilidad | Sin recompilación | config.yaml leído al inicio |
| **Runtime Binding** | Modificabilidad | Sin reinicio | Endpoint /reload-config |

**Cada táctica resuelve un problema específico de arquitectura de software distribuido.**
