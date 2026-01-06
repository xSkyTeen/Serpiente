import time
import sys
import os
import math
from datetime import datetime, timezone

# Fix de rutas para el entorno local
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.database import DatabaseManager
except ImportError:
    # Mock para pruebas sin infraestructura
    class DatabaseManager:
        def get_client(self): return self

        def table(self, _): return self

        def select(self, _): return self

        def order(self, *args, **kwargs): return self

        def limit(self, _): return self

        def eq(self, *args, **kwargs): return self

        def maybe_single(self): return self

        def execute(self):
            class Res: data = [{"id": 1, "punto_medio_x": 280, "tiene_celular": False}]

            return Res()

        def update(self, _): return self

        def insert(self, _): return self


# --- MOTOR DE LÓGICA DIFUSA (FUZZY LOGIC CORE) ---

def trap_mf(x, a, b, c, d):
    """Función de pertenencia Trapezoidal"""
    return max(0, min((x - a) / (b - a) if b > a else 1, 1, (d - x) / (d - c) if d > c else 1))


def logic_fuzzy_risk(punto_x, line_x, vel, cel):
    """
    Motor de Inferencia Difusa Real (12 Reglas).
    Variables de Entrada:
    - dist_rel: Distancia del punto medio a la línea de seguridad (line_x - punto_x).
    - vel: Velocidad de aproximación (px/s).
    """
    dist_rel = line_x - punto_x

    # 1. FUZZIFICACIÓN: Definición de Conjuntos (Membership Functions)

    # Distancia (px)
    d_critica = trap_mf(dist_rel, -500, -500, 0, 30)  # Ya cruzó o está a nada
    d_peligro = trap_mf(dist_rel, 20, 50, 80, 120)  # En la zona naranja
    d_segura = trap_mf(dist_rel, 100, 200, 1000, 1000)  # Lejos

    # Velocidad (px/s) - Positivo es que se acerca a la línea
    v_asustado = trap_mf(vel, 60, 100, 1000, 1000)  # Viene volando
    v_normal = trap_mf(vel, 5, 20, 40, 60)  # Caminando normal
    v_quieto = trap_mf(vel, -15, -5, 5, 15)  # Parado o micro-movimientos
    v_se_va = trap_mf(vel, -1000, -1000, -30, -10)  # Se está alejando

    # 2. BASE DE REGLAS (Heurística de 12 Reglas)
    # Formato: (Grado de Verdad, Valor de Riesgo)

    reglas = [
        # Bloque: Distancia Crítica
        (min(d_critica, v_asustado), 100),  # Regla 1: Encima y rápido -> CATÁSTROFE
        (min(d_critica, v_normal), 98),  # Regla 2: Encima y normal -> PARADA YA
        (min(d_critica, v_quieto), 95),  # Regla 3: Encima y quieto -> RIESGO EXTREMO
        (min(d_critica, v_se_va), 80),  # Regla 4: Encima pero saliendo -> ALERTA MÁXIMA

        # Bloque: Distancia Peligro
        (min(d_peligro, v_asustado), 90),  # Regla 5: Cerca y volando -> PRE-PARADA
        (min(d_peligro, v_normal), 65),  # Regla 6: Cerca y normal -> ADVERTENCIA FUERTE
        (min(d_peligro, v_quieto), 40),  # Regla 7: Cerca y quieto -> MONITOREO
        (min(d_peligro, v_se_va), 20),  # Regla 8: Cerca pero saliendo -> BAJA ALERTA

        # Bloque: Distancia Segura
        (min(d_segura, v_asustado), 45),  # Regla 9: Lejos pero viene rápido -> OJO AHÍ
        (min(d_segura, v_normal), 15),  # Regla 10: Lejos y normal -> NOMINAL
        (min(d_segura, v_quieto), 5),  # Regla 11: Lejos y quieto -> TODO FINO
        (min(d_segura, v_se_va), 0)  # Regla 12: Lejos y se va -> RELAX TOTAL
    ]

    # 3. DEFUZZIFICACIÓN (Promedio Ponderado)
    numerador = sum(grado * riesgo for grado, riesgo in reglas)
    denominador = sum(grado for grado, _ in reglas)

    riesgo_base = (numerador / denominador) if denominador > 0 else 0

    # Modificador por Celular (Multiplicador Heurístico de Peligro)
    # Si tiene celular, el riesgo percibido sube un 40% porque no está atento
    if cel:
        riesgo_base = min(99.9, riesgo_base * 1.4)

    return riesgo_base


class AgentBrain:
    def __init__(self):
        self.db = DatabaseManager().get_client()
        self.last_processed_id = 0
        self.prev_dist_rel = None
        self.prev_time = None
        self.line_x = 300  # Debe coincidir con el VisionCore

        print("🧠 [CEREBRO] Inicializando Lógica Difusa V4.5 (12 Reglas)...")
        self.ensure_telemetry_row()

    def ensure_telemetry_row(self):
        try:
            res = self.db.table("telemetria_cerebro").select("id").eq("id", 1).execute()
            if not res.data:
                self.db.table("telemetria_cerebro").insert({
                    "id": 1, "riesgo_actual": 0.0, "estado_logico": "READY"
                }).execute()
        except Exception as e:
            print(f"⚠️ Error DB Init: {e}")

    def calcular_velocidad(self, dist_actual):
        """Calcula px/s. Positivo = Se acerca a la línea"""
        now = time.time()
        vel = 0.0
        if self.prev_dist_rel is not None and self.prev_time is not None:
            dt = now - self.prev_time
            if dt > 0.001:
                # Si la distancia relativa disminuye, es que se acerca
                # vel = (cambio de distancia) / tiempo
                vel = (self.prev_dist_rel - dist_actual) / dt

        self.prev_dist_rel = dist_actual
        self.prev_time = now
        return vel

    def run(self):
        print("🐍 [S.E.R.P.I.E.N.T.E.] Brain ONLINE | Lógica Difusa Activada")
        last_ui_update = 0

        while True:
            try:
                # 1. Obtener Percepción (Último punto medio detectado)
                sens_res = self.db.table("mundo_percepcion").select("*").order("id", desc=True).limit(1).execute()
                ctx_res = self.db.table("estado_maquina").select("*").eq("id", 1).maybe_single().execute()

                if sens_res.data and ctx_res.data:
                    p = sens_res.data[0]
                    c = ctx_res.data

                    # Extraer punto medio (ahora usamos la nueva columna)
                    punto_x = p.get('punto_medio_x', 0)
                    dist_rel = self.line_x - punto_x

                    # 2. Análisis Cinético
                    vel_px_s = self.calcular_velocidad(dist_rel)

                    # 3. Inferencia Difusa Real
                    riesgo = logic_fuzzy_risk(punto_x, self.line_x, vel_px_s, p['tiene_celular'])

                    # 4. Motor de Decisiones STRIPS (simplificado)
                    accion = None
                    msg = "OPERACIÓN NOMINAL"

                    if riesgo > 85:
                        accion = "PARADA_TOTAL"
                        msg = f"🚨 EMERGENCIA: Riesgo {riesgo:.1f}%"
                    elif riesgo > 40:
                        accion = "ADVERTENCIA"
                        msg = f"⚠️ ALERTA: Riesgo {riesgo:.1f}%"
                    elif p['tiene_celular']:
                        msg = "📱 DISTRACCIÓN DETECTADA"

                    # 5. Ejecutar Acción si es crítica
                    if accion and p['id'] > self.last_processed_id:
                        self.db.table("acciones_sistema").insert({
                            "accion": accion, "motivo": msg, "riesgo": riesgo
                        }).execute()
                        self.last_processed_id = p['id']

                        if accion == "PARADA_TOTAL":
                            self.db.table("estado_maquina").update({"estado_operativo": "STOP"}).eq("id", 1).execute()

                    # 6. Telemetría Sync
                    if time.time() - last_ui_update > 0.3:
                        self.db.table("telemetria_cerebro").update({
                            "riesgo_actual": float(riesgo),
                            "estado_logico": msg,
                            "ultimo_calculo": datetime.now(timezone.utc).isoformat()
                        }).eq("id", 1).execute()

                        color = "🔴" if riesgo > 70 else "🟡" if riesgo > 30 else "🟢"
                        print(
                            f"{color} [FUZZY] Riesgo: {riesgo:05.2f}% | Dist: {int(dist_rel)}px | Vel: {vel_px_s:+.1f}px/s")
                        last_ui_update = time.time()

            except Exception as e:
                print(f"❌ Error en Loop Cerebral: {e}")
                time.sleep(1)

            time.sleep(0.05)  # 20Hz para que la respuesta sea instantánea


if __name__ == "__main__":
    AgentBrain().run()