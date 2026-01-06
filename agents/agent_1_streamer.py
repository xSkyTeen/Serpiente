import zmq
import time
from flask import Flask, Response
from flask_cors import CORS

# --- CONFIGURACIÓN FLASK ---
app = Flask(__name__)
CORS(app)

print("📺 [STREAMER] Iniciando servidor de video desacoplado...")

# Configurar ZMQ Subscriber
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")  # Se conecta al Detector
socket.setsockopt(zmq.SUBSCRIBE, b"")  # Suscribirse a todo


def generate_frames():
    """Recibe frames de ZMQ y los sirve por HTTP"""
    while True:
        try:
            # Recibir frame JPG comprimido (bloqueante pero rápido)
            frame_bytes = socket.recv()

            # Formato Multipart para streaming MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error stream: {e}")
            time.sleep(0.1)


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
def status():
    return {"status": "online", "source": "ZMQ"}


if __name__ == "__main__":
    # Corremos en el puerto 5001
    print("🚀 Streamer listo en http://localhost:5001/video_feed")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)