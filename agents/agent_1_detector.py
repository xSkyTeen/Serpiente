import time
import cv2
import zmq
import base64
import sys
import os

# Fix de rutas para que no haya problemas con los imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ultralytics import YOLO
from core.database import DatabaseManager


class VisionCore:
    def __init__(self):
        print("🔌 [DETECTOR] Conectando a Base de Datos...")
        self.db = DatabaseManager().get_client()

        print("🧠 [DETECTOR] Cargando YOLOv8...")
        self.model = YOLO('yolov8n.pt')

        print("📡 [DETECTOR] Abriendo socket ZMQ (Puerto 5555)...")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5555")

        # Configuración de la línea de seguridad
        self.line_x = 300
        self.maintenance_mode = False

    def get_camera(self):
        # Intentamos abrir la cámara (índice 0 o 1)
        for index in [0, 1]:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                print(f"✅ Cámara encontrada en índice {index}")
                return cap
        return None

    def run(self):
        cap = self.get_camera()
        if not cap:
            print("❌ ERROR: No hay cámara. El detector no puede iniciar.")
            return

        print("👁️ [DETECTOR] Iniciando bucle de visión de alta velocidad...")
        last_state_check = 0
        last_db_update = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Fallo de lectura de cámara.")
                time.sleep(0.5)
                continue

            # Redimensionamos para que el YOLO vuele
            frame = cv2.resize(frame, (640, 480))

            frame = cv2.flip(frame, 1)

            # --- 1. SINCRONIZACIÓN DE ESTADO (BD) ---
            if time.time() - last_state_check > 2:
                try:
                    data = self.db.table("estado_maquina").select("modo_mantenimiento").eq("id",
                                                                                           1).maybe_single().execute()
                    if data and data.data:
                        self.maintenance_mode = data.data['modo_mantenimiento']
                except:
                    pass
                last_state_check = time.time()

            # --- 2. INFERENCIA CON YOLO ---
            # Detectamos personas (class 0) y celulares (class 67)
            results = self.model(frame, verbose=False, classes=[0, 67])

            # --- 3. DIBUJADO Y CÁLCULO DE CENTROS ---
            color_ui = (0, 255, 0) if self.maintenance_mode else (0, 0, 255)
            cv2.line(frame, (self.line_x, 0), (self.line_x, 480), color_ui, 2)

            detected = False
            punto_medio_x = 0
            has_phone = False

            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if cls == 67:  # Celular
                        has_phone = True
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                        cv2.putText(frame, "CELL", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                    if cls == 0:  # Persona
                        detected = True
                        # Calculamos el centro exacto del bounding box
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        punto_medio_x = cx  # Este es el valor que nos interesa

                        # Marcamos el punto medio con un círculo para visualización
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

                        # Lógica de color según posición del centro respecto a la línea
                        # (Asumiendo que cruzar hacia la derecha es peligro)
                        es_peligro = cx > self.line_x
                        col = (0, 0, 255) if es_peligro else (0, 255, 0)

                        cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
                        cv2.putText(frame, f"MID: {cx}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)

            # --- 4. ENVÍO A BD (Actualizando a Punto Medio) ---
            if detected and (time.time() - last_db_update > 0.8):
                try:
                    # Determinamos zonas basadas en el punto medio absoluto
                    # zona_peligro: el centro cruzó la línea
                    # zona_advertencia: el centro está a menos de 80px de la línea
                    distancia_relativa = self.line_x - punto_medio_x

                    self.db.table("mundo_percepcion").insert({
                        "hay_persona": True,
                        "punto_medio_x": punto_medio_x,  # REEMPLAZO DE DISTANCIA_LINEA
                        "tiene_celular": has_phone,
                        "zona_peligro": punto_medio_x > self.line_x,
                        "zona_advertencia": 0 < distancia_relativa < 80
                    }).execute()

                    print(f"📡 BD Sync | Punto Medio: {punto_medio_x}px | Cel: {has_phone}")
                    last_db_update = time.time()
                except Exception as e:
                    print(f"⚠️ Error BD: {e}")

            # --- 5. TRANSMISIÓN STREAMING (ZMQ) ---
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            self.socket.send(buffer)


if __name__ == "__main__":
    VisionCore().run()