#!/usr/bin/env python3
"""
Script de corrección rápida para PH Control
Ejecuta todas las correcciones necesarias para resolver problemas comunes
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def run_command(command, description):
    """Ejecutar un comando y mostrar el resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completado")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
        else:
            print(f"❌ Error en {description}")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Excepción en {description}: {e}")
        return False

def main():
    """Función principal de corrección"""
    print("🚀 Iniciando corrección rápida de PH Control...")
    print("=" * 50)
    
    # Lista de correcciones a ejecutar
    fixes = [
        ("python test_connection.py", "Probando conexión a base de datos"),
        ("python fix_admin_credentials.py", "Corrigiendo credenciales de administrador"),
        ("python test_credentials.py", "Verificando credenciales de usuarios"),
    ]
    
    success_count = 0
    total_fixes = len(fixes)
    
    for command, description in fixes:
        if run_command(command, description):
            success_count += 1
        print()
    
    # Resumen
    print("=" * 50)
    print(f"📊 Resumen: {success_count}/{total_fixes} correcciones exitosas")
    
    if success_count == total_fixes:
        print("✅ Todas las correcciones se aplicaron correctamente")
        print("\n📋 Credenciales disponibles:")
        print("   Admin General: admin@phcontrol.com / admin123")
        print("   Admin PH: adminph@phcontrol.com / admin123")
        print("   Residente: residente@phcontrol.com / resident123")
        print("\n🌐 Accede a la aplicación en: http://localhost:5003")
    else:
        print("⚠️  Algunas correcciones fallaron. Revisa los errores arriba.")
        print("📖 Consulta TROUBLESHOOTING.md para más información")
    
    return success_count == total_fixes

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)