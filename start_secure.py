#!/usr/bin/env python3
"""
Script de inicio seguro para PH Control
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal de inicio"""
    print("🚀 Iniciando PH Control de forma segura...")
    print("=" * 50)
    
    # Verificar si existe configuración personalizada
    if not os.path.exists('.env'):
        print("⚠️  No se encontró archivo .env")
        print("🔧 Creando configuración básica...")
        
        # Crear .env básico
        with open('.env', 'w') as f:
            f.write("""# Configuración básica de PH Control
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
PORT=5003
DATABASE_URL=sqlite:///ph_control.db
CREATE_SAMPLE_DATA=true
""")
        print("✅ Archivo .env creado")
    
    # Verificar si necesita configuración inicial
    if not os.path.exists('ph_control.db'):
        print("🔧 Primera ejecución detectada")
        print("📝 Configurando usuario administrador...")
        
        # Ejecutar configuración inicial
        os.system('python setup_credentials.py')
    
    # Ejecutar correcciones rápidas
    print("🔧 Ejecutando correcciones...")
    os.system('python quick_fix.py')
    
    # Iniciar aplicación
    print("🌐 Iniciando aplicación...")
    os.system('python app.py')

if __name__ == "__main__":
    main()