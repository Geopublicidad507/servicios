#!/usr/bin/env python3
"""
Script para limpiar registros duplicados en MongoDB
"""
import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_mongo import init_mongo_db, User, Property, Unit, NotificationDoc, Expense, MaintenanceTask
from flask import Flask

def clean_duplicates():
    """Limpiar registros duplicados en MongoDB"""
    app = Flask(__name__)
    app.config['MONGO_URI'] = 'mongodb+srv://geopublicidad507_db_user:Cdeg14650641*@consultor351.yv7gbsp.mongodb.net/miDB?retryWrites=true&w=majority'
    init_mongo_db(app)

    with app.app_context():
        print("START Limpiando registros duplicados...")
        
        # Limpiar usuarios duplicados
        emails_seen = set()
        users_to_delete = []
        
        for user in User.objects.all():
            if user.email in emails_seen:
                users_to_delete.append(user)
                print(f"DUPLICATE Usuario duplicado encontrado: {user.email}")
            else:
                emails_seen.add(user.email)
        
        # Eliminar duplicados
        for user in users_to_delete:
            user.delete()
            print(f"OK Usuario duplicado eliminado: {user.email}")
        
        # Limpiar propiedades duplicadas
        codes_seen = set()
        properties_to_delete = []
        
        for prop in Property.objects.all():
            if prop.code in codes_seen:
                properties_to_delete.append(prop)
                print(f"DUPLICATE Propiedad duplicada encontrada: {prop.code}")
            else:
                codes_seen.add(prop.code)
        
        for prop in properties_to_delete:
            prop.delete()
            print(f"OK Propiedad duplicada eliminada: {prop.code}")
        
        print("OK Limpieza completada")
        print(f"   USER Usuarios restantes: {User.objects.count()}")
        print(f"   BUILDING Propiedades restantes: {Property.objects.count()}")

if __name__ == '__main__':
    clean_duplicates()