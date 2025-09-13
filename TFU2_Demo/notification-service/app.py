from flask import Flask, jsonify, request
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SERVICE_NAME = "notification-service"
SERVICE_PORT = 8081

@app.route("/health")
def health():
    """Endpoint de salud básico"""
    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/")
def home():
    """Endpoint principal del servicio de notificaciones"""
    return jsonify({
        "service": "Notification Service",
        "version": "1.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/notify", methods=["POST"])
def send_notification():
    """Endpoint básico para enviar notificaciones"""
    try:
        data = request.get_json() or {}
        message = data.get("message", "Notificación de prueba")
        recipient = data.get("recipient", "sistema")
        
        logger.info(f"📬 Enviando notificación a {recipient}: {message}")
        
        notification_id = f"notif_{int(datetime.now().timestamp())}"
        
        response = {
            "status": "success",
            "notification_id": notification_id,
            "message": message,
            "recipient": recipient,
            "sent_at": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    logger.info(f"🚀 Iniciando {SERVICE_NAME} en puerto {SERVICE_PORT}")
    app.run(host="0.0.0.0", port=SERVICE_PORT, debug=False)
