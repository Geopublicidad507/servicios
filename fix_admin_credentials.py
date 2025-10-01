#!/usr/bin/env python3
"""
Script para verificar y corregir las credenciales del administrador
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

def fix_admin_credentials():
    """Verificar y corregir credenciales del administrador"""
    print("🔧 Verificando credenciales del administrador...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar usuario administrador
            admin = User.query.filter_by(email='admin@phcontrol.com').first()
            
            if not admin:
                print("❌ Usuario administrador no encontrado")
                print("🔧 Creando usuario administrador...")
                
                admin = User(
                    email='admin@phcontrol.com',
                    first_name='Administrador',
                    last_name='General',
                    role='admin_general',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuario administrador creado")
            else:
                print("✅ Usuario administrador encontrado")
                
                # Verificar contraseña
                if admin.check_password('admin123'):
                    print("✅ Contraseña correcta")
                else:
                    print("❌ Contraseña incorrecta, corrigiendo...")
                    admin.set_password('admin123')
                    db.session.commit()
                    print("✅ Contraseña corregida")
                
                # Verificar que esté activo
                if not admin.is_active:
                    print("❌ Usuario inactivo, activando...")
                    admin.is_active = True
                    db.session.commit()
                    print("✅ Usuario activado")
            
            # Verificar otros usuarios de prueba
            users_to_check = [
                ('adminph@phcontrol.com', 'admin123', 'admin_ph', 'Administrador', 'PH'),
                ('residente@phcontrol.com', 'resident123', 'resident', 'Usuario', 'Residente')
            ]
            
            for email, password, role, first_name, last_name in users_to_check:
                user = User.query.filter_by(email=email).first()
                if not user:
                    print(f"🔧 Creando usuario {email}...")
                    user = User(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        is_active=True
                    )
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                    print(f"✅ Usuario {email} creado")
                else:
                    # Verificar contraseña
                    if not user.check_password(password):
                        print(f"🔧 Corrigiendo contraseña para {email}...")
                        user.set_password(password)
                        db.session.commit()
                        print(f"✅ Contraseña corregida para {email}")
            
            print("✅ Verificación de credenciales completada")
            print("\n📋 Credenciales disponibles:")
            print("   Admin General: admin@phcontrol.com / admin123")
            print("   Admin PH: adminph@phcontrol.com / admin123")
            print("   Residente: residente@phcontrol.com / resident123")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verificando credenciales: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = fix_admin_credentials()
    sys.exit(0 if success else 1)