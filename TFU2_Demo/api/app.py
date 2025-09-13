from flask import Flask, jsonify, request
import yaml, os, requests
import logging
from datetime import datetime

app = Flask(__name__)

# Cargar configuración desde archivo externo - Binding en tiempo de configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Configurar logging basado en la configuración
log_level = getattr(logging, config['logging']['level'])
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_feature_enabled(feature_name):
    """Verifica si una funcionalidad está habilitada via configuración"""
    return config.get('feature_flags', {}).get(feature_name, False)

def get_service_info():
    """Obtiene información del servicio desde configuración"""
    return {
        "service_name": config['service_discovery']['consul']['service_name'],
        "version": "1.0",
        "environment": config['environment']['name'],
        "port": config['api']['port'],
        "debug_mode": config['environment']['debug']
    }

@app.route("/")
def home():
    """Endpoint principal - muestra configuración actual"""
    logger.info("Solicitud recibida en endpoint principal")
    
    # Verificar modo de mantenimiento
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
        "configuration_summary": {
            "database_max_connections": config['database']['max_connections'],
            "features_enabled": {k: v for k, v in config['feature_flags'].items() if v},
            "rate_limit_rpm": config['api']['rate_limit']['requests_per_minute'],
            "log_level": config['logging']['level']
        }
    }
    
    # Incluir configuración completa solo si está en modo debug
    if config['environment']['debug']:
        response_data["full_config"] = config
    
    return jsonify(response_data)

@app.route("/health")
def health():
    """Endpoint de salud del servicio"""
    logger.debug("Health check solicitado")
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": get_service_info(),
        "features": {
            "reports": is_feature_enabled('enable_reports'),
            "notifications": is_feature_enabled('enable_notifications'),
            "caching": is_feature_enabled('enable_caching'),
            "metrics": is_feature_enabled('enable_metrics')
        }
    }
    
    return jsonify(health_data)

@app.route("/notify")
def notify():
    """Descubrimiento dinámico de servicios - busca servicio de notificaciones en registry"""
    logger.info("Solicitud de notificación recibida")
    
    # Verificar si las notificaciones están habilitadas
    if not is_feature_enabled('enable_notifications'):
        logger.warning("Servicio de notificaciones deshabilitado por configuración")
        return jsonify({
            "status": "disabled",
            "message": "Servicio de notificaciones deshabilitado por configuración"
        }), 400
    
    # Descubrimiento dinámico: buscar servicio de notificaciones en registry
    registry_url = os.getenv("REGISTRY_URL", "http://registry:8500")
    consul_config = config['service_discovery']['consul']
    
    try:
        logger.info(f"Buscando servicios en {registry_url}")
        r = requests.get(
            f"{registry_url}/v1/catalog/service/notify", 
            timeout=config['external_services']['notification_service']['timeout_ms']/1000
        )
        services = r.json()
        
        if services:
            service = services[0]
            logger.info(f"Servicio de notificación encontrado: {service['ServiceAddress']}")
            return jsonify({
                "status": "Notificación enviada",
                "service_address": service["ServiceAddress"],
                "service_port": service["ServicePort"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning("No hay servicios de notificaciones registrados")
            return jsonify({
                "status": "No hay servicio de notificaciones registrado",
                "registry_checked": registry_url,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error al conectar con registry: {str(e)}")
        return jsonify({
            "error": str(e),
            "registry_url": registry_url,
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/config")
def show_config():
    """Endpoint para mostrar configuración actual (útil para debugging)"""
    if not config['environment']['debug']:
        return jsonify({"error": "Endpoint solo disponible en modo debug"}), 403
    
    return jsonify({
        "current_config": config,
        "config_file": "/app/config.yaml",
        "last_modified": datetime.now().isoformat()
    })

@app.route("/reload-config", methods=["POST"])
def reload_config():
    """Endpoint para recargar configuración sin reiniciar (demonstration)"""
    global config
    
    try:
        with open("config.yaml", "r") as f:
            new_config = yaml.safe_load(f)
        
        old_debug = config['environment']['debug']
        config = new_config
        
        # Reconfigurar logging si cambió
        if old_debug != config['environment']['debug']:
            log_level = getattr(logging, config['logging']['level'])
            logging.getLogger().setLevel(log_level)
        
        logger.info("Configuración recargada exitosamente")
        return jsonify({
            "status": "success",
            "message": "Configuración recargada exitosamente",
            "timestamp": datetime.now().isoformat(),
            "new_config_summary": {
                "environment": config['environment']['name'],
                "debug": config['environment']['debug'],
                "features_enabled": sum(1 for v in config['feature_flags'].values() if v)
            }
        })
        
    except Exception as e:
        logger.error(f"Error al recargar configuración: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error al recargar configuración: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    # Usar configuración del archivo para puerto y modo debug
    port = config.get('api', {}).get('port', 8080)
    debug_mode = config.get('environment', {}).get('debug', False)
    
    logger.info(f"Iniciando aplicación en puerto {port}, debug={debug_mode}")
    logger.info(f"Entorno: {config['environment']['name']}")
    logger.info(f"Features habilitadas: {[k for k, v in config['feature_flags'].items() if v]}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
