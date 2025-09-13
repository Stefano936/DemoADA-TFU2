from flask import Flask, jsonify, request
import requests
import yaml
import os
import time
import logging
from datetime import datetime
import threading

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración del servicio
SERVICE_NAME = "notify"
SERVICE_PORT = 8081
CONSUL_HOST = os.getenv("CONSUL_HOST", "registry")
CONSUL_PORT = os.getenv("CONSUL_PORT", "8500")
SERVICE_ID = f"{SERVICE_NAME}-{SERVICE_PORT}"

def register_with_consul():
    """Registra este servicio en Consul - Descubrimiento Dinámico"""
    consul_url = f"http://{CONSUL_HOST}:{CONSUL_PORT}"
    
    # Definir el servicio para registro
    service_definition = {
        "ID": SERVICE_ID,
        "Name": SERVICE_NAME,
        "Port": SERVICE_PORT,
        "Address": os.getenv("SERVICE_IP", "notification-service"),
        "Tags": ["notification", "messaging", "v1.0"],
        "Check": {
            "HTTP": f"http://notification-service:{SERVICE_PORT}/health",
            "Interval": "10s",
            "Timeout": "3s"
        }
    }
    
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt + 1}/{max_retries}: Registrando servicio en Consul...")
            response = requests.put(
                f"{consul_url}/v1/agent/service/register",
                json=service_definition,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Servicio {SERVICE_NAME} registrado exitosamente en Consul")
                logger.info(f"   - ID: {SERVICE_ID}")
                logger.info(f"   - Puerto: {SERVICE_PORT}")
                logger.info(f"   - Health Check: http://notification-service:{SERVICE_PORT}/health")
                return True
            else:
                logger.warning(f"❌ Error al registrar servicio. Status: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"❌ Error conectando con Consul (intento {attempt + 1}): {str(e)}")
            
        if attempt < max_retries - 1:
            logger.info(f"⏳ Reintentando en {retry_delay} segundos...")
            time.sleep(retry_delay)
    
    logger.error("❌ No se pudo registrar el servicio en Consul después de todos los intentos")
    return False

def deregister_from_consul():
    """Desregistra el servicio de Consul al apagar"""
    consul_url = f"http://{CONSUL_HOST}:{CONSUL_PORT}"
    
    try:
        response = requests.put(f"{consul_url}/v1/agent/service/deregister/{SERVICE_ID}")
        if response.status_code == 200:
            logger.info(f"✅ Servicio {SERVICE_ID} desregistrado de Consul")
        else:
            logger.warning(f"❌ Error al desregistrar servicio. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error al desregistrar servicio: {str(e)}")

def health_check_loop():
    """Mantiene el servicio saludable en Consul"""
    while True:
        try:
            time.sleep(30)  # Cada 30 segundos
            # Aquí podrías implementar verificaciones adicionales de salud
            logger.debug("Health check automático ejecutado")
        except Exception as e:
            logger.error(f"Error en health check loop: {str(e)}")

@app.route("/health")
def health():
    """Endpoint de salud para Consul"""
    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "service_id": SERVICE_ID,
        "timestamp": datetime.now().isoformat(),
        "uptime": "OK"
    })

@app.route("/")
def home():
    """Endpoint principal del servicio de notificaciones"""
    return jsonify({
        "service": "Notification Service",
        "version": "1.0",
        "status": "running",
        "endpoints": ["/notify", "/health", "/status"],
        "registered_in_consul": True,
        "service_id": SERVICE_ID,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/notify", methods=["POST"])
def send_notification():
    """Endpoint para enviar notificaciones"""
    try:
        data = request.get_json() or {}
        message = data.get("message", "Notificación de prueba")
        recipient = data.get("recipient", "sistema")
        
        logger.info(f"📬 Enviando notificación a {recipient}: {message}")
        
        # Simular envío de notificación
        notification_id = f"notif_{int(time.time())}"
        
        response = {
            "status": "success",
            "notification_id": notification_id,
            "message": message,
            "recipient": recipient,
            "sent_at": datetime.now().isoformat(),
            "service": SERVICE_NAME
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/status")
def status():
    """Estado del servicio y su registro en Consul"""
    consul_url = f"http://{CONSUL_HOST}:{CONSUL_PORT}"
    
    try:
        # Verificar registro en Consul
        response = requests.get(f"{consul_url}/v1/agent/service/{SERVICE_ID}")
        consul_registered = response.status_code == 200
        
        # Obtener información del servicio desde Consul
        if consul_registered:
            service_info = response.json()
        else:
            service_info = None
            
    except Exception as e:
        consul_registered = False
        service_info = None
        logger.warning(f"No se pudo verificar estado en Consul: {str(e)}")
    
    return jsonify({
        "service_name": SERVICE_NAME,
        "service_id": SERVICE_ID,
        "port": SERVICE_PORT,
        "consul_registered": consul_registered,
        "consul_service_info": service_info,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    logger.info("🚀 Iniciando Servicio de Notificaciones...")
    logger.info(f"   - Puerto: {SERVICE_PORT}")
    logger.info(f"   - Consul: {CONSUL_HOST}:{CONSUL_PORT}")
    
    # Registrar en Consul al iniciar
    registration_success = register_with_consul()
    
    if registration_success:
        # Iniciar health check en background
        health_thread = threading.Thread(target=health_check_loop, daemon=True)
        health_thread.start()
        
        # Configurar para desregistrar al salir
        import atexit
        atexit.register(deregister_from_consul)
    
    # Iniciar el servidor Flask
    logger.info("🌐 Servicio listo para recibir peticiones")
    app.run(host="0.0.0.0", port=SERVICE_PORT, debug=False)
