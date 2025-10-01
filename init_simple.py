import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_database_connection():
    """Prueba simple de conexión a la base de datos"""
    try:
        # Obtener URL de la base de datos
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///ph_control.db')
        
        print(f"🔍 Probando conexión a: {db_url}")
        
        # Crear engine sin conectar
        engine = create_engine(db_url)
        
        # Intentar conectar
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Conexión exitosa a la base de datos")
            return True
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)