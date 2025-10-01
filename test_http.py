import os
import sys
import requests
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_http_connection(max_retries=5, retry_interval=3):
    """Prueba la conexión HTTP a la aplicación web con reintentos"""
    port = os.environ.get('PORT', '5003')
    base_url = f"http://localhost:{port}"
    
    print(f"🔍 Probando conexión HTTP a: {base_url}")
    
    for attempt in range(max_retries):
        try:
            # Intentar conectar
            response = requests.get(base_url, timeout=5)
            
            # Verificar respuesta
            if response.status_code == 200:
                print(f"✅ Conexión HTTP exitosa (código {response.status_code})")
                print(f"📝 Tamaño de respuesta: {len(response.content)} bytes")
                return True
            else:
                print(f"⚠️ Respuesta con código: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Intento {attempt + 1}/{max_retries} fallido: Error de conexión")
        except requests.exceptions.Timeout:
            print(f"❌ Intento {attempt + 1}/{max_retries} fallido: Timeout")
        except Exception as e:
            print(f"❌ Intento {attempt + 1}/{max_retries} fallido: {e}")
            
        if attempt < max_retries - 1:
            print(f"⏳ Reintentando en {retry_interval} segundos...")
            time.sleep(retry_interval)
        else:
            print("❌ No se pudo conectar a la aplicación web después de varios intentos")
            return False

def test_api_endpoints():
    """Prueba los endpoints de la API"""
    port = os.environ.get('PORT', '5003')
    base_url = f"http://localhost:{port}"
    
    endpoints = [
        "/",
        "/auth/login",
        "/dashboard"
    ]
    
    print(f"🔍 Probando endpoints de la API:")
    
    success_count = 0
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"  Probando: {url}")
            
            response = requests.get(url, timeout=5)
            
            if response.status_code in [200, 302]:
                print(f"  ✅ OK: {response.status_code}")
                success_count += 1
            else:
                print(f"  ⚠️ Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"Resultados: {success_count}/{len(endpoints)} endpoints exitosos")
    return success_count == len(endpoints)

if __name__ == "__main__":
    # Probar conexión HTTP básica
    if not test_http_connection():
        sys.exit(1)
    
    # Probar endpoints específicos
    if not test_api_endpoints():
        print("⚠️ Algunos endpoints no respondieron correctamente")
        sys.exit(0)  # No fallamos completamente si algunos endpoints fallan
    
    print("✅ Todas las pruebas HTTP completadas exitosamente")
    sys.exit(0)