import os
import sys
from app import app
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

if __name__ == "__main__":
    try:
        # Obtener configuración
        port = int(os.environ.get('PORT', 5003))
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🚀 Iniciando PH Control en puerto {port}")
        print(f"🐛 Debug mode: {debug}")
        print(f"🌐 Accesible en: http://{host}:{port}")
        print("=" * 50)
        
        # Iniciar aplicación
        app.run(debug=debug, host=host, port=port, threaded=True)
        
    except Exception as e:
        print(f"❌ Error iniciando la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)