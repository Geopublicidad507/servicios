#!/usr/bin/env python3
"""
Script para crear todos los usuarios del sistema PH Control
"""
import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_mongo import init_mongo_db, User
from flask import Flask

def create_all_users():
    """Crear todos los usuarios del sistema"""
    app = Flask(__name__)
    app.config['MONGO_URI'] = 'mongodb+srv://geopublicidad507_db_user:Cdeg14650641*@consultor351.yv7gbsp.mongodb.net/miDB?retryWrites=true&w=majority'
    init_mongo_db(app)

    with app.app_context():
        print("START Creando usuarios del sistema...")
        
        # Lista de usuarios a crear
        users_data = [
            # Administradores Generales
            {
                'email': 'admin@phcontrol.com',
                'first_name': 'Administrador',
                'last_name': 'General',
                'role': 'admin_general',
                'password': 'admin123',
                'phone': '+507 6000-0001'
            },
            {
                'email': 'superadmin@phcontrol.com',
                'first_name': 'Super',
                'last_name': 'Administrador',
                'role': 'admin_general',
                'password': 'super123',
                'phone': '+507 6000-0002'
            },
            
            # Administradores de PH
            {
                'email': 'adminph1@phcontrol.com',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'role': 'admin_ph',
                'password': 'adminph123',
                'phone': '+507 6100-0001'
            },
            {
                'email': 'adminph2@phcontrol.com',
                'first_name': 'María',
                'last_name': 'González',
                'role': 'admin_ph',
                'password': 'adminph123',
                'phone': '+507 6100-0002'
            },
            {
                'email': 'adminph3@phcontrol.com',
                'first_name': 'José',
                'last_name': 'Martínez',
                'role': 'admin_ph',
                'password': 'adminph123',
                'phone': '+507 6100-0003'
            },
            
            # Residentes
            {
                'email': 'residente1@phcontrol.com',
                'first_name': 'Ana',
                'last_name': 'López',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0001'
            },
            {
                'email': 'residente2@phcontrol.com',
                'first_name': 'Pedro',
                'last_name': 'Sánchez',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0002'
            },
            {
                'email': 'residente3@phcontrol.com',
                'first_name': 'Laura',
                'last_name': 'Herrera',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0003'
            },
            {
                'email': 'residente4@phcontrol.com',
                'first_name': 'Miguel',
                'last_name': 'Torres',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0004'
            },
            {
                'email': 'residente5@phcontrol.com',
                'first_name': 'Carmen',
                'last_name': 'Vega',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0005'
            },
            {
                'email': 'residente6@phcontrol.com',
                'first_name': 'Roberto',
                'last_name': 'Morales',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0006'
            },
            {
                'email': 'residente7@phcontrol.com',
                'first_name': 'Patricia',
                'last_name': 'Jiménez',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0007'
            },
            {
                'email': 'residente8@phcontrol.com',
                'first_name': 'Fernando',
                'last_name': 'Castro',
                'role': 'resident',
                'password': 'resident123',
                'phone': '+507 6200-0008'
            },
            
            # Proveedores
            {
                'email': 'proveedor1@phcontrol.com',
                'first_name': 'Técnico',
                'last_name': 'Mantenimiento',
                'role': 'provider',
                'password': 'provider123',
                'phone': '+507 6300-0001'
            },
            {
                'email': 'proveedor2@phcontrol.com',
                'first_name': 'Empresa',
                'last_name': 'Limpieza',
                'role': 'provider',
                'password': 'provider123',
                'phone': '+507 6300-0002'
            },
            {
                'email': 'proveedor3@phcontrol.com',
                'first_name': 'Seguridad',
                'last_name': 'Integral',
                'role': 'provider',
                'password': 'provider123',
                'phone': '+507 6300-0003'
            },
            {
                'email': 'proveedor4@phcontrol.com',
                'first_name': 'Jardinería',
                'last_name': 'Verde',
                'role': 'provider',
                'password': 'provider123',
                'phone': '+507 6300-0004'
            },
            
            # Visitantes
            {
                'email': 'visitante1@phcontrol.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'role': 'visitor',
                'password': 'visitor123',
                'phone': '+507 6400-0001'
            },
            {
                'email': 'visitante2@phcontrol.com',
                'first_name': 'Sofia',
                'last_name': 'Ramírez',
                'role': 'visitor',
                'password': 'visitor123',
                'phone': '+507 6400-0002'
            }
        ]
        
        created_count = 0
        existing_count = 0
        
        for user_data in users_data:
            try:
                # Verificar si el usuario ya existe
                existing_user = User.objects.get(email=user_data['email'])
                print(f"OK Usuario ya existe: {user_data['email']}")
                existing_count += 1
            except User.DoesNotExist:
                # Crear nuevo usuario
                user = User(
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone=user_data.get('phone'),
                    role=user_data['role'],
                    is_active=True
                )
                user.set_password(user_data['password'])
                user.save()
                print(f"OK Usuario creado: {user_data['email']} ({user_data['role']})")
                created_count += 1
        
        print()
        print("CELEBRATION Creación de usuarios completada!")
        print("Resumen:")
        print(f"   USER Usuarios creados: {created_count}")
        print(f"   USER Usuarios existentes: {existing_count}")
        print(f"   USER Total usuarios: {User.objects.count()}")
        
        # Mostrar resumen por rol
        print()
        print("Usuarios por rol:")
        roles = ['admin_general', 'admin_ph', 'resident', 'provider', 'visitor']
        for role in roles:
            count = User.objects(role=role).count()
            print(f"   {role}: {count}")

if __name__ == '__main__':
    create_all_users()