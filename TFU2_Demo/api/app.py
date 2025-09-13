from flask import Flask, jsonify, request
import yaml
import logging
from datetime import datetime

app = Flask(__name__)

# TÁCTICA 1: Binding en tiempo de configuración - Configuración externa
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Configurar logging basado en la configuración
log_level = getattr(logging, config['logging']['level'])
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_feature_enabled(feature_name):
    """TÁCTICA 1: Verifica feature flags desde configuración externa"""
    return config.get('feature_flags', {}).get(feature_name, False)

def get_service_info():
    """Obtiene información del servicio desde configuración"""
    return {
        "service_name": config['api']['service_name'],
        "version": "1.0",
        "environment": config['environment']['name'],
        "port": config['api']['port']
    }

@app.route("/")
def home():
    """Endpoint principal - demuestra binding de configuración"""
    logger.info("Solicitud recibida en endpoint principal")
    
    # TÁCTICA 1: Verificar modo de mantenimiento desde configuración
    if is_feature_enabled('maintenance_mode'):
        return jsonify({
            "status": "maintenance",
            "message": "Sistema en modo de mantenimiento",
            "timestamp": datetime.now().isoformat()
        }), 503
    
    response_data = {
        "message": "API Principal funcionando",
        "service_info": get_service_info(),
        "timestamp": datetime.now().isoformat(),
        "features_enabled": {k: v for k, v in config['feature_flags'].items() if v}
    }
    
    return jsonify(response_data)

@app.route("/health")
def health():
    """Endpoint de salud del servicio"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": get_service_info()
    })

@app.route("/config")
def show_config():
    """Endpoint para mostrar configuración actual"""
    return jsonify({
        "current_config": config,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/reload-config", methods=["POST"])
def reload_config():
    """TÁCTICA 2: Binding en tiempo de ejecución - Recarga configuración sin reiniciar"""
    global config
    
    try:
        with open("config.yaml", "r") as f:
            new_config = yaml.safe_load(f)
        
        config = new_config
        
        # Reconfigurar logging si cambió
        log_level = getattr(logging, config['logging']['level'])
        logging.getLogger().setLevel(log_level)
        
        logger.info("Configuración recargada exitosamente")
        return jsonify({
            "status": "success",
            "message": "Configuración recargada exitosamente",
            "timestamp": datetime.now().isoformat(),
            "new_features": {k: v for k, v in config['feature_flags'].items() if v}
        })
        
    except Exception as e:
        logger.error(f"Error al recargar configuración: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error al recargar configuración: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    # TÁCTICA 1: Usar configuración del archivo para puerto
    port = config.get('api', {}).get('port', 8080)
    
    logger.info(f"Iniciando aplicación en puerto {port}")
    logger.info(f"Entorno: {config['environment']['name']}")
    logger.info(f"Features habilitadas: {[k for k, v in config['feature_flags'].items() if v]}")
    
    app.run(host="0.0.0.0", port=port, debug=False)
