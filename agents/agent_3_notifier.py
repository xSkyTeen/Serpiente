import time
import requests
import os
import threading
import winsound
from core.database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

load_dotenv()


class AgentExecutor:
    def __init__(self):
        self.db = DatabaseManager().get_client()
        self.last_action_id = 0
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.manager_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        # Siren state
        self._siren_on = False
        self._siren_event = threading.Event()
        self._siren_thread = None

    def notificar_telegram(self, mensaje):
        if not self.telegram_token: return
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={"chat_id": self.chat_id, "text": mensaje})
            print("✈️ Telegram Enviado.")
        except Exception as e:
            print(f"❌ Error Telegram: {e}")

    def _read_riesgo(self):
        try:
            telem = self.db.table("telemetria_cerebro").select("riesgo_actual").eq("id", 1).maybe_single().execute().data
            if telem and isinstance(telem, dict) and 'riesgo_actual' in telem:
                return float(telem['riesgo_actual'])
        except Exception as e:
            print("⚠️ Error leyendo riesgo:", e)
        return None

    def _siren_worker(self, interval=1.0):
        print("🔔 Siren worker started")
        # Ruta al archivo de sonido
        sound_path = os.path.join(os.path.dirname(__file__), 'sounds', 'SonidoAlarma.wav')
        if not os.path.exists(sound_path):
            print(f"⚠️ Sound file not found: {sound_path} — usando salida por consola")
        try:
            while not self._siren_event.is_set():
                if os.path.exists(sound_path):
                    # Reproducir de forma asíncrona; se repetirá cada intervalo
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    print("🔊 SIRENA: ON")
                time.sleep(interval)
            # Al salir, detener cualquier sonido en reproducción
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        except Exception as e:
            print("⚠️ Error en siren worker:", e)
        print("🔕 Siren worker stopped")

    def siren_on(self):
        if self._siren_on:
            return
        self._siren_event.clear()
        self._siren_thread = threading.Thread(target=self._siren_worker, daemon=True)
        self._siren_thread.start()
        self._siren_on = True
        print("✅ Sirena ACTIVADA")

    def siren_off(self):
        if not self._siren_on:
            return
        self._siren_event.set()
        if self._siren_thread:
            self._siren_thread.join(timeout=2)
        self._siren_on = False
        print("✅ Sirena DESACTIVADA")

    def ejecutar_interlock(self):
        """Simula el corte de energía físico (Pantalla Roja)"""
        os.system('color 4f')  # Rojo Windows
        print("\n🛑🛑 INTERLOCK ACTIVADO: CORTE DE ENERGÍA 🛑🛑\n")
        time.sleep(2)
        os.system('color 07')  # Reset

    def emitir_sonido(self):
        """Simula sirena (Pantalla Amarilla)"""
        os.system('color 60')  # Amarillo Windows
        print("\n⚠️  ALERTA SONORA: PRECAUCIÓN  ⚠️\n")
        time.sleep(1)
        os.system('color 07')

    def run(self):
        print("🤖 [AGENTE 3] Ejecutor de Efectos Físicos Listo...")

        # Sincronización
        try:
            last = self.db.table("acciones_sistema").select("id").order("id", desc=True).limit(1).execute().data
            if last: self.last_action_id = last[0]['id']
        except:
            pass

        while True:
            # 1) Procesar acciones en cola (si las hay)
            try:
                accs = self.db.table("acciones_sistema").select("*").gt("id", self.last_action_id).execute().data
            except Exception:
                accs = []

            for act in accs or []:
                self.last_action_id = act['id']
                cmd = act['accion']
                print(f"⚙️ Procesando Orden: {cmd}")

                if cmd == "PARADA_TOTAL":
                    # Precondiciones según nivel de riesgo
                    riesgo_actual = self._read_riesgo()
                    # 1) Notificar SOLO si riesgo == 100
                    if riesgo_actual is not None and int(riesgo_actual) == 100:
                        try:
                            self.notificar_telegram(f"🚨 URGENTE: Parada de Planta.\nMotivo: {act['motivo']}\nRiesgo Calc: {act['riesgo']}")
                        except Exception:
                            pass
                    else:
                        print("ℹ️ PARADA_TOTAL recibida pero no se notifica: riesgo_actual != 100", riesgo_actual)

                    # 2) Activar sirena SOLO si riesgo > 90
                    if riesgo_actual is not None and riesgo_actual > 90:
                        try:
                            self.siren_on()
                            try:
                                self.notificar_telegram(f"🔊 Sirena activada por riesgo {riesgo_actual:.1f}%")
                            except Exception:
                                pass
                        except Exception as e:
                            print("❌ Error activando sirena:", e)
                    else:
                        print("ℹ️ No se activa sirena: riesgo_actual <= 90", riesgo_actual)

                    # 3) Ejecutar interlock siempre que llegue la orden (acción física)
                    try:
                        self.ejecutar_interlock()
                    except Exception as e:
                        print("❌ Error ejecutando interlock:", e)

                elif cmd == "ADVERTENCIA":
                    # Mantener comportamiento (sonido breve) y notificar
                    self.emitir_sonido()
                    try:
                        self.notificar_telegram(f"⚠️ ADVERTENCIA: {act.get('motivo','Usuario distraído')} | Riesgo: {act.get('riesgo',0):.1f}%")
                    except Exception:
                        pass

                elif cmd == "LOG":
                    print(f"✅ Auditoría Registrada: {act['motivo']}")

            # 2) Supervisar telemetría para control automático de sirena
            try:
                telem = self.db.table("telemetria_cerebro").select("riesgo_actual").eq("id", 1).maybe_single().execute().data
                riesgo = None
                if telem and isinstance(telem, dict) and 'riesgo_actual' in telem:
                    riesgo = float(telem['riesgo_actual'])
                if riesgo is not None:
                    # Encender sirena si peligro total
                    if riesgo >= 100 and not self._siren_on:
                        try:
                            self.notificar_telegram(f"🚨 Riesgo maximo detectado: {riesgo:.1f}% — activando sirena")
                        except Exception:
                            pass
                        try:
                            self.siren_on()
                        except Exception as e:
                            print("❌ Error encendiendo sirena por telemetría:", e)

                    # Apagar sirena cuando riesgo baja a <= 80
                    if riesgo <= 80 and self._siren_on:
                        try:
                            self.siren_off()
                        except Exception as e:
                            print("❌ Error apagando sirena por telemetría:", e)
                        try:
                            self.notificar_telegram(f"ℹ️ Riesgo reducido: {riesgo:.1f}% — sirena apagada")
                        except Exception:
                            pass
            except Exception as e:
                print("⚠️ Error leyendo telemetría:", e)

            time.sleep(0.5)


if __name__ == "__main__":
    AgentExecutor().run()