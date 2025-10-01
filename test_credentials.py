#!/usr/bin/env python3
"""
Script para probar las credenciales de los usuarios
"""
import os
import sys
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

def test_credentials():
    """Probar las credenciales de los usuarios"""
    print("🔐 Probando credenciales de usuarios...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Credenciales a probar
            test_users = [
                ('admin@phcontrol.com', 'admin123', 'Administrador General'),
                ('adminph@phcontrol.com', 'admin123', 'Administrador PH'),
                ('residente@phcontrol.com', 'resident123', 'Residente')
            ]
            
            print(f"📊 Total de usuarios en la base de datos: {User.query.count()}")
            print()
            
            for email, password, description in test_users:
                user = User.query.filter_by(email=email).first()
                
                if user:
                    if user.check_password(password):
                        status = "✅ CORRECTO"
                        active_status = "✅ ACTIVO" if user.is_active else "❌ INACTIVO"
                    else:
                        status = "❌ INCORRECTO"
                        active_status = "✅ ACTIVO" if user.is_active else "❌ INACTIVO"
                    
                    print(f"{description}:")
                    print(f"  Email: {email}")
                    print(f"  Contraseña: {status}")
                    print(f"  Estado: {active_status}")
                    print(f"  Rol: {user.role}")
                    print(f"  Último login: {user.last_login or 'Nunca'}")
                else:
                    print(f"{description}:")
                    print(f"  Email: {email}")
                    print(f"  Estado: ❌ NO EXISTE")
                
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error probando credenciales: {e}")
            return False

if __name__ == "__main__":
    success = test_credentials()
    sys.exit(0 if success else 1)