import subprocess
import time
import sys
import os

project_root = os.getcwd()
env = os.environ.copy()
env["PYTHONPATH"] = project_root
if sys.platform == "win32":
    env["PYTHONPATH"] = project_root + ";" + env.get("PYTHONPATH", "")

commands = [
    # 1. Backend Web
    [sys.executable, "backend/app.py"],

    # 2.A. Agente 1 PARTE A: Detector (YOLO + Cámara + ZMQ)
    [sys.executable, "agents/agent_1_detector.py"],

    # 2.B. Agente 1 PARTE B: Streamer (Flask + ZMQ)
    [sys.executable, "agents/agent_1_streamer.py"],

    # 3. Agente 2: Cerebro
    [sys.executable, "agents/agent_2_brain.py"],

    # 4. Agente 3: Ejecutor
    [sys.executable, "agents/agent_3_notifier.py"]
]

# ... (El resto del código de launch_system y stop_system queda IGUAL)
# Solo asegúrate de copiar el resto del archivo anterior o déjalo como estaba si ya lo tenías.
# Aquí repito la función launch para que no te pierdas:

processes = []


def launch_system():
    print(f"🚀 [SISTEMA INDUSTRIAL] Inicializando Arquitectura Desacoplada...")
    print(f"📂 Root: {project_root}")
    print("-------------------------------------------------------")

    for cmd in commands:
        try:
            p = subprocess.Popen(cmd, env=env, shell=False)
            processes.append(p)
            print(f"✅ Proceso Iniciado: {cmd[1]}")
            time.sleep(1.0)
        except Exception as e:
            print(f"❌ Error: {e}")

    print("-------------------------------------------------------")
    print("✨ SISTEMA 100% OPERATIVO. (Ctrl+C para salir)")


def stop_system():
    print("\n🛑 Apagando...")
    for p in processes:
        try:
            if sys.platform == "win32":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
            else:
                p.terminate()
        except:
            pass


if __name__ == "__main__":
    try:
        launch_system()
        while True: time.sleep(1)
    except KeyboardInterrupt:
        stop_system()