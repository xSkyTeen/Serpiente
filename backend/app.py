import os
import sys
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Fix de rutas para encontrar core
base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, '..'))
sys.path.append(project_root)

from core.database import DatabaseManager

app = Flask(__name__, static_folder=os.path.join(project_root, 'frontend'))
CORS(app)

db = DatabaseManager().get_client()


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/live')
def get_live_data():
    """Ruta de emergencia para jalar datos si el Realtime falla"""
    try:
        # Jalamos lo último de cada mesa
        telemetry = db.table("telemetria_cerebro").select("*").eq("id", 1).maybe_single().execute().data
        vision = db.table("mundo_percepcion").select("*").order("id", desc=True).limit(1).execute().data
        machine = db.table("estado_maquina").select("*").eq("id", 1).maybe_single().execute().data

        return jsonify({
            "success": True,
            "telemetry": telemetry,
            "vision": vision[0] if vision else None,
            "machine": machine
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)