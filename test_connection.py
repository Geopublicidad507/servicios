import os
import sys
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_database_connection(max_retries=5, retry_interval=3):
    """Prueba la conexión a la base de datos con reintentos"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://phcontrol:phcontrol123@ph-database:5432/phcontrol_db')
    
    print(f"🔍 Probando conexión a: {db_url}")
    
    for attempt in range(max_retries):
        try:
            # Crear engine
            engine = create_engine(db_url)
            
            # Intentar conectar
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Conexión exitosa a la base de datos")
                print(f"📊 Versión de PostgreSQL: {version}")
                return True
                
        except Exception as e:
            print(f"❌ Intento {attempt + 1}/{max_retries} fallido: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Reintentando en {retry_interval} segundos...")
                time.sleep(retry_interval)
            else:
                print("❌ No se pudo conectar a la base de datos después de varios intentos")
                return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)