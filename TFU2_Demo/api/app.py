from flask import Flask, jsonify
import yaml, os, requests

app = Flask(__name__)

# Cargar configuración desde archivo externo
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

@app.route("/")
def home():
    return jsonify({"message": "API Principal funcionando", "config": config})

@app.route("/notify")
def notify():
    # Descubrimiento dinámico: buscar servicio de notificaciones en registry
    registry_url = os.getenv("REGISTRY_URL", "http://registry:8500")
    try:
        r = requests.get(f"{registry_url}/v1/catalog/service/notify")
        services = r.json()
        if services:
            return jsonify({"status": "Notificación enviada", "service": services[0]["ServiceAddress"]})
        else:
            return jsonify({"status": "No hay servicio de notificaciones registrado"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
