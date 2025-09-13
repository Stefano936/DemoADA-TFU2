### Paso 1: Descargar y ubicarse
```powershell
cd C:\Users\stuff\Desktop\DemoADA-TFU2\TFU2_Demo
```

### Paso 2: Levantar todo el sistema
```powershell
docker-compose up --build
```

Esto va a:
- Construir las imágenes de Docker para la API y el servicio de notificaciones
- Levantar Consul (nuestro service registry)
- Iniciar todos los servicios y conectarlos entre sí

**Tip**: La primera vez puede tardar unos minutos porque tiene que descargar las imágenes base.

### Paso 3: Verificar que todo funciona
Una vez que veas que los logs se calmaron, abrí tu navegador y visitá:

- **API principal**: http://localhost:8080 - Acá vas a ver la info del sistema
- **Consul UI**: http://localhost:8500/ui - Para ver qué servicios están registrados
- **Servicio de notificaciones**: http://localhost:8081 - Un servicio auxiliar

Si ves respuestas JSON en la API principal, ¡ya está todo funcionando! 🎉

## 🧪 Probando las tácticas

### Táctica 1: Rollback en acción
Supongamos que algo se rompe y necesitás volver atrás rápido:

```powershell
# Hacer rollback completo
.\rollback.ps1

# O solo verificar el estado sin hacer cambios
.\rollback.ps1 -VerifyOnly
```

El script va a:
- Hacer backup del estado actual
- Parar los servicios que están corriendo
- Levantar la versión "estable" del sistema
- Verificar que todo esté funcionando

### Táctica 2: Cambiar configuración sin parar nada
Abrí el archivo `config.yaml` con tu editor favorito y cambiá algo. Por ejemplo:

```yaml
feature_flags:
  enable_notifications: false  # cambiar a false
  maintenance_mode: true       # cambiar a true
```

Después, desde cualquier terminal:
```bash
# Recargar la configuración
curl -X POST http://localhost:8080/reload-config

# Ver cómo cambió el comportamiento
curl http://localhost:8080
```

¡Sin reiniciar nada! La app va a responder diferente según la nueva configuración.

### Táctica 3: Descubrimiento automático de servicios
```bash
# Ver qué servicios están registrados en Consul
curl http://localhost:8500/v1/catalog/services

# Hacer que la API busque automáticamente el servicio de notificaciones
curl http://localhost:8080/notify
```

La API va a buscar dinámicamente dónde está el servicio de notificaciones sin que nosotros le hayamos dicho la dirección.

## 📋 Endpoints útiles para probar

- `GET /` - Info general del sistema
- `GET /health` - Estado de salud de la API
- `GET /config` - Ver configuración completa (solo en modo debug)
- `POST /reload-config` - Recargar configuración sin reiniciar
- `GET /notify` - Probar descubrimiento de servicios

## 🛠️ Si algo no funciona

### Los contenedores no levantan
```powershell
# Ver qué está pasando
docker-compose logs

# Limpiar todo y empezar de nuevo
docker-compose down
docker-compose up --build
```

### Puertos ocupados
Si te dice que un puerto está ocupado, podés ver qué lo está usando:
```powershell
netstat -ano | findstr :8080
```

### Problemas con PowerShell
Si el script de rollback no funciona, puede ser por las políticas de ejecución:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🎯 ¿Qué demuestra cada táctica?

- **Rollback**: El sistema puede recuperarse de fallas automáticamente en menos de 1 minuto
- **Configuración**: Podés cambiar el comportamiento sin tocar código ni reiniciar
- **Descubrimiento**: Los servicios se encuentran solos, facilitando el scaling y la integración

## 🚫 Para parar todo
Cuando termines de probar:
```powershell
docker-compose down
```

Esto va a parar y limpiar todos los contenedores.

---

**¿Dudas?** Este README debería cubrir todo lo básico, pero si algo no está claro o no funciona como esperás, revisá los logs con `docker-compose logs` - ahí generalmente está la pista de qué está pasando.
