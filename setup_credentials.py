#!/usr/bin/env python3
"""
Script de configuración inicial de credenciales
"""
import os
import sys
import getpass
from dotenv import load_dotenv
from flask import Flask
from models import db, User

# Cargar variables de entorno
load_dotenv()

def create_app():
    """Crear una instancia de la aplicación Flask"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ph_control.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def setup_admin_user():
    """Configurar usuario administrador con credenciales personalizadas"""
    print("🔧 Configuración inicial de usuario administrador")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            db.create_all()
            
            # Verificar si ya existe un administrador
            admin = User.query.filter_by(role='admin_general').first()
            
            if admin:
                print(f"✅ Ya existe un administrador: {admin.email}")
                response = input("¿Deseas actualizar las credenciales? (s/n): ").lower()
                if response != 's':
                    return True
            
            # Solicitar credenciales
            print("\n📝 Ingresa las credenciales del administrador:")
            email = input("Email: ").strip()
            
            if not email:
                email = "admin@phcontrol.com"
                print(f"Usando email por defecto: {email}")
            
            first_name = input("Nombre: ").strip() or "Administrador"
            last_name = input("Apellido: ").strip() or "General"
            
            # Solicitar contraseña de forma segura
            while True:
                password = getpass.getpass("Contraseña: ")
                if len(password) >= 6:
                    break
                print("❌ La contraseña debe tener al menos 6 caracteres")
            
            # Crear o actualizar usuario
            if admin:
                admin.email = email
                admin.first_name = first_name
                admin.last_name = last_name
                admin.set_password(password)
                admin.is_active = True
                print("✅ Usuario administrador actualizado")
            else:
                admin = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='admin_general',
                    is_active=True
                )
                admin.set_password(password)
                db.session.add(admin)
                print("✅ Usuario administrador creado")
            
            db.session.commit()
            
            print(f"\n🎉 Configuración completada!")
            print(f"📧 Email: {email}")
            print(f"👤 Nombre: {first_name} {last_name}")
            print(f"🔑 Contraseña: [configurada]")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en configuración: {e}")
            db.session.rollback()
            return False

def main():
    """Función principal"""
    print("🚀 Configuración inicial de PH Control")
    print("=" * 50)
    
    success = setup_admin_user()
    
    if success:
        print("\n✅ Configuración completada exitosamente")
        print("🌐 Puedes iniciar la aplicación con: python app.py")
    else:
        print("\n❌ Error en la configuración")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)