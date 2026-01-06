import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables desde .env (pip install python-dotenv)
load_dotenv()

class DatabaseManager:
    _instance = None

    def __new__(cls):
        """Implementación del patrón Singleton para no abrir 1000 conexiones"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("❌ Faltan credenciales de Supabase en .env")
            cls._instance.client: Client = create_client(url, key)
            print("✅ Conexión a Base de Datos: EXITOSA")
        return cls._instance

    def get_client(self):
        return self.client

# Uso rápido: db = DatabaseManager().get_client()